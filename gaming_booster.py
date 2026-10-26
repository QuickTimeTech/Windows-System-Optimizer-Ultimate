# gaming_booster.py
import threading
import subprocess
import psutil
import customtkinter as ctk
from backend_engine import SystemEngine


class GamingBoosterView(ctk.CTkFrame):
    """Modular Gaming & Performance Booster: Power Plan Switcher + Non-Blocking Game Mode Optimizer."""

    # Standard Windows Power Scheme GUIDs
    GUID_ULTIMATE = "e9a42b02-d5df-448d-aa00-03f14749eb61"
    GUID_HIGH = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    GUID_BALANCED = "381b4222-f694-41f0-9685-ff5bb260df2e"
    GUID_SAVER = "a1841308-3541-4fab-bc81-f71556f20b4a"

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ==========================================
        # CARD 1: WINDOWS POWER PLAN SWITCHER
        # ==========================================
        self.power_card = ctk.CTkFrame(self)
        self.power_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            self.power_card,
            text="⚡ WINDOWS POWER PLAN CONTROLLER",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w", padx=15, pady=(12, 2))

        self.active_plan_label = ctk.CTkLabel(
            self.power_card,
            text="Active Plan: Checking...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2FA572",
        )
        self.active_plan_label.pack(anchor="w", padx=15, pady=(0, 10))

        self.btn_ultimate = ctk.CTkButton(
            self.power_card,
            text="🔥 Unlock & Enable 'Ultimate Performance'",
            height=34,
            fg_color="#D35400",
            hover_color="#A04000",
            font=ctk.CTkFont(weight="bold"),
            command=self.enable_ultimate_plan,
        )
        self.btn_ultimate.pack(fill="x", padx=15, pady=4)

        self.btn_high = ctk.CTkButton(
            self.power_card,
            text="🚀 High Performance Plan",
            height=34,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.set_power_plan(self.GUID_HIGH, "High Performance"),
        )
        self.btn_high.pack(fill="x", padx=15, pady=4)

        self.btn_balanced = ctk.CTkButton(
            self.power_card,
            text="⚖️ Balanced Plan (Default)",
            height=34,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.set_power_plan(self.GUID_BALANCED, "Balanced"),
        )
        self.btn_balanced.pack(fill="x", padx=15, pady=(4, 15))

        # ==========================================
        # CARD 2: 1-CLICK GAME MODE BOOSTER
        # ==========================================
        self.game_card = ctk.CTkFrame(self)
        self.game_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            self.game_card,
            text="🎮 1-CLICK GAME & FPS BOOSTER",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#9B59B6",
        ).pack(anchor="w", padx=15, pady=(12, 2))

        ctk.CTkLabel(
            self.game_card,
            text="Pauses background disk/CPU hogs, throttles background apps, and purges RAM.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 10))

        self.var_stop_search = ctk.BooleanVar(value=True)
        self.var_stop_sysmain = ctk.BooleanVar(value=True)
        self.var_stop_diag = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(
            self.game_card, text="Pause Windows Search Indexer (WSearch)", variable=self.var_stop_search
        ).pack(anchor="w", padx=15, pady=4)

        ctk.CTkCheckBox(
            self.game_card, text="Pause SysMain / Superfetch Disk Preloader", variable=self.var_stop_sysmain
        ).pack(anchor="w", padx=15, pady=4)

        ctk.CTkCheckBox(
            self.game_card, text="Pause Windows Telemetry & Spooler (DiagTrack/Spooler)", variable=self.var_stop_diag
        ).pack(anchor="w", padx=15, pady=4)

        btn_row = ctk.CTkFrame(self.game_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(10, 15))

        self.engage_btn = ctk.CTkButton(
            btn_row,
            text="⚡ ENGAGE GAME MODE",
            height=36,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(weight="bold"),
            command=self.engage_game_mode,
        )
        self.engage_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.restore_btn = ctk.CTkButton(
            btn_row,
            text="🔄 Restore Services",
            height=36,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(weight="bold"),
            command=self.restore_normal_mode,
        )
        self.restore_btn.pack(side="right", expand=True, fill="x", padx=(5, 0))

        # ==========================================
        # PROGRESS & LOG OUTPUT
        # ==========================================
        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.grid(row=1, column=0, columnspan=2, pady=(0, 8), sticky="ew")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.log_message("Gaming & Performance Booster Ready.")

        self.refresh_active_plan()

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def set_ui_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        for btn in [self.btn_ultimate, self.btn_high, self.btn_balanced, self.engage_btn, self.restore_btn]:
            btn.configure(state=state)
        if busy:
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.set(0)

    def refresh_active_plan(self):
        def worker():
            try:
                out = subprocess.check_output(
                    ["powercfg", "/getactivescheme"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    text=True,
                    timeout=3,
                ).strip()
                if "(" in out and ")" in out:
                    plan_name = out.split("(")[-1].split(")")[0]
                else:
                    plan_name = out
                self.after(0, lambda p=plan_name: self.active_plan_label.configure(text=f"Active Plan: {p}"))
            except Exception:
                self.after(0, lambda: self.active_plan_label.configure(text="Active Plan: Standard"))

        threading.Thread(target=worker, daemon=True).start()

    def set_power_plan(self, guid: str, name: str):
        def worker():
            self.after(0, lambda: self.set_ui_busy(True))
            self.after(0, lambda: self.log_message(f"\n--- Switching Power Plan to {name} ---"))
            try:
                # Duplicate scheme first in case High Performance is hidden on Modern Standby laptops
                subprocess.run(
                    ["powercfg", "-duplicatescheme", guid],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True,
                    timeout=4,
                )
                subprocess.run(
                    ["powercfg", "/setactive", guid],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    check=True,
                    timeout=4,
                )
                self.after(0, lambda: self.log_message(f"[+] Activated '{name}' power plan."))
                self.refresh_active_plan()
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Could not switch plan: {err}"))
            finally:
                self.after(0, lambda: self.set_ui_busy(False))

        threading.Thread(target=worker, daemon=True).start()

    def enable_ultimate_plan(self):
        """Unlocks and activates Windows Ultimate Performance power scheme."""
        def worker():
            self.after(0, lambda: self.set_ui_busy(True))
            self.after(0, lambda: self.log_message("\n--- Unlocking Ultimate Performance Power Plan ---"))
            try:
                existing = subprocess.check_output(
                    ["powercfg", "/list"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    text=True,
                    timeout=4,
                )
                target_guid = None
                for line in existing.splitlines():
                    if "Ultimate Performance" in line or self.GUID_ULTIMATE in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            target_guid = parts[1].strip().split()[0]
                            break

                if not target_guid:
                    dup_out = subprocess.check_output(
                        ["powercfg", "-duplicatescheme", self.GUID_ULTIMATE],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        text=True,
                        timeout=4,
                    )
                    if ":" in dup_out:
                        target_guid = dup_out.split(":")[1].strip().split()[0]
                    else:
                        target_guid = self.GUID_ULTIMATE

                subprocess.run(
                    ["powercfg", "/setactive", target_guid],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    check=True,
                    timeout=4,
                )
                self.after(0, lambda: self.log_message("[+] Ultimate Performance Plan unlocked & activated!"))
                self.refresh_active_plan()
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Failed to unlock Ultimate plan: {err}"))
            finally:
                self.after(0, lambda: self.set_ui_busy(False))

        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def _stop_service_fast(service_name: str) -> tuple[bool, str]:
        """Uses PowerShell Stop-Service -Force -NoWait with a strict timeout so it never hangs."""
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                f"Stop-Service -Name '{service_name}' -Force -NoWait -ErrorAction Stop",
            ]
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=4,
            )
            if res.returncode == 0:
                return True, "Paused"
            return False, "Already stopped or protected"
        except subprocess.TimeoutExpired:
            return True, "Stop signal sent (background)"
        except Exception:
            return False, "Skipped"

    def engage_game_mode(self):
        def worker():
            self.after(0, lambda: self.set_ui_busy(True))
            self.after(0, lambda: self.log_message("\n========================================"))
            self.after(0, lambda: self.log_message(" ⚡ ENGAGING 1-CLICK GAME MODE"))
            self.after(0, lambda: self.log_message("========================================"))

            try:
                # Step 1: Pause selected background services (Non-blocking with 4s timeout)
                if SystemEngine.is_admin():
                    services_to_stop = []
                    if self.var_stop_search.get():
                        services_to_stop.append(("WSearch", "Windows Search Indexer"))
                    if self.var_stop_sysmain.get():
                        services_to_stop.append(("SysMain", "SysMain / Superfetch"))
                    if self.var_stop_diag.get():
                        services_to_stop.append(("DiagTrack", "Connected User Telemetry"))
                        services_to_stop.append(("Spooler", "Print Spooler"))

                    for svc, label in services_to_stop:
                        self.after(0, lambda l=label: self.log_message(f"[*] Stopping {l}..."))
                        ok, status_msg = self._stop_service_fast(svc)
                        symbol = "[+]" if ok else "[-]"
                        self.after(
                            0,
                            lambda s=symbol, l=label, m=status_msg: self.log_message(f"{s} {l}: {m}"),
                        )
                else:
                    self.after(
                        0,
                        lambda: self.log_message(
                            "[!] Running without Admin: Skipping service stops (RAM & CPU boost will still run)."
                        ),
                    )

                # Step 2: Lower background CPU/RAM hog process priorities
                self.after(0, lambda: self.log_message("[*] Throttling heavy background apps..."))
                protected = {
                    "system",
                    "idle",
                    "explorer.exe",
                    "dwm.exe",
                    "csrss.exe",
                    "wininit.exe",
                    "winlogon.exe",
                    "services.exe",
                    "lsass.exe",
                    "svchost.exe",
                    "python.exe",
                    "python3.11.exe",
                    "pc_optimizer_ultimate.exe",
                }
                throttled = 0
                for proc in psutil.process_iter(["pid", "name", "memory_info"]):
                    try:
                        name = (proc.info["name"] or "").lower()
                        pid = proc.info["pid"]
                        if pid in (0, 4) or name in protected:
                            continue
                        if (proc.info["memory_info"].rss / (1024 * 1024)) > 150:
                            p = psutil.Process(pid)
                            if p.nice() == psutil.NORMAL_PRIORITY_CLASS:
                                p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                                throttled += 1
                    except Exception:
                        continue
                self.after(
                    0,
                    lambda c=throttled: self.log_message(
                        f"[+] Set {c} heavy background processes to Below Normal CPU priority."
                    ),
                )

                # Step 3: Trim physical RAM working sets
                SystemEngine.optimize_ram(lambda m: self.after(0, lambda msg=m: self.log_message(msg)))

                # Step 4: Flush DNS cache for clean network routing
                SystemEngine.flush_dns(lambda m: self.after(0, lambda msg=m: self.log_message(msg)))

                self.after(
                    0,
                    lambda: self.log_message("\n🎉 GAME MODE ACTIVE! Maximum RAM, CPU & Network Ready."),
                )
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Game Mode error: {err}"))
            finally:
                # Always stop the progress bar and re-enable buttons!
                self.after(0, lambda: self.set_ui_busy(False))

        threading.Thread(target=worker, daemon=True).start()

    def restore_normal_mode(self):
        def worker():
            self.after(0, lambda: self.set_ui_busy(True))
            self.after(0, lambda: self.log_message("\n--- Restoring Normal Windows Services & Priorities ---"))
            try:
                if SystemEngine.is_admin():
                    for svc, label in [
                        ("WSearch", "Windows Search"),
                        ("SysMain", "SysMain / Superfetch"),
                        ("Spooler", "Print Spooler"),
                    ]:
                        try:
                            subprocess.run(
                                [
                                    "powershell",
                                    "-NoProfile",
                                    "-Command",
                                    f"Start-Service -Name '{svc}' -ErrorAction SilentlyContinue",
                                ],
                                capture_output=True,
                                creationflags=subprocess.CREATE_NO_WINDOW,
                                timeout=4,
                            )
                            self.after(0, lambda l=label: self.log_message(f"[+] Restarted service: {l}"))
                        except subprocess.TimeoutExpired:
                            self.after(0, lambda l=label: self.log_message(f"[+] Start signal sent to: {l}"))

                # Restore process priorities back to Normal
                restored = 0
                for proc in psutil.process_iter(["pid"]):
                    try:
                        p = psutil.Process(proc.info["pid"])
                        if p.nice() == psutil.BELOW_NORMAL_PRIORITY_CLASS:
                            p.nice(psutil.NORMAL_PRIORITY_CLASS)
                            restored += 1
                    except Exception:
                        continue

                self.after(
                    0,
                    lambda r=restored: self.log_message(
                        f"[+] Restored {r} background processes back to Normal CPU priority."
                    ),
                )
                self.after(0, lambda: self.log_message("=== Normal Mode Restored ==="))
            finally:
                self.after(0, lambda: self.set_ui_busy(False))

        threading.Thread(target=worker, daemon=True).start()