# disk_health_analyzer.py
import os
import json
import threading
import subprocess
from tkinter import filedialog
import customtkinter as ctk
from backend_engine import SystemEngine


class DiskHealthAnalyzerView(ctk.CTkFrame):
    """Modular Physical Disk S.M.A.R.T. Health Monitor + Subfolder Space Analyzer."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # ==========================================
        # SECTION 1: PHYSICAL DRIVE S.M.A.R.T. HEALTH
        # ==========================================
        smart_header = ctk.CTkFrame(self, fg_color="transparent")
        smart_header.grid(row=0, column=0, pady=(0, 6), sticky="ew")

        ctk.CTkLabel(
            smart_header,
            text="💿 Physical Drive S.M.A.R.T. Health & Telemetry",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        self.refresh_smart_btn = ctk.CTkButton(
            smart_header,
            text="🔄 Refresh Drive Health",
            width=155,
            height=30,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.load_smart_health,
        )
        self.refresh_smart_btn.pack(side="right")

        self.smart_scroll = ctk.CTkScrollableFrame(self, height=135, orientation="horizontal")
        self.smart_scroll.grid(row=1, column=0, pady=(0, 12), sticky="ew")

        # ==========================================
        # SECTION 2: SUBFOLDER SPACE ANALYZER (TREEMAP LIST)
        # ==========================================
        analyzer_bar = ctk.CTkFrame(self)
        analyzer_bar.grid(row=2, column=0, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(
            analyzer_bar, text="📊 Analyze Folder:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(15, 5), pady=12)

        default_dir = os.path.expanduser("~")
        self.folder_entry = ctk.CTkEntry(analyzer_bar, width=320)
        self.folder_entry.insert(0, default_dir)
        self.folder_entry.pack(side="left", padx=5, pady=12, fill="x", expand=True)

        ctk.CTkButton(
            analyzer_bar,
            text="📂 Browse",
            width=85,
            fg_color="#34495E",
            hover_color="#2C3E50",
            command=self.browse_folder,
        ).pack(side="left", padx=5, pady=12)

        self.analyze_btn = ctk.CTkButton(
            analyzer_bar,
            text="🔍 Rank Subfolder Sizes",
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(weight="bold"),
            command=self.start_folder_analysis,
        )
        self.analyze_btn.pack(side="right", padx=15, pady=12)

        # ==========================================
        # RESULTS AREA FOR SUBFOLDER RANKING
        # ==========================================
        self.results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.results_frame.grid(row=3, column=0, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(
            self.results_frame,
            text="Click 'Rank Subfolder Sizes' to see which subfolders are using the most disk space.",
            text_color="gray",
        )
        self.status_label.grid(row=0, column=0, pady=(0, 4), sticky="w")

        self.folders_scroll = ctk.CTkScrollableFrame(self.results_frame)
        self.folders_scroll.grid(row=1, column=0, sticky="nsew")

    # ==========================================
    # S.M.A.R.T. PHYSICAL DISK TELEMETRY
    # ==========================================
    def load_smart_health(self):
        self.refresh_smart_btn.configure(state="disabled", text="Checking...")
        for widget in self.smart_scroll.winfo_children():
            widget.destroy()
        threading.Thread(target=self._smart_worker, daemon=True).start()

    def _smart_worker(self):
        ps_cmd = (
            "$disks = Get-PhysicalDisk | ForEach-Object { "
            "$rel = $_ | Get-StorageReliabilityCounter -ErrorAction SilentlyContinue; "
            "[PSCustomObject]@{ "
            "FriendlyName = $_.FriendlyName; "
            "MediaType = $_.MediaType.ToString(); "
            "BusType = $_.BusType.ToString(); "
            "HealthStatus = $_.HealthStatus.ToString(); "
            "OperationalStatus = $_.OperationalStatus.ToString(); "
            "Size = $_.Size; "
            "Temperature = if ($rel) { $rel.Temperature } else { $null }; "
            "Wear = if ($rel) { $rel.Wear } else { $null }; "
            "ReadErrors = if ($rel) { $rel.ReadErrorsTotal } else { $null } "
            "} }; "
            "@($disks) | ConvertTo-Json -Compress"
        )
        disks = []
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=6,
            ).strip()
            if out:
                parsed = json.loads(out)
                disks = [parsed] if isinstance(parsed, dict) else parsed
        except Exception:
            pass

        self.after(0, lambda: self._render_smart_cards(disks))

    def _render_smart_cards(self, disks: list):
        self.refresh_smart_btn.configure(state="normal", text="🔄 Refresh Drive Health")

        if not disks:
            ctk.CTkLabel(
                self.smart_scroll, text="Could not read physical S.M.A.R.T. data.", text_color="gray"
            ).pack(padx=20, pady=20)
            return

        for idx, d in enumerate(disks):
            card = ctk.CTkFrame(self.smart_scroll, width=310, height=120)
            card.grid(row=0, column=idx, padx=8, pady=5, sticky="ns")

            name = d.get("FriendlyName") or f"Physical Drive {idx}"
            media = d.get("MediaType") or "Storage"
            bus = d.get("BusType") or "Bus"
            health = d.get("HealthStatus") or "Unknown"
            op_status = d.get("OperationalStatus") or "OK"
            size_bytes = int(d.get("Size") or 0)
            temp = d.get("Temperature")
            wear = d.get("Wear")

            is_healthy = health.lower() == "healthy"
            badge_color = "#2FA572" if is_healthy else "#E74C3C"
            badge_icon = "✅" if is_healthy else "⚠️"

            # Title Row
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(8, 2))

            ctk.CTkLabel(
                top_row,
                text=f"💽 {name[:24]}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#3B8ED0",
            ).pack(side="left")

            ctk.CTkLabel(
                top_row,
                text=f"  {badge_icon} {health}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=badge_color,
            ).pack(side="right")

            # Specs Row
            ctk.CTkLabel(
                card,
                text=f"Capacity: {SystemEngine.format_bytes(size_bytes)}  |  Type: {media} ({bus})",
                font=ctk.CTkFont(size=11),
                text_color="lightgray",
            ).pack(anchor="w", padx=12, pady=2)

            temp_str = f"{temp} °C" if temp is not None and temp > 0 else "N/A (Run as Admin)"
            wear_str = f"{wear}%" if wear is not None else "0%"

            ctk.CTkLabel(
                card,
                text=f"Status: {op_status}  |  Temp: {temp_str}  |  Wear: {wear_str}",
                font=ctk.CTkFont(size=11),
                text_color="gray",
            ).pack(anchor="w", padx=12, pady=(0, 8))

    # ==========================================
    # SUBFOLDER SPACE ANALYZER
    # ==========================================
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_entry.get())
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, os.path.normpath(folder))

    def start_folder_analysis(self):
        target = self.folder_entry.get().strip()
        if not os.path.exists(target):
            self.status_label.configure(text="Error: Folder path does not exist!", text_color="#E74C3C")
            return

        self.analyze_btn.configure(state="disabled", text="Calculating...")
        self.status_label.configure(
            text=f"Calculating subfolder sizes inside {target}... (This may take 10-20 seconds)",
            text_color="#3B8ED0",
        )

        for widget in self.folders_scroll.winfo_children():
            widget.destroy()

        threading.Thread(target=self._folder_worker, args=(target,), daemon=True).start()

    @classmethod
    def _get_dir_size_fast(cls, path: str) -> int:
        """Fast recursive directory byte counter using os.scandir."""
        total = 0
        try:
            with os.scandir(path) as it:
                for entry in it:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                        elif entry.is_dir(follow_symlinks=False):
                            total += cls._get_dir_size_fast(entry.path)
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass
        return total

    def _folder_worker(self, target: str):
        subfolders = []
        root_files_size = 0

        try:
            with os.scandir(target) as it:
                for entry in it:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            folder_size = self._get_dir_size_fast(entry.path)
                            if folder_size > 0:
                                subfolders.append((entry.name, entry.path, folder_size))
                        elif entry.is_file(follow_symlinks=False):
                            root_files_size += entry.stat(follow_symlinks=False).st_size
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError) as e:
            self.after(
                0,
                lambda err=e: self.status_label.configure(
                    text=f"Access Denied: {err}", text_color="#E74C3C"
                ),
            )
            self.after(0, lambda: self.analyze_btn.configure(state="normal", text="🔍 Rank Subfolder Sizes"))
            return

        if root_files_size > 0:
            subfolders.append(("[Files directly in root folder]", target, root_files_size))

        subfolders.sort(key=lambda x: x[2], reverse=True)
        total_scanned = sum(x[2] for x in subfolders)

        self.after(0, lambda: self._render_folder_ranks(subfolders[:25], total_scanned, target))

    def _render_folder_ranks(self, top_folders: list, total_scanned: int, target: str):
        self.analyze_btn.configure(state="normal", text="🔍 Rank Subfolder Sizes")

        if not top_folders or total_scanned == 0:
            self.status_label.configure(text="No accessible files found in this directory.", text_color="gray")
            return

        self.status_label.configure(
            text=f"Total Scanned in '{os.path.basename(target) or target}': {SystemEngine.format_bytes(total_scanned)}",
            text_color="#2FA572",
        )

        for name, full_path, size_bytes in top_folders:
            pct = (size_bytes / total_scanned) if total_scanned > 0 else 0.0

            row = ctk.CTkFrame(self.folders_scroll)
            row.pack(fill="x", padx=5, pady=4)

            left_box = ctk.CTkFrame(row, fg_color="transparent")
            left_box.pack(side="left", fill="x", expand=True, padx=12, pady=8)

            header_line = ctk.CTkFrame(left_box, fg_color="transparent")
            header_line.pack(fill="x")

            ctk.CTkLabel(
                header_line,
                text=f"📁 {name}",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left")

            ctk.CTkLabel(
                header_line,
                text=f"{SystemEngine.format_bytes(size_bytes)}  ({pct * 100:.1f}%)",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#3B8ED0",
            ).pack(side="right")

            bar = ctk.CTkProgressBar(left_box, height=8, progress_color="#E67E22")
            bar.pack(fill="x", pady=(6, 2))
            bar.set(min(1.0, max(0.02, pct)))

            # Button to drill down or open in Explorer
            btn_box = ctk.CTkFrame(row, fg_color="transparent")
            btn_box.pack(side="right", padx=10, pady=8)

            if name != "[Files directly in root folder]":
                ctk.CTkButton(
                    btn_box,
                    text="🔎 Drill In",
                    width=80,
                    height=28,
                    fg_color="#3B8ED0",
                    command=lambda p=full_path: self.drill_into_folder(p),
                ).pack(side="left", padx=4)

            ctk.CTkButton(
                btn_box,
                text="📂 Explorer",
                width=85,
                height=28,
                fg_color="#34495E",
                hover_color="#2C3E50",
                command=lambda p=full_path: subprocess.Popen(["explorer", p]),
            ).pack(side="left", padx=4)

    def drill_into_folder(self, folder_path: str):
        """Sets the selected subfolder as the new target and immediately analyzes it."""
        self.folder_entry.delete(0, "end")
        self.folder_entry.insert(0, folder_path)
        self.start_folder_analysis()