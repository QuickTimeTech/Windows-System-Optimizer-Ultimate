# cpu_ram_tuner.py
import os
import shutil
import threading
import subprocess
import psutil
import customtkinter as ctk
from backend_engine import SystemEngine


class CpuRamTunerView(ctk.CTkFrame):
    """Modular CPU Priority Tamer, Deep System Cache Cleaner & SSD TRIM Optimizer."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ==========================================
        # CARD 1: CPU TAMER & MEMORY OPTIMIZER
        # ==========================================
        cpu_card = ctk.CTkFrame(self)
        cpu_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            cpu_card,
            text="🧠 CPU PRIORITY TAMER & RAM PURGE",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            cpu_card,
            text="Throttle background CPU hogs and reclaim locked physical memory.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 10))

        self.tame_cpu_btn = ctk.CTkButton(
            cpu_card,
            text="⚡ Tame Background CPU Hogs (Set Below Normal Priority)",
            height=34,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.tame_cpu_processes,
        )
        self.tame_cpu_btn.pack(fill="x", padx=15, pady=4)

        self.restore_cpu_btn = ctk.CTkButton(
            cpu_card,
            text="🔄 Restore All Process Priorities to Normal",
            height=34,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(weight="bold"),
            command=self.restore_cpu_priorities,
        )
        self.restore_cpu_btn.pack(fill="x", padx=15, pady=4)

        self.deep_ram_btn = ctk.CTkButton(
            cpu_card,
            text="🚀 Deep Working-Set RAM Purge + Garbage Collect",
            height=34,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(weight="bold"),
            command=self.deep_ram_purge,
        )
        self.deep_ram_btn.pack(fill="x", padx=15, pady=(4, 15))

        # ==========================================
        # CARD 2: DEEP SYSTEM CACHES & SSD TRIM
        # ==========================================
        cache_card = ctk.CTkFrame(self)
        cache_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            cache_card,
            text="🧹 DEEP SYSTEM CACHES & SSD OPTIMIZER",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#2FA572",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            cache_card,
            text="Clear corrupted icon/thumbnail caches, Windows Update leftovers, and TRIM SSDs.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 10))

        self.thumb_btn = ctk.CTkButton(
            cache_card,
            text="🖼️ Clear Windows Explorer Thumbnail & Icon Cache",
            height=34,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(weight="bold"),
            command=self.clear_thumbnail_cache,
        )
        self.thumb_btn.pack(fill="x", padx=15, pady=4)

        self.wu_cache_btn = ctk.CTkButton(
            cache_card,
            text="📦 Clean Windows Update Download Cache (Admin)",
            height=34,
            fg_color="#D35400",
            hover_color="#A04000",
            font=ctk.CTkFont(weight="bold"),
            command=self.clean_windows_update_cache,
        )
        self.wu_cache_btn.pack(fill="x", padx=15, pady=4)

        self.trim_btn = ctk.CTkButton(
            cache_card,
            text="💿 Run SSD ReTrim / Drive Optimizer on C: (Admin)",
            height=34,
            fg_color="#C0392B",
            hover_color="#922B21",
            font=ctk.CTkFont(weight="bold"),
            command=self.optimize_ssd_trim,
        )
        self.trim_btn.pack(fill="x", padx=15, pady=(4, 15))

        # ==========================================
        # PROGRESS & LOG CONSOLE
        # ==========================================
        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.grid(row=1, column=0, columnspan=2, pady=(0, 8), sticky="ew")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.log_message("CPU & RAM Deep Tuner Ready.")

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def tame_cpu_processes(self):
        """Finds non-critical processes using heavy CPU/RAM and lowers their scheduling priority."""
        def worker():
            self.after(0, self.progress.start)
            self.after(0, lambda: self.log_message("\n--- Scanning for Background CPU & Memory Hogs ---"))

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

            tamed_count = 0
            for proc in psutil.process_iter(["pid", "name", "memory_info"]):
                try:
                    name = (proc.info["name"] or "").lower()
                    pid = proc.info["pid"]
                    if pid in (0, 4) or name in protected:
                        continue

                    mem_mb = proc.info["memory_info"].rss / (1024 * 1024)
                    if mem_mb > 120:  # Throttle heavy background apps using >120MB RAM
                        p = psutil.Process(pid)
                        if p.nice() == psutil.NORMAL_PRIORITY_CLASS:
                            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                            tamed_count += 1
                            self.after(
                                0,
                                lambda n=proc.info["name"], m=mem_mb: self.log_message(
                                    f"[+] Lowered CPU priority for: {n} ({m:.0f} MB)"
                                ),
                            )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            self.after(
                0,
                lambda: self.log_message(
                    f"=== CPU Taming Complete! Throttled {tamed_count} heavy background processes ==="
                ),
            )
            self.after(0, self.progress.stop)
            self.after(0, lambda: self.progress.set(0))

        threading.Thread(target=worker, daemon=True).start()

    def restore_cpu_priorities(self):
        def worker():
            self.after(0, self.progress.start)
            self.after(0, lambda: self.log_message("\n--- Restoring Process Priorities to Normal ---"))
            restored = 0
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    p = psutil.Process(proc.info["pid"])
                    if p.nice() == psutil.BELOW_NORMAL_PRIORITY_CLASS:
                        p.nice(psutil.NORMAL_PRIORITY_CLASS)
                        restored += 1
                except Exception:
                    continue
            self.after(0, lambda: self.log_message(f"=== Restored {restored} processes to Normal priority ==="))
            self.after(0, self.progress.stop)
            self.after(0, lambda: self.progress.set(0))

        threading.Thread(target=worker, daemon=True).start()

    def deep_ram_purge(self):
        def worker():
            self.after(0, self.progress.start)
            SystemEngine.optimize_ram(lambda m: self.after(0, lambda msg=m: self.log_message(msg)))
            self.after(0, self.progress.stop)
            self.after(0, lambda: self.progress.set(0))

        threading.Thread(target=worker, daemon=True).start()

    def clear_thumbnail_cache(self):
        def worker():
            self.after(0, self.progress.start)
            self.after(0, lambda: self.log_message("\n--- Cleaning Windows Explorer Thumbnail Cache ---"))
            explorer_dir = os.path.join(
                os.environ.get("LOCALAPPDATA", ""), r"Microsoft\Windows\Explorer"
            )
            freed = 0
            removed = 0
            if os.path.exists(explorer_dir):
                for f in os.listdir(explorer_dir):
                    if f.startswith("thumbcache_") or f.startswith("iconcache_"):
                        fpath = os.path.join(explorer_dir, f)
                        try:
                            size = os.path.getsize(fpath)
                            os.unlink(fpath)
                            freed += size
                            removed += 1
                        except OSError:
                            continue
            self.after(
                0,
                lambda: self.log_message(
                    f"[+] Removed {removed} unlocked thumbnail/icon cache databases ({SystemEngine.format_bytes(freed)} freed)."
                ),
            )
            self.after(0, self.progress.stop)
            self.after(0, lambda: self.progress.set(0))

        threading.Thread(target=worker, daemon=True).start()

    def clean_windows_update_cache(self):
        if not SystemEngine.is_admin():
            self.log_message("\n[!] Admin Rights Required to clean C:\\Windows\\SoftwareDistribution\\Download.")
            return

        def worker():
            self.after(0, self.progress.start)
            self.after(0, lambda: self.log_message("\n--- Cleaning Windows Update Download Cache ---"))
            wu_dir = r"C:\Windows\SoftwareDistribution\Download"
            subprocess.run(["net", "stop", "wuauserv"], creationflags=subprocess.CREATE_NO_WINDOW)

            freed = 0
            if os.path.exists(wu_dir):
                for item in os.listdir(wu_dir):
                    p = os.path.join(wu_dir, item)
                    try:
                        if os.path.isfile(p):
                            freed += os.path.getsize(p)
                            os.unlink(p)
                        elif os.path.isdir(p):
                            shutil.rmtree(p)
                    except Exception:
                        continue

            subprocess.run(["net", "start", "wuauserv"], creationflags=subprocess.CREATE_NO_WINDOW)
            self.after(
                0,
                lambda: self.log_message(
                    f"=== Windows Update Cache Cleaned! Freed {SystemEngine.format_bytes(freed)} ==="
                ),
            )
            self.after(0, self.progress.stop)
            self.after(0, lambda: self.progress.set(0))

        threading.Thread(target=worker, daemon=True).start()

    def optimize_ssd_trim(self):
        if not SystemEngine.is_admin():
            self.log_message("\n[!] Admin Rights Required to run SSD TRIM optimization.")
            return

        def worker():
            self.after(0, self.progress.start)
            self.after(0, lambda: self.log_message("\n--- Running Windows Drive Optimizer (defrag C: /O) ---"))
            try:
                out = subprocess.check_output(
                    ["defrag", "C:", "/O"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    text=True,
                )
                for line in out.splitlines():
                    if line.strip():
                        self.after(0, lambda l=line.strip(): self.log_message(f"  {l}"))
                self.after(0, lambda: self.log_message("=== Drive C: TRIM / Optimization Complete! ==="))
            except Exception as e:
                self.after(0, lambda err=e: self.log_message(f"[!] Optimization error: {err}"))
            finally:
                self.after(0, self.progress.stop)
                self.after(0, lambda: self.progress.set(0))

        threading.Thread(target=worker, daemon=True).start()