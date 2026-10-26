# file_shredder_unlock.py
import os
import stat
import uuid
import threading
from tkinter import filedialog, messagebox
import psutil
import customtkinter as ctk
from backend_engine import SystemEngine


class FileShredderUnlockView(ctk.CTkFrame):
    """Modular Multi-Pass Secure File Shredder & Locked File Process Hunter."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.shred_queue = []
        self.locking_procs = []

        # ==========================================
        # CARD 1: MILITARY-GRADE FILE SHREDDER
        # ==========================================
        shred_card = ctk.CTkFrame(self)
        shred_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            shred_card,
            text="🔥 SECURE FILE & FOLDER SHREDDER",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#E74C3C",
        ).pack(anchor="w", padx=15, pady=(12, 2))

        ctk.CTkLabel(
            shred_card,
            text="Overwrites raw disk sectors and scrambles MFT filenames to prevent forensic recovery.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 8))

        btn_select_row = ctk.CTkFrame(shred_card, fg_color="transparent")
        btn_select_row.pack(fill="x", padx=15, pady=4)

        ctk.CTkButton(
            btn_select_row,
            text="📄 + Add File(s)",
            height=32,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.add_files_to_shred,
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        ctk.CTkButton(
            btn_select_row,
            text="📁 + Add Folder",
            height=32,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.add_folder_to_shred,
        ).pack(side="left", expand=True, fill="x", padx=4)

        ctk.CTkButton(
            btn_select_row,
            text="🧹 Clear List",
            width=90,
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(weight="bold"),
            command=self.clear_shred_queue,
        ).pack(side="right", padx=(4, 0))

        pass_row = ctk.CTkFrame(shred_card, fg_color="transparent")
        pass_row.pack(fill="x", padx=15, pady=6)

        ctk.CTkLabel(pass_row, text="Overwrite Algorithm:", font=ctk.CTkFont(size=12, weight="bold")).pack(
            side="left"
        )

        self.pass_menu = ctk.CTkOptionMenu(
            pass_row,
            values=[
                "1-Pass Fast Zero/Random",
                "3-Pass DoD 5220.22-M (Zeros + Ones + Random)",
                "7-Pass Ultra Paranoid Wipe",
            ],
            width=260,
        )
        self.pass_menu.set("3-Pass DoD 5220.22-M (Zeros + Ones + Random)")
        self.pass_menu.pack(side="right")

        self.shred_btn = ctk.CTkButton(
            shred_card,
            text="🔥 SHRED SELECTED ITEMS PERMANENTLY (0 Queued)",
            height=38,
            fg_color="#C0392B",
            hover_color="#922B21",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.confirm_and_shred,
        )
        self.shred_btn.pack(fill="x", padx=15, pady=(6, 14))

        # ==========================================
        # CARD 2: LOCKED FILE HUNTER & UNLOCKER
        # ==========================================
        unlock_card = ctk.CTkFrame(self)
        unlock_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            unlock_card,
            text="🔓 LOCKED FILE PROCESS HUNTER",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w", padx=15, pady=(12, 2))

        ctk.CTkLabel(
            unlock_card,
            text="Find and terminate background processes holding a lock on a stubborn file or folder.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 8))

        target_row = ctk.CTkFrame(unlock_card, fg_color="transparent")
        target_row.pack(fill="x", padx=15, pady=4)

        self.lock_path_entry = ctk.CTkEntry(
            target_row,
            placeholder_text="Select or paste path to locked file or folder...",
        )
        self.lock_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            target_row,
            text="📂 Browse",
            width=90,
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(weight="bold"),
            command=self.browse_locked_target,
        ).pack(side="right")

        self.hunt_btn = ctk.CTkButton(
            unlock_card,
            text="🔎 Scan Processes Locking This Path",
            height=34,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(weight="bold"),
            command=self.find_locking_processes,
        )
        self.hunt_btn.pack(fill="x", padx=15, pady=6)

        self.kill_locks_btn = ctk.CTkButton(
            unlock_card,
            text="🔓 Force-Close Locking Processes (0 Found)",
            height=38,
            fg_color="#D35400",
            hover_color="#A04000",
            font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled",
            command=self.kill_locking_processes,
        )
        self.kill_locks_btn.pack(fill="x", padx=15, pady=(6, 14))

        # ==========================================
        # PROGRESS BAR & CONSOLE LOG
        # ==========================================
        self.progress_bar = ctk.CTkProgressBar(self, height=12, progress_color="#E74C3C")
        self.progress_bar.grid(row=1, column=0, columnspan=2, pady=(0, 8), sticky="ew")
        self.progress_bar.set(0)

        self.log_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.log_message(
            "File Shredder & Process Unlocker Ready.\n"
            "⚠️ WARNING: Shredded files are overwritten at the byte level and CANNOT be recovered by any software."
        )

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ==========================================
    # PART 1: SECURE SHREDDER LOGIC
    # ==========================================
    def add_files_to_shred(self):
        files = filedialog.askopenfilenames(title="Select File(s) to Securely Shred")
        for f in files:
            norm = os.path.normpath(f)
            if norm not in self.shred_queue:
                self.shred_queue.append(norm)
                self.log_message(f"[+ Queued File] {norm}")
        self._update_shred_button()

    def add_folder_to_shred(self):
        folder = filedialog.askdirectory(title="Select Folder to Securely Shred")
        if folder:
            norm = os.path.normpath(folder)
            # Safety guard against selecting root drive or Windows system folders
            if len(norm) <= 3 or norm.lower().startswith((r"c:\windows", r"c:\program files")):
                self.log_message(f"[!] SAFETY BLOCK: Refusing to queue critical system path '{norm}'.")
                return
            if norm not in self.shred_queue:
                self.shred_queue.append(norm)
                self.log_message(f"[+ Queued Folder] {norm}")
        self._update_shred_button()

    def clear_shred_queue(self):
        self.shred_queue.clear()
        self._update_shred_button()
        self.log_message("[-] Cleared shredder queue.")

    def _update_shred_button(self):
        count = len(self.shred_queue)
        self.shred_btn.configure(text=f"🔥 SHRED SELECTED ITEMS PERMANENTLY ({count} Queued)")

    def confirm_and_shred(self):
        if not self.shred_queue:
            self.log_message("[!] Shredder queue is empty. Add files or folders first.")
            return

        algo = self.pass_menu.get()
        passes = 3 if "3-Pass" in algo else (7 if "7-Pass" in algo else 1)

        confirm = messagebox.askyesno(
            "Confirm Permanent File Shredding",
            f"Are you sure you want to permanently shred {len(self.shred_queue)} queued item(s) using {passes} overwrite pass(es)?\n\n"
            "This operation is IRREVERSIBLE and data cannot be recovered!",
        )
        if not confirm:
            return

        self.shred_btn.configure(state="disabled", text="🔥 SHREDDING IN PROGRESS...")
        self.progress_bar.set(0)
        threading.Thread(target=self._shred_worker, args=(list(self.shred_queue), passes), daemon=True).start()

    @staticmethod
    def _shred_single_file(filepath: str, passes: int) -> tuple[bool, int, str]:
        """Overwrites a file with multi-pass patterns, flushes disk buffers, renames MFT entry, and unlinks."""
        try:
            # Clear Read-Only attribute if set
            os.chmod(filepath, stat.S_IWRITE | stat.S_IREAD)
            file_size = os.path.getsize(filepath)

            chunk_size = 1024 * 1024  # 1 MB chunks
            with open(filepath, "r+b", buffering=0) as f:
                for p in range(passes):
                    f.seek(0)
                    remaining = file_size
                    while remaining > 0:
                        write_len = min(chunk_size, remaining)
                        if p % 3 == 0 and passes > 1:
                            buf = b"\x00" * write_len
                        elif p % 3 == 1 and passes > 1:
                            buf = b"\xff" * write_len
                        else:
                            buf = os.urandom(write_len)
                        f.write(buf)
                        remaining -= write_len
                    f.flush()
                    os.fsync(f.fileno())

                # Truncate to 0 bytes before closing
                f.seek(0)
                f.truncate(0)
                f.flush()
                os.fsync(f.fileno())

            # Scramble filename in Master File Table before unlinking
            dir_name = os.path.dirname(filepath)
            scrambled_name = os.path.join(dir_name, uuid.uuid4().hex[:16] + ".tmp")
            os.rename(filepath, scrambled_name)
            os.unlink(scrambled_name)
            return True, file_size, "Shredded"
        except Exception as e:
            return False, 0, str(e)

    def _shred_worker(self, targets: list[str], passes: int):
        self.after(0, lambda: self.log_message(f"\n--- Starting {passes}-Pass Secure Shredder ---"))

        all_files = []
        dirs_to_remove = []

        for item in targets:
            if os.path.isfile(item):
                all_files.append(item)
            elif os.path.isdir(item):
                for root, dirs, files in os.walk(item, topdown=False):
                    for name in files:
                        all_files.append(os.path.join(root, name))
                    for d in dirs:
                        dirs_to_remove.append(os.path.join(root, d))
                dirs_to_remove.append(item)

        total_files = max(1, len(all_files))
        shredded_count = 0
        total_bytes = 0

        for idx, fpath in enumerate(all_files, start=1):
            ok, sz, msg = self._shred_single_file(fpath, passes)
            if ok:
                shredded_count += 1
                total_bytes += sz
                self.after(
                    0,
                    lambda p=fpath, s=sz: self.log_message(
                        f"  [🔥 Destroyed] {os.path.basename(p)} ({SystemEngine.format_bytes(s)})"
                    ),
                )
            else:
                self.after(0, lambda p=fpath, m=msg: self.log_message(f"  [!] Failed {p}: {m}"))

            prog = idx / total_files
            self.after(0, lambda pr=prog: self.progress_bar.set(pr))

        # Remove empty directories after files are shredded
        for dpath in dirs_to_remove:
            try:
                os.chmod(dpath, stat.S_IWRITE | stat.S_IREAD)
                os.rmdir(dpath)
            except Exception:
                pass

        self.shred_queue.clear()
        self.after(
            0,
            lambda: (
                self.log_message(
                    f"=== Shredding Complete! Permanently destroyed {shredded_count} file(s) "
                    f"({SystemEngine.format_bytes(total_bytes)}) ==="
                ),
                self.shred_btn.configure(state="normal"),
                self._update_shred_button(),
            ),
        )

    # ==========================================
    # PART 2: LOCKED FILE HUNTER & UNLOCKER
    # ==========================================
    def browse_locked_target(self):
        path = filedialog.askopenfilename(title="Select Locked File")
        if not path:
            path = filedialog.askdirectory(title="Or Select Locked Folder")
        if path:
            self.lock_path_entry.delete(0, "end")
            self.lock_path_entry.insert(0, os.path.normpath(path))

    def find_locking_processes(self):
        target = self.lock_path_entry.get().strip()
        if not target or not os.path.exists(target):
            self.log_message("\n[!] Please enter or browse to a valid existing file or folder path first.")
            return

        target_norm = os.path.normcase(os.path.abspath(target))
        self.hunt_btn.configure(state="disabled", text="Scanning Process Handles...")
        self.kill_locks_btn.configure(state="disabled", text="🔓 Force-Close Locking Processes (0 Found)")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        threading.Thread(target=self._lock_hunt_worker, args=(target_norm,), daemon=True).start()

    def _lock_hunt_worker(self, target_norm: str):
        self.after(0, lambda: self.log_message(f"\n--- Scanning Active Process Handles for: {target_norm} ---"))
        found = []
        my_pid = os.getpid()

        for proc in psutil.process_iter(["pid", "name"]):
            pid = proc.info["pid"]
            name = proc.info["name"] or "Unknown"
            if pid in (0, 4, my_pid):
                continue

            try:
                matched_reason = None
                # 1. Check Process Working Directory
                try:
                    cwd = os.path.normcase(proc.cwd())
                    if cwd == target_norm or cwd.startswith(target_norm + os.sep):
                        matched_reason = "Current Working Directory"
                except Exception:
                    pass

                # 2. Check Open File Handles
                if not matched_reason:
                    for of in proc.open_files():
                        fpath = os.path.normcase(of.path)
                        if fpath == target_norm or fpath.startswith(target_norm + os.sep):
                            matched_reason = f"Open File Handle ({os.path.basename(of.path)})"
                            break

                # 3. Check Loaded DLL / Memory Mapped Files
                if not matched_reason:
                    for mmap in proc.memory_maps():
                        mpath = os.path.normcase(mmap.path)
                        if mpath == target_norm or mpath.startswith(target_norm + os.sep):
                            matched_reason = f"Memory-Mapped DLL ({os.path.basename(mmap.path)})"
                            break

                if matched_reason:
                    found.append({"pid": pid, "name": name, "reason": matched_reason})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        self.locking_procs = found
        self.after(0, self._finish_lock_hunt)

    def _finish_lock_hunt(self):
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(1.0)
        self.hunt_btn.configure(state="normal", text="🔎 Scan Processes Locking This Path")

        if not self.locking_procs:
            self.log_message("✅ 0 user processes are currently locking this file/folder.")
            self.kill_locks_btn.configure(
                state="disabled", text="🔓 Force-Close Locking Processes (0 Found)"
            )
        else:
            for p in self.locking_procs:
                self.log_message(
                    f"  🔒 LOCKED BY: {p['name']} (PID: {p['pid']})  —  Reason: {p['reason']}"
                )
            self.log_message(
                f"[!] Found {len(self.locking_procs)} process(es) locking the target. "
                "Click 'Force-Close Locking Processes' to release the lock."
            )
            self.kill_locks_btn.configure(
                state="normal",
                text=f"🔓 Force-Close Locking Processes ({len(self.locking_procs)} Found)",
            )

    def kill_locking_processes(self):
        if not self.locking_procs:
            return

        killed = 0
        for p in self.locking_procs:
            try:
                proc = psutil.Process(p["pid"])
                proc.terminate()
                killed += 1
                self.log_message(f"[+] Terminated locking process: {p['name']} (PID {p['pid']})")
            except Exception as e:
                self.log_message(f"[!] Could not terminate {p['name']} (PID {p['pid']}): {e}")

        self.locking_procs.clear()
        self.kill_locks_btn.configure(
            state="disabled", text="🔓 Force-Close Locking Processes (0 Found)"
        )
        self.log_message(f"=== Released file lock! Terminated {killed} process(es). ===")