# duplicate_finder.py
import os
import hashlib
import threading
import subprocess
from collections import defaultdict
from tkinter import filedialog
import customtkinter as ctk
from backend_engine import SystemEngine


class DuplicateFinderView(ctk.CTkFrame):
    """Modular Duplicate File Finder using Size Grouping + SHA-256 Hashing."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ==========================================
        # TOP CONTROLS BAR
        # ==========================================
        top_bar = ctk.CTkFrame(self)
        top_bar.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(
            top_bar, text="Folder:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(15, 5), pady=12)

        default_scan_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(default_scan_dir):
            default_scan_dir = os.path.expanduser("~")

        self.path_entry = ctk.CTkEntry(top_bar, width=260)
        self.path_entry.insert(0, default_scan_dir)
        self.path_entry.pack(side="left", padx=5, pady=12)

        self.browse_btn = ctk.CTkButton(
            top_bar,
            text="📂 Browse",
            width=85,
            fg_color="#34495E",
            hover_color="#2C3E50",
            command=self.browse_folder,
        )
        self.browse_btn.pack(side="left", padx=5, pady=12)

        ctk.CTkLabel(top_bar, text="Min Size:").pack(side="left", padx=(10, 5))
        self.min_size_menu = ctk.CTkOptionMenu(
            top_bar, values=["1 KB", "100 KB", "1 MB", "10 MB"], width=95
        )
        self.min_size_menu.set("100 KB")
        self.min_size_menu.pack(side="left", padx=5)

        self.scan_btn = ctk.CTkButton(
            top_bar,
            text="🔍 Scan Duplicates",
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.start_scan,
        )
        self.scan_btn.pack(side="right", padx=15, pady=12)

        # ==========================================
        # STATUS BAR & PROGRESS
        # ==========================================
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.grid(row=1, column=0, pady=(0, 6), sticky="ew")

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Select a folder (like Downloads, Documents, or Pictures) to find identical files.",
            text_color="gray",
        )
        self.status_label.pack(side="left")

        # ==========================================
        # RESULTS SCROLLABLE AREA
        # ==========================================
        self.results_scroll = ctk.CTkScrollableFrame(self)
        self.results_scroll.grid(row=2, column=0, sticky="nsew")

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.path_entry.get())
        if folder:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, os.path.normpath(folder))

    def get_min_bytes(self) -> int:
        val = self.min_size_menu.get()
        mapping = {
            "1 KB": 1024,
            "100 KB": 100 * 1024,
            "1 MB": 1024 * 1024,
            "10 MB": 10 * 1024 * 1024,
        }
        return mapping.get(val, 1024)

    @staticmethod
    def compute_sha256(filepath: str) -> str | None:
        """Reads file in 64KB chunks and returns its SHA-256 hex digest."""
        hasher = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, PermissionError):
            return None

    def start_scan(self):
        target_dir = self.path_entry.get().strip()
        if not os.path.exists(target_dir):
            self.status_label.configure(text="Error: Folder path does not exist!", text_color="#E74C3C")
            return

        min_bytes = self.get_min_bytes()
        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.status_label.configure(
            text="Pass 1/2: Grouping files by byte size...", text_color="#3B8ED0"
        )

        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        threading.Thread(
            target=self.scan_worker, args=(target_dir, min_bytes), daemon=True
        ).start()

    def scan_worker(self, target_dir: str, min_bytes: int):
        # Pass 1: Group files by exact byte size
        size_groups = defaultdict(list)
        for root, _, files in os.walk(target_dir):
            if "AppData" in root or "$RECYCLE.BIN" in root:
                continue
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    if os.path.islink(filepath):
                        continue
                    size = os.path.getsize(filepath)
                    if size >= min_bytes:
                        size_groups[size].append(filepath)
                except OSError:
                    continue

        # Filter down to only sizes that have 2 or more files
        candidates = {s: paths for s, paths in size_groups.items() if len(paths) > 1}
        total_candidates = sum(len(p) for p in candidates.values())

        self.after(
            0,
            lambda: self.status_label.configure(
                text=f"Pass 2/2: Computing SHA-256 hashes for {total_candidates} candidate files...",
                text_color="#9B59B6",
            ),
        )

        # Pass 2: Group by SHA-256 hash
        duplicates = []  # List of tuples: (file_size, sha256_hash, [filepaths])
        wasted_bytes = 0

        for size, paths in candidates.items():
            hash_groups = defaultdict(list)
            for path in paths:
                file_hash = self.compute_sha256(path)
                if file_hash:
                    hash_groups[file_hash].append(path)

            for file_hash, identical_paths in hash_groups.items():
                if len(identical_paths) > 1:
                    duplicates.append((size, file_hash, identical_paths))
                    wasted_bytes += size * (len(identical_paths) - 1)

        # Sort by largest wasted space first
        duplicates.sort(key=lambda x: x[0] * (len(x[2]) - 1), reverse=True)
        self.after(0, lambda: self.render_results(duplicates[:25], len(duplicates), wasted_bytes))

    def render_results(self, top_groups, total_groups: int, wasted_bytes: int):
        self.scan_btn.configure(state="normal", text="🔍 Scan Duplicates")

        if not top_groups:
            self.status_label.configure(
                text="Scan complete! No duplicate files found in this folder.", text_color="#2FA572"
            )
            ctk.CTkLabel(
                self.results_scroll, text="🎉 Clean! No duplicate files detected."
            ).pack(pady=25)
            return

        self.status_label.configure(
            text=(
                f"Found {total_groups} duplicate groups ({SystemEngine.format_bytes(wasted_bytes)} "
                f"reclaimable space). Showing top {len(top_groups)} groups:"
            ),
            text_color="#2FA572",
        )

        for size, file_hash, paths in top_groups:
            group_card = ctk.CTkFrame(self.results_scroll)
            group_card.pack(fill="x", padx=5, pady=6)

            # Group Header showing File Name, Size, and Short SHA-256 Hash
            header = ctk.CTkFrame(group_card, fg_color="transparent")
            header.pack(fill="x", padx=12, pady=(8, 4))

            sample_name = os.path.basename(paths[0])
            ctk.CTkLabel(
                header,
                text=f"📄 {sample_name}  ({SystemEngine.format_bytes(size)} each)",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#3B8ED0",
            ).pack(side="left")

            ctk.CTkLabel(
                header,
                text=f"SHA-256: {file_hash[:16]}...",
                font=ctk.CTkFont(family="Consolas", size=11),
                text_color="gray",
            ).pack(side="right")

            # List each file in the duplicate group
            for idx, filepath in enumerate(paths):
                row = ctk.CTkFrame(group_card, fg_color=("gray85", "gray17"))
                row.pack(fill="x", padx=12, pady=3)

                badge_text = "✅ Original (Keep)" if idx == 0 else "⚠️ Duplicate"
                badge_color = "#2FA572" if idx == 0 else "#E67E22"

                ctk.CTkLabel(
                    row,
                    text=badge_text,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=badge_color,
                    width=125,
                    anchor="w",
                ).pack(side="left", padx=10, pady=6)

                ctk.CTkLabel(
                    row,
                    text=filepath,
                    font=ctk.CTkFont(size=11),
                    text_color="lightgray",
                    wraplength=420,
                    justify="left",
                ).pack(side="left", padx=5, pady=6, fill="x", expand=True)

                # Show in Folder Button
                ctk.CTkButton(
                    row,
                    text="📂 Open",
                    width=65,
                    height=26,
                    fg_color="#34495E",
                    hover_color="#2C3E50",
                    command=lambda p=filepath: subprocess.Popen(f'explorer /select,"{p}"'),
                ).pack(side="right", padx=(4, 8), pady=6)

                # Delete Button (Only on Duplicate rows so user doesn't accidentally delete the Original)
                if idx > 0:
                    del_btn = ctk.CTkButton(
                        row,
                        text="🗑️ Delete",
                        width=75,
                        height=26,
                        fg_color="#C0392B",
                        hover_color="#922B21",
                    )
                    del_btn.configure(
                        command=lambda p=filepath, r=row: self.delete_duplicate_file(p, r)
                    )
                    del_btn.pack(side="right", padx=4, pady=6)

            ctk.CTkLabel(group_card, text="", height=4).pack()

    def delete_duplicate_file(self, filepath: str, row_widget: ctk.CTkFrame):
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
            row_widget.destroy()
            self.status_label.configure(
                text=f"Deleted duplicate: {os.path.basename(filepath)}", text_color="#2FA572"
            )
        except Exception as e:
            self.status_label.configure(
                text=f"Could not delete {os.path.basename(filepath)}: {e}", text_color="#E74C3C"
            )