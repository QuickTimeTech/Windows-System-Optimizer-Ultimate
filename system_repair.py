# system_repair.py
import os
import threading
import subprocess
import webbrowser
import customtkinter as ctk
from backend_engine import SystemEngine


class SystemRepairView(ctk.CTkFrame):
    """Modular Windows Health Check, SFC/DISM Repair, and Battery Report Generator."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ==========================================
        # CARD 1: SYSTEM FILE & IMAGE REPAIR (ADMIN)
        # ==========================================
        self.repair_card = ctk.CTkFrame(self)
        self.repair_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            self.repair_card,
            text="🛠️ WINDOWS SYSTEM FILE REPAIR",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            self.repair_card,
            text="Scan and repair corrupted Windows system files (Requires Admin).",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 10))

        self.sfc_btn = ctk.CTkButton(
            self.repair_card,
            text="🛡️ Run SFC /scannow (System File Checker)",
            height=34,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#3B8ED0",
            command=self.run_sfc_scan,
        )
        self.sfc_btn.pack(fill="x", padx=15, pady=4)

        self.dism_check_btn = ctk.CTkButton(
            self.repair_card,
            text="🔍 Run DISM /ScanHealth (Check Image)",
            height=34,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#2FA572",
            hover_color="#1D7A52",
            command=self.run_dism_scan,
        )
        self.dism_check_btn.pack(fill="x", padx=15, pady=4)

        self.dism_restore_btn = ctk.CTkButton(
            self.repair_card,
            text="🚑 Run DISM /RestoreHealth (Deep Repair)",
            height=34,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#D35400",
            hover_color="#A04000",
            command=self.run_dism_restore,
        )
        self.dism_restore_btn.pack(fill="x", padx=15, pady=(4, 15))

        # ==========================================
        # CARD 2: BATTERY, POWER & NETWORK DIAGNOSTICS
        # ==========================================
        self.diag_card = ctk.CTkFrame(self)
        self.diag_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            self.diag_card,
            text="🔋 BATTERY & HARDWARE DIAGNOSTICS",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#9B59B6",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            self.diag_card,
            text="Generate official Windows HTML reports or reset stuck network sockets.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 10))

        self.battery_btn = ctk.CTkButton(
            self.diag_card,
            text="🔋 Generate & Open Battery Health Report",
            height=34,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#8E44AD",
            hover_color="#6C3483",
            command=self.generate_battery_report,
        )
        self.battery_btn.pack(fill="x", padx=15, pady=4)

        self.energy_btn = ctk.CTkButton(
            self.diag_card,
            text="⚡ Generate System Power Efficiency Report",
            height=34,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#34495E",
            hover_color="#2C3E50",
            command=self.generate_energy_report,
        )
        self.energy_btn.pack(fill="x", padx=15, pady=4)

        self.winsock_btn = ctk.CTkButton(
            self.diag_card,
            text="🌐 Reset Winsock Network Catalog (Admin)",
            height=34,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#C0392B",
            hover_color="#922B21",
            command=self.reset_winsock,
        )
        self.winsock_btn.pack(fill="x", padx=15, pady=(4, 15))

        # ==========================================
        # PROGRESS BAR & LIVE CONSOLE OUTPUT
        # ==========================================
        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.grid(row=1, column=0, columnspan=2, pady=(0, 8), sticky="ew")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=2, column=0, columnspan=2, sticky="nsew")

        self.log_message("Windows Repair & Diagnostic Center Ready.")
        if not SystemEngine.is_admin():
            self.log_message(
                "[!] Notice: You are running in Standard User Mode. "
                "Battery Report works normally, but SFC, DISM, and Winsock require running as Administrator."
            )

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def set_buttons_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in [
            self.sfc_btn,
            self.dism_check_btn,
            self.dism_restore_btn,
            self.battery_btn,
            self.energy_btn,
            self.winsock_btn,
        ]:
            btn.configure(state=state)
        if not enabled:
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.set(0)

    def run_stream_command(self, title: str, cmd: list[str], require_admin: bool = True):
        """Runs a Windows CLI command in a background thread and streams live lines to the GUI."""
        if require_admin and not SystemEngine.is_admin():
            self.log_message(f"\n[!] Cannot run '{title}': Please restart the app as Administrator.")
            return

        def worker():
            self.after(0, lambda: self.set_buttons_state(False))
            self.after(0, lambda: self.log_message(f"\n--- Starting {title} ---"))
            self.after(0, lambda: self.log_message("This may take a few minutes. Live output will appear below..."))

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="oem",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                for line in proc.stdout:
                    clean_line = line.strip().replace("\x00", "")
                    if clean_line:
                        self.after(0, lambda l=clean_line: self.log_message(f"  {l}"))

                proc.wait()
                self.after(0, lambda: self.log_message(f"=== {title} Finished (Exit Code: {proc.returncode}) ==="))
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Error running {title}: {err}"))
            finally:
                self.after(0, lambda: self.set_buttons_state(True))

        threading.Thread(target=worker, daemon=True).start()

    # ==========================================
    # COMMAND HANDLERS
    # ==========================================
    def run_sfc_scan(self):
        self.run_stream_command("System File Checker (SFC /scannow)", ["sfc", "/scannow"], require_admin=True)

    def run_dism_scan(self):
        self.run_stream_command(
            "DISM Image Health Scan", ["DISM.exe", "/Online", "/Cleanup-image", "/Scanhealth"], require_admin=True
        )

    def run_dism_restore(self):
        self.run_stream_command(
            "DISM Deep Image Repair", ["DISM.exe", "/Online", "/Cleanup-image", "/Restorehealth"], require_admin=True
        )

    def reset_winsock(self):
        self.run_stream_command(
            "Winsock Network Reset", ["netsh", "winsock", "reset"], require_admin=True
        )

    def generate_battery_report(self):
        """Generates a Windows Battery Health HTML report and opens it in the default web browser."""
        def worker():
            self.after(0, lambda: self.set_buttons_state(False))
            self.after(0, lambda: self.log_message("\n--- Generating Windows Battery Health Report ---"))

            report_path = os.path.join(os.path.expanduser("~"), "battery_health_report.html")
            try:
                res = subprocess.run(
                    ["powercfg", "/batteryreport", "/output", report_path],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                if res.returncode == 0 and os.path.exists(report_path):
                    self.after(0, lambda: self.log_message(f"[+] Report saved to: {report_path}"))
                    self.after(0, lambda: self.log_message("[*] Opening report in your default browser..."))
                    webbrowser.open(f"file://{os.path.abspath(report_path)}")
                else:
                    msg = res.stderr.strip() or res.stdout.strip() or "No battery detected (Desktop PC)."
                    self.after(0, lambda m=msg: self.log_message(f"[-] Could not generate battery report: {m}"))
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Failed to generate battery report: {err}"))
            finally:
                self.after(0, lambda: self.set_buttons_state(True))

        threading.Thread(target=worker, daemon=True).start()

    def generate_energy_report(self):
        """Runs a 60-second powercfg /energy trace (Requires Admin) and opens the HTML report."""
        if not SystemEngine.is_admin():
            self.log_message("\n[!] Power Efficiency Diagnostics requires Administrator privileges.")
            return

        def worker():
            self.after(0, lambda: self.set_buttons_state(False))
            self.after(
                0,
                lambda: self.log_message(
                    "\n--- Tracing System Power Usage (60 Seconds) ---\n"
                    "Windows is observing system behavior for 60 seconds. Please wait..."
                ),
            )
            report_path = os.path.join(os.path.expanduser("~"), "power_efficiency_report.html")
            try:
                res = subprocess.run(
                    ["powercfg", "/energy", "/output", report_path],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                if os.path.exists(report_path):
                    self.after(0, lambda: self.log_message(f"[+] Energy report saved to: {report_path}"))
                    self.after(0, lambda: self.log_message("[*] Opening report in your default browser..."))
                    webbrowser.open(f"file://{os.path.abspath(report_path)}")
                else:
                    self.after(0, lambda: self.log_message(f"[-] Energy trace message: {res.stdout.strip()}"))
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Error during energy trace: {err}"))
            finally:
                self.after(0, lambda: self.set_buttons_state(True))

        threading.Thread(target=worker, daemon=True).start()