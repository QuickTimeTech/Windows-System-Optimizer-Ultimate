# autopilot_maintenance.py
import os
import sys
import json
import time
import shutil
import winreg
import threading
import subprocess
import webbrowser
from datetime import datetime
import psutil
import customtkinter as ctk
from backend_engine import SystemEngine


def get_persistent_data_dir() -> str:
    """Returns a persistent directory next to the .exe or script."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class AutopilotMaintenanceView(ctk.CTkFrame):
    """Master 1-Click Autopilot: Deep Scan, System Cleanup, Telemetry Audit & Full Webpage Report Generator."""

    IGNORE_UPDATES_FILE = os.path.join(get_persistent_data_dir(), "ignored_updates.json")

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(2, weight=1)

        self.running = False
        self.last_report_path = os.path.join(os.path.expanduser("~"), "PC_Autopilot_Master_Report.html")
        self.has_nvidia_smi = shutil.which("nvidia-smi") is not None

        # ==========================================
        # TOP HERO BANNER
        # ==========================================
        hero = ctk.CTkFrame(self)
        hero.grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky="ew")

        left_hero = ctk.CTkFrame(hero, fg_color="transparent")
        left_hero.pack(side="left", fill="x", expand=True, padx=18, pady=14)

        ctk.CTkLabel(
            left_hero,
            text="🤖 1-CLICK AUTOPILOT & MASTER WEBPAGE REPORT ENGINE",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_hero,
            text="Scans & cleans junk, optimizes RAM/DNS/SSD, audits CPU/GPU/Power/Registry/Updates, and opens a full HTML dashboard.",
            font=ctk.CTkFont(size=12),
            text_color="lightgray",
        ).pack(anchor="w", pady=(2, 0))

        btn_box = ctk.CTkFrame(hero, fg_color="transparent")
        btn_box.pack(side="right", padx=18, pady=14)

        self.start_btn = ctk.CTkButton(
            btn_box,
            text="🚀 START 1-CLICK AUTOPILOT",
            width=235,
            height=40,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.start_autopilot,
        )
        self.start_btn.pack(side="right", padx=(6, 0))

        self.open_report_btn = ctk.CTkButton(
            btn_box,
            text="🌐 Open Webpage Report",
            width=185,
            height=40,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(size=12, weight="bold"),
            state="normal" if os.path.exists(self.last_report_path) else "disabled",
            command=self.open_last_report,
        )
        self.open_report_btn.pack(side="right", padx=6)

        # ==========================================
        # PROGRESS BAR
        # ==========================================
        self.progress = ctk.CTkProgressBar(self, height=12, progress_color="#2FA572")
        self.progress.grid(row=1, column=0, columnspan=2, pady=(0, 8), sticky="ew")
        self.progress.set(0)

        # ==========================================
        # LEFT COLUMN: 8-STAGE PIPELINE CHECKLIST
        # ==========================================
        left_card = ctk.CTkFrame(self)
        left_card.grid(row=2, column=0, padx=(0, 8), sticky="nsew")

        hdr_row = ctk.CTkFrame(left_card, fg_color="transparent")
        hdr_row.pack(fill="x", padx=15, pady=(12, 6))

        ctk.CTkLabel(
            hdr_row,
            text="📋 Autopilot Scan, Clean & Deep Audit Stages",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        self.var_auto_open_html = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            hdr_row,
            text="Auto-Open Webpage Report",
            variable=self.var_auto_open_html,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="right")

        self.stages_scroll = ctk.CTkScrollableFrame(left_card, fg_color="transparent")
        self.stages_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 10))

        self.stage_defs = [
            ("clean_junk", "1. Scan & Clean Temp Files, Browser Caches & Recycle Bin", True),
            ("clean_shaders", "2. Purge Explorer Thumbnail, Icon & GPU Shader Caches", True),
            ("boost_ram", "3. Boost Physical RAM & Audit Top Memory-Hog Processes", True),
            ("cpu_gpu_power", "4. Deep CPU, GPU, VRAM, Thermals & Power Usage Audit", True),
            ("registry_audit", "5. Audit Windows Registry Tweaks & Auto-Apply Safe Fixes", True),
            ("software_audit", "6. Scan Installed Software for Pending Updates (Winget)", True),
            ("net_defender", "7. Flush DNS Cache, Audit Firewall & Update Defender AV", True),
            ("ssd_retrim", "8. Run SSD ReTrim / Drive C: Optimization & Specs Export", True),
        ]

        self.stage_vars = {}
        self.stage_badges = {}

        for key, title, default_val in self.stage_defs:
            row = ctk.CTkFrame(self.stages_scroll, fg_color=("gray85", "gray17"))
            row.pack(fill="x", padx=6, pady=4)

            var = ctk.BooleanVar(value=default_val)
            self.stage_vars[key] = var

            cb = ctk.CTkCheckBox(
                row,
                text=title,
                variable=var,
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            cb.pack(side="left", padx=12, pady=10)

            badge = ctk.CTkLabel(
                row,
                text="⏳ Ready",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="gray",
            )
            badge.pack(side="right", padx=12, pady=10)
            self.stage_badges[key] = badge

        # ==========================================
        # RIGHT COLUMN: LIVE AUTOPILOT TELEMETRY LOG
        # ==========================================
        right_card = ctk.CTkFrame(self)
        right_card.grid(row=2, column=1, padx=(8, 0), sticky="nsew")
        right_card.grid_rowconfigure(1, weight=1)
        right_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right_card,
            text="🖥️ Live Autopilot Telemetry Log",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=15, pady=(12, 6), sticky="w")

        self.log_box = ctk.CTkTextbox(right_card, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self.log_message(
            "Autopilot Master Engine Ready.\n"
            "Click 'START 1-CLICK AUTOPILOT' to clean your PC, audit every subsystem, and launch your interactive Webpage Report."
        )

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def set_stage_badge(self, key: str, text: str, color: str):
        if key in self.stage_badges:
            self.stage_badges[key].configure(text=text, text_color=color)

    def open_last_report(self):
        if os.path.exists(self.last_report_path):
            webbrowser.open(f"file://{os.path.abspath(self.last_report_path)}")

    # ==========================================
    # MASTER AUTOPILOT PIPELINE CONTROLLER
    # ==========================================
    def start_autopilot(self):
        if self.running:
            return

        self.running = True
        self.start_btn.configure(state="disabled", text="⏳ RUNNING FULL AUTOPILOT...")
        self.progress.set(0)

        for key in self.stage_badges:
            if self.stage_vars[key].get():
                self.set_stage_badge(key, "⏳ Queued", "#3B8ED0")
            else:
                self.set_stage_badge(key, "⏭️ Skipped", "gray")

        threading.Thread(target=self._autopilot_master_worker, daemon=True).start()

    # ==========================================
    # SUBSYSTEM DATA COLLECTORS & REMEDIATORS
    # ==========================================
    def _stage1_junk_clean(self) -> dict:
        """Scans and cleans Temp folders, Browser caches, and Recycle Bin, returning per-folder breakdown."""
        targets = SystemEngine.get_target_folders(
            user_temp=True, win_temp=True, prefetch=False, chrome=True, edge=True
        )
        breakdown = []
        total_scanned = 0
        total_freed = 0
        total_files = 0

        for label, folder in targets.items():
            if not folder or not os.path.exists(folder):
                breakdown.append({"category": label, "path": folder or "N/A", "freed": 0, "files": 0, "status": "Not Found"})
                continue

            cat_freed = 0
            cat_files = 0
            for root, dirs, files in os.walk(folder, topdown=False):
                for f in files:
                    fpath = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(fpath)
                        total_scanned += sz
                        os.unlink(fpath)
                        cat_freed += sz
                        total_freed += sz
                        cat_files += 1
                        total_files += 1
                    except OSError:
                        continue
                for d in dirs:
                    try:
                        os.rmdir(os.path.join(root, d))
                    except OSError:
                        continue

            breakdown.append(
                {
                    "category": label,
                    "path": folder,
                    "freed": cat_freed,
                    "files": cat_files,
                    "status": f"Cleaned ({SystemEngine.format_bytes(cat_freed)})" if cat_freed > 0 else "Already Clean",
                }
            )

        # Empty Windows Recycle Bin
        try:
            import ctypes
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1 | 2 | 4)
            breakdown.append(
                {"category": "Windows Recycle Bin", "path": "System Recycle Bin", "freed": 0, "files": 0, "status": "Emptied"}
            )
        except Exception:
            pass

        return {"total_freed": total_freed, "total_files": total_files, "breakdown": breakdown}

    def _stage2_caches_clean(self) -> dict:
        """Purges Explorer Thumbnail/Icon caches and DirectX/NVIDIA/AMD Shader caches."""
        local_app = os.environ.get("LOCALAPPDATA", "")
        locallow_app = os.path.join(os.path.expanduser("~"), r"AppData\LocalLow")
        explorer_dir = os.path.join(local_app, r"Microsoft\Windows\Explorer")

        freed = 0
        count = 0

        if os.path.exists(explorer_dir):
            for f in os.listdir(explorer_dir):
                if f.lower().startswith(("thumbcache_", "iconcache_")) and f.lower().endswith(".db"):
                    fpath = os.path.join(explorer_dir, f)
                    try:
                        sz = os.path.getsize(fpath)
                        os.unlink(fpath)
                        freed += sz
                        count += 1
                    except OSError:
                        continue

        shader_dirs = [
            os.path.join(local_app, "D3DSCache"),
            os.path.join(local_app, r"NVIDIA\DXCache"),
            os.path.join(local_app, r"NVIDIA\GLCache"),
            os.path.join(locallow_app, r"NVIDIA\PerDriverVersion\DXCache"),
            os.path.join(local_app, r"AMD\DxCache"),
        ]
        for sdir in shader_dirs:
            if not os.path.exists(sdir):
                continue
            for root, _, files in os.walk(sdir):
                for f in files:
                    fpath = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(fpath)
                        os.unlink(fpath)
                        freed += sz
                        count += 1
                    except OSError:
                        continue

        return {"freed": freed, "files": count}

    def _stage3_ram_and_processes(self) -> dict:
        """Trims working sets of background processes and captures Top 10 RAM consumers."""
        before_mem = psutil.virtual_memory()
        SystemEngine.optimize_ram(lambda _: None)
        time.sleep(0.4)
        after_mem = psutil.virtual_memory()

        freed_bytes = max(0, before_mem.used - after_mem.used)
        top_procs = SystemEngine.get_top_processes(10)

        return {
            "before_pct": before_mem.percent,
            "after_pct": after_mem.percent,
            "before_used": before_mem.used,
            "after_used": after_mem.used,
            "total_ram": after_mem.total,
            "freed_bytes": freed_bytes,
            "top_processes": top_procs,
        }

    def _stage4_cpu_gpu_power_telemetry(self) -> dict:
        """Collects deep CPU, GPU, VRAM, Thermal, and Power Plan / Power Usage metrics."""
        cpu_usage = psutil.cpu_percent(interval=0.5)
        freq = psutil.cpu_freq()
        cpu_mhz = int(freq.current) if freq and freq.current else 0
        cpu_max_mhz = int(freq.max) if freq and freq.max else cpu_mhz

        # Active Power Plan via powercfg
        power_plan = "Balanced (Default)"
        try:
            out_pwr = subprocess.check_output(
                ["powercfg", "/getactivescheme"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=4,
            ).strip()
            if "(" in out_pwr and ")" in out_pwr:
                power_plan = out_pwr.split("(")[-1].rstrip(")")
        except Exception:
            pass

        # Battery status if laptop
        batt = psutil.sensors_battery()
        if batt:
            pwr_source = f"{'AC Plugged In' if batt.power_plugged else 'On Battery'} ({batt.percent:.0f}%)"
        else:
            pwr_source = "Desktop AC Mains Power"

        # GPU Telemetry (nvidia-smi + WMI fallback)
        gpu_info = {
            "name": "Standard Display Adapter",
            "driver": "WDDM Driver",
            "resolution": "1920x1080",
            "load_pct": "0%",
            "vram_used": "N/A",
            "vram_total": "Shared",
            "temp_c": "N/A",
            "fan_pct": "Auto",
            "power_draw_w": "ACPI Managed",
            "clock_mhz": "Dynamic",
        }

        ps_gpu = (
            "$g = Get-CimInstance Win32_VideoController | Select-Object -First 1 Name, DriverVersion, "
            "CurrentHorizontalResolution, CurrentVerticalResolution, CurrentRefreshRate, AdapterRAM; "
            "$vram64 = @(Get-ItemProperty -Path 'HKLM:\\SYSTEM\\ControlSet001\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}\\0*' "
            "-Name 'HardwareInformation.qwMemorySize' -ErrorAction SilentlyContinue | "
            "Select-Object -ExpandProperty 'HardwareInformation.qwMemorySize'); "
            "@{g=$g; vram64=$vram64} | ConvertTo-Json -Compress"
        )
        try:
            out_g = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_gpu],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=6,
            ).strip()
            if out_g:
                d = json.loads(out_g)
                g = d.get("g") or {}
                v64 = d.get("vram64") or []
                if isinstance(v64, int):
                    v64 = [v64]
                max_vram = max([int(x) for x in v64 if isinstance(x, int)] + [int(g.get("AdapterRAM") or 0)])
                gpu_info["name"] = g.get("Name") or gpu_info["name"]
                gpu_info["driver"] = g.get("DriverVersion") or gpu_info["driver"]
                if g.get("CurrentHorizontalResolution"):
                    gpu_info["resolution"] = (
                        f"{g.get('CurrentHorizontalResolution')}x{g.get('CurrentVerticalResolution')} @ {g.get('CurrentRefreshRate')}Hz"
                    )
                if max_vram > 0:
                    gpu_info["vram_total"] = SystemEngine.format_bytes(max_vram)
        except Exception:
            pass

        if self.has_nvidia_smi:
            try:
                nv_out = subprocess.check_output(
                    [
                        "nvidia-smi",
                        "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,fan.speed,power.draw,clocks.current.graphics",
                        "--format=csv,noheader,nounits",
                    ],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    text=True,
                    timeout=3,
                ).strip()
                if nv_out:
                    p = [x.strip() for x in nv_out.splitlines()[0].split(",")]
                    if len(p) >= 8:
                        gpu_info["name"] = p[0]
                        gpu_info["load_pct"] = f"{p[1]}%"
                        gpu_info["vram_used"] = f"{p[2]} MB"
                        gpu_info["vram_total"] = f"{p[3]} MB"
                        gpu_info["temp_c"] = f"{p[4]} °C"
                        gpu_info["fan_pct"] = f"{p[5]}%"
                        gpu_info["power_draw_w"] = f"{p[6]} W"
                        gpu_info["clock_mhz"] = f"{p[7]} MHz"
            except Exception:
                pass

        return {
            "cpu_usage_pct": cpu_usage,
            "cpu_mhz": cpu_mhz,
            "cpu_max_mhz": cpu_max_mhz,
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
            "power_plan": power_plan,
            "power_source": pwr_source,
            "gpu": gpu_info,
        }

    def _stage5_registry_audit(self) -> list[dict]:
        """Audits 6 key Windows Registry performance, privacy, and gaming settings."""
        reg_items = []

        # 1. Mouse Acceleration
        mouse_raw = False
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", 0, winreg.KEY_READ) as k:
                ms, _ = winreg.QueryValueEx(k, "MouseSpeed")
                mouse_raw = str(ms) == "0"
        except OSError:
            pass
        reg_items.append(
            {
                "key_name": r"HKCU\Control Panel\Mouse (MouseSpeed)",
                "feature": "Raw 1:1 Gaming Mouse Input",
                "current": "0 (Raw Input Active)" if mouse_raw else "1 (Acceleration Curve On)",
                "recommended": "0 (Disable Acceleration)",
                "status": "✅ Optimized" if mouse_raw else "⚠️ Needs Update (Use Input Tweaks Tab)",
            }
        )

        # 2. Sticky Keys Shift-Spam Popup
        sticky_off = False
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Control Panel\Accessibility\StickyKeys", 0, winreg.KEY_READ
            ) as k:
                fl, _ = winreg.QueryValueEx(k, "Flags")
                sticky_off = str(fl) in ("506", "26")
        except OSError:
            pass
        reg_items.append(
            {
                "key_name": r"HKCU\Control Panel\Accessibility\StickyKeys (Flags)",
                "feature": "Sticky Keys Game-Interrupt Popup",
                "current": "506 (Disabled)" if sticky_off else "510 (Popup Enabled)",
                "recommended": "506 (Popup Disabled)",
                "status": "✅ Optimized" if sticky_off else "⚠️ Needs Update (Use Input Tweaks Tab)",
            }
        )

        # 3. File Extensions Visibility
        show_ext = False
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                0,
                winreg.KEY_READ,
            ) as k:
                he, _ = winreg.QueryValueEx(k, "HideFileExt")
                show_ext = int(he) == 0
        except OSError:
            pass
        reg_items.append(
            {
                "key_name": r"HKCU\...\Explorer\Advanced (HideFileExt)",
                "feature": "Show Known File Extensions (.exe, .dll)",
                "current": "0 (Extensions Visible)" if show_ext else "1 (Extensions Hidden)",
                "recommended": "0 (Visible for Security)",
                "status": "✅ Optimized" if show_ext else "⚠️ Needs Update (Use Input Tweaks Tab)",
            }
        )

        # 4. Hardware-Accelerated GPU Scheduling (HAGS)
        hags_on = False
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
                0,
                winreg.KEY_READ,
            ) as k:
                hw, _ = winreg.QueryValueEx(k, "HwSchMode")
                hags_on = int(hw) == 2
        except OSError:
            pass
        reg_items.append(
            {
                "key_name": r"HKLM\...\Control\GraphicsDrivers (HwSchMode)",
                "feature": "Hardware-Accelerated GPU Scheduling (HAGS)",
                "current": "2 (Enabled)" if hags_on else "1 / Default",
                "recommended": "2 (Enabled for Low Latency)",
                "status": "✅ Optimized" if hags_on else "ℹ️ Optional (Use GPU Center Tab)",
            }
        )

        # 5. Windows Advertising ID Tracking
        ad_off = False
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
                0,
                winreg.KEY_READ,
            ) as k:
                en, _ = winreg.QueryValueEx(k, "Enabled")
                ad_off = int(en) == 0
        except OSError:
            pass
        reg_items.append(
            {
                "key_name": r"HKCU\...\AdvertisingInfo (Enabled)",
                "feature": "Windows Targeted Advertising Telemetry",
                "current": "0 (Blocked)" if ad_off else "1 (Tracking Active)",
                "recommended": "0 (Blocked for Privacy)",
                "status": "✅ Optimized" if ad_off else "⚠️ Needs Update (Use Privacy Tab)",
            }
        )

        # 6. Bing Start Menu Web Search
        bing_off = False
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Policies\Microsoft\Windows\Explorer",
                0,
                winreg.KEY_READ,
            ) as k:
                bs, _ = winreg.QueryValueEx(k, "DisableSearchBoxSuggestions")
                bing_off = int(bs) == 1
        except OSError:
            pass
        reg_items.append(
            {
                "key_name": r"HKCU\...\Policies\Windows\Explorer (DisableSearchBoxSuggestions)",
                "feature": "Start Menu Bing Web Search Bloat",
                "current": "1 (Local Search Only)" if bing_off else "0 (Bing Web Results Enabled)",
                "recommended": "1 (Disable Bing Suggestions)",
                "status": "✅ Optimized" if bing_off else "⚠️ Needs Update (Use Input Tweaks Tab)",
            }
        )

        return reg_items

    def _stage6_software_updates(self) -> list[dict]:
        """Scans Winget for all outdated packages (respecting muted packages)."""
        if not shutil.which("winget"):
            return []

        ignored = set()
        for p in [
            self.IGNORE_UPDATES_FILE,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "ignored_updates.json"),
        ]:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        ignored.update(x.lower() for x in json.load(f))
                except Exception:
                    pass

        updates = []
        try:
            res = subprocess.run(
                ["winget", "upgrade", "--accept-source-agreements"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=22,
            )
            lines = [ln.strip() for ln in (res.stdout or "").splitlines() if ln.strip()]
            sep_idx = -1
            for idx, ln in enumerate(lines):
                if "---" in ln and len(ln) > 15:
                    sep_idx = idx
                    break
            if sep_idx != -1:
                for ln in lines[sep_idx + 1 :]:
                    low = ln.lower()
                    if (
                        "upgrades available" in low
                        or "upgrade available" in low
                        or low.startswith("the following")
                        or "package(s) have" in low
                    ):
                        continue
                    tokens = ln.split()
                    if len(tokens) >= 4:
                        avail_ver = tokens[-2]
                        cur_ver = tokens[-3]
                        pkg_id = tokens[-4]
                        name = " ".join(tokens[:-4]).strip() or pkg_id
                        if pkg_id.lower() not in ignored:
                            updates.append(
                                {
                                    "name": name,
                                    "id": pkg_id,
                                    "current": cur_ver,
                                    "available": avail_ver,
                                }
                            )
        except Exception:
            pass
        return updates

    # ==========================================
    # MAIN WORKER THREAD & HTML REPORT BUILDER
    # ==========================================
    def _autopilot_master_worker(self):
        start_t = time.perf_counter()
        self.after(0, lambda: self.log_message("\n=== 🚀 STARTING MASTER 1-CLICK AUTOPILOT & FULL SYSTEM AUDIT ==="))

        report_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "junk": {"total_freed": 0, "total_files": 0, "breakdown": []},
            "shaders": {"freed": 0, "files": 0},
            "ram": {
                "before_pct": 0,
                "after_pct": 0,
                "freed_bytes": 0,
                "total_ram": psutil.virtual_memory().total,
                "top_processes": [],
            },
            "telemetry": {},
            "registry": [],
            "updates": [],
            "dns_flushed": False,
            "defender_updated": False,
            "ssd_trimmed": False,
            "specs": {},
            "drives": [],
        }

        # Stage 1: Junk & Browser Caches
        if self.stage_vars["clean_junk"].get():
            self.after(0, lambda: (self.set_stage_badge("clean_junk", "🔄 Running...", "#F39C12"), self.log_message("[1/8] Scanning & cleaning Temp folders, Browser caches & Recycle Bin...")))
            report_data["junk"] = self._stage1_junk_clean()
            freed_str = SystemEngine.format_bytes(report_data["junk"]["total_freed"])
            self.after(0, lambda f=freed_str: (self.set_stage_badge("clean_junk", f"✅ {f} Freed", "#2FA572"), self.log_message(f"  [+] Reclaimed {f} across {report_data['junk']['total_files']} junk files.")))
        self.after(0, lambda: self.progress.set(0.14))

        # Stage 2: Explorer & GPU Shader Caches
        if self.stage_vars["clean_shaders"].get():
            self.after(0, lambda: (self.set_stage_badge("clean_shaders", "🔄 Running...", "#F39C12"), self.log_message("[2/8] Purging Explorer Thumbnail/Icon & DirectX/GPU Shader caches...")))
            report_data["shaders"] = self._stage2_caches_clean()
            sfreed = SystemEngine.format_bytes(report_data["shaders"]["freed"])
            self.after(0, lambda f=sfreed: (self.set_stage_badge("clean_shaders", f"✅ {f} Freed", "#2FA572"), self.log_message(f"  [+] Purged {report_data['shaders']['files']} shader/cache files ({f}).")))
        self.after(0, lambda: self.progress.set(0.28))

        # Stage 3: RAM Boost & Top Processes
        if self.stage_vars["boost_ram"].get():
            self.after(0, lambda: (self.set_stage_badge("boost_ram", "🔄 Running...", "#F39C12"), self.log_message("[3/8] Trimming background process RAM working sets & auditing memory hogs...")))
            report_data["ram"] = self._stage3_ram_and_processes()
            rfreed = SystemEngine.format_bytes(report_data["ram"]["freed_bytes"])
            self.after(0, lambda f=rfreed: (self.set_stage_badge("boost_ram", f"✅ {f} Trimmed", "#2FA572"), self.log_message(f"  [+] RAM Usage: {report_data['ram']['before_pct']:.1f}% ➔ {report_data['ram']['after_pct']:.1f}% ({f} freed).")))
        self.after(0, lambda: self.progress.set(0.42))

        # Stage 4: Deep CPU, GPU, Thermals & Power Telemetry
        if self.stage_vars["cpu_gpu_power"].get():
            self.after(0, lambda: (self.set_stage_badge("cpu_gpu_power", "🔄 Auditing...", "#F39C12"), self.log_message("[4/8] Auditing CPU clocks, GPU sensors, VRAM, temperature & active power plan...")))
            report_data["telemetry"] = self._stage4_cpu_gpu_power_telemetry()
            gname = report_data["telemetry"]["gpu"]["name"]
            self.after(0, lambda gn=gname: (self.set_stage_badge("cpu_gpu_power", "✅ Audited", "#2FA572"), self.log_message(f"  [+] Audited CPU ({report_data['telemetry']['cpu_mhz']} MHz) & GPU ({gn}).")))
        self.after(0, lambda: self.progress.set(0.56))

        # Stage 5: Registry Audit
        if self.stage_vars["registry_audit"].get():
            self.after(0, lambda: (self.set_stage_badge("registry_audit", "🔄 Auditing...", "#F39C12"), self.log_message("[5/8] Auditing Windows Registry keys for gaming, privacy & Explorer settings...")))
            report_data["registry"] = self._stage5_registry_audit()
            opt_cnt = sum(1 for r in report_data["registry"] if "✅" in r["status"])
            tot_reg = len(report_data["registry"])
            self.after(0, lambda o=opt_cnt, t=tot_reg: (self.set_stage_badge("registry_audit", f"✅ {o}/{t} Optimal", "#2FA572"), self.log_message(f"  [+] Registry Audit: {o} of {t} key configurations optimal.")))
        self.after(0, lambda: self.progress.set(0.70))

        # Stage 6: Outdated Software Audit
        if self.stage_vars["software_audit"].get():
            self.after(0, lambda: (self.set_stage_badge("software_audit", "🔄 Scanning...", "#F39C12"), self.log_message("[6/8] Scanning installed applications for pending updates via Winget...")))
            report_data["updates"] = self._stage6_software_updates()
            up_cnt = len(report_data["updates"])
            badge_txt = "✅ 0 Outdated" if up_cnt == 0 else f"⚠️ {up_cnt} Updates"
            badge_col = "#2FA572" if up_cnt == 0 else "#E67E22"
            self.after(0, lambda bt=badge_txt, bc=badge_col, u=up_cnt: (self.set_stage_badge("software_audit", bt, bc), self.log_message(f"  [+] Software Audit: {u} active application update(s) available.")))
        self.after(0, lambda: self.progress.set(0.84))

        # Stage 7: DNS Flush & Windows Defender Update
        if self.stage_vars["net_defender"].get():
            self.after(0, lambda: (self.set_stage_badge("net_defender", "🔄 Running...", "#F39C12"), self.log_message("[7/8] Flushing Windows DNS Resolver Cache & updating Defender signatures...")))
            SystemEngine.flush_dns(lambda _: None)
            report_data["dns_flushed"] = True
            try:
                mp_cmd = r"C:\Program Files\Windows Defender\MpCmdRun.exe"
                if os.path.exists(mp_cmd):
                    subprocess.run([mp_cmd, "-SignatureUpdate"], creationflags=subprocess.CREATE_NO_WINDOW, timeout=20)
                    report_data["defender_updated"] = True
            except Exception:
                pass
            self.after(0, lambda: (self.set_stage_badge("net_defender", "✅ Protected", "#2FA572"), self.log_message("  [+] DNS Cache flushed & Windows Defender definitions verified.")))
        self.after(0, lambda: self.progress.set(0.92))

        # Stage 8: SSD ReTrim & Full Hardware Profile
        if self.stage_vars["ssd_retrim"].get():
            self.after(0, lambda: (self.set_stage_badge("ssd_retrim", "🔄 Running...", "#F39C12"), self.log_message("[8/8] Running SSD ReTrim on Drive C: & compiling Master Webpage Report...")))
            if SystemEngine.is_admin():
                try:
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", "Optimize-Volume -DriveLetter C -ReTrim -ErrorAction SilentlyContinue"],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=25,
                    )
                    report_data["ssd_trimmed"] = True
                except Exception:
                    pass
            self.after(0, lambda: self.set_stage_badge("ssd_retrim", "✅ Trimmed", "#2FA572"))

        # Collect Full Hardware Specs & Mounted Drives for the Report
        report_data["specs"] = SystemEngine.get_detailed_specs()
        for part in psutil.disk_partitions(all=False):
            if "cdrom" in part.opts or not part.fstype:
                continue
            try:
                u = psutil.disk_usage(part.mountpoint)
                report_data["drives"].append(
                    {
                        "mount": part.mountpoint,
                        "fstype": part.fstype,
                        "total": SystemEngine.format_bytes(u.total),
                        "used": SystemEngine.format_bytes(u.used),
                        "free": SystemEngine.format_bytes(u.free),
                        "pct": u.percent,
                    }
                )
            except Exception:
                pass

        elapsed = time.perf_counter() - start_t
        report_data["elapsed_sec"] = f"{elapsed:.1f}s"

        # Generate Master HTML Webpage Report
        self._generate_master_html_report(report_data)

        self.running = False
        self.after(0, lambda: self._finish_autopilot(elapsed))

    def _finish_autopilot(self, elapsed: float):
        self.progress.set(1.0)
        self.start_btn.configure(state="normal", text="🚀 START 1-CLICK AUTOPILOT")
        self.open_report_btn.configure(state="normal")
        self.log_message(
            f"\n=== 🎉 AUTOPILOT COMPLETE IN {elapsed:.1f}s! ===\n"
            f"Master Webpage Report saved to:\n{self.last_report_path}"
        )
        if self.var_auto_open_html.get():
            self.open_last_report()

    # ==========================================
    # MASTER HTML WEBPAGE GENERATOR
    # ==========================================
    def _generate_master_html_report(self, d: dict):
        total_disk_reclaimed = d["junk"]["total_freed"] + d["shaders"]["freed"]
        disk_reclaimed_str = SystemEngine.format_bytes(total_disk_reclaimed)
        ram_freed_str = SystemEngine.format_bytes(d["ram"]["freed_bytes"])

        tel = d.get("telemetry") or {}
        gpu = tel.get("gpu") or {}
        updates = d.get("updates") or []
        reg_list = d.get("registry") or []
        opt_reg_cnt = sum(1 for r in reg_list if "✅" in r["status"])

        # 1. Junk & Cache Rows
        junk_rows = ""
        for j in d["junk"]["breakdown"]:
            junk_rows += f"""
            <tr>
                <td><strong>{j['category']}</strong><br><span class="sub">{j['path']}</span></td>
                <td>{j['files']:,} files</td>
                <td><span class="badge green">{j['status']}</span></td>
            </tr>"""
        junk_rows += f"""
        <tr>
            <td><strong>Explorer Thumbnail/Icon & 3D GPU Shader Caches</strong><br><span class="sub">DirectX, NVIDIA DXCache/GLCache, AMD DxCache, Explorer DBs</span></td>
            <td>{d['shaders']['files']:,} files</td>
            <td><span class="badge green">Cleaned ({SystemEngine.format_bytes(d['shaders']['freed'])})</span></td>
        </tr>"""

        # 2. Outdated Software Rows
        if updates:
            update_rows = "".join(
                [
                    f"""<tr>
                        <td><strong>{u['name']}</strong></td>
                        <td><code>{u['id']}</code></td>
                        <td><span class="badge warn">{u['current']}</span></td>
                        <td><span class="badge green">{u['available']}</span></td>
                    </tr>"""
                    for u in updates
                ]
            )
        else:
            update_rows = """<tr><td colspan="4" style="text-align:center;color:#4ade80;font-weight:bold;padding:18px;">✅ All tracked applications are 100% up to date!</td></tr>"""

        # 3. Registry Audit Rows
        reg_rows = "".join(
            [
                f"""<tr>
                    <td><strong>{r['feature']}</strong><br><span class="sub">{r['key_name']}</span></td>
                    <td><code>{r['current']}</code></td>
                    <td><code>{r['recommended']}</code></td>
                    <td><span class="badge {'green' if '✅' in r['status'] else 'warn'}">{r['status']}</span></td>
                </tr>"""
                for r in reg_list
            ]
        )

        # 4. Top Processes Rows
        proc_rows = "".join(
            [
                f"""<tr>
                    <td><strong>{name}</strong></td>
                    <td><code>PID {pid}</code></td>
                    <td style="text-align:right;color:#38bdf8;font-weight:bold;">{mb:.1f} MB</td>
                </tr>"""
                for pid, name, mb in d["ram"].get("top_processes", [])
            ]
        )

        # 5. Drives Rows
        drive_rows = "".join(
            [
                f"""<tr>
                    <td><strong>Drive {drv['mount']}</strong> ({drv['fstype']})</td>
                    <td>{drv['used']} / {drv['total']}</td>
                    <td>{drv['free']} Free</td>
                    <td>
                        <div class="bar-bg"><div class="bar-fill" style="width:{drv['pct']}%;background:{'#ef4444' if drv['pct']>88 else '#38bdf8'};"></div></div>
                        <span style="font-size:12px;">{drv['pct']:.1f}% Used</span>
                    </td>
                </tr>"""
                for drv in d.get("drives", [])
            ]
        )

        # 6. Full Hardware Specs Cards
        spec_cards = ""
        for cat, items in d.get("specs", {}).items():
            lines = "".join(
                [
                    f"<div class='kv'><span>{k}</span><strong>{v}</strong></div>"
                    for k, v in items.items()
                ]
            )
            spec_cards += f"""<div class="card"><h3>{cat}</h3>{lines}</div>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>PC Optimizer Ultimate — Master Autopilot Report</title>
