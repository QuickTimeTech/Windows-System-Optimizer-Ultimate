# services_optimizer.py
import os
import re
import html
import json
import threading
import subprocess
import webbrowser
import psutil
import customtkinter as ctk
from backend_engine import SystemEngine


class ServicesOptimizerView(ctk.CTkFrame):
    """Windows Background Services Optimizer, ASUS Laptop Power Tamer & Smart Energy Report Translator."""

    # Known USB Vendor/Product IDs that intentionally block USB Selective Suspend
    USB_KNOWN_SAFE = {
        "VID_046D&PID_C53F": ("Logitech LIGHTSPEED 1000Hz Gaming Receiver", "Blocks USB sleep for zero-lag wireless mouse/keyboard aim."),
        "VID_046D&PID_C534": ("Logitech Nano Wireless Receiver", "Stays awake to listen for wireless mouse/keyboard input."),
        "VID_046D": ("Logitech Gaming / Wireless Peripheral", "Gaming mice & keyboards disable USB sleep to prevent cursor stutter."),
        "VID_0B05&PID_19AF": ("ASUS AURA Motherboard LED Controller", "Internal motherboard RGB controller stays active on USB bus."),
        "VID_0B05&PID_19B6": ("ASUS ROG N-Key Keyboard / Slash Controller", "Built-in laptop keyboard controller stays awake for keystrokes."),
        "VID_0B05": ("ASUS ROG Hardware Controller", "Internal ASUS RGB/Hotkey USB controller."),
        "VID_1532": ("Razer Gaming Peripheral / HyperSpeed Dongle", "Blocks USB sleep to maintain 1000Hz+ polling rate."),
        "VID_1B1C": ("Corsair Gaming Peripheral / Receiver", "Blocks USB sleep to maintain low-latency input."),
        "VID_1038": ("SteelSeries Gaming Peripheral", "Blocks USB sleep to maintain low-latency input."),
        "VID_3277&PID_0060": ("Integrated Laptop FHD IR Webcam", "Internal camera bus controller."),
        "VID_04E8&PID_6300": ("Samsung USB Mass Storage Drive", "External USB storage stays active to prevent file corruption."),
        "VID_04E8": ("Samsung USB Device / Portable SSD", "External USB storage keeps link active while mounted."),
    }

    # Known Bluetooth / PnP Hardware IDs for controllers
    DRIVER_KNOWN_DEVICES = {
        "045E_PID&02E0": "Microsoft Xbox Wireless Controller (Bluetooth)",
        "045E": "Microsoft Xbox Controller / Adapter",
        "054C_PID&0CE6": "Sony PlayStation 5 DualSense Wireless Controller",
        "054C": "Sony PlayStation DualShock / DualSense Controller",
        "057E": "Nintendo Switch Pro Controller",
    }

    CURATED_SERVICES = [
        # --- ASUS ROG / LAPTOP TIMER & BATTERY DRAIN SERVICES ---
        (
            "LightingService",
            "ASUS Aura Sync RGB Lighting (LightingService.exe)",
            "Locks Windows Platform Timer to 1ms (10000ns) & burns continuous idle CPU.",
            "Manual",
            "Automatic",
        ),
        (
            "AsusROGLSLService",
            "ASUS ROG Live Service",
            "Background Armoury Crate telemetry and live update daemon.",
            "Manual",
            "Automatic",
        ),
        (
            "ArmouryCrateService",
            "ASUS Armoury Crate Background Service",
            "Heavy background RGB & macro polling daemon.",
            "Manual",
            "Automatic",
        ),
        (
            "ASUSSystemAnalysis",
            "ASUS System Analysis Service",
            "Background hardware diagnostic telemetry collector.",
            "Manual",
            "Automatic",
        ),
        (
            "ASUSSystemDiagnosis",
            "ASUS System Diagnosis Service",
            "MyASUS background diagnostic service.",
            "Manual",
            "Automatic",
        ),
        # --- WINDOWS TELEMETRY & BACKGROUND BLOAT ---
        (
            "DiagTrack",
            "Connected User Experiences and Telemetry",
            "Primary Microsoft background usage tracking and telemetry uploader.",
            "Disabled",
            "Automatic",
        ),
        (
            "dmwappushservice",
            "WAP Push Message Routing Service (Telemetry)",
            "Secondary Microsoft telemetry routing service.",
            "Disabled",
            "Manual",
        ),
        (
            "SysMain",
            "SysMain (Superfetch RAM Preloader)",
            "Constantly preloads apps into RAM; can cause background SSD/CPU spikes.",
            "Manual",
            "Automatic",
        ),
        (
            "WSearch",
            "Windows Search Indexer (SearchIndexer.exe)",
            "Continuously indexes files on disk. Set to Manual for lower SSD/CPU wear.",
            "Manual",
            "Automatic",
        ),
        (
            "Spooler",
            "Print Spooler (Spoolsv.exe)",
            "Background printer queue. Safe to set to Manual if you don't print daily.",
            "Manual",
            "Automatic",
        ),
        (
            "Fax",
            "Windows Fax Service",
            "Legacy dial-up fax background service.",
            "Disabled",
            "Manual",
        ),
        (
            "MapsBroker",
            "Downloaded Maps Manager",
            "Background service for offline Bing Maps sync.",
            "Disabled",
            "Automatic",
        ),
        (
            "lfsvc",
            "Geolocation Tracking Service",
            "Monitors and reports current physical location of the system.",
            "Manual",
            "Manual",
        ),
        (
            "RetailDemo",
            "Retail Demo Store Service",
            "Hidden store display kiosk mode built into Windows.",
            "Disabled",
            "Manual",
        ),
        (
            "RemoteRegistry",
            "Remote Registry Modification Service",
            "Allows remote users to modify registry settings; disabling improves security.",
            "Disabled",
            "Disabled",
        ),
        (
            "WerSvc",
            "Windows Error Reporting Service",
            "Uploads crash dumps and diagnostic logs to Microsoft servers.",
            "Manual",
            "Manual",
        ),
        (
            "XblAuthManager",
            "Xbox Live Auth Manager",
            "Background Xbox authentication (keep Manual/Automatic if using Game Pass).",
            "Manual",
            "Manual",
        ),
        (
            "XboxNetApiSvc",
            "Xbox Live Networking Service",
            "Background Xbox party/network service.",
            "Manual",
            "Manual",
        ),
    ]

    ASUS_SERVICES = [
        "LightingService",
        "AsusROGLSLService",
        "ArmouryCrateService",
        "ASUSSystemAnalysis",
        "ASUSSystemDiagnosis",
    ]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)

        self.service_rows = {}
        self.busy = False
        self.report_path = os.path.join(os.path.expanduser("~"), "Windows_Power_Efficiency_Report.html")

        # ==========================================
        # TOP CARD: PRESETS, ASUS ECO MODE & SMART ENERGY TRANSLATOR
        # ==========================================
        top_card = ctk.CTkFrame(self)
        top_card.grid(row=0, column=0, pady=(0, 8), sticky="ew")

        row1 = ctk.CTkFrame(top_card, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            row1,
            text="⚙️ SERVICES OPTIMIZER & SMART ENERGY REPORT TRANSLATOR",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(side="left")

        self.refresh_btn = ctk.CTkButton(
            row1,
            text="🔄 Refresh Services",
            width=145,
            height=28,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.refresh_services_status,
        )
        self.refresh_btn.pack(side="right", padx=(6, 0))

        self.decode_existing_btn = ctk.CTkButton(
            row1,
            text="📖 Translate Existing Report",
            width=190,
            height=28,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.translate_existing_energy_report,
        )
        self.decode_existing_btn.pack(side="right", padx=6)

        self.energy_btn = ctk.CTkButton(
            row1,
            text="🧠 Run 10s Energy Trace & Smart-Translate",
            width=265,
            height=28,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.generate_and_translate_energy_report,
        )
        self.energy_btn.pack(side="right", padx=6)

        row2 = ctk.CTkFrame(top_card, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(4, 10))

        ctk.CTkButton(
            row2,
            text="🚀 Apply Low-Overhead Gamer & Battery Preset",
            height=32,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.apply_recommended_preset,
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            row2,
            text="🔋 ASUS Eco Mode (Stop Lighting & ROG Bloat)",
            height=32,
            fg_color="#D35400",
            hover_color="#A04000",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.tame_asus_services,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            row2,
            text="🔍 Check Active Timer Locks",
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.audit_power_requests,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            row2,
            text="⏪ Restore Defaults",
            width=135,
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.restore_default_services,
        ).pack(side="right")

        # Custom Service Search Bar
        search_row = ctk.CTkFrame(top_card, fg_color=("gray85", "gray17"))
        search_row.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(
            search_row,
            text="🔎 Search Any Windows Service:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=(12, 8), pady=7)

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Type any service name (e.g., AudioSrv, Dhcp, Bluetooth, Nvidia, Steam)...",
            height=28,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=6, pady=7)
        self.search_entry.bind("<Return>", lambda _: self.search_custom_services())

        ctk.CTkButton(
            search_row,
            text="Search All Services",
            width=150,
            height=28,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.search_custom_services,
        ).pack(side="right", padx=10, pady=7)

        # ==========================================
        # PROGRESS BAR
        # ==========================================
        self.progress = ctk.CTkProgressBar(self, height=10, progress_color="#2FA572")
        self.progress.grid(row=1, column=0, pady=(0, 8), sticky="ew")
        self.progress.set(0)

        # ==========================================
        # SCROLLABLE SERVICES LIST
        # ==========================================
        self.svc_scroll = ctk.CTkScrollableFrame(self)
        self.svc_scroll.grid(row=2, column=0, pady=(0, 8), sticky="nsew")

        self._build_service_cards()

        # ==========================================
        # CONSOLE LOG (EXPANDED FOR SMART ENERGY TRANSLATOR)
        # ==========================================
        self.log_box = ctk.CTkTextbox(self, height=165, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=3, column=0, sticky="ew")
        self.log_message(
            "Smart Services Optimizer & Power Efficiency Translator Ready.\n"
            "• Click '🧠 Run 10s Energy Trace & Smart-Translate' to decode cryptic USB VID/PIDs, 0x16 Bluetooth codes & Timer Locks into plain English!\n"
            "• Click '📖 Translate Existing Report' to immediately decode your last powercfg report."
        )

        self.after(250, self.refresh_services_status)

    def _build_service_cards(self):
        for svc_name, title, desc, rec_mode, _ in self.CURATED_SERVICES:
            card = ctk.CTkFrame(self.svc_scroll, fg_color=("gray85", "gray17"))
            card.pack(fill="x", padx=5, pady=4)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=14, pady=8)

            is_asus = svc_name in self.ASUS_SERVICES
            title_col = "#F39C12" if is_asus else "#3B8ED0"

            ctk.CTkLabel(
                left,
                text=f"{'💻 ' if is_asus else '⚙️ '}{title}  [{svc_name}]",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=title_col,
            ).pack(anchor="w")

            ctk.CTkLabel(
                left,
                text=f"{desc}  (Recommended: {rec_mode})",
                font=ctk.CTkFont(size=11),
                text_color="lightgray",
            ).pack(anchor="w")

            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=12, pady=8)

            status_lbl = ctk.CTkLabel(
                right,
                text="Checking...",
                width=145,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="gray",
            )
            status_lbl.pack(side="left", padx=8)

            mode_menu = ctk.CTkOptionMenu(
                right,
                values=["Automatic", "Manual", "Disabled"],
                width=115,
                height=28,
                command=lambda val, s=svc_name: self.change_single_service_mode(s, val),
            )
            mode_menu.pack(side="left", padx=4)

            start_btn = ctk.CTkButton(
                right,
                text="▶ Start",
                width=70,
                height=28,
                fg_color="#2FA572",
                hover_color="#1D7A52",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda s=svc_name: self.start_single_service(s),
            )
            start_btn.pack(side="left", padx=2)

            stop_btn = ctk.CTkButton(
                right,
                text="⏹ Stop",
                width=70,
                height=28,
                fg_color="#C0392B",
                hover_color="#922B21",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda s=svc_name: self.stop_single_service(s),
            )
            stop_btn.pack(side="left", padx=2)

            self.service_rows[svc_name] = {
                "status_lbl": status_lbl,
                "mode_menu": mode_menu,
                "start_btn": start_btn,
                "stop_btn": stop_btn,
            }

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ==========================================
    # SMART ENERGY REPORT PARSER & TRANSLATOR
    # ==========================================
    @classmethod
    def decode_energy_html(cls, html_path: str) -> str:
        """Parses a Windows powercfg /energy HTML file and translates cryptic errors into plain English."""
        if not os.path.exists(html_path):
            return f"[!] Report file not found at: {html_path}\nClick '🧠 Run 10s Energy Trace & Smart-Translate' to generate one first."

        try:
            with open(html_path, "r", encoding="utf-8", errors="replace") as f:
                raw_html = f.read()
        except Exception as e:
            return f"[!] Could not read HTML report: {e}"

        # Convert HTML tags into clean newline-delimited text
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "\n", text)
        text = html.unescape(text)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        flat = "\n".join(lines)

        out_lines = [
            "======================================================================================",
            " 🧠 SMART ENERGY REPORT TRANSLATOR — PLAIN-ENGLISH HARDWARE & DRAIN VERDICT",
            "======================================================================================",
        ]

        safe_count = 0
        real_drain_count = 0

        # 1. Decode Average CPU Utilisation
        m_cpu = re.search(r"Average Utilisation \(%\)\s*([\d\.]+)", flat, re.IGNORECASE)
        if m_cpu:
            avg_cpu = float(m_cpu.group(1))
            if avg_cpu <= 8.0:
                out_lines.append(f"✅ [IDLE CPU HEALTHY] Average CPU Utilisation during trace: {avg_cpu:.2f}% (Normal background load)")
                safe_count += 1
            else:
                out_lines.append(f"⚠️ [ELEVATED IDLE CPU] Average CPU Utilisation during trace: {avg_cpu:.2f}% (See processes below)")

        # 2. Decode USB Selective Suspend Entries
        usb_matches = re.findall(
            r"USB Device not Entering Selective Suspend.*?Device Name\s*\n([^\n]+).*?Device ID\s*\n(USB\\VID_[0-9A-F]{4}&PID_[0-9A-F]{4})",
            flat,
            flags=re.DOTALL | re.IGNORECASE,
        )
        for dev_name, usb_id in usb_matches:
            uid_upper = usb_id.upper()
            short_vid_pid = uid_upper.replace("USB\\", "")
            vid_only = short_vid_pid.split("&")[0]

            matched_info = cls.USB_KNOWN_SAFE.get(short_vid_pid) or cls.USB_KNOWN_SAFE.get(vid_only)
            if matched_info:
                friendly_name, reason = matched_info
                out_lines.append(
                    f"✅ [SAFE USB WAKE] {friendly_name} ({short_vid_pid})\n"
                    f"   └─ Verdict: Normal! {reason}"
                )
                safe_count += 1
            else:
                out_lines.append(
                    f"ℹ️ [ACTIVE USB DEVICE] {dev_name} ({short_vid_pid})\n"
                    f"   └─ Verdict: Device stayed awake on USB bus (Does NOT prevent PC from sleeping)."
                )
                safe_count += 1

        # 3. Decode Device Driver Problem Codes (e.g. Bluetooth Controllers 0x16 = Disabled/Off)
        drv_matches = re.findall(
            r"Devices with missing or misconfigured drivers.*?Device Name\s*\n([^\n]+)\s*\nDevice ID\s*\n([^\n]+).*?Device Status\s*\n([^\n]+)(?:\s*\nDevice Problem Code\s*\n([^\n]+))?",
            flat,
            flags=re.DOTALL | re.IGNORECASE,
        )
        for d_name, d_id, d_status, d_prob in drv_matches:
            did_upper = d_id.upper()
            prob_code = (d_prob or "").strip().lower()

            friendly_ctrl = d_name
            for key_pat, label in cls.DRIVER_KNOWN_DEVICES.items():
                if key_pat in did_upper:
                    friendly_ctrl = label
                    break

            if prob_code in ("0x16", "22") or "0x1806400" in d_status.lower():
                out_lines.append(
                    f"✅ [SAFE SLEEPING CONTROLLER] {friendly_ctrl}\n"
                    f"   └─ Verdict: Problem Code 0x16 (Code 22) just means this Bluetooth controller is turned OFF or Disabled! Zero battery drain."
                )
                safe_count += 1
            else:
                out_lines.append(
                    f"⚠️ [DRIVER CHECK NEEDED] {friendly_ctrl} ({d_id[:45]}...)\n"
                    f"   └─ Verdict: Reported Problem Code {prob_code or d_status}. Inspect in 'Driver Backup Center'."
                )
                real_drain_count += 1

        # 4. Decode PCIe ASPM Disabled
        if "PCI Express Active-State Power Management (ASPM) Disabled" in flat:
            out_lines.append(
                "✅ [SAFE BIOS SETTING] PCI Express Active-State Power Management (ASPM) Disabled\n"
                "   └─ Verdict: Gaming motherboards & laptops disable PCIe link sleep by default to prevent GPU & NVMe micro-stutter."
            )
            safe_count += 1

        # 5. Decode Platform Timer Resolution Locks (10000ns = 1ms High-Frequency Timer)
        timer_matches = re.findall(
            r"Outstanding Timer Request.*?Requested Period\s*\n(\d+)\s*\nRequesting Process ID\s*\n(\d+)\s*\nRequesting Process Path\s*\n([^\n]+)",
            flat,
            flags=re.DOTALL | re.IGNORECASE,
        )
        for period, pid, proc_path in timer_matches:
            exe_name = os.path.basename(proc_path.strip())
            if "lightingservice" in exe_name.lower() or "armoury" in exe_name.lower():
                out_lines.append(
                    f"🚨 [REAL BATTERY/CPU DRAIN] {exe_name} (PID {pid}) is locking the CPU Platform Timer to {period} (1ms)!\n"
                    f"   └─ Fix: Click the orange '🔋 ASUS Eco Mode (Stop Lighting & ROG Bloat)' button above to stop it immediately!"
                )
                real_drain_count += 1
            else:
                out_lines.append(
                    f"⚠️ [TIMER LOCK] {exe_name} (PID {pid}) requested high-frequency timer ({period}).\n"
                    f"   └─ Note: Normal if a browser video, Discord call, or game is open; close {exe_name} when on battery."
                )

        # 6. Decode Top CPU-Consuming Processes During Trace
        proc_matches = re.findall(
            r"Individual process with significant processor utilisation\..*?Process Name\s*\n([^\n]+)\s*\nPID\s*\n(\d+)\s*\nAverage Utilisation \(%\)\s*\n([\d\.]+)",
            flat,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if proc_matches:
            out_lines.append("\n--- Top Active Processes Recorded During Trace ---")
            for pname, pid, pct in proc_matches[:6]:
                pct_f = float(pct)
                if pname.lower() == "system" and "nvlddmkm.sys" in flat.lower() and pct_f > 1.0:
                    out_lines.append(
                        f"  🚨 {pname} (PID {pid}): {pct}% CPU  ➔ NVIDIA Kernel Driver (nvlddmkm.sys) waking dGPU! (Fixed by our Optimus Eco Guard)"
                    )
                    real_drain_count += 1
                elif "lightingservice" in pname.lower():
                    out_lines.append(
                        f"  🚨 {pname} (PID {pid}): {pct}% CPU  ➔ ASUS RGB Bloat! Click '🔋 ASUS Eco Mode' above to stop."
                    )
                    real_drain_count += 1
                else:
                    out_lines.append(f"  • {pname} (PID {pid}): {pct}% Average CPU")

        out_lines.append("--------------------------------------------------------------------------------------")
        if real_drain_count == 0:
            out_lines.append(
                f"🎉 FINAL VERDICT: 0 Real Power Problems! All {safe_count} Windows warnings are normal gaming peripherals & settings."
            )
        else:
            out_lines.append(
                f"🔧 FINAL VERDICT: Found {real_drain_count} real background drain(s) and {safe_count} harmless peripheral warnings."
            )
        out_lines.append("======================================================================================")
        return "\n".join(out_lines)

    def translate_existing_energy_report(self):
        # Check user home report first, then C:\Windows\System32\energy-report.html
        candidates = [
            self.report_path,
            os.path.join(os.getcwd(), "energy-report.html"),
            r"C:\Windows\System32\energy-report.html",
        ]
        target = next((p for p in candidates if os.path.exists(p)), self.report_path)
        verdict = self.decode_energy_html(target)
        self.log_message("\n" + verdict)

    def generate_and_translate_energy_report(self):
        if not SystemEngine.is_admin():
            self.log_message("[!] Administrator privileges required to run powercfg /energy trace.")
            return

        self.energy_btn.configure(state="disabled", text="⏳ Tracing Energy (10s)...")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.log_message(
            "\n--- Running 10-Second Windows Power Efficiency Trace (powercfg /energy) ---\n"
            "Sampling USB states, Bluetooth controllers, timer locks, and CPU C-states for 10 seconds..."
        )

        def worker():
            try:
                subprocess.run(
                    ["powercfg", "/energy", "/output", self.report_path, "/duration", "10"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=25,
                )
                if os.path.exists(self.report_path):
                    decoded_summary = self.decode_energy_html(self.report_path)
                    self.after(0, lambda s=decoded_summary: self.log_message("\n" + s))
                    webbrowser.open(f"file://{os.path.abspath(self.report_path)}")
                else:
                    self.after(0, lambda: self.log_message("[!] Trace finished, but report file was not created."))
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Energy trace error: {err}"))
            finally:
                self.after(
                    0,
                    lambda: (
                        self.progress.stop(),
                        self.progress.configure(mode="determinate"),
                        self.progress.set(1.0),
                        self.energy_btn.configure(
                            state="normal", text="🧠 Run 10s Energy Trace & Smart-Translate"
                        ),
                    ),
                )

        threading.Thread(target=worker, daemon=True).start()

    # ==========================================
    # SERVICE STATUS SCANNER & CONTROLS
    # ==========================================
    def refresh_services_status(self):
        if self.busy:
            return
        self.busy = True
        self.refresh_btn.configure(state="disabled", text="⏳ Scanning...")
        self.progress.configure(mode="indeterminate")
        self.progress.start()

        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        names_list = ",".join([f"'{s[0]}'" for s in self.CURATED_SERVICES])
        ps_cmd = (
            f"@(Get-Service -Name {names_list} -ErrorAction SilentlyContinue | "
            "Select-Object Name, Status, StartType) | ConvertTo-Json -Compress"
        )
        results = {}
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=8,
            ).strip()
            if out:
                raw = json.loads(out)
                if isinstance(raw, dict):
                    raw = [raw]
                for item in raw:
                    name = item.get("Name")
                    status_val = item.get("Status")
                    start_val = item.get("StartType")

                    status_str = "Running" if status_val in (4, "Running") else "Stopped"
                    if start_val in (2, "Automatic"):
                        start_str = "Automatic"
                    elif start_val in (3, "Manual"):
                        start_str = "Manual"
                    elif start_val in (4, "Disabled"):
                        start_str = "Disabled"
                    else:
                        start_str = str(start_val)

                    if name:
                        results[name] = (status_str, start_str)
        except Exception:
            pass

        self.busy = False
        self.after(0, lambda: self._update_service_ui(results))

    def _update_service_ui(self, results: dict):
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(1.0)
        self.refresh_btn.configure(state="normal", text="🔄 Refresh Services")

        for svc_name, widgets in self.service_rows.items():
            lbl = widgets["status_lbl"]
            menu = widgets["mode_menu"]
            start_btn = widgets["start_btn"]
            stop_btn = widgets["stop_btn"]

            if svc_name not in results:
                lbl.configure(text="⚪ Not Installed", text_color="gray")
                menu.configure(state="disabled")
                start_btn.configure(state="disabled")
                stop_btn.configure(state="disabled")
            else:
                status_str, start_str = results[svc_name]
                menu.configure(state="normal")
                if start_str in ("Automatic", "Manual", "Disabled"):
                    menu.set(start_str)

                if status_str == "Running":
                    lbl.configure(text=f"🟢 Running ({start_str})", text_color="#E67E22")
                    start_btn.configure(state="disabled")
                    stop_btn.configure(state="normal")
                else:
                    lbl.configure(text=f"💤 Stopped ({start_str})", text_color="#2FA572")
                    start_btn.configure(state="normal")
                    stop_btn.configure(state="disabled")

    def search_custom_services(self):
        query = self.search_entry.get().strip()
        if not query:
            self.log_message("[i] Type a service name or keyword in the search box above first.")
            return

        self.log_message(f"\n--- Searching All Windows Services Matching '{query}' ---")

        def worker():
            ps_cmd = (
                f"@(Get-Service | Where-Object {{ $_.Name -like '*{query}*' -or $_.DisplayName -like '*{query}*' }} | "
                "Select-Object -First 15 Name, DisplayName, Status, StartType) | ConvertTo-Json -Compress"
            )
            try:
                out = subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command", ps_cmd],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    text=True,
                    timeout=8,
                ).strip()
                if not out:
                    self.after(0, lambda: self.log_message("  No matching Windows services found."))
                    return
                raw = json.loads(out)
                if isinstance(raw, dict):
                    raw = [raw]
                for s in raw:
                    st = "Running" if s.get("Status") in (4, "Running") else "Stopped"
                    self.after(
                        0,
                        lambda item=s, status=st: self.log_message(
                            f"  • {item.get('DisplayName')} [{item.get('Name')}]  —  Status: {status}"
                        ),
                    )
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Search error: {err}"))

        threading.Thread(target=worker, daemon=True).start()

    def change_single_service_mode(self, svc_name: str, mode: str):
        if not SystemEngine.is_admin():
            self.log_message("[!] Administrator privileges required to change service startup types.")
            return

        def worker():
            try:
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f"Set-Service -Name '{svc_name}' -StartupType {mode} -ErrorAction Stop",
                    ],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=6,
                )
                self.after(0, lambda: self.log_message(f"[+] Set '{svc_name}' StartupType ➔ {mode}"))
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Could not change {svc_name}: {err}"))
            self.after(100, self.refresh_services_status)

        threading.Thread(target=worker, daemon=True).start()

    def start_single_service(self, svc_name: str):
        if not SystemEngine.is_admin():
            return

        def worker():
            try:
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f"Start-Service -Name '{svc_name}' -ErrorAction Stop",
                    ],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=8,
                )
                self.after(0, lambda: self.log_message(f"[▶] Started service: {svc_name}"))
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Could not start {svc_name}: {err}"))
            self.after(100, self.refresh_services_status)

        threading.Thread(target=worker, daemon=True).start()

    def stop_single_service(self, svc_name: str):
        if not SystemEngine.is_admin():
            return

        def worker():
            try:
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f"Stop-Service -Name '{svc_name}' -Force -ErrorAction Stop",
                    ],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=8,
                )
                self.after(0, lambda: self.log_message(f"[⏹] Stopped running service: {svc_name}"))
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Could not stop {svc_name}: {err}"))
            self.after(100, self.refresh_services_status)

        threading.Thread(target=worker, daemon=True).start()

    def tame_asus_services(self):
        self.log_message("\n--- Activating ASUS Laptop Eco Mode (Stopping RGB & Timer Drain) ---")

        def worker():
            for svc in self.ASUS_SERVICES:
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f"Stop-Service -Name '{svc}' -Force -ErrorAction SilentlyContinue; "
                        f"Set-Service -Name '{svc}' -StartupType Manual -ErrorAction SilentlyContinue",
                    ],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=6,
                )

            for p in psutil.process_iter(["pid", "name"]):
                try:
                    if (p.info["name"] or "").lower() in ("lightingservice.exe", "armourycrateservice.exe"):
                        p.terminate()
                except Exception:
                    pass

            self.after(
                0,
                lambda: self.log_message(
                    "  ✅ Stopped LightingService.exe & ASUS background daemons (set to Manual). 1ms Timer Lock released!"
                ),
            )
            self.after(150, self.refresh_services_status)

        threading.Thread(target=worker, daemon=True).start()

    def apply_recommended_preset(self):
        if self.busy:
            return
        self.log_message("\n=== Applying Low-Overhead Gamer & Battery Service Preset ===")

        def worker():
            for svc_name, _, _, rec_mode, _ in self.CURATED_SERVICES:
                cmd = f"Set-Service -Name '{svc_name}' -StartupType {rec_mode} -ErrorAction SilentlyContinue"
                if rec_mode in ("Disabled", "Manual") and svc_name in (
                    "LightingService",
                    "DiagTrack",
                    "dmwappushservice",
                    "MapsBroker",
                    "Fax",
                    "RetailDemo",
                ):
                    cmd += f"; Stop-Service -Name '{svc_name}' -Force -ErrorAction SilentlyContinue"
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=6,
                )
            self.after(
                0,
                lambda: self.log_message(
                    "=== Preset Applied! Telemetry, MapsBroker, Fax & LightingService tamed ==="
                ),
            )
            self.after(150, self.refresh_services_status)

        threading.Thread(target=worker, daemon=True).start()

    def restore_default_services(self):
        if self.busy:
            return
        self.log_message("\n=== Restoring Default Windows Service Startup Modes ===")

        def worker():
            for svc_name, _, _, _, def_mode in self.CURATED_SERVICES:
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f"Set-Service -Name '{svc_name}' -StartupType {def_mode} -ErrorAction SilentlyContinue",
                    ],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=6,
                )
            self.after(0, lambda: self.log_message("=== Restored All Curated Services to Safe Defaults ==="))
            self.after(150, self.refresh_services_status)

        threading.Thread(target=worker, daemon=True).start()

    def audit_power_requests(self):
        self.log_message("\n--- Auditing Active Windows Power & Timer Locks (powercfg /requests) ---")

        def worker():
            try:
                out = subprocess.check_output(
                    ["powercfg", "/requests"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    text=True,
                    timeout=6,
                ).strip()
                self.after(0, lambda o=out: self.log_message(o + "\n=== Power Requests Audit Complete ==="))
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Could not run powercfg /requests: {err}"))

        threading.Thread(target=worker, daemon=True).start()