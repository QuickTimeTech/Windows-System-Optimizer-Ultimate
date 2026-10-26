# restore_scheduler.py
import json
import threading
import subprocess
from datetime import datetime
import customtkinter as ctk
from backend_engine import SystemEngine


class RestoreSchedulerView(ctk.CTkFrame):
    """Modular Windows System Restore Point Manager & Weekly Task Scheduler."""

    TASK_NAME = "PCOptimizer_Weekly_AutoClean"

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ==========================================
        # CARD 1: SYSTEM RESTORE POINT CREATOR
        # ==========================================
        restore_card = ctk.CTkFrame(self)
        restore_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            restore_card,
            text="⏪ WINDOWS SYSTEM RESTORE POINT MANAGER",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            restore_card,
            text="Create a safety snapshot before modifying drivers, apps, or registry.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 8))

        self.desc_entry = ctk.CTkEntry(
            restore_card,
            placeholder_text="Restore Point Name (e.g. Pre-Optimization Snapshot)",
        )
        self.desc_entry.insert(0, f"PC Optimizer Snapshot ({datetime.now().strftime('%Y-%m-%d')})")
        self.desc_entry.pack(fill="x", padx=15, pady=4)

        self.create_rp_btn = ctk.CTkButton(
            restore_card,
            text="🛡️ Create System Restore Point Now (Admin)",
            height=34,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(weight="bold"),
            command=self.create_restore_point,
        )
        self.create_rp_btn.pack(fill="x", padx=15, pady=4)

        btn_row = ctk.CTkFrame(restore_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(4, 15))

        self.list_rp_btn = ctk.CTkButton(
            btn_row,
            text="🔄 List Restore Points",
            height=32,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.list_restore_points,
        )
        self.list_rp_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        ctk.CTkButton(
            btn_row,
            text="⏪ Launch Windows Restore UI",
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: subprocess.Popen(["rstrui.exe"]),
        ).pack(side="right", expand=True, fill="x", padx=(4, 0))

        # ==========================================
        # CARD 2: AUTOMATED WEEKLY TASK SCHEDULER
        # ==========================================
        sched_card = ctk.CTkFrame(self)
        sched_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            sched_card,
            text="⏰ AUTOMATED WEEKLY MAINTENANCE SCHEDULER",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#9B59B6",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        self.sched_status_lbl = ctk.CTkLabel(
            sched_card,
            text="Task Status: Checking Windows Task Scheduler...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray",
        )
        self.sched_status_lbl.pack(anchor="w", padx=15, pady=(0, 8))

        day_row = ctk.CTkFrame(sched_card, fg_color="transparent")
        day_row.pack(fill="x", padx=15, pady=4)

        ctk.CTkLabel(day_row, text="Run Every:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 8))
        self.day_menu = ctk.CTkOptionMenu(
            day_row,
            values=["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"],
            width=100,
        )
        self.day_menu.set("SUN")
        self.day_menu.pack(side="left", padx=4)

        ctk.CTkLabel(day_row, text="at 12:00 PM (Silent Temp & DNS Clean)", text_color="gray").pack(
            side="left", padx=8
        )

        self.enable_sched_btn = ctk.CTkButton(
            sched_card,
            text="✅ Enable Weekly Auto-Clean Task (Admin)",
            height=34,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(weight="bold"),
            command=self.install_scheduled_task,
        )
        self.enable_sched_btn.pack(fill="x", padx=15, pady=4)

        self.disable_sched_btn = ctk.CTkButton(
            sched_card,
            text="❌ Remove Scheduled Auto-Clean Task",
            height=32,
            fg_color="#C0392B",
            hover_color="#922B21",
            font=ctk.CTkFont(weight="bold"),
            command=self.remove_scheduled_task,
        )
        self.disable_sched_btn.pack(fill="x", padx=15, pady=(4, 15))

        # ==========================================
        # PROGRESS BAR & CONSOLE LOG
        # ==========================================
        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.grid(row=1, column=0, columnspan=2, pady=(0, 8), sticky="ew")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.log_message(
            "System Restore & Task Scheduler Ready.\n"
            "Note: Windows limits Checkpoint-Computer creation to 1 restore point every 24 hours unless bypassed."
        )

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        for btn in [self.create_rp_btn, self.list_rp_btn, self.enable_sched_btn, self.disable_sched_btn]:
            btn.configure(state=state)
        if busy:
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.set(0)

    # ==========================================
    # SYSTEM RESTORE POINT FUNCTIONS
    # ==========================================
    def list_restore_points(self):
        self.check_scheduled_task()
        if not SystemEngine.is_admin():
            self.log_message("\n[!] Listing System Restore points requires Administrator privileges.")
            return

        def worker():
            self.after(0, lambda: self.set_busy(True))
            self.after(0, lambda: self.log_message("\n--- Querying Existing Windows System Restore Points ---"))
            ps_cmd = (
                "$rps = @(Get-ComputerRestorePoint -ErrorAction SilentlyContinue | "
                "Select-Object SequenceNumber, Description, CreationTime); "
                "$rps | ConvertTo-Json -Compress"
            )
            try:
                out = subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command", ps_cmd],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    text=True,
                    timeout=8,
                ).strip()
                if out:
                    raw = json.loads(out)
                    points = [raw] if isinstance(raw, dict) else raw
                    for rp in points:
                        seq = rp.get("SequenceNumber")
                        desc = rp.get("Description")
                        self.after(
                            0,
                            lambda s=seq, d=desc: self.log_message(f"  [#{s}]  {d}"),
                        )
                    self.after(
                        0,
                        lambda c=len(points): self.log_message(f"=== Found {c} System Restore Point(s) ==="),
                    )
                else:
                    self.after(
                        0,
                        lambda: self.log_message(
                            "[-] No existing System Restore points found on drive C:."
                        ),
                    )
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Error reading restore points: {err}"))
            finally:
                self.after(0, lambda: self.set_busy(False))

        threading.Thread(target=worker, daemon=True).start()

    def create_restore_point(self):
        if not SystemEngine.is_admin():
            self.log_message("\n[!] Admin Rights Required to create a Windows System Restore Point.")
            return

        desc = self.desc_entry.get().strip() or "PC Optimizer Safety Restore Point"
        # Sanitize quotes for PowerShell
        desc = desc.replace("'", "").replace('"', "")

        def worker():
            self.after(0, lambda: self.set_busy(True))
            self.after(0, lambda: self.log_message(f"\n--- Creating System Restore Point: '{desc}' ---"))
            self.after(0, lambda: self.log_message("[*] Enabling System Restore on C:\\ and setting frequency..."))

            ps_cmd = (
                "Enable-ComputerRestore -Drive 'C:\\' -ErrorAction SilentlyContinue; "
                "Set-ItemProperty -Path 'HKLM:\\Software\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore' "
                "-Name 'SystemRestorePointCreationFrequency' -Value 0 -Type DWord -ErrorAction SilentlyContinue; "
                f"Checkpoint-Computer -Description '{desc}' -RestorePointType 'MODIFY_SETTINGS'"
            )
            try:
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=60,
                )
                if res.returncode == 0:
                    self.after(
                        0,
                        lambda: self.log_message(f"[+] Successfully created System Restore Point: '{desc}'!"),
                    )
                else:
                    err_txt = (res.stderr or res.stdout or "Unknown error").strip()
                    self.after(0, lambda m=err_txt: self.log_message(f"[!] Could not create restore point: {m}"))
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Restore Point creation error: {err}"))
            finally:
                self.after(0, lambda: self.set_busy(False))
                self.list_restore_points()

        threading.Thread(target=worker, daemon=True).start()

    # ==========================================
    # WINDOWS TASK SCHEDULER FUNCTIONS
    # ==========================================
    def check_scheduled_task(self):
        def worker():
            try:
                res = subprocess.run(
                    ["schtasks", "/Query", "/TN", self.TASK_NAME],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=4,
                )
                if res.returncode == 0:
                    self.after(
                        0,
                        lambda: self.sched_status_lbl.configure(
                            text=f"Task Status: ✅ ACTIVE ({self.TASK_NAME})", text_color="#2FA572"
                        ),
                    )
                else:
                    self.after(
                        0,
                        lambda: self.sched_status_lbl.configure(
                            text="Task Status: ⏸️ Not Scheduled", text_color="gray"
                        ),
                    )
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def install_scheduled_task(self):
        if not SystemEngine.is_admin():
            self.log_message("\n[!] Admin Rights Required to register a Windows Scheduled Task.")
            return

        day = self.day_menu.get()

        def worker():
            self.after(0, lambda: self.set_busy(True))
            self.after(
                0,
                lambda: self.log_message(f"\n--- Registering Weekly Auto-Clean Task (Every {day} at 12:00) ---"),
            )
            # Safe command that cleans User/Windows Temp and flushes DNS silently
            task_cmd = (
                'cmd.exe /c "del /q /f /s %TEMP%\\* >nul 2>&1 & '
                'del /q /f /s C:\\Windows\\Temp\\* >nul 2>&1 & '
                'ipconfig /flushdns >nul 2>&1"'
            )
            try:
                res = subprocess.run(
                    [
                        "schtasks",
                        "/Create",
                        "/SC",
                        "WEEKLY",
                        "/D",
                        day,
                        "/TN",
                        self.TASK_NAME,
                        "/TR",
                        task_cmd,
                        "/ST",
                        "12:00",
                        "/RL",
                        "HIGHEST",
                        "/F",
                    ],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=8,
                )
                if res.returncode == 0:
                    self.after(
                        0,
                        lambda: self.log_message(
                            f"[+] Scheduled Task '{self.TASK_NAME}' created! Will run every {day} at 12:00 PM."
                        ),
                    )
                else:
                    self.after(
                        0,
                        lambda m=res.stderr.strip(): self.log_message(f"[!] Task Scheduler error: {m}"),
                    )
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Error creating task: {err}"))
            finally:
                self.after(0, lambda: self.set_busy(False))
                self.check_scheduled_task()

        threading.Thread(target=worker, daemon=True).start()

    def remove_scheduled_task(self):
        if not SystemEngine.is_admin():
            self.log_message("\n[!] Admin Rights Required to remove a Scheduled Task.")
            return

        def worker():
            self.after(0, lambda: self.set_busy(True))
            try:
                res = subprocess.run(
                    ["schtasks", "/Delete", "/TN", self.TASK_NAME, "/F"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5,
                )
                if res.returncode == 0:
                    self.after(
                        0,
                        lambda: self.log_message(f"[+] Removed Scheduled Task '{self.TASK_NAME}'."),
                    )
                else:
                    self.after(0, lambda: self.log_message("[-] No scheduled task was registered."))
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Error removing task: {err}"))
            finally:
                self.after(0, lambda: self.set_busy(False))
                self.check_scheduled_task()

        threading.Thread(target=worker, daemon=True).start()