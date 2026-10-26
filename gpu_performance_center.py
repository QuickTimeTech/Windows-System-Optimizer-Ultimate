# gpu_performance_center.py
import os
import json
import shutil
import winreg
import threading
import subprocess
import customtkinter as ctk
from backend_engine import SystemEngine


class GpuPerformanceCenterView(ctk.CTkFrame):
    """Modular GPU Hardware Inspector, Live Telemetry Monitor & Shader/HAGS Optimizer."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.polling_active = False
        self.has_nvidia_smi = shutil.which("nvidia-smi") is not None
        self.gpu_specs_list = []

        # ==========================================
        # TOP LIVE GPU TELEMETRY GAUGES
        # ==========================================
        telemetry_card = ctk.CTkFrame(self)
        telemetry_card.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="ew")
        telemetry_card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        header = ctk.CTkFrame(telemetry_card, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=4, padx=15, pady=(10, 6), sticky="ew")

        self.gpu_title_lbl = ctk.CTkLabel(
            header,
            text="🎮 LIVE GRAPHICS CARD TELEMETRY & PERFORMANCE",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#3B8ED0",
        )
        self.gpu_title_lbl.pack(side="left")

        self.poll_switch_var = ctk.BooleanVar(value=True)
        self.poll_switch = ctk.CTkSwitch(
            header,
            text="Live Telemetry Polling (2s)",
            variable=self.poll_switch_var,
            progress_color="#2FA572",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.toggle_polling,
        )
        self.poll_switch.pack(side="right")

        # Gauge 1: GPU 3D Core Load
        g1 = ctk.CTkFrame(telemetry_card, fg_color=("gray85", "gray17"))
        g1.grid(row=1, column=0, padx=(15, 6), pady=(0, 12), sticky="nsew")
        ctk.CTkLabel(g1, text="3D CORE LOAD", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray").pack(
            pady=(8, 0)
        )
        self.load_val_lbl = ctk.CTkLabel(
            g1, text="0.0%", font=ctk.CTkFont(size=22, weight="bold"), text_color="#3B8ED0"
        )
        self.load_val_lbl.pack(pady=2)
        self.load_bar = ctk.CTkProgressBar(g1, height=10, progress_color="#3B8ED0")
        self.load_bar.pack(fill="x", padx=12, pady=(2, 10))
        self.load_bar.set(0)

        # Gauge 2: Dedicated VRAM Usage
        g2 = ctk.CTkFrame(telemetry_card, fg_color=("gray85", "gray17"))
        g2.grid(row=1, column=1, padx=6, pady=(0, 12), sticky="nsew")
        ctk.CTkLabel(g2, text="VRAM MEMORY", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray").pack(
            pady=(8, 0)
        )
        self.vram_val_lbl = ctk.CTkLabel(
            g2, text="0 MB / 0 MB", font=ctk.CTkFont(size=18, weight="bold"), text_color="#9B59B6"
        )
        self.vram_val_lbl.pack(pady=4)
        self.vram_bar = ctk.CTkProgressBar(g2, height=10, progress_color="#9B59B6")
        self.vram_bar.pack(fill="x", padx=12, pady=(2, 10))
        self.vram_bar.set(0)

        # Gauge 3: GPU Temperature & Fan Speed
        g3 = ctk.CTkFrame(telemetry_card, fg_color=("gray85", "gray17"))
        g3.grid(row=1, column=2, padx=6, pady=(0, 12), sticky="nsew")
        ctk.CTkLabel(
            g3, text="GPU TEMP & FAN", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray"
        ).pack(pady=(8, 0))
        self.temp_val_lbl = ctk.CTkLabel(
            g3, text="-- °C", font=ctk.CTkFont(size=22, weight="bold"), text_color="#2FA572"
        )
        self.temp_val_lbl.pack(pady=2)
        self.fan_sub_lbl = ctk.CTkLabel(g3, text="Fan Speed: --%", font=ctk.CTkFont(size=11), text_color="lightgray")
        self.fan_sub_lbl.pack(pady=(0, 8))

        # Gauge 4: Clocks & Power Draw
        g4 = ctk.CTkFrame(telemetry_card, fg_color=("gray85", "gray17"))
        g4.grid(row=1, column=3, padx=(6, 15), pady=(0, 12), sticky="nsew")
        ctk.CTkLabel(
            g4, text="CLOCK & POWER", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray"
        ).pack(pady=(8, 0))
        self.clock_val_lbl = ctk.CTkLabel(
            g4, text="-- MHz", font=ctk.CTkFont(size=20, weight="bold"), text_color="#E67E22"
        )
        self.clock_val_lbl.pack(pady=2)
        self.power_sub_lbl = ctk.CTkLabel(
            g4, text="Power: -- W", font=ctk.CTkFont(size=11), text_color="lightgray"
        )
        self.power_sub_lbl.pack(pady=(0, 8))

        # ==========================================
        # MIDDLE ROW: HARDWARE SPECS & OPTIMIZER TOOLS
        # ==========================================
        # Left Card: Detailed GPU Specs
        specs_card = ctk.CTkFrame(self)
        specs_card.grid(row=1, column=0, padx=(0, 8), pady=(0, 10), sticky="nsew")

        spec_hdr = ctk.CTkFrame(specs_card, fg_color="transparent")
        spec_hdr.pack(fill="x", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            spec_hdr,
            text="🔍 INSTALLED DISPLAY ADAPTER SPECS",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3B8ED0",
        ).pack(side="left")

        ctk.CTkButton(
            spec_hdr,
            text="🔄 Refresh Specs",
            width=120,
            height=26,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.load_gpu_specs,
        ).pack(side="right")

        self.specs_box = ctk.CTkFrame(specs_card, fg_color="transparent")
        self.specs_box.pack(fill="both", expand=True, padx=15, pady=(4, 12))

        # Right Card: GPU Maintenance & Boost Tools
        tools_card = ctk.CTkFrame(self)
        tools_card.grid(row=1, column=1, padx=(8, 0), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            tools_card,
            text="⚡ GPU SHADER CACHE & HAGS OPTIMIZER",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#2FA572",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        self.hags_status_lbl = ctk.CTkLabel(
            tools_card,
            text="Hardware-Accelerated GPU Scheduling (HAGS): Checking...",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray",
        )
        self.hags_status_lbl.pack(anchor="w", padx=15, pady=(0, 8))

        self.shader_btn = ctk.CTkButton(
            tools_card,
            text="🧹 Purge DirectX, NVIDIA & AMD Shader Caches (Fixes Stutters)",
            height=34,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(weight="bold"),
            command=self.clear_shader_caches,
        )
        self.shader_btn.pack(fill="x", padx=15, pady=4)

        hags_row = ctk.CTkFrame(tools_card, fg_color="transparent")
        hags_row.pack(fill="x", padx=15, pady=4)

        ctk.CTkButton(
            hags_row,
            text="⚡ Enable HAGS (Admin)",
            height=32,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.set_hags_mode(True),
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        ctk.CTkButton(
            hags_row,
            text="⏸️ Disable HAGS (Admin)",
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.set_hags_mode(False),
        ).pack(side="right", expand=True, fill="x", padx=(4, 0))

        bottom_tools_row = ctk.CTkFrame(tools_card, fg_color="transparent")
        bottom_tools_row.pack(fill="x", padx=15, pady=(4, 12))

        ctk.CTkButton(
            bottom_tools_row,
            text="🔄 Restart GPU Driver",
            height=32,
            fg_color="#D35400",
            hover_color="#A04000",
            font=ctk.CTkFont(weight="bold"),
            command=self.restart_gpu_driver,
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        ctk.CTkButton(
            bottom_tools_row,
            text="🖥️ Windows Graphics Settings",
            height=32,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: subprocess.Popen(["explorer.exe", "ms-settings:display-advancedgraphics"]),
        ).pack(side="right", expand=True, fill="x", padx=(4, 0))

        # ==========================================
        # BOTTOM LOG & TELEMETRY HISTORY CONSOLE
        # ==========================================
        self.log_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.log_message(
            f"GPU Performance Center Initialized. "
            f"Telemetry Mode: {'NVIDIA-SMI Direct Hardware Sensors' if self.has_nvidia_smi else 'Windows WDDM 3D Performance Counters'}."
        )

        self.check_hags_status()

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ==========================================
    # LIVE GPU TELEMETRY POLLING
    # ==========================================
    def start_polling(self):
        if not self.polling_active:
            self.polling_active = True
            if not self.gpu_specs_list:
                self.load_gpu_specs()
            self._poll_cycle()

    def toggle_polling(self):
        if self.poll_switch_var.get():
            self.polling_active = True
            self._poll_cycle()
        else:
            self.polling_active = False

    def _poll_cycle(self):
        if not self.polling_active or not self.poll_switch_var.get():
            return

        def worker():
            metrics = self._fetch_live_gpu_metrics()
            self.after(0, lambda m=metrics: self._update_gauges(m))

        threading.Thread(target=worker, daemon=True).start()
        self.after(2200, self._poll_cycle)

    def _fetch_live_gpu_metrics(self) -> dict:
        """Queries nvidia-smi if available, otherwise uses Windows WDDM GPU Performance Counters."""
        if self.has_nvidia_smi:
            try:
                out = subprocess.check_output(
                    [
                        "nvidia-smi",
                        "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,fan.speed,power.draw,clocks.current.graphics",
                        "--format=csv,noheader,nounits",
                    ],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    text=True,
                    timeout=2,
                ).strip()
                if out:
                    line = out.splitlines()[0]
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 8:
                        name = parts[0]
                        load = float(parts[1]) if parts[1].replace(".", "").isdigit() else 0.0
                        vram_used = float(parts[2]) if parts[2].replace(".", "").isdigit() else 0.0
                        vram_total = float(parts[3]) if parts[3].replace(".", "").isdigit() else 1.0
                        temp = parts[4] if parts[4].replace(".", "").isdigit() else "--"
                        fan = parts[5] if parts[5].replace(".", "").isdigit() else "Auto"
                        power = parts[6] if parts[6].replace(".", "").isdigit() else "--"
                        clock = parts[7] if parts[7].replace(".", "").isdigit() else "--"
                        return {
                            "name": name,
                            "load": load,
                            "vram_used": vram_used,
                            "vram_total": vram_total,
                            "temp": f"{temp} °C",
                            "temp_num": float(temp) if temp != "--" else 0,
                            "fan": f"Fan Speed: {fan}%",
                            "clock": f"{clock} MHz",
                            "power": f"Power Draw: {power} W",
                        }
            except Exception:
                pass

        # Fallback for AMD Radeon / Intel Arc / Integrated GPUs via Windows WDDM Counters
        ps_cmd = (
            "$load = (Get-Counter '\\GPU Engine(*engtype_3D)\\Utilization Percentage' -ErrorAction SilentlyContinue).CounterSamples "
            "| Measure-Object -Property CookedValue -Sum | Select-Object -ExpandProperty Sum; "
            "$vram = (Get-Counter '\\GPU Adapter Memory(*)\\Dedicated Usage' -ErrorAction SilentlyContinue).CounterSamples "
            "| Measure-Object -Property CookedValue -Maximum | Select-Object -ExpandProperty Maximum; "
            "@{load=$load; vram=$vram} | ConvertTo-Json -Compress"
        )
        load_val = 0.0
        vram_used_mb = 0.0
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=3,
            ).strip()
            if out:
                d = json.loads(out)
                load_val = min(100.0, float(d.get("load") or 0.0))
                vram_used_mb = float(d.get("vram") or 0.0) / (1024 * 1024)
        except Exception:
            pass

        total_vram_mb = self.gpu_specs_list[0].get("vram_mb", 4096) if self.gpu_specs_list else 4096
        gpu_name = self.gpu_specs_list[0].get("name", "Graphics Adapter") if self.gpu_specs_list else "Graphics Adapter"

        return {
            "name": gpu_name,
            "load": load_val,
            "vram_used": vram_used_mb,
            "vram_total": max(1.0, float(total_vram_mb)),
            "temp": "WDDM Active",
            "temp_num": 50,
            "fan": "Sensor: Windows WDDM",
            "clock": "Dynamic Boost",
            "power": "ACPI Managed",
        }

    def _update_gauges(self, m: dict):
        self.gpu_title_lbl.configure(text=f"🎮 LIVE GPU TELEMETRY — {m['name']}")

        load = m["load"]
        self.load_val_lbl.configure(text=f"{load:.1f}%")
        self.load_bar.set(min(1.0, load / 100.0))

        used = m["vram_used"]
        tot = m["vram_total"]
        pct = min(1.0, used / tot) if tot > 0 else 0
        self.vram_val_lbl.configure(text=f"{used:.0f} / {tot:.0f} MB ({pct * 100:.0f}%)")
        self.vram_bar.set(pct)

        t_col = "#2FA572" if m["temp_num"] < 75 else ("#E67E22" if m["temp_num"] < 85 else "#E74C3C")
        self.temp_val_lbl.configure(text=m["temp"], text_color=t_col)
        self.fan_sub_lbl.configure(text=m["fan"])

        self.clock_val_lbl.configure(text=m["clock"])
        self.power_sub_lbl.configure(text=m["power"])

    # ==========================================
    # GPU HARDWARE SPECIFICATIONS LOADER
    # ==========================================
    def load_gpu_specs(self):
        def worker():
            ps_cmd = (
                "$gpus = @(Get-CimInstance Win32_VideoController | "
                "Select-Object Name, DriverVersion, DriverDate, VideoProcessor, "
                "CurrentHorizontalResolution, CurrentVerticalResolution, CurrentRefreshRate, "
                "AdapterRAM, Status, PNPDeviceID); "
                "$vram64 = @(Get-ItemProperty -Path 'HKLM:\\SYSTEM\\ControlSet001\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}\\0*' "
                "-Name 'HardwareInformation.qwMemorySize' -ErrorAction SilentlyContinue | "
                "Select-Object -ExpandProperty 'HardwareInformation.qwMemorySize'); "
                "@{gpus=$gpus; vram64=$vram64} | ConvertTo-Json -Compress"
            )
            parsed_gpus = []
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

                    for g in gpus:
                        wmi_ram = int(g.get("AdapterRAM") or 0)
                        true_vram_bytes = max(wmi_ram, max_reg_vram)
                        vram_mb = int(true_vram_bytes / (1024 * 1024)) if true_vram_bytes > 0 else 4096

                        h_res = g.get("CurrentHorizontalResolution")
                        v_res = g.get("CurrentVerticalResolution")
                        hz = g.get("CurrentRefreshRate")
                        res_str = f"{h_res} x {v_res} @ {hz} Hz" if h_res and v_res else "Secondary / Headless"

                        parsed_gpus.append(
                            {
                                "name": (g.get("Name") or "Unknown GPU").strip(),
                                "driver": (g.get("DriverVersion") or "Unknown").strip(),
                                "processor": (g.get("VideoProcessor") or "Standard GPU Core").strip(),
                                "resolution": res_str,
                                "vram_str": SystemEngine.format_bytes(true_vram_bytes) if true_vram_bytes else "Shared Memory",
                                "vram_mb": vram_mb,
                                "status": (g.get("Status") or "OK").strip(),
                                "pnp_id": (g.get("PNPDeviceID") or "").strip(),
                            }
                        )
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Error reading GPU specs: {err}"))

            self.gpu_specs_list = parsed_gpus
            self.after(0, self._render_gpu_specs)

        threading.Thread(target=worker, daemon=True).start()

    def _render_gpu_specs(self):
        for w in self.specs_box.winfo_children():
            w.destroy()

        if not self.gpu_specs_list:
            ctk.CTkLabel(self.specs_box, text="No graphics adapters detected.", text_color="gray").pack(pady=10)
            return

        primary = self.gpu_specs_list[0]
        rows = [
            ("Graphics Card Model", primary["name"]),
            ("Dedicated Video Memory", primary["vram_str"]),
            ("Installed Driver Version", primary["driver"]),
            ("GPU Die / Processor", primary["processor"]),
            ("Active Display Mode", primary["resolution"]),
            ("Device Manager Health", f"✅ {primary['status']}"),
        ]
        if len(self.gpu_specs_list) > 1:
            secondary_names = ", ".join([g["name"] for g in self.gpu_specs_list[1:]])
            rows.append(("Secondary Adapter(s)", secondary_names))

        for k, v in rows:
            line = ctk.CTkFrame(self.specs_box, fg_color="transparent")
            line.pack(fill="x", pady=2)
            ctk.CTkLabel(line, text=f"{k}:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            ctk.CTkLabel(line, text=str(v), font=ctk.CTkFont(size=12), text_color="#3B8ED0").pack(side="right")

    # ==========================================
    # SHADER CACHE CLEANER, HAGS & DRIVER RESET
    # ==========================================
    def clear_shader_caches(self):
        def worker():
            self.after(0, lambda: self.log_message("\n--- Purging DirectX, NVIDIA, AMD & Intel Shader Caches ---"))
            local_app = os.environ.get("LOCALAPPDATA", "")
            locallow_app = os.path.join(os.path.expanduser("~"), r"AppData\LocalLow")

            shader_dirs = [
                ("DirectX D3DSCache", os.path.join(local_app, "D3DSCache")),
                ("NVIDIA DXCache", os.path.join(local_app, r"NVIDIA\DXCache")),
                ("NVIDIA GLCache", os.path.join(local_app, r"NVIDIA\GLCache")),
                ("NVIDIA ComputeCache", os.path.join(locallow_app, r"NVIDIA\PerDriverVersion\DXCache")),
                ("AMD DxCache", os.path.join(local_app, r"AMD\DxCache")),
                ("AMD GL Cache", os.path.join(local_app, r"AMD\GLCache")),
                ("Intel ShaderCache", os.path.join(locallow_app, r"Intel\ShaderCache")),
            ]

            total_freed = 0
            files_deleted = 0

            for label, folder in shader_dirs:
                if not os.path.exists(folder):
                    continue
                folder_freed = 0
                for root, _, files in os.walk(folder):
                    for f in files:
                        fpath = os.path.join(root, f)
                        try:
                            sz = os.path.getsize(fpath)
                            os.unlink(fpath)
                            folder_freed += sz
                            total_freed += sz
                            files_deleted += 1
                        except OSError:
                            continue
                if folder_freed > 0:
                    self.after(
                        0,
                        lambda l=label, b=folder_freed: self.log_message(
                            f"  [+] Cleaned {l}: {SystemEngine.format_bytes(b)} freed"
                        ),
                    )

            self.after(
                0,
                lambda: self.log_message(
                    f"=== Shader Cache Purge Complete! Deleted {files_deleted} compiled shader files "
                    f"({SystemEngine.format_bytes(total_freed)} freed) ==="
                ),
            )

        threading.Thread(target=worker, daemon=True).start()

    def check_hags_status(self):
        key_path = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, "HwSchMode")
                if int(val) == 2:
                    self.hags_status_lbl.configure(
                        text="Hardware-Accelerated GPU Scheduling (HAGS): ✅ ENABLED (Mode 2)",
                        text_color="#2FA572",
                    )
                else:
                    self.hags_status_lbl.configure(
                        text="Hardware-Accelerated GPU Scheduling (HAGS): ⏸️ DISABLED (Mode 1)",
                        text_color="#E67E22",
                    )
        except OSError:
            self.hags_status_lbl.configure(
                text="Hardware-Accelerated GPU Scheduling (HAGS): Standard OS Default",
                text_color="gray",
            )

    def set_hags_mode(self, enable: bool):
        if not SystemEngine.is_admin():
            self.log_message("\n[!] Admin Rights Required to toggle Hardware-Accelerated GPU Scheduling.")
            return

        key_path = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
        target_val = 2 if enable else 1
        try:
            with winreg.CreateKeyEx(
                winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, "HwSchMode", 0, winreg.REG_DWORD, target_val)
            self.check_hags_status()
            state_str = "ENABLED" if enable else "DISABLED"
            self.log_message(
                f"[+] Set Hardware-Accelerated GPU Scheduling (HwSchMode) to {state_str}. "
                "(Restart your PC for Windows to apply the new scheduler mode)."
            )
        except Exception as e:
            self.log_message(f"[!] Could not update HAGS registry setting: {e}")

    def restart_gpu_driver(self):
        if not SystemEngine.is_admin():
            self.log_message("\n[!] Admin Rights Required to restart the display driver.")
            return

        if not self.gpu_specs_list or not self.gpu_specs_list[0].get("pnp_id"):
            self.log_message("\n[!] No GPU PnP Device ID loaded yet.")
            return

        pnp_id = self.gpu_specs_list[0]["pnp_id"]
        gpu_name = self.gpu_specs_list[0]["name"]

        def worker():
            self.after(
                0,
                lambda: self.log_message(
                    f"\n--- Restarting Display Adapter '{gpu_name}' (Screen may blink briefly) ---"
                ),
            )
            try:
                res = subprocess.run(
                    ["pnputil", "/restart-device", pnp_id],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10,
                )
                if res.returncode == 0:
                    self.after(0, lambda: self.log_message(f"[+] Successfully restarted '{gpu_name}' driver!"))
                else:
                    self.after(
                        0,
                        lambda m=res.stdout.strip(): self.log_message(f"[-] Driver restart finished: {m}"),
                    )
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Error restarting GPU driver: {err}"))

        threading.Thread(target=worker, daemon=True).start()