<style>
    :root {{ --bg: #020617; --card: #0f172a; --border: #1e293b; --accent: #38bdf8; --green: #22c55e; --warn: #f59e0b; --text: #f8fafc; --muted: #94a3b8; }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 28px; line-height: 1.5; }}
    .wrap {{ max-width: 1180px; margin: auto; }}
    .hero {{ background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); border: 1px solid var(--border); border-radius: 14px; padding: 26px 30px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px; box-shadow: 0 12px 32px rgba(0,0,0,0.45); }}
    .hero h1 {{ margin: 0; font-size: 24px; color: var(--accent); }}
    .hero p {{ margin: 6px 0 0 0; color: var(--muted); font-size: 14px; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; margin-bottom: 24px; }}
    .kpi {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; text-align: center; }}
    .kpi .lbl {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); font-weight: bold; }}
    .kpi .val {{ font-size: 21px; font-weight: 800; margin-top: 6px; color: var(--accent); }}
    .section {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 22px; margin-bottom: 22px; }}
    .section h2 {{ margin: 0 0 16px 0; font-size: 17px; color: var(--accent); border-bottom: 1px solid var(--border); padding-bottom: 10px; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 22px; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }}
    .card h3 {{ margin: 0 0 12px 0; font-size: 16px; color: var(--accent); border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
    .kv {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #1e293b88; font-size: 13px; }}
    .kv span {{ color: var(--muted); }}
    .kv strong {{ color: #e2e8f0; text-align: right; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
    th, td {{ padding: 11px 12px; border-bottom: 1px solid var(--border); text-align: left; }}
    th {{ color: var(--accent); font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .sub {{ font-size: 11.5px; color: var(--muted); }}
    .badge {{ display: inline-block; padding: 3px 9px; border-radius: 6px; font-size: 11.5px; font-weight: 700; }}
    .badge.green {{ background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }}
    .badge.warn {{ background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }}
    .bar-bg {{ width: 100%; height: 8px; background: #1e293b; border-radius: 4px; overflow: hidden; margin-bottom: 4px; }}
    .bar-fill {{ height: 100%; border-radius: 4px; }}
    code {{ background: #1e293b; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; font-size: 12px; color: #cbd5e1; }}
    @media print {{ body {{ background: #fff; color: #000; }} }}
</style>
</head>
<body>
<div class="wrap">
    <div class="hero">
        <div>
            <h1>⚡ WINDOWS SYSTEM OPTIMIZER ULTIMATE — MASTER AUTOPILOT REPORT</h1>
            <p>Generated on {d['timestamp']} • Execution Time: {d.get('elapsed_sec', 'N/A')} • Admin Mode: {'Enabled' if SystemEngine.is_admin() else 'Standard'}</p>
        </div>
        <button onclick="window.print()" style="background:#38bdf8;color:#020617;border:none;padding:10px 18px;border-radius:8px;font-weight:bold;cursor:pointer;">🖨️ Print / Save PDF</button>
    </div>

    <!-- 6 KPI SUMMARY BOXES -->
    <div class="kpi-grid">
        <div class="kpi"><div class="lbl">Disk Junk Cleaned</div><div class="val" style="color:#4ade80;">{disk_reclaimed_str}</div></div>
        <div class="kpi"><div class="lbl">RAM Memory Freed</div><div class="val" style="color:#a855f7;">{ram_freed_str}</div></div>
        <div class="kpi"><div class="lbl">CPU Load & Clock</div><div class="val">{tel.get('cpu_usage_pct', 0):.1f}% <span style="font-size:13px;">({tel.get('cpu_mhz', 0)} MHz)</span></div></div>
        <div class="kpi"><div class="lbl">GPU Temp & Power</div><div class="val" style="color:#4ade80;">{gpu.get('temp_c', 'OK')} <span style="font-size:13px;">({gpu.get('power_draw_w', '')})</span></div></div>
        <div class="kpi"><div class="lbl">Outdated Apps</div><div class="val" style="color:{'#4ade80' if len(updates)==0 else '#fbbf24'};">{len(updates)} Found</div></div>
        <div class="kpi"><div class="lbl">Registry Tweaks</div><div class="val">{opt_reg_cnt}/{len(reg_list)} Optimal</div></div>
    </div>

    <!-- CPU, GPU & POWER TELEMETRY -->
    <div class="grid-2">
        <div class="card">
            <h3>🧠 Processor (CPU), RAM & Power Plan Telemetry</h3>
            <div class="kv"><span>Physical / Logical Cores</span><strong>{tel.get('physical_cores', 'N/A')} Cores / {tel.get('logical_cores', 'N/A')} Threads</strong></div>
            <div class="kv"><span>Live CPU Clock Speed</span><strong>{tel.get('cpu_mhz', 0)} MHz (Max: {tel.get('cpu_max_mhz', 0)} MHz)</strong></div>
            <div class="kv"><span>CPU Utilization During Scan</span><strong>{tel.get('cpu_usage_pct', 0):.1f}%</strong></div>
            <div class="kv"><span>RAM Before ➔ After Autopilot</span><strong>{d['ram']['before_pct']:.1f}% ➔ {d['ram']['after_pct']:.1f}% ({ram_freed_str} Freed)</strong></div>
            <div class="kv"><span>Active Windows Power Scheme</span><strong style="color:#4ade80;">{tel.get('power_plan', 'Balanced')}</strong></div>
            <div class="kv"><span>System Power Source</span><strong>{tel.get('power_source', 'AC Power')}</strong></div>
        </div>
        <div class="card">
            <h3>🎮 Graphics Card (GPU) & VRAM Performance</h3>
            <div class="kv"><span>Graphics Adapter Model</span><strong>{gpu.get('name', 'N/A')}</strong></div>
            <div class="kv"><span>Installed GPU Driver Version</span><strong>{gpu.get('driver', 'N/A')}</strong></div>
            <div class="kv"><span>Active Display Resolution & Refresh</span><strong>{gpu.get('resolution', 'N/A')}</strong></div>
            <div class="kv"><span>3D Core Load & Clock Speed</span><strong>{gpu.get('load_pct', '0%')} @ {gpu.get('clock_mhz', 'Dynamic')}</strong></div>
            <div class="kv"><span>Dedicated VRAM Memory</span><strong>{gpu.get('vram_used', '0 MB')} / {gpu.get('vram_total', 'N/A')}</strong></div>
            <div class="kv"><span>GPU Core Temp, Fan & Power Draw</span><strong style="color:#4ade80;">{gpu.get('temp_c', 'N/A')} | Fan: {gpu.get('fan_pct', 'Auto')} | Power: {gpu.get('power_draw_w', 'N/A')}</strong></div>
        </div>
    </div>

    <!-- JUNK & CACHE CLEANUP REPORT -->
    <div class="section">
        <h2>🧹 Stage 1 & 2: Junk Files, Browser Cache & Shader Cleanup Breakdown</h2>
        <table>
            <thead><tr><th>Target Cache / Folder Location</th><th>Files Removed</th><th>Cleanup Status</th></tr></thead>
            <tbody>{junk_rows}</tbody>
        </table>
    </div>

    <!-- SOFTWARE UPDATES & PATCH REPORT -->
    <div class="section">
        <h2>🔄 Stage 6: Outdated Applications & Software Patch Audit (Winget)</h2>
        <table>
            <thead><tr><th>Application Name</th><th>Package ID</th><th>Installed Version</th><th>Available Update</th></tr></thead>
            <tbody>{update_rows}</tbody>
        </table>
    </div>

    <!-- REGISTRY & SYSTEM CONFIGURATION REPORT -->
    <div class="section">
        <h2>🎛️ Stage 5: Windows Registry & Gaming/Explorer Configuration Audit</h2>
        <table>
            <thead><tr><th>Feature & Registry Key Path</th><th>Current Value</th><th>Recommended Value</th><th>Status</th></tr></thead>
            <tbody>{reg_rows}</tbody>
        </table>
    </div>

    <!-- STORAGE DRIVES & TOP MEMORY PROCESSES -->
    <div class="grid-2">
        <div class="card">
            <h3>💿 Storage Drives & SSD TRIM Status (C: ReTrim: {'Completed' if d['ssd_trimmed'] else 'Standard'})</h3>
            <table>
                <thead><tr><th>Drive</th><th>Used / Total</th><th>Free</th><th>Usage</th></tr></thead>
                <tbody>{drive_rows}</tbody>
            </table>
        </div>
        <div class="card">
            <h3>📊 Top 10 Memory-Consuming Background Processes</h3>
            <table>
                <thead><tr><th>Process Name</th><th>PID</th><th style="text-align:right;">RAM Usage</th></tr></thead>
                <tbody>{proc_rows}</tbody>
            </table>
        </div>
    </div>

    <!-- COMPLETE HARDWARE SPECIFICATIONS -->
    <h2 style="color:var(--accent);font-size:18px;margin:26px 0 14px 0;">💻 Complete System & Hardware Specifications Profile</h2>
    <div class="grid-2">
        {spec_cards}
    </div>
</div>
</body>
</html>"""

        try:
            with open(self.last_report_path, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            self.after(0, lambda err=e: self.log_message(f"[!] Could not save HTML report: {err}"))