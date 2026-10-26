# large_file_finder.py
import os
import threading
import subprocess
import customtkinter as ctk
from backend_engine import SystemEngine


class LargeFileFinderView(ctk.CTkFrame):
    """A modular CustomTkinter view that lives in its own file and plugs into main.py."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header Bar
        top_bar = ctk.CTkFrame(self)
        top_bar.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(
            top_bar, text="Scan Folder:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(15, 5), pady=12)

        default_path = os.path.expanduser("~")
        self.path_entry = ctk.CTkEntry(top_bar, width=320)
        self.path_entry.insert(0, default_path)
        self.path_entry.pack(side="left", padx=5, pady=12)

        ctk.CTkLabel(top_bar, text="Min Size (MB):").pack(side="left", padx=(10, 5))
        self.size_option = ctk.CTkOptionMenu(top_bar, values=["50", "100", "250", "500", "1000"], width=80)
        self.size_option.set("100")
        self.size_option.pack(side="left", padx=5)

        self.scan_btn = ctk.CTkButton(
            top_bar,
            text="🔍 Find Large Files",
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.start_scan,
        )
        self.scan_btn.pack(side="right", padx=15, pady=12)

        # Status Label
        self.status_label = ctk.CTkLabel(
            self, text="Ready to scan for large forgotten files.", text_color="gray"
        )
        self.status_label.grid(row=1, column=0, pady=(0, 5), sticky="w")

        # Results Scrollable Frame
        self.results_scroll = ctk.CTkScrollableFrame(self)
        self.results_scroll.grid(row=2, column=0, sticky="nsew")

    def start_scan(self):
        target_dir = self.path_entry.get().strip()
        min_mb = int(self.size_option.get())
        if not os.path.exists(target_dir):
            self.status_label.configure(text="Error: Folder path does not exist!", text_color="#E74C3C")
            return

        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.status_label.configure(text=f"Scanning {target_dir} for files over {min_mb} MB...", text_color="#3B8ED0")

        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        threading.Thread(target=self.scan_worker, args=(target_dir, min_mb), daemon=True).start()

    def scan_worker(self, target_dir, min_mb):
        min_bytes = min_mb * 1024 * 1024
        found_files = []

        for root, dirs, files in os.walk(target_dir):
            # Skip AppData to focus on personal files first and speed up scan
            if "AppData" in root:
                continue
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                    if size >= min_bytes:
                        found_files.append((filepath, size))
                except OSError:
                    continue

        found_files.sort(key=lambda x: x[1], reverse=True)
        top_files = found_files[:30]  # Show top 30 largest files

        self.after(0, lambda: self.render_results(top_files, len(found_files)))

    def render_results(self, top_files, total_count):
        self.scan_btn.configure(state="normal", text="🔍 Find Large Files")
        self.status_label.configure(
            text=f"Scan complete! Found {total_count} large files (Showing top {len(top_files)}).",
            text_color="#2FA572",
        )

        if not top_files:
            ctk.CTkLabel(self.results_scroll, text="No files found exceeding the selected size.").pack(pady=20)
            return

        for filepath, size in top_files:
            card = ctk.CTkFrame(self.results_scroll)
            card.pack(fill="x", padx=5, pady=4)

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=12, pady=8)

            filename = os.path.basename(filepath)
            ctk.CTkLabel(
                info_frame,
                text=f"{filename}  —  {SystemEngine.format_bytes(size)}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#3B8ED0",
            ).pack(anchor="w")

            ctk.CTkLabel(
                info_frame, text=filepath, font=ctk.CTkFont(size=11), text_color="gray", wraplength=480, justify="left"
            ).pack(anchor="w")

            # Button to highlight the file in Windows Explorer
            ctk.CTkButton(
                card,
                text="📂 Show in Folder",
                width=110,
                height=28,
                fg_color="#34495E",
                hover_color="#2C3E50",
                command=lambda p=filepath: subprocess.Popen(f'explorer /select,"{p}"'),
            ).pack(side="right", padx=12, pady=8)