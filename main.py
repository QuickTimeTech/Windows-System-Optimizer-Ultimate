# main.py
import os
import re
import sys
import gc
import json
import socket
import shutil
import ctypes
import importlib
import threading
import subprocess
import multiprocessing
from datetime import datetime
import psutil
import customtkinter as ctk

from backend_engine import SystemEngine

try:
    from icon_generator import ensure_app_icon
except ImportError:
    def ensure_app_icon(path="app_icon.ico"):
        return path

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def get_resource_path(relative_path: str) -> str:
    """Returns the correct file path for both normal Python and PyInstaller --onefile executables."""
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)


def elevate_to_admin():
    """If not running as Administrator, prompts Windows UAC and relaunches the script elevated."""
    if SystemEngine.is_admin():
        return

    try:
        if getattr(sys, "frozen", False):
            executable = sys.executable
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        else:
            executable = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            params = " ".join([f'"{script_path}"'] + [f'"{arg}"' for arg in sys.argv[1:]])

        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
        if int(ret) > 32:
            sys.exit(0)
    except Exception:
        pass


class MissingModuleFallbackView(ctk.CTkFrame):
    """Displayed if a module file hasn't been created in the project folder yet."""

    def __init__(self, master, module_filename: str, class_name: str, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        card = ctk.CTkFrame(self)
        card.pack(expand=True, fill="both", padx=40, pady=40)

        ctk.CTkLabel(
            card,
            text=f"🧩 Module File Not Found: {module_filename}.py",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#E67E22",
        ).pack(pady=(60, 10))

        ctk.CTkLabel(
            card,
            text=f"Save '{module_filename}.py' (containing '{class_name}') into your system-cleanr folder\nand restart the app to activate this tab.",
            font=ctk.CTkFont(size=13),
            text_color="lightgray",
        ).pack(pady=10)


def safe_load_view(master, module_name: str, class_name: str):
    """Safely imports and instantiates a modular view class without crashing if the file is missing."""
    try:
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
        return cls(master)
    except Exception:
        return MissingModuleFallbackView(master, module_name, class_name)


class PCCleanerUltimate(ctk.CTk):
    def __init__(self):
        super().__init__()

        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PCOptimizer.Ultimate.Suite.Portable")
        except Exception:
            pass

        self.title("Windows System Optimizer Ultimate - IT Maintenance Suite")
        self.geometry("1280x830")
        self.minsize(1140, 720)

        icon_file = get_resource_path("app_icon.ico")
        ensure_app_icon(icon_file)
        if os.path.exists(icon_file):
            try:
                self.iconbitmap(icon_file)
            except Exception:
                pass

        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Lightweight Telemetry, Laptop Optimus Guard & Drive State
        self.has_nvidia_smi = shutil.which("nvidia-smi") is not None
        self.is_laptop = psutil.sensors_battery() is not None
        self.live_gpu_pct = 0.0
        self.live_gpu_temp = ""
        self._gpu_poll_busy = False
        self._gpu_tick_counter = 0

        self.available_drives = self._get_mounted_drives()
        self.current_drive_idx = 0

        # ==========================================
        # SIDEBAR NAVIGATION (CATEGORIZED & ALIGNED)
        # ==========================================
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self.sidebar, text="⚡ PC OPTIMIZER", font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(16, 2))

        admin_text = "🔰 Admin Mode: ON" if SystemEngine.is_admin() else "⚠️ Standard User Mode"
        admin_color = "#2FA572" if SystemEngine.is_admin() else "#E67E22"
        ctk.CTkLabel(
            self.sidebar, text=admin_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=admin_color
        ).grid(row=1, column=0, padx=20, pady=(0, 8))

        # Scrollable Sidebar Menu Organized by Category (34 Tools)
        self.nav_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", width=230)
        self.nav_scroll.grid(row=2, column=0, padx=6, pady=4, sticky="nsew")

        self.nav_buttons = []

        # --- CATEGORY 1: QUICK START & AUDIT ---
        self.create_nav_category("QUICK START & AUDIT", first=True)
        self.nav_btn_autopilot = self.create_nav_button("🤖", "1-Click Autopilot", self.show_autopilot_view)
        self.nav_btn_scorecard = self.create_nav_button("📋", "PC Health Scorecard", self.show_scorecard_view)
        self.nav_btn_trayguard = self.create_nav_button("📌", "Tray Auto-RAM Guard", self.show_trayguard_view)

        # --- CATEGORY 2: PERFORMANCE & TUNING ---
        self.create_nav_category("PERFORMANCE & TUNING")
        self.nav_btn_hud = self.create_nav_button("🎯", "Floating Gaming HUD", self.show_hud_view)
        self.nav_btn_tuner = self.create_nav_button("🧠", "CPU & RAM Tuner", self.show_tuner_view)
        self.nav_btn_services = self.create_nav_button("⚙️", "Services & Power Tamer", self.show_services_view)
        self.nav_btn_gpu = self.create_nav_button("📈", "GPU Performance Center", self.show_gpu_view)
        self.nav_btn_bench = self.create_nav_button("⏱", "CPU & Disk Benchmark", self.show_bench_view)
        self.nav_btn_gaming = self.create_nav_button("🎮", "Gaming & Power Plans", self.show_gaming_view)
        self.nav_btn_procs = self.create_nav_button("📊", "Process Manager", self.show_process_view)
        self.nav_btn_startup = self.create_nav_button("🚀", "Startup Apps Manager", self.show_startup_view)

        # --- CATEGORY 3: STORAGE & CLEANUP ---
        self.create_nav_category("STORAGE & CLEANUP")
        self.nav_btn_cleaner = self.create_nav_button("🧹", "Junk & Quick Clean", self.show_cleaner_view)
        self.nav_btn_disk = self.create_nav_button("💿", "Disk SMART & Space", self.show_disk_view)
        self.nav_btn_large = self.create_nav_button("📦", "Large File Finder", self.show_large_files_view)
        self.nav_btn_dupes = self.create_nav_button("📑", "Duplicate File Finder", self.show_dupes_view)
        self.nav_btn_shred = self.create_nav_button("🔥", "File Shredder & Unlocker", self.show_shred_view)
        self.nav_btn_uninstall = self.create_nav_button("🚮", "App Uninstaller", self.show_uninstaller_view)

        # --- CATEGORY 4: UPDATES & RECOVERY ---
        self.create_nav_category("UPDATES & RECOVERY")
        self.nav_btn_winget = self.create_nav_button("📥", "1-Click App Installer", self.show_winget_view)
        self.nav_btn_updates = self.create_nav_button("🔄", "Software Update Center", self.show_updates_view)
        self.nav_btn_restore = self.create_nav_button("⏪", "Restore & Scheduler", self.show_restore_view)
        self.nav_btn_repair = self.create_nav_button("🔧", "Windows Repair & Battery", self.show_repair_view)
        self.nav_btn_crash = self.create_nav_button("🚨", "Crash & Event Logs", self.show_crash_view)

        # --- CATEGORY 5: PRIVACY & CUSTOMIZATION ---
        self.create_nav_category("PRIVACY & CUSTOMIZATION")
        self.nav_btn_privacy = self.create_nav_button("🔒", "Privacy & Debloater", self.show_privacy_view)
        self.nav_btn_uitweaks = self.create_nav_button("🎛", "Input & Explorer Tweaks", self.show_uitweaks_view)
        self.nav_btn_ctx = self.create_nav_button("⚡", "Shell & Hosts Shield", self.show_ctx_view)

        # --- CATEGORY 6: NETWORK & SECURITY ---
        self.create_nav_category("NETWORK & SECURITY")
        self.nav_btn_lan = self.create_nav_button("📡", "LAN Ping Sweep Scanner", self.show_lan_view)
        self.nav_btn_wifi = self.create_nav_button("🔑", "Wi-Fi Vault & DNS", self.show_wifi_view)
        self.nav_btn_net = self.create_nav_button("🌐", "Speed & Ping Test", self.show_net_view)
        self.nav_btn_sec = self.create_nav_button("🔰", "Security & Open Ports", self.show_sec_view)

        # --- CATEGORY 7: HARDWARE & DRIVERS ---
        self.create_nav_category("HARDWARE & DRIVERS")
        self.nav_btn_bios = self.create_nav_button("🏷", "Product Key & BIOS/TPM", self.show_bios_view)
        self.nav_btn_sysinfo = self.create_nav_button("💻", "Full Hardware Specs", self.show_sysinfo_view)
        self.nav_btn_monitor = self.create_nav_button("🖥", "Display & Pixel Tester", self.show_monitor_view)
        self.nav_btn_drivers = self.create_nav_button("🔌", "Driver Backup Center", self.show_drivers_view)
        self.nav_btn_devices = self.create_nav_button("🎧", "Connected Devices", self.show_devices_view)

        # UI Theme Switcher at bottom of Sidebar
        ctk.CTkLabel(self.sidebar, text="UI Theme:", font=ctk.CTkFont(size=12)).grid(
            row=3, column=0, padx=20, pady=(6, 0), sticky="w"
        )
        self.theme_menu = ctk.CTkOptionMenu(
            self.sidebar, values=["Dark", "Light", "System"], command=ctk.set_appearance_mode
        )
        self.theme_menu.grid(row=4, column=0, padx=20, pady=(4, 14), sticky="ew")

        # ==========================================
        # TOP LIVE TELEMETRY BAR (UNIFORM 4-COLUMN GRID)
        # ==========================================
        self.telemetry_frame = ctk.CTkFrame(self)
        self.telemetry_frame.grid(row=0, column=1, padx=20, pady=(15, 10), sticky="ew")
        self.telemetry_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="telemetry")

        # 1. CPU Gauge
        self.cpu_label = ctk.CTkLabel(
            self.telemetry_frame, text="CPU: 0.0%", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.cpu_label.grid(row=0, column=0, padx=10, pady=(10, 2))
        self.cpu_bar = ctk.CTkProgressBar(self.telemetry_frame, height=12, progress_color="#3B8ED0")
        self.cpu_bar.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="ew")

        # 2. RAM Gauge
        self.ram_label = ctk.CTkLabel(
            self.telemetry_frame, text="RAM: 0% (0 / 0 GB)", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.ram_label.grid(row=0, column=1, padx=10, pady=(10, 2))
        self.ram_bar = ctk.CTkProgressBar(self.telemetry_frame, height=12, progress_color="#9B59B6")
        self.ram_bar.grid(row=1, column=1, padx=14, pady=(0, 12), sticky="ew")

        # 3. GPU Gauge
        self.gpu_label = ctk.CTkLabel(
            self.telemetry_frame, text="GPU: 0.0%", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.gpu_label.grid(row=0, column=2, padx=10, pady=(10, 2))
        self.gpu_bar = ctk.CTkProgressBar(self.telemetry_frame, height=12, progress_color="#2FA572")
        self.gpu_bar.grid(row=1, column=2, padx=14, pady=(0, 12), sticky="ew")

        # 4. Clickable Disk Gauge
        self.disk_btn = ctk.CTkButton(
            self.telemetry_frame,
            text="Disk (C:) 🔄: 0%",
            height=24,
            fg_color="transparent",
            hover_color=("gray80", "gray25"),
            text_color=("gray10", "gray90"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.cycle_selected_drive,
        )
        self.disk_btn.grid(row=0, column=3, padx=10, pady=(8, 2))
        self.disk_bar = ctk.CTkProgressBar(self.telemetry_frame, height=12, progress_color="#E67E22")
        self.disk_bar.grid(row=1, column=3, padx=14, pady=(0, 12), sticky="ew")

        # ==========================================
        # LIGHTWEIGHT LAZY-LOADED VIEW CACHE
        # ==========================================
        self.loaded_views = {}
        self.active_frame = None

        self.view_cleaner = ctk.CTkFrame(self, fg_color="transparent")
        self.view_procs = ctk.CTkFrame(self, fg_color="transparent")
        self.view_startup = ctk.CTkFrame(self, fg_color="transparent")
        self.view_sysinfo = None

        self.cached_specs = {}
        self.smart_loaded_once = False
        self.sec_loaded_once = False
        self.drivers_loaded_once = False
        self.devices_loaded_once = False
        self.crash_loaded_once = False
        self.wifi_loaded_once = False
        self.restore_loaded_once = False
        self.scorecard_loaded_once = False

        self._last_cpu_str = ""
        self._last_ram_str = ""
        self._last_gpu_str = ""
        self._last_disk_str = ""

        self.setup_cleaner_view()
        self.setup_process_view()
        self.setup_startup_view()

        # Load Tray Guard in background so system tray icon & global hotkeys are ready
        self.view_trayguard = self.get_lazy_view("tray_ram_guard", "TrayRamGuardView")

        # Start on 1-Click Autopilot View
        self.show_autopilot_view()
        self.update_live_stats()

    # ==========================================
    # DRIVE CYCLER & LAZY VIEW LOADER
    # ==========================================
    @staticmethod
    def _get_mounted_drives() -> list[str]:
        drives = []
        try:
            for part in psutil.disk_partitions(all=False):
                if "cdrom" in part.opts or not part.fstype:
                    continue
                drives.append(part.mountpoint)
        except Exception:
            pass
        return drives if drives else ["C:\\"]

    def cycle_selected_drive(self):
        self.available_drives = self._get_mounted_drives()
        if not self.available_drives:
            return
        self.current_drive_idx = (self.current_drive_idx + 1) % len(self.available_drives)
        self._refresh_disk_gauge(force=True)

    def _refresh_disk_gauge(self, force: bool = False):
        if not self.available_drives:
            self.available_drives = ["C:\\"]
        if self.current_drive_idx >= len(self.available_drives):
            self.current_drive_idx = 0

        mount = self.available_drives[self.current_drive_idx]
        drive_letter = mount.rstrip("\\")
        try:
            usage = psutil.disk_usage(mount)
            free_gb = usage.free / (1024**3)
            new_str = f"Disk ({drive_letter}) 🔄: {usage.percent:.1f}% ({free_gb:.0f} GB Free)"
            if force or new_str != self._last_disk_str:
                self._last_disk_str = new_str
                self.disk_btn.configure(text=new_str)
                self.disk_bar.set(usage.percent / 100.0)
        except Exception:
            self.disk_btn.configure(text=f"Disk ({drive_letter}) 🔄: N/A")
            self.disk_bar.set(0)

    def get_lazy_view(self, module_name: str, class_name: str):
        if module_name not in self.loaded_views:
            self.loaded_views[module_name] = safe_load_view(self, module_name, class_name)
        return self.loaded_views[module_name]

    def on_window_close(self):
        if (
            hasattr(self.view_trayguard, "var_close_to_tray")
            and self.view_trayguard.var_close_to_tray.get()
            and getattr(self.view_trayguard, "tray_running", False)
        ):
            self.view_trayguard.hide_to_tray()
            gc.collect()
        else:
            if hasattr(self.view_trayguard, "stop_tray"):
                self.view_trayguard.stop_tray()
            self.destroy()

    # ==========================================
    # CATEGORIZED NAVIGATION BUILDERS
    # ==========================================
    def create_nav_category(self, title: str, first: bool = False):
        if not first:
            divider = ctk.CTkFrame(self.nav_scroll, height=1, fg_color=("gray75", "gray28"))
            divider.pack(fill="x", padx=10, pady=(10, 4))

        lbl = ctk.CTkLabel(
            self.nav_scroll,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#3B8ED0",
            anchor="w",
        )
        lbl.pack(fill="x", padx=12, pady=(4 if first else 2, 2))

    def create_nav_button(self, icon: str, label: str, command):
        clean_icon = icon.replace("\ufe0f", "")
        btn = ctk.CTkButton(
            self.nav_scroll,
            text=f" {clean_icon}   {label}",
            height=32,
            anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray75", "gray25"),
            command=command,
        )
        btn.pack(fill="x", padx=4, pady=1)
        self.nav_buttons.append(btn)
        return btn

    def select_nav(self, active_btn, target_frame):
        for btn in self.nav_buttons:
            btn.configure(fg_color="transparent")
        active_btn.configure(fg_color=("gray75", "gray25"))

        if "gpu_performance_center" in self.loaded_views:
            gpu_v = self.loaded_views["gpu_performance_center"]
            if target_frame is not gpu_v and hasattr(gpu_v, "polling_active"):
                gpu_v.polling_active = False

        if self.active_frame is not None:
            self.active_frame.grid_forget()

        self.active_frame = target_frame
        self.active_frame.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="nsew")

    def show_autopilot_view(self):
        v = self.get_lazy_view("autopilot_maintenance", "AutopilotMaintenanceView")
        self.select_nav(self.nav_btn_autopilot, v)

    def show_scorecard_view(self):
        v = self.get_lazy_view("pc_health_scorecard", "PcHealthScorecardView")
        self.select_nav(self.nav_btn_scorecard, v)
        if not self.scorecard_loaded_once and hasattr(v, "run_health_audit"):
            self.scorecard_loaded_once = True
            v.run_health_audit()

    def show_trayguard_view(self):
        self.select_nav(self.nav_btn_trayguard, self.view_trayguard)

    def show_hud_view(self):
        v = self.get_lazy_view("hud_overlay", "HudOverlayView")
        self.select_nav(self.nav_btn_hud, v)

    def show_cleaner_view(self):
        self.select_nav(self.nav_btn_cleaner, self.view_cleaner)

    def show_tuner_view(self):
        v = self.get_lazy_view("cpu_ram_tuner", "CpuRamTunerView")
        self.select_nav(self.nav_btn_tuner, v)

    def show_services_view(self):
        v = self.get_lazy_view("services_optimizer", "ServicesOptimizerView")
        self.select_nav(self.nav_btn_services, v)

    def show_gpu_view(self):
        v = self.get_lazy_view("gpu_performance_center", "GpuPerformanceCenterView")
        self.select_nav(self.nav_btn_gpu, v)
        if hasattr(v, "start_polling"):
            v.start_polling()

    def show_bench_view(self):
        v = self.get_lazy_view("thermal_stress_bench", "ThermalStressBenchView")
        self.select_nav(self.nav_btn_bench, v)

    def show_winget_view(self):
        v = self.get_lazy_view("winget_app_installer", "WingetAppInstallerView")
        self.select_nav(self.nav_btn_winget, v)

    def show_updates_view(self):
        v = self.get_lazy_view("update_center", "UpdateCenterView")
        self.select_nav(self.nav_btn_updates, v)

    def show_restore_view(self):
        v = self.get_lazy_view("restore_scheduler", "RestoreSchedulerView")
        self.select_nav(self.nav_btn_restore, v)
        if not self.restore_loaded_once and hasattr(v, "check_scheduled_task"):
            self.restore_loaded_once = True
            v.check_scheduled_task()

    def show_gaming_view(self):
        v = self.get_lazy_view("gaming_booster", "GamingBoosterView")
        self.select_nav(self.nav_btn_gaming, v)
        if hasattr(v, "refresh_active_plan"):
            v.refresh_active_plan()

    def show_privacy_view(self):
        v = self.get_lazy_view("privacy_debloater", "PrivacyDebloaterView")
        self.select_nav(self.nav_btn_privacy, v)
        if hasattr(v, "sync_switches_with_registry"):
            v.sync_switches_with_registry()

    def show_uitweaks_view(self):
        v = self.get_lazy_view("win11_ui_customizer", "Win11UiCustomizerView")
        self.select_nav(self.nav_btn_uitweaks, v)
        if hasattr(v, "sync_from_registry"):
            v.sync_from_registry()

    def show_ctx_view(self):
        v = self.get_lazy_view("context_hosts_manager", "ContextHostsManagerView")
        self.select_nav(self.nav_btn_ctx, v)
        if hasattr(v, "refresh_state"):
            v.refresh_state()

    def show_disk_view(self):
        v = self.get_lazy_view("disk_health_analyzer", "DiskHealthAnalyzerView")
        self.select_nav(self.nav_btn_disk, v)
        if not self.smart_loaded_once and hasattr(v, "load_smart_health"):
            self.smart_loaded_once = True
            v.load_smart_health()

    def show_large_files_view(self):
        v = self.get_lazy_view("large_file_finder", "LargeFileFinderView")
        self.select_nav(self.nav_btn_large, v)

    def show_dupes_view(self):
        v = self.get_lazy_view("duplicate_finder", "DuplicateFinderView")
        self.select_nav(self.nav_btn_dupes, v)

    def show_shred_view(self):
        v = self.get_lazy_view("file_shredder_unlock", "FileShredderUnlockView")
        self.select_nav(self.nav_btn_shred, v)

    def show_uninstaller_view(self):
        v = self.get_lazy_view("app_uninstaller", "AppUninstallerView")
        self.select_nav(self.nav_btn_uninstall, v)
        if hasattr(v, "all_apps") and not v.all_apps:
            v.load_installed_apps()

    def show_bios_view(self):
        v = self.get_lazy_view("product_key_bios", "ProductKeyBiosView")
        self.select_nav(self.nav_btn_bios, v)

    def show_monitor_view(self):
        v = self.get_lazy_view("display_monitor_tester", "DisplayMonitorTesterView")
        self.select_nav(self.nav_btn_monitor, v)

    def show_drivers_view(self):
        v = self.get_lazy_view("driver_backup_center", "DriverBackupCenterView")
        self.select_nav(self.nav_btn_drivers, v)
        if not self.drivers_loaded_once and hasattr(v, "scan_drivers"):
            self.drivers_loaded_once = True
            v.scan_drivers()

    def show_devices_view(self):
        v = self.get_lazy_view("connected_devices", "ConnectedDevicesView")
        self.select_nav(self.nav_btn_devices, v)
        if not self.devices_loaded_once and hasattr(v, "scan_peripherals"):
            self.devices_loaded_once = True
            v.scan_peripherals()

    def show_lan_view(self):
        v = self.get_lazy_view("lan_network_scanner", "LanNetworkScannerView")
        self.select_nav(self.nav_btn_lan, v)

    def show_wifi_view(self):
        v = self.get_lazy_view("wifi_vault_dns", "WifiVaultDnsView")
        self.select_nav(self.nav_btn_wifi, v)
        if not self.wifi_loaded_once and hasattr(v, "scan_saved_wifi"):
            self.wifi_loaded_once = True
            v.scan_saved_wifi()

    def show_net_view(self):
        v = self.get_lazy_view("network_speedtest", "NetworkSpeedtestView")
        self.select_nav(self.nav_btn_net, v)

    def show_sec_view(self):
        v = self.get_lazy_view("security_port_scanner", "SecurityPortScannerView")
        self.select_nav(self.nav_btn_sec, v)
        if not self.sec_loaded_once and hasattr(v, "check_security_status"):
            self.sec_loaded_once = True
            v.check_security_status()
            v.scan_network_connections()

    def show_crash_view(self):
        v = self.get_lazy_view("crash_inspector", "CrashInspectorView")
        self.select_nav(self.nav_btn_crash, v)
        if not self.crash_loaded_once and hasattr(v, "scan_crash_logs"):
            self.crash_loaded_once = True
            v.scan_crash_logs()

    def show_repair_view(self):
        v = self.get_lazy_view("system_repair", "SystemRepairView")
        self.select_nav(self.nav_btn_repair, v)

    def show_process_view(self):
        self.select_nav(self.nav_btn_procs, self.view_procs)
        self.refresh_process_list()

    def show_startup_view(self):
        self.select_nav(self.nav_btn_startup, self.view_startup)
        self.refresh_startup_list()

    def show_sysinfo_view(self):
        if self.view_sysinfo is None:
            self.view_sysinfo = ctk.CTkFrame(self, fg_color="transparent")
            self.setup_sysinfo_view()
        self.select_nav(self.nav_btn_sysinfo, self.view_sysinfo)

    # ==========================================
    # VIEW: CLEANER & RAM UI
    # ==========================================
    def setup_cleaner_view(self):
        self.view_cleaner.grid_columnconfigure(0, weight=1)
        self.view_cleaner.grid_rowconfigure(3, weight=1)

        options_card = ctk.CTkFrame(self.view_cleaner)
        options_card.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        options_card.grid_columnconfigure((0, 1, 2), weight=1)

        self.var_user_temp = ctk.BooleanVar(value=True)
        self.var_win_temp = ctk.BooleanVar(value=True)
        self.var_prefetch = ctk.BooleanVar(value=False)
        self.var_recycle = ctk.BooleanVar(value=True)
        self.var_chrome = ctk.BooleanVar(value=True)
        self.var_edge = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(options_card, text="User Temp (%TEMP%)", variable=self.var_user_temp).grid(
            row=0, column=0, padx=15, pady=12, sticky="w"
        )
        ctk.CTkCheckBox(options_card, text="Windows Temp", variable=self.var_win_temp).grid(
            row=0, column=1, padx=15, pady=12, sticky="w"
        )
        ctk.CTkCheckBox(options_card, text="Prefetch Cache (Admin)", variable=self.var_prefetch).grid(
            row=0, column=2, padx=15, pady=12, sticky="w"
        )
        ctk.CTkCheckBox(options_card, text="Chrome & Brave Cache", variable=self.var_chrome).grid(
            row=1, column=0, padx=15, pady=12, sticky="w"
        )
        ctk.CTkCheckBox(options_card, text="Microsoft Edge Cache", variable=self.var_edge).grid(
            row=1, column=1, padx=15, pady=12, sticky="w"
        )
        ctk.CTkCheckBox(options_card, text="Empty Recycle Bin", variable=self.var_recycle).grid(
            row=1, column=2, padx=15, pady=12, sticky="w"
        )

        btn_frame = ctk.CTkFrame(self.view_cleaner, fg_color="transparent")
        btn_frame.grid(row=1, column=0, pady=5, sticky="ew")

        self.scan_btn = ctk.CTkButton(
            btn_frame,
            text="🔍 Scan Junk",
            height=40,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#3B8ED0",
            command=lambda: self.run_engine_task(self.task_scan),
        )
        self.scan_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.clean_btn = ctk.CTkButton(
            btn_frame,
            text="🧹 Clean Disk Now",
            height=40,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#2FA572",
            hover_color="#1D7A52",
            command=lambda: self.run_engine_task(self.task_clean),
        )
        self.clean_btn.pack(side="left", expand=True, fill="x", padx=6)

        self.ram_btn = ctk.CTkButton(
            btn_frame,
            text="🚀 Boost RAM",
            height=40,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#8E44AD",
            hover_color="#6C3483",
            command=lambda: self.run_engine_task(lambda: SystemEngine.optimize_ram(self.log_message)),
        )
        self.ram_btn.pack(side="left", expand=True, fill="x", padx=6)

        self.dns_btn = ctk.CTkButton(
            btn_frame,
            text="🌐 Flush DNS",
            height=40,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#D35400",
            hover_color="#A04000",
            command=lambda: self.run_engine_task(lambda: SystemEngine.flush_dns(self.log_message)),
        )
        self.dns_btn.pack(side="right", expand=True, fill="x", padx=(6, 0))

        self.progress = ctk.CTkProgressBar(self.view_cleaner, mode="indeterminate")
        self.progress.grid(row=2, column=0, pady=8, sticky="ew")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self.view_cleaner, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=3, column=0, sticky="nsew")
        self.log_message("IT Maintenance Suite Ready. All 34 tools active with Laptop Optimus Sleep Guard & Global Hotkeys enabled.")

    def current_targets(self):
        return SystemEngine.get_target_folders(
            user_temp=self.var_user_temp.get(),
            win_temp=self.var_win_temp.get(),
            prefetch=self.var_prefetch.get(),
            chrome=self.var_chrome.get(),
            edge=self.var_edge.get(),
        )

    def task_scan(self):
        SystemEngine.scan_junk(self.current_targets(), self.var_recycle.get(), self.log_message)

    def task_clean(self):
        SystemEngine.clean_junk(self.current_targets(), self.var_recycle.get(), self.log_message)

    def run_engine_task(self, func):
        def wrapper():
            self.set_ui_state(False)
            try:
                func()
            finally:
                self.set_ui_state(True)

        threading.Thread(target=wrapper, daemon=True).start()

    # ==========================================
    # PROCESS & STARTUP VIEWS
    # ==========================================
    def setup_process_view(self):
        self.view_procs.grid_columnconfigure(0, weight=1)
        self.view_procs.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(self.view_procs, fg_color="transparent")
        top_bar.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        ctk.CTkLabel(
            top_bar, text="Top 15 Memory-Consuming Processes", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        ctk.CTkButton(top_bar, text="🔄 Refresh List", width=130, command=self.refresh_process_list).pack(
            side="right"
        )

        self.proc_scroll = ctk.CTkScrollableFrame(self.view_procs)
        self.proc_scroll.grid(row=1, column=0, sticky="nsew")

    def refresh_process_list(self):
        for widget in self.proc_scroll.winfo_children():
            widget.destroy()

        for pid, name, mem_mb in SystemEngine.get_top_processes(15):
            row_frame = ctk.CTkFrame(self.proc_scroll)
            row_frame.pack(fill="x", padx=5, pady=4)
            ctk.CTkLabel(row_frame, text=f"{name} (PID: {pid})", font=ctk.CTkFont(weight="bold")).pack(
                side="left", padx=15, pady=8
            )
            ctk.CTkButton(
                row_frame,
                text="End Task",
                width=85,
                height=28,
                fg_color="#C0392B",
                hover_color="#922B21",
                command=lambda p=pid, n=name: self.kill_process(p, n),
            ).pack(side="right", padx=12, pady=8)
            ctk.CTkLabel(
                row_frame, text=f"{mem_mb:.1f} MB", text_color="#3B8ED0", font=ctk.CTkFont(weight="bold")
            ).pack(side="right", padx=15)

    def kill_process(self, pid, name):
        try:
            psutil.Process(pid).terminate()
            self.log_message(f"[+] Terminated process: {name} (PID {pid})")
        except Exception as e:
            self.log_message(f"[!] Could not terminate {name}: {e}")
        self.after(400, self.refresh_process_list)

    def setup_startup_view(self):
        self.view_startup.grid_columnconfigure(0, weight=1)
        self.view_startup.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(self.view_startup, fg_color="transparent")
        top_bar.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        ctk.CTkLabel(
            top_bar, text="Windows Registry Startup Programs", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        self.startup_status = ctk.CTkLabel(top_bar, text="", font=ctk.CTkFont(size=12), text_color="#2FA572")
        self.startup_status.pack(side="left", padx=15)

        ctk.CTkButton(top_bar, text="🔄 Refresh", width=110, command=self.refresh_startup_list).pack(
            side="right"
        )

        self.startup_scroll = ctk.CTkScrollableFrame(self.view_startup)
        self.startup_scroll.grid(row=1, column=0, sticky="nsew")

    def refresh_startup_list(self):
        for widget in self.startup_scroll.winfo_children():
            widget.destroy()

        items = SystemEngine.get_startup_apps()
        if not items:
            ctk.CTkLabel(self.startup_scroll, text="No registry startup programs found.").pack(pady=20)
            return

        for name, cmd, scope in items:
            card = ctk.CTkFrame(self.startup_scroll)
            card.pack(fill="x", padx=5, pady=5)

            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=12, pady=(8, 2))
            ctk.CTkLabel(header, text=name, font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

            ctk.CTkButton(
                header,
                text="❌ Remove from Startup",
                width=160,
                height=26,
                fg_color="#C0392B",
                hover_color="#922B21",
                command=lambda n=name, s=scope: self.remove_startup_item(n, s),
            ).pack(side="right", padx=(10, 0))

            ctk.CTkLabel(header, text=scope, text_color="#3B8ED0", font=ctk.CTkFont(size=11)).pack(
                side="right"
            )
            ctk.CTkLabel(
                card, text=cmd, font=ctk.CTkFont(size=11), text_color="gray", wraplength=580, justify="left"
            ).pack(anchor="w", padx=12, pady=(0, 8))

    def remove_startup_item(self, name: str, scope: str):
        if hasattr(SystemEngine, "delete_startup_app"):
            ok, msg = SystemEngine.delete_startup_app(name, scope)
            color = "#2FA572" if ok else "#E74C3C"
            self.startup_status.configure(text=msg, text_color=color)
            self.refresh_startup_list()

    # ==========================================
    # DEEP GRAPHICS (GPU) & NETWORK COLLECTORS FOR SYSTEM SPECS
    # ==========================================
    @staticmethod
    def collect_all_gpu_specs() -> dict[str, dict[str, str]]:
        """Collects complete WMI, 64-bit Registry VRAM, and live NVIDIA/WDDM sensor specs for all GPUs."""
        gpu_sections = {}

        ps_cmd = (
            "$gpus = @(Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | "
            "Select-Object Name, AdapterCompatibility, DriverVersion, DriverDate, VideoProcessor, "
            "VideoModeDescription, CurrentHorizontalResolution, CurrentVerticalResolution, "
            "CurrentRefreshRate, MinRefreshRate, MaxRefreshRate, CurrentBitsPerPixel, "
            "AdapterRAM, Status, PNPDeviceID, InfSection); "
            "$vram64 = @(Get-ItemProperty -Path 'HKLM:\\SYSTEM\\ControlSet001\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}\\0*' "
            "-Name 'HardwareInformation.qwMemorySize' -ErrorAction SilentlyContinue | "
            "Select-Object -ExpandProperty 'HardwareInformation.qwMemorySize'); "
            "@{gpus=$gpus; vram64=$vram64} | ConvertTo-Json -Compress -Depth 3"
        )
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=8,
            ).strip()
            if out:
                data = json.loads(out)
                raw_gpus = data.get("gpus") or []
                gpus = [raw_gpus] if isinstance(raw_gpus, dict) else raw_gpus
                raw_vram64 = data.get("vram64") or []
                vram64_list = [raw_vram64] if isinstance(raw_vram64, int) else raw_vram64
                max_reg_vram = max([int(x) for x in vram64_list if isinstance(x, int)], default=0)

                for idx, g in enumerate(gpus, start=1):
                    name = (g.get("Name") or f"Display Adapter {idx}").strip()
                    wmi_ram = int(g.get("AdapterRAM") or 0)
                    true_vram = max(wmi_ram, max_reg_vram) if idx == 1 else wmi_ram
                    vram_str = SystemEngine.format_bytes(true_vram) if true_vram > 0 else "Dynamic Shared Memory"

                    h_res = g.get("CurrentHorizontalResolution")
                    v_res = g.get("CurrentVerticalResolution")
                    hz = g.get("CurrentRefreshRate")
                    min_hz = g.get("MinRefreshRate")
                    max_hz = g.get("MaxRefreshRate")
                    bpp = g.get("CurrentBitsPerPixel")

                    res_str = f"{h_res} x {v_res} @ {hz} Hz" if (h_res and v_res) else "Secondary / Offscreen"
                    hz_range = f"{min_hz} Hz – {max_hz} Hz" if (min_hz and max_hz) else f"{hz or 60} Hz"

                    raw_date = str(g.get("DriverDate") or "")
                    if "/Date(" in raw_date:
                        try:
                            ms = int(re.search(r"\d+", raw_date).group(0))
                            drv_date = datetime.fromtimestamp(ms / 1000.0).strftime("%Y-%m-%d")
                        except Exception:
                            drv_date = "Installed"
                    elif len(raw_date) >= 8 and raw_date[:8].isdigit():
                        drv_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
                    else:
                        drv_date = raw_date[:10] if raw_date else "Installed"

                    card_title = f"🎮 Graphics Adapter #{idx}: {name}"
                    gpu_sections[card_title] = {
                        "GPU Model Name": name,
                        "Vendor / Manufacturer": (g.get("AdapterCompatibility") or "Standard").strip(),
                        "GPU Die / Video Processor": (g.get("VideoProcessor") or name).strip(),
                        "Dedicated Video Memory (VRAM)": vram_str,
                        "Installed Driver Version": (g.get("DriverVersion") or "Unknown").strip(),
                        "Driver Release Date": drv_date,
                        "Active Display Resolution": res_str,
                        "Supported Refresh Rate Range": hz_range,
                        "Color Bit Depth": f"{bpp}-bit True Color" if bpp else "32-bit",
                        "Driver INF Profile": (g.get("InfSection") or "Standard WDDM").strip(),
                        "Device Manager Status": f"🟢 {g.get('Status') or 'OK'}",
                    }
        except Exception:
            pass

        if shutil.which("nvidia-smi"):
            try:
                nv_out = subprocess.check_output(
                    [
                        "nvidia-smi",
                        "--query-gpu=name,vbios_version,pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,utilization.gpu,utilization.memory,memory.used,memory.free,memory.total,temperature.gpu,fan.speed,power.draw,power.limit,clocks.current.graphics,clocks.current.memory,pstate",
                        "--format=csv,noheader,nounits",
                    ],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    text=True,
                    timeout=3,
                ).strip()
                if nv_out:
                    p = [x.strip() for x in nv_out.splitlines()[0].split(",")]
                    if len(p) >= 17:
                        gpu_sections[f"📈 Live GPU Hardware Sensors ({p[0]})"] = {
                            "VBIOS Firmware Version": p[1],
                            "PCIe Bus Link Speed & Width": f"PCIe Gen {p[2]} (Max Gen {p[3]}) @ x{p[4]} Lanes",
                            "Live 3D Core Load": f"{p[5]}%",
                            "Memory Controller Load": f"{p[6]}%",
                            "Dedicated VRAM Usage": f"{p[7]} MB Used  /  {p[9]} MB Total ({p[8]} MB Free)",
                            "GPU Core Temperature": f"{p[10]} °C",
                            "Cooling Fan Speed": f"{p[11]}%",
                            "Live Power Draw / TDP Limit": f"{p[12]} W  /  {p[13]} W Limit",
                            "Live Graphics Core Clock": f"{p[14]} MHz",
                            "Live VRAM Memory Clock": f"{p[15]} MHz",
                            "GPU Power State (P-State)": p[16],
                        }
            except Exception:
                pass

        return gpu_sections

    @staticmethod
    def collect_all_network_specs() -> dict[str, dict[str, str]]:
        """Enumerates Wireless (Wi-Fi) Radio Telemetry + ALL Physical/Virtual Network Adapters (LAN, Wi-Fi, VPN)."""
        net_sections = {}

        try:
            wlan_out = subprocess.check_output(
                ["netsh", "wlan", "show", "interfaces"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=4,
            )
            if "there is no wireless interface" not in wlan_out.lower():
                wifi_info = {}
                wanted_fields = {
                    "Name": "Adapter Interface",
                    "Description": "Wi-Fi Hardware Chip",
                    "State": "Connection State",
                    "SSID": "Connected Wi-Fi SSID",
                    "BSSID": "Access Point BSSID",
                    "Radio type": "Wi-Fi Radio Standard",
                    "Band": "Frequency Band",
                    "Channel": "Wireless Channel",
                    "Signal": "Signal Strength",
                    "Receive rate (Mbps)": "RX Link Rate (Mbps)",
                    "Transmit rate (Mbps)": "TX Link Rate (Mbps)",
                    "Authentication": "Security Auth",
                }
                for line in wlan_out.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k_clean = k.strip()
                        v_clean = v.strip()
                        if k_clean in wanted_fields and v_clean:
                            if k_clean == "SSID" and "Connected Wi-Fi SSID" in wifi_info:
                                continue
                            wifi_info[wanted_fields[k_clean]] = v_clean
                if wifi_info:
                    net_sections["📶 Wireless (Wi-Fi) Radio Telemetry"] = wifi_info
        except Exception:
            pass

        ps_ipcfg = {}
        try:
            ps_cmd = (
                "@(Get-NetIPConfiguration -ErrorAction SilentlyContinue | ForEach-Object { "
                "@{Alias=$_.InterfaceAlias; Desc=$_.InterfaceDescription; "
                "GW=($_.IPv4DefaultGateway.NextHop -join ', '); "
                "DNS=($_.DNSServer.ServerAddresses -join ', ')} "
                "}) | ConvertTo-Json -Compress"
            )
            out_ps = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=6,
            ).strip()
            if out_ps:
                raw_list = json.loads(out_ps)
                if isinstance(raw_list, dict):
                    raw_list = [raw_list]
                for item in raw_list:
                    alias = item.get("Alias")
                    if alias:
                        ps_ipcfg[alias] = item
        except Exception:
            pass

        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        io_counters = psutil.net_io_counters(pernic=True)

        for nic_name, addr_list in addrs.items():
            if "loopback" in nic_name.lower():
                continue

            st = stats.get(nic_name)
            io = io_counters.get(nic_name)

            mac_addr = "N/A"
            ipv4_addr = "Not Assigned"
            netmask = "N/A"
            ipv6_addr = "N/A"

            for snic in addr_list:
                if snic.family == psutil.AF_LINK:
                    mac_addr = snic.address
                elif snic.family == socket.AF_INET:
                    ipv4_addr = snic.address
                    netmask = snic.netmask or "N/A"
                elif snic.family == socket.AF_INET6 and ipv6_addr == "N/A":
                    ipv6_addr = snic.address.split("%")[0]

            is_up = st.isup if st else False
            speed_mbps = f"{st.speed} Mbps" if (st and st.speed and st.speed < 100000) else "Auto / Virtual"

            if not is_up and ipv4_addr == "Not Assigned" and (not io or (io.bytes_sent == 0 and io.bytes_recv == 0)):
                continue

            low_name = nic_name.lower()
            if any(w in low_name for w in ("wi-fi", "wlan", "wireless")):
                icon = "📶"
                type_tag = "Wireless Adapter"
            elif any(w in low_name for w in ("ethernet", "lan", "realtek", "intel")):
                icon = "🔌"
                type_tag = "Ethernet LAN"
            elif any(w in low_name for w in ("bluetooth",)):
                icon = "🦷"
                type_tag = "Bluetooth PAN"
            else:
                icon = "🌐"
                type_tag = "Virtual / VPN Adapter"

            extra = ps_ipcfg.get(nic_name, {})
            hw_desc = extra.get("Desc") or type_tag
            gw = extra.get("GW") or "None"
            dns = extra.get("DNS") or "Automatic"

            sent_str = SystemEngine.format_bytes(io.bytes_sent) if io else "0 B"
            recv_str = SystemEngine.format_bytes(io.bytes_recv) if io else "0 B"

            card_title = f"{icon} Network Adapter: {nic_name}"
            net_sections[card_title] = {
                "Hardware Controller": hw_desc,
                "Adapter Status": "🟢 Connected (Up)" if is_up else "⚪ Disconnected (Down)",
                "IPv4 Address": f"{ipv4_addr}  (Mask: {netmask})" if ipv4_addr != "Not Assigned" else "Not Assigned",
                "IPv6 Address": ipv6_addr,
                "Physical MAC Address": mac_addr,
                "Negotiated Link Speed": speed_mbps,
                "Default Gateway": gw,
                "DNS Servers": dns[:48] + ("..." if len(dns) > 48 else ""),
                "Session Traffic (TX / RX)": f"⬆ {sent_str} Sent  |  ⬇ {recv_str} Received",
            }

        return net_sections

    def setup_sysinfo_view(self):
        self.view_sysinfo.grid_columnconfigure(0, weight=1)
        self.view_sysinfo.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(self.view_sysinfo, fg_color="transparent")
        top_bar.grid(row=0, column=0, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(
            top_bar,
            text="Complete Hardware, Graphics (GPU), LAN & Wireless Specifications",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        self.export_btn = ctk.CTkButton(
            top_bar,
            text="📄 Export Specs to .TXT",
            width=180,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(weight="bold"),
            command=self.export_specs_to_txt,
        )
        self.export_btn.pack(side="right", padx=(6, 0))

        self.refresh_specs_btn = ctk.CTkButton(
            top_bar,
            text="🔄 Refresh Specs & Sensors",
            width=195,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.refresh_sysinfo_cards,
        )
        self.refresh_specs_btn.pack(side="right", padx=6)

        self.sysinfo_scroll = ctk.CTkScrollableFrame(self.view_sysinfo)
        self.sysinfo_scroll.grid(row=1, column=0, sticky="nsew")
        self.sysinfo_scroll.grid_columnconfigure((0, 1), weight=1)

        self.refresh_sysinfo_cards()

    def refresh_sysinfo_cards(self):
        for w in self.sysinfo_scroll.winfo_children():
            w.destroy()

        base_specs = SystemEngine.get_detailed_specs()
        gpu_specs = self.collect_all_gpu_specs()
        net_specs = self.collect_all_network_specs()

        combined = {}
        for k, v in base_specs.items():
            combined[k] = v
        for k, v in gpu_specs.items():
            combined[k] = v
        for k, v in net_specs.items():
            combined[k] = v

        self.cached_specs = combined

        for idx, (category, items) in enumerate(self.cached_specs.items()):
            card = ctk.CTkFrame(self.sysinfo_scroll)
            card.grid(row=idx // 2, column=idx % 2, padx=8, pady=8, sticky="nsew")
            ctk.CTkLabel(
                card, text=category, font=ctk.CTkFont(size=15, weight="bold"), text_color="#3B8ED0"
            ).pack(anchor="w", padx=15, pady=(12, 6))
            for key, val in items.items():
                line = ctk.CTkFrame(card, fg_color="transparent")
                line.pack(fill="x", padx=15, pady=2)
                ctk.CTkLabel(line, text=f"{key}:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
                ctk.CTkLabel(line, text=str(val), font=ctk.CTkFont(size=12), text_color="lightgray").pack(
                    side="right"
                )
            ctk.CTkLabel(card, text="", height=6).pack()

    def export_specs_to_txt(self):
        report_file = os.path.join(os.path.expanduser("~"), "PC_Hardware_Specs_Report.txt")
        lines = [
            "==========================================================",
            f" WINDOWS SYSTEM OPTIMIZER - HARDWARE, GPU & NETWORK REPORT ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
            "==========================================================\n",
        ]
        for category, items in self.cached_specs.items():
            lines.append(f"[{category.upper()}]")
            for k, v in items.items():
                lines.append(f"  {k:<30}: {v}")
            lines.append("")

        try:
            with open(report_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            subprocess.Popen(["notepad.exe", report_file])
        except Exception as e:
            self.log_message(f"[!] Could not export specs report: {e}")

    # ==========================================
    # ULTRA-LIGHTWEIGHT, OPTIMUS-SAFE TELEMETRY LOOP
    # ==========================================
    def _poll_top_gpu_async(self):
        if self._gpu_poll_busy or not self.has_nvidia_smi:
            return

        gpu_tab_open = (
            "gpu_performance_center" in self.loaded_views
            and self.active_frame is self.loaded_views["gpu_performance_center"]
        )
        if self.is_laptop and not gpu_tab_open:
            return

        self._gpu_poll_busy = True

        def worker():
            try:
                out = subprocess.check_output(
                    [
                        "nvidia-smi",
                        "--query-gpu=utilization.gpu,temperature.gpu",
                        "--format=csv,noheader,nounits",
                    ],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    text=True,
                    timeout=2,
                ).strip()
                if out:
                    parts = [p.strip() for p in out.splitlines()[0].split(",")]
                    if len(parts) >= 2:
                        self.live_gpu_pct = float(parts[0]) if parts[0].replace(".", "").isdigit() else 0.0
                        self.live_gpu_temp = f" ({parts[1]}°C)" if parts[1].isdigit() else ""
            except Exception:
                pass
            finally:
                self._gpu_poll_busy = False

        threading.Thread(target=worker, daemon=True).start()

    def update_live_stats(self):
        if not self.winfo_viewable() or self.state() == "iconic":
            self.after(4000, self.update_live_stats)
            return

        cpu_p = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()

        self._gpu_tick_counter += 1
        if self._gpu_tick_counter % 2 == 1:
            self._poll_top_gpu_async()

        new_cpu_str = f"CPU: {cpu_p:.1f}%"
        if new_cpu_str != self._last_cpu_str:
            self._last_cpu_str = new_cpu_str
            self.cpu_label.configure(text=new_cpu_str)
            self.cpu_bar.set(cpu_p / 100.0)

        used_gb = ram.used / (1024**3)
        total_gb = ram.total / (1024**3)
        new_ram_str = f"RAM: {ram.percent:.1f}% ({used_gb:.1f} / {total_gb:.1f} GB)"
        if new_ram_str != self._last_ram_str:
            self._last_ram_str = new_ram_str
            self.ram_label.configure(text=new_ram_str)
            self.ram_bar.set(ram.percent / 100.0)

        gpu_tab_open = (
            "gpu_performance_center" in self.loaded_views
            and self.active_frame is self.loaded_views["gpu_performance_center"]
        )
        if self.is_laptop and not gpu_tab_open:
            new_gpu_str = "GPU: Optimus Eco (dGPU Sleep Guard)"
            if new_gpu_str != self._last_gpu_str:
                self._last_gpu_str = new_gpu_str
                self.gpu_label.configure(text=new_gpu_str)
                self.gpu_bar.set(0.0)
        else:
            new_gpu_str = f"GPU: {self.live_gpu_pct:.1f}%{self.live_gpu_temp}"
            if new_gpu_str != self._last_gpu_str:
                self._last_gpu_str = new_gpu_str
                self.gpu_label.configure(text=new_gpu_str)
                self.gpu_bar.set(min(1.0, self.live_gpu_pct / 100.0))

        self._refresh_disk_gauge()

        self.after(2500, self.update_live_stats)

    def log_message(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def set_ui_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in [self.scan_btn, self.clean_btn, self.ram_btn, self.dns_btn]:
            btn.configure(state=state)
        if not enabled:
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.set(0)


def run_headless_silent_autopilot():
    """Executes Autopilot cleanup, RAM trim, and DNS flush silently when launched with --silent-autopilot."""
    targets = SystemEngine.get_target_folders(
        user_temp=True, win_temp=True, prefetch=False, chrome=True, edge=True
    )
    SystemEngine.clean_junk(targets, True, lambda _: None)
    SystemEngine.optimize_ram(lambda _: None)
    SystemEngine.flush_dns(lambda _: None)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    elevate_to_admin()
    if "--silent-autopilot" in sys.argv or "--silent-clean" in sys.argv:
        run_headless_silent_autopilot()
        sys.exit(0)
    app = PCCleanerUltimate()
    app.mainloop()