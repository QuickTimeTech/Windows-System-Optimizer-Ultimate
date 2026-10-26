# backend_engine.py
import os
import json
import shutil
import ctypes
from ctypes import wintypes
import socket
import platform
import subprocess
import winreg
from datetime import datetime
import psutil


class SHQUERYRBINFO(ctypes.Structure):
    """Windows API structure for querying Recycle Bin size and item count."""
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("i64Size", ctypes.c_longlong),
        ("i64NumItems", ctypes.c_longlong),
    ]


class SystemEngine:
    """Backend engine containing all Windows cleaning, RAM, and hardware functions."""

    @staticmethod
    def is_admin() -> bool:
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    @staticmethod
    def format_bytes(size: float) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    @staticmethod
    def get_recycle_bin_info() -> tuple[int, int]:
        """Returns (total_bytes, total_items) currently in the Windows Recycle Bin."""
        rb_info = SHQUERYRBINFO()
        rb_info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
        try:
            res = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rb_info))
            if res == 0:  # S_OK
                return int(rb_info.i64Size), int(rb_info.i64NumItems)
        except Exception:
            pass
        return 0, 0

    @staticmethod
    def get_target_folders(user_temp=True, win_temp=True, prefetch=False, chrome=True, edge=True) -> dict:
        targets = {}
        local_app = os.environ.get("LOCALAPPDATA", "")

        if user_temp:
            targets["User Temp"] = os.environ.get("TEMP")
        if win_temp:
            targets["Windows Temp"] = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Temp")
        if prefetch:
            targets["Prefetch"] = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Prefetch")
        if chrome and local_app:
            targets["Chrome Cache"] = os.path.join(local_app, r"Google\Chrome\User Data\Default\Cache\Cache_Data")
            targets["Brave Cache"] = os.path.join(
                local_app, r"BraveSoftware\Brave-Browser\User Data\Default\Cache\Cache_Data"
            )
        if edge and local_app:
            targets["Edge Cache"] = os.path.join(local_app, r"Microsoft\Edge\User Data\Default\Cache\Cache_Data")
        return targets

    @classmethod
    def scan_junk(cls, targets: dict, check_recycle: bool, log_callback):
        """Scans target folders AND the Recycle Bin (if checked) and logs reclaimable space."""
        log_callback("\n--- Starting Deep System Scan ---")
        total_bytes = 0
        total_files = 0

        for name, folder in targets.items():
            if not folder or not os.path.exists(folder):
                continue
            folder_bytes = 0
            folder_files = 0
            try:
                for root, _, files in os.walk(folder):
                    for f in files:
                        try:
                            folder_bytes += os.path.getsize(os.path.join(root, f))
                            folder_files += 1
                        except OSError:
                            continue
                total_bytes += folder_bytes
                total_files += folder_files
                log_callback(f"[*] {name}: {folder_files} files ({cls.format_bytes(folder_bytes)})")
            except PermissionError:
                log_callback(f"[!] {name}: Access Denied (Run as Admin)")

        if check_recycle:
            rb_bytes, rb_items = cls.get_recycle_bin_info()
            total_bytes += rb_bytes
            total_files += rb_items
            log_callback(f"[*] Recycle Bin: {rb_items} items ({cls.format_bytes(rb_bytes)})")

        log_callback(f"=== Scan Complete: {total_files} items ({cls.format_bytes(total_bytes)}) reclaimable ===")

    @classmethod
    def clean_junk(cls, targets: dict, empty_recycle: bool, log_callback):
        """Deletes junk files and optionally empties the Recycle Bin (counting its freed space)."""
        log_callback("\n--- Starting System Cleanup ---")
        freed_bytes = 0
        deleted_count = 0
        skipped_count = 0

        for name, folder in targets.items():
            if not folder or not os.path.exists(folder):
                continue
            log_callback(f"Cleaning {name}...")
            try:
                for item in os.listdir(folder):
                    item_path = os.path.join(folder, item)
                    try:
                        if os.path.isfile(item_path) or os.path.islink(item_path):
                            size = os.path.getsize(item_path)
                            os.unlink(item_path)
                            freed_bytes += size
                            deleted_count += 1
                        elif os.path.isdir(item_path):
                            dir_size = sum(
                                os.path.getsize(os.path.join(r, f))
                                for r, _, files in os.walk(item_path)
                                for f in files
                                if os.path.exists(os.path.join(r, f))
                            )
                            shutil.rmtree(item_path)
                            freed_bytes += dir_size
                            deleted_count += 1
                    except Exception:
                        skipped_count += 1
            except PermissionError:
                log_callback(f"[!] Access Denied to {name}. Try running as Admin.")

        if empty_recycle:
            log_callback("Emptying Recycle Bin...")
            rb_bytes, rb_items = cls.get_recycle_bin_info()
            if rb_items > 0 or rb_bytes > 0:
                try:
                    res = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
                    if res == 0:
                        freed_bytes += rb_bytes
                        deleted_count += rb_items
                        log_callback(f"[+] Recycle Bin emptied ({cls.format_bytes(rb_bytes)} freed).")
                    else:
                        log_callback("[-] Could not empty Recycle Bin.")
                except Exception as e:
                    log_callback(f"[!] Recycle Bin error: {e}")
            else:
                log_callback("[-] Recycle Bin is already empty.")

        log_callback(
            f"=== Cleanup Finished! Freed {cls.format_bytes(freed_bytes)} "
            f"({deleted_count} removed, {skipped_count} active skipped) ==="
        )

    @classmethod
    def optimize_ram(cls, log_callback):
        log_callback("\n--- Starting RAM Optimization ---")
        mem_before = psutil.virtual_memory().available
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_SET_QUOTA = 0x0100
        trimmed = 0

        for proc in psutil.process_iter(["pid"]):
            pid = proc.info["pid"]
            if pid in (0, 4):
                continue
            handle = None
            try:
                handle = ctypes.windll.kernel32.OpenProcess(
                    PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA, False, pid
                )
                if handle and ctypes.windll.psapi.EmptyWorkingSet(handle) != 0:
                    trimmed += 1
            except Exception:
                pass
            finally:
                if handle:
                    ctypes.windll.kernel32.CloseHandle(handle)

        mem_after = psutil.virtual_memory().available
        freed_ram = max(0, mem_after - mem_before)
        log_callback(f"[*] Trimmed memory working sets for {trimmed} processes.")
        log_callback(f"=== RAM Boost Complete! Freed {cls.format_bytes(freed_ram)} ===")

    @staticmethod
    def flush_dns(log_callback):
        log_callback("\n--- Flushing Windows DNS Cache ---")
        try:
            subprocess.run(["ipconfig", "/flushdns"], creationflags=subprocess.CREATE_NO_WINDOW, check=True)
            log_callback("[+] Successfully flushed the DNS Resolver Cache.")
        except Exception as e:
            log_callback(f"[!] Failed to flush DNS: {e}")

    @staticmethod
    def get_top_processes(limit=15):
        processes = []
        for p in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                mem_mb = p.info["memory_info"].rss / (1024 * 1024)
                if p.info["pid"] not in (0, 4):
                    processes.append((p.info["pid"], p.info["name"], mem_mb))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        processes.sort(key=lambda x: x[2], reverse=True)
        return processes[:limit]

    @staticmethod
    def get_startup_apps():
        startup_items = []
        reg_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "Current User"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "Local Machine"),
        ]
        for hive, path, scope in reg_paths:
            try:
                with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as key:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup_items.append((name, value, scope))
                            i += 1
                        except OSError:
                            break
            except OSError:
                continue
        return startup_items

    @staticmethod
    def delete_startup_app(name: str, scope: str) -> tuple[bool, str]:
        """Removes an application from Windows Registry Run startup keys."""
        hive = winreg.HKEY_CURRENT_USER if scope == "Current User" else winreg.HKEY_LOCAL_MACHINE
        path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
            return True, f"Removed '{name}' from {scope} startup."
        except PermissionError:
            return False, f"Access Denied removing '{name}' (Run as Administrator)."
        except OSError as e:
            return False, f"Could not remove '{name}': {e}"

    @staticmethod
    def decode_ddr_type(smbios_code: int) -> str:
        """Maps Windows SMBIOSMemoryType integer codes to DDR generation names."""
        ddr_map = {
            20: "DDR",
            21: "DDR2",
            24: "DDR3",
            26: "DDR4",
            29: "LPDDR3",
            30: "LPDDR4",
            34: "DDR5",
            35: "LPDDR5",
        }
        return ddr_map.get(smbios_code, "DRAM")

    @staticmethod
    def get_wmi_hardware_info() -> dict:
        """Fetches CPU, Motherboard, BIOS, GPU, and physical RAM sticks in one PowerShell CIM call."""
        ps_script = (
            "$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1 "
            "Name, Manufacturer, MaxClockSpeed, SocketDesignation, L2CacheSize, L3CacheSize; "
            "$board = Get-CimInstance Win32_BaseBoard | Select-Object -First 1 "
            "Manufacturer, Product, SerialNumber, Version; "
            "$bios = Get-CimInstance Win32_BIOS | Select-Object -First 1 "
            "Manufacturer, SMBIOSBIOSVersion, ReleaseDate; "
            "$gpu = @(Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, AdapterRAM); "
            "$ram = @(Get-CimInstance Win32_PhysicalMemory | Select-Object "
            "BankLabel, DeviceLocator, Capacity, Speed, ConfiguredClockSpeed, Manufacturer, PartNumber, SMBIOSMemoryType); "
            "$memArray = Get-CimInstance Win32_PhysicalMemoryArray | Select-Object -First 1 MemoryDevices; "
            "@{cpu=$cpu; board=$board; bios=$bios; gpu=$gpu; ram=$ram; memArray=$memArray} | ConvertTo-Json -Compress"
        )
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_script],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=6,
            ).strip()
            return json.loads(out) if out else {}
        except Exception:
            return {}

    @classmethod
    def get_detailed_specs(cls):
        uname = platform.uname()
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        net = psutil.net_io_counters()
        boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M")
        cpu_freq = psutil.cpu_freq()

        wmi = cls.get_wmi_hardware_info()
        cpu_wmi = wmi.get("cpu") or {}
        board_wmi = wmi.get("board") or {}
        bios_wmi = wmi.get("bios") or {}
        gpu_wmi = wmi.get("gpu") or []
        ram_wmi = wmi.get("ram") or []
        mem_array_wmi = wmi.get("memArray") or {}

        if isinstance(gpu_wmi, dict):
            gpu_wmi = [gpu_wmi]
        if isinstance(ram_wmi, dict):
            ram_wmi = [ram_wmi]

        # 1. Format CPU fields
        cpu_name = (cpu_wmi.get("Name") or uname.processor or "Windows x64 Processor").strip()
        cpu_socket = cpu_wmi.get("SocketDesignation") or "Standard Socket"
        max_clock = cpu_wmi.get("MaxClockSpeed")
        cur_clock = f"{cpu_freq.current:.0f} MHz" if cpu_freq else (f"{max_clock} MHz" if max_clock else "N/A")
        l2_kb = cpu_wmi.get("L2CacheSize") or 0
        l3_kb = cpu_wmi.get("L3CacheSize") or 0
        cache_str = f"L2: {l2_kb / 1024:.1f} MB | L3: {l3_kb / 1024:.1f} MB" if (l2_kb or l3_kb) else "Integrated"

        # 2. Format Motherboard & BIOS fields
        mb_vendor = board_wmi.get("Manufacturer") or "OEM Manufacturer"
        mb_model = board_wmi.get("Product") or "System Board"
        mb_serial = board_wmi.get("SerialNumber") or "Default"
        bios_ver = bios_wmi.get("SMBIOSBIOSVersion") or "System BIOS"
        bios_vendor = bios_wmi.get("Manufacturer") or "OEM"

        # 3. Format Physical RAM Sticks & Slots
        total_slots = mem_array_wmi.get("MemoryDevices") or len(ram_wmi) or 2
        used_slots = len(ram_wmi)

        ram_card_info = {
            "Total Installed": f"{cls.format_bytes(mem.total)} ({100 - mem.percent:.0f}% Available)",
            "DIMM Slots Used": f"{used_slots} of {total_slots} Slots Populated",
        }

        if ram_wmi:
            first_type_code = int(ram_wmi[0].get("SMBIOSMemoryType") or 0)
            ddr_gen = cls.decode_ddr_type(first_type_code)

            for idx, stick in enumerate(ram_wmi, start=1):
                cap_bytes = int(stick.get("Capacity") or 0)
                cap_str = cls.format_bytes(cap_bytes) if cap_bytes else "Unknown"
                speed = stick.get("ConfiguredClockSpeed") or stick.get("Speed") or "N/A"
                vendor = (stick.get("Manufacturer") or "OEM").strip()
                part = (stick.get("PartNumber") or "").strip()
                locator = (stick.get("DeviceLocator") or stick.get("BankLabel") or f"Slot {idx}").strip()

                stick_desc = f"{cap_str} {ddr_gen} @ {speed} MHz ({vendor}"
                if part and part.lower() != "unknown":
                    stick_desc += f" {part}"
                stick_desc += ")"

                ram_card_info[f"Stick #{idx} [{locator}]"] = stick_desc
        else:
            ram_card_info["Memory Modules"] = "Standard System Memory"

        ram_card_info["Pagefile / Swap"] = f"{cls.format_bytes(swap.used)} / {cls.format_bytes(swap.total)}"

        # 4. Format GPU fields
        if gpu_wmi:
            gpu_names = ", ".join([g.get("Name", "GPU").strip() for g in gpu_wmi if g.get("Name")])
            gpu_driver = gpu_wmi[0].get("DriverVersion") or "Standard"
        else:
            gpu_names = "Standard Display Adapter"
            gpu_driver = "Windows Default"

        # 5. Battery Status
        battery = psutil.sensors_battery()
        bat_status = (
            f"{battery.percent:.0f}% ({'Charging' if battery.power_plugged else 'On Battery'})"
            if battery
            else "Desktop / AC Power"
        )

        # 6. Local IP & Disks
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = "127.0.0.1"

        disks_info = {}
        for part in psutil.disk_partitions(all=False):
            if "cdrom" in part.opts or not part.fstype:
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks_info[f"Drive {part.device} ({part.fstype})"] = (
                    f"{cls.format_bytes(usage.used)} / {cls.format_bytes(usage.total)} ({usage.percent}%)"
                )
            except PermissionError:
                continue

        return {
            "Processor (CPU)": {
                "Model": cpu_name,
                "Cores / Threads": f"{psutil.cpu_count(logical=False)} Cores / {psutil.cpu_count(logical=True)} Threads",
                "Socket": cpu_socket,
                "Clock Speed": cur_clock,
                "CPU Cache": cache_str,
            },
            "Motherboard & BIOS": {
                "Manufacturer": mb_vendor,
                "Board Model": mb_model,
                "BIOS Version": f"{bios_ver} ({bios_vendor})",
                "Serial Number": mb_serial,
                "Architecture": uname.machine,
            },
            "Physical Memory (RAM Sticks)": ram_card_info,
            "Graphics & Display": {
                "GPU Model": gpu_names,
                "Driver Version": gpu_driver,
                "System Uptime": f"Since {boot_time}",
                "Power Status": bat_status,
            },
            "Operating System & Network": {
                "OS": f"{uname.system} {uname.release} (Build {uname.version})",
                "PC Name": uname.node,
                "Local IPv4": local_ip,
                "Network Traffic": f"↑ {cls.format_bytes(net.bytes_sent)} | ↓ {cls.format_bytes(net.bytes_recv)}",
            },
            "Storage Partitions": disks_info if disks_info else {"C:\\": "Online"},
        }