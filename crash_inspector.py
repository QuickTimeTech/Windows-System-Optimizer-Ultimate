# crash_inspector.py
import os
import json
import threading
import subprocess
import customtkinter as ctk
from backend_engine import SystemEngine


class CrashInspectorView(ctk.CTkFrame):
    """Modular Windows Event Log Crash Inspector, BSOD Minidump Detector & Reliability Launcher."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.all_events = []

        # ==========================================
        # CARD 1: BSOD MINIDUMP & QUICK TOOLS BANNER
        # ==========================================
        top_card = ctk.CTkFrame(self)
        top_card.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        left_box = ctk.CTkFrame(top_card, fg_color="transparent")
        left_box.pack(side="left", fill="x", expand=True, padx=15, pady=10)

        ctk.CTkLabel(
            left_box,
            text="🚨 WINDOWS CRASH, BSOD & EVENT LOG INSPECTOR",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w")

        self.dump_badge = ctk.CTkLabel(
            left_box,
            text="BSOD Crash Dumps: Checking C:\\Windows\\Minidump...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray",
        )
        self.dump_badge.pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            top_card,
            text="📈 Reliability Monitor",
            width=155,
            height=34,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: subprocess.Popen(["perfmon", "/rel"]),
        ).pack(side="right", padx=(6, 15), pady=12)

        ctk.CTkButton(
            top_card,
            text="📜 Event Viewer",
            width=130,
            height=34,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: subprocess.Popen(["mmc", "eventvwr.msc"]),
        ).pack(side="right", padx=6, pady=12)

        # ==========================================
        # CARD 2: FILTER & SEARCH BAR
        # ==========================================
        filter_bar = ctk.CTkFrame(self)
        filter_bar.grid(row=1, column=0, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(
            filter_bar, text="🔎 Filter Logs:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(15, 5), pady=12)

        self.log_type_menu = ctk.CTkOptionMenu(
            filter_bar,
            values=[
                "All Critical & Error Events",
                "Critical Events Only (Kernel/Power)",
                "Application Crashes & Hang Events",
                "System & Driver Errors",
            ],
            width=235,
            command=lambda _: self.render_events(),
        )
        self.log_type_menu.set("All Critical & Error Events")
        self.log_type_menu.pack(side="left", padx=5, pady=12)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_events())

        self.search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text="Search by Provider, Event ID, or crashing .exe...",
            textvariable=self.search_var,
        )
        self.search_entry.pack(side="left", padx=8, pady=12, fill="x", expand=True)

        self.scan_btn = ctk.CTkButton(
            filter_bar,
            text="🔄 Scan Event Logs",
            width=150,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.scan_crash_logs,
        )
        self.scan_btn.pack(side="right", padx=15, pady=12)

        # ==========================================
        # STATUS BAR
        # ==========================================
        self.status_label = ctk.CTkLabel(
            self,
            text="Click 'Scan Event Logs' to retrieve recent Critical & Error entries from Windows Event Viewer.",
            text_color="gray",
        )
        self.status_label.grid(row=2, column=0, pady=(0, 4), sticky="w")

        # ==========================================
        # SCROLLABLE EVENT CARDS
        # ==========================================
        self.events_scroll = ctk.CTkScrollableFrame(self)
        self.events_scroll.grid(row=3, column=0, sticky="nsew")

    def check_minidumps(self):
        """Checks C:\\Windows\\Minidump for BSOD .dmp files."""
        minidump_dir = r"C:\Windows\Minidump"
        full_dump = r"C:\Windows\MEMORY.DMP"
        dmp_files = []

        if os.path.exists(minidump_dir):
            try:
                dmp_files = [f for f in os.listdir(minidump_dir) if f.lower().endswith(".dmp")]
            except PermissionError:
                pass

        has_full = os.path.exists(full_dump)

        if dmp_files or has_full:
            count_str = f"{len(dmp_files)} Minidump(s)" + (" + MEMORY.DMP" if has_full else "")
            self.dump_badge.configure(
                text=f"⚠️ BSOD Crash Dumps Found: {count_str} in C:\\Windows\\Minidump",
                text_color="#E74C3C",
            )
        else:
            self.dump_badge.configure(
                text="✅ BSOD Crash Dumps: 0 Found (No recent Blue Screen dump files on disk)",
                text_color="#2FA572",
            )

    def scan_crash_logs(self):
        self.check_minidumps()
        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.status_label.configure(
            text="Querying Windows System & Application Event Logs for Critical (Level 1) & Error (Level 2) events...",
            text_color="#3B8ED0",
        )
        threading.Thread(target=self._event_worker, daemon=True).start()

    def _event_worker(self):
        ps_cmd = (
            "$sys = @(Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2} -MaxEvents 35 "
            "-ErrorAction SilentlyContinue | Select-Object "
            "@{N='Time';E={$_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')}}, "
            "Id, LevelDisplayName, ProviderName, LogName, Message); "
            "$app = @(Get-WinEvent -FilterHashtable @{LogName='Application'; Level=1,2} -MaxEvents 35 "
            "-ErrorAction SilentlyContinue | Select-Object "
            "@{N='Time';E={$_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')}}, "
            "Id, LevelDisplayName, ProviderName, LogName, Message); "
            "@($sys + $app) | Sort-Object Time -Descending | ConvertTo-Json -Compress"
        )
        events = []
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=12,
            ).strip()
            if out:
                raw = json.loads(out)
                events = [raw] if isinstance(raw, dict) else raw
        except Exception:
            pass

        cleaned = []
        for ev in events:
            msg = (ev.get("Message") or "No event description provided.").strip()
            # Collapse multi-line whitespace for cleaner card display
            msg_single = " ".join(msg.split())
            if len(msg_single) > 260:
                msg_single = msg_single[:260] + "..."

            cleaned.append(
                {
                    "time": ev.get("Time") or "Unknown Time",
                    "id": ev.get("Id") or 0,
                    "level": (ev.get("LevelDisplayName") or "Error").strip(),
                    "provider": (ev.get("ProviderName") or "Windows").strip(),
                    "log": (ev.get("LogName") or "System").strip(),
                    "message": msg_single,
                }
            )

        self.all_events = cleaned
        self.after(0, self._finish_scan)

    def _finish_scan(self):
        self.scan_btn.configure(state="normal", text="🔄 Scan Event Logs")
        self.render_events()

    def render_events(self):
        for widget in self.events_scroll.winfo_children():
            widget.destroy()

        mode = self.log_type_menu.get()
        query = self.search_var.get().strip().lower()

        filtered = []
        for ev in self.all_events:
            if mode == "Critical Events Only (Kernel/Power)" and "critical" not in ev["level"].lower():
                continue
            if mode == "Application Crashes & Hang Events" and ev["log"].lower() != "application":
                continue
            if mode == "System & Driver Errors" and ev["log"].lower() != "system":
                continue

            if query:
                haystack = f"{ev['provider']} {ev['id']} {ev['message']} {ev['log']}".lower()
                if query not in haystack:
                    continue

            filtered.append(ev)

        display_list = filtered[:60]
        self.status_label.configure(
            text=f"Found {len(filtered)} recent error/crash events (Showing latest {len(display_list)}).",
            text_color="#2FA572",
        )

        if not display_list:
            ctk.CTkLabel(
                self.events_scroll,
                text="🎉 No matching Critical or Error events found in recent logs!",
                text_color="gray",
            ).pack(pady=25)
            return

        for ev in display_list:
            is_crit = "critical" in ev["level"].lower()
            card = ctk.CTkFrame(
                self.events_scroll,
                fg_color=("#FADBD8", "#3B1818") if is_crit else ("gray85", "gray17"),
            )
            card.pack(fill="x", padx=5, pady=4)

            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=12, pady=(8, 2))

            badge_icon = "🚨 CRITICAL" if is_crit else "⚠️ ERROR"
            badge_color = "#E74C3C" if is_crit else "#E67E22"

            ctk.CTkLabel(
                header,
                text=f"{badge_icon}  |  [{ev['log']}] {ev['provider']}  (Event ID: {ev['id']})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=badge_color,
            ).pack(side="left")

            ctk.CTkLabel(
                header,
                text=ev["time"],
                font=ctk.CTkFont(family="Consolas", size=11),
                text_color="lightgray",
            ).pack(side="right")

            ctk.CTkLabel(
                card,
                text=ev["message"],
                font=ctk.CTkFont(size=11),
                text_color="lightgray",
                wraplength=760,
                justify="left",
            ).pack(anchor="w", padx=12, pady=(2, 8))