# security_port_scanner.py
import json
import socket
import threading
import subprocess
import psutil
import customtkinter as ctk


class SecurityPortScannerView(ctk.CTkFrame):
    """Modular Active Network Connection Inspector, Port Scanner & Firewall Status Monitor."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.all_connections = []

        # ==========================================
        # CARD 1: DEFENDER & FIREWALL STATUS BANNER
        # ==========================================
        self.sec_card = ctk.CTkFrame(self)
        self.sec_card.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        self.sec_card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.lbl_defender = ctk.CTkLabel(
            self.sec_card, text="🛡️ Defender: Checking...", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_defender.grid(row=0, column=0, padx=10, pady=12)

        self.lbl_fw_domain = ctk.CTkLabel(
            self.sec_card, text="🔥 Domain FW: --", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_fw_domain.grid(row=0, column=1, padx=10, pady=12)

        self.lbl_fw_private = ctk.CTkLabel(
            self.sec_card, text="🏠 Private FW: --", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_fw_private.grid(row=0, column=2, padx=10, pady=12)

        self.lbl_fw_public = ctk.CTkLabel(
            self.sec_card, text="🌐 Public FW: --", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_fw_public.grid(row=0, column=3, padx=10, pady=12)

        # ==========================================
        # CARD 2: SEARCH & CONNECTION FILTER BAR
        # ==========================================
        filter_bar = ctk.CTkFrame(self)
        filter_bar.grid(row=1, column=0, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(
            filter_bar, text="🔎 Filter:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(15, 5), pady=12)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_filtered_connections())

        self.search_entry = ctk.CTkEntry(
            filter_bar,
            width=230,
            placeholder_text="Search app (.exe), IP, or port...",
            textvariable=self.search_var,
        )
        self.search_entry.pack(side="left", padx=5, pady=12, fill="x", expand=True)

        self.mode_menu = ctk.CTkOptionMenu(
            filter_bar,
            values=["External Connections (ESTABLISHED)", "Listening Ports (LISTEN)", "All Active Sockets"],
            width=245,
            command=lambda _: self.render_filtered_connections(),
        )
        self.mode_menu.set("External Connections (ESTABLISHED)")
        self.mode_menu.pack(side="left", padx=8, pady=12)

        self.refresh_btn = ctk.CTkButton(
            filter_bar,
            text="🔄 Scan Connections",
            width=150,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.scan_network_connections,
        )
        self.refresh_btn.pack(side="right", padx=15, pady=12)

        # ==========================================
        # STATUS BAR
        # ==========================================
        self.status_label = ctk.CTkLabel(
            self,
            text="Click 'Scan Connections' to inspect live network sockets and open ports.",
            text_color="gray",
        )
        self.status_label.grid(row=2, column=0, pady=(0, 4), sticky="w")

        # ==========================================
        # SCROLLABLE CONNECTIONS TABLE
        # ==========================================
        self.conn_scroll = ctk.CTkScrollableFrame(self)
        self.conn_scroll.grid(row=3, column=0, sticky="nsew")

    # ==========================================
    # WINDOWS DEFENDER & FIREWALL CHECK
    # ==========================================
    def check_security_status(self):
        threading.Thread(target=self._security_worker, daemon=True).start()

    def _security_worker(self):
        ps_cmd = (
            "$mp = Get-MpComputerStatus -ErrorAction SilentlyContinue | "
            "Select-Object RealTimeProtectionEnabled, AntivirusEnabled; "
            "$fw = @(Get-NetFirewallProfile -ErrorAction SilentlyContinue | Select-Object Name, Enabled); "
            "@{mp=$mp; fw=$fw} | ConvertTo-Json -Compress"
        )
        data = {}
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=5,
            ).strip()
            if out:
                data = json.loads(out)
        except Exception:
            pass

        self.after(0, lambda: self._update_security_badges(data))

    def _update_security_badges(self, data: dict):
        mp = data.get("mp") or {}
        rtp = mp.get("RealTimeProtectionEnabled")
        if rtp is True:
            self.lbl_defender.configure(text="🛡️ Defender Real-Time: ON", text_color="#2FA572")
        elif rtp is False:
            self.lbl_defender.configure(text="⚠️ Defender Real-Time: OFF", text_color="#E74C3C")
        else:
            self.lbl_defender.configure(text="🛡️ Defender: Active", text_color="#3B8ED0")

        fw_list = data.get("fw") or []
        if isinstance(fw_list, dict):
            fw_list = [fw_list]

        fw_map = {item.get("Name", "").lower(): bool(item.get("Enabled")) for item in fw_list}

        for key, widget, label in [
            ("domain", self.lbl_fw_domain, "Domain FW"),
            ("private", self.lbl_fw_private, "Private FW"),
            ("public", self.lbl_fw_public, "Public FW"),
        ]:
            if key in fw_map:
                is_on = fw_map[key]
                widget.configure(
                    text=f"{'✅' if is_on else '❌'} {label}: {'ON' if is_on else 'OFF'}",
                    text_color="#2FA572" if is_on else "#E74C3C",
                )

    # ==========================================
    # LIVE NETWORK CONNECTIONS & PORT SCANNER
    # ==========================================
    def scan_network_connections(self):
        self.refresh_btn.configure(state="disabled", text="Scanning...")
        self.status_label.configure(text="Scanning active TCP/IP sockets and mapping PIDs...", text_color="#3B8ED0")
        threading.Thread(target=self._connections_worker, daemon=True).start()

    def _connections_worker(self):
        # Cache process names for fast lookup
        pid_names = {}
        for p in psutil.process_iter(["pid", "name"]):
            try:
                pid_names[p.info["pid"]] = p.info["name"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        connections = []
        try:
            for conn in psutil.net_connections(kind="tcp"):
                if not conn.laddr:
                    continue

                local_ip = conn.laddr.ip
                local_port = conn.laddr.port
                local_str = f"{local_ip}:{local_port}"

                if conn.raddr:
                    remote_ip = conn.raddr.ip
                    remote_port = conn.raddr.port
                    remote_str = f"{remote_ip}:{remote_port}"
                else:
                    remote_ip = ""
                    remote_str = "0.0.0.0:* (Listening)"

                pid = conn.pid or 0
                proc_name = pid_names.get(pid, "System / Service")
                status = conn.status

                # Determine if this is an external (non-loopback) connection
                is_external = bool(
                    remote_ip
                    and not remote_ip.startswith("127.")
                    and remote_ip != "::1"
                )

                connections.append(
                    {
                        "pid": pid,
                        "name": proc_name,
                        "local": local_str,
                        "remote": remote_str,
                        "remote_ip": remote_ip,
                        "port": local_port,
                        "status": status,
                        "is_external": is_external,
                    }
                )
        except Exception:
            pass

        # Sort established external connections first, then by process name
        connections.sort(key=lambda x: (not x["is_external"], x["name"].lower()))
        self.all_connections = connections
        self.after(0, self._finish_scan)

    def _finish_scan(self):
        self.refresh_btn.configure(state="normal", text="🔄 Scan Connections")
        self.render_filtered_connections()

    def render_filtered_connections(self):
        for widget in self.conn_scroll.winfo_children():
            widget.destroy()

        mode = self.mode_menu.get()
        query = self.search_var.get().strip().lower()

        filtered = []
        for c in self.all_connections:
            if mode == "External Connections (ESTABLISHED)":
                if c["status"] != "ESTABLISHED" or not c["is_external"]:
                    continue
            elif mode == "Listening Ports (LISTEN)":
                if c["status"] != "LISTEN":
                    continue

            if query:
                haystack = f"{c['name']} {c['local']} {c['remote']} {c['pid']}".lower()
                if query not in haystack:
                    continue

            filtered.append(c)

        display_list = filtered[:65]
        self.status_label.configure(
            text=f"Found {len(filtered)} matching sockets (Showing top {len(display_list)}).",
            text_color="#2FA572",
        )

        if not display_list:
            ctk.CTkLabel(
                self.conn_scroll, text="No matching network connections found.", text_color="gray"
            ).pack(pady=25)
            return

        for conn in display_list:
            row = ctk.CTkFrame(self.conn_scroll)
            row.pack(fill="x", padx=5, pady=3)

            # Process Name & PID
            proc_text = f"⚡ {conn['name']} (PID: {conn['pid']})"
            ctk.CTkLabel(
                row,
                text=proc_text,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#3B8ED0",
                width=220,
                anchor="w",
            ).pack(side="left", padx=12, pady=8)

            # Local -> Remote Address Mapping
            route_text = f"Local: {conn['local']}   ➔   Remote: {conn['remote']}"
            ctk.CTkLabel(
                row,
                text=route_text,
                font=ctk.CTkFont(family="Consolas", size=11),
                text_color="lightgray",
                anchor="w",
            ).pack(side="left", padx=8, pady=8, fill="x", expand=True)

            # Kill Process Button (if non-system PID)
            if conn["pid"] not in (0, 4):
                ctk.CTkButton(
                    row,
                    text="End App",
                    width=78,
                    height=26,
                    fg_color="#C0392B",
                    hover_color="#922B21",
                    command=lambda p=conn["pid"], n=conn["name"]: self.kill_connected_app(p, n),
                ).pack(side="right", padx=(6, 12), pady=6)

            # Status Badge
            badge_color = "#2FA572" if conn["status"] == "ESTABLISHED" else "#E67E22"
            ctk.CTkLabel(
                row,
                text=conn["status"],
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=badge_color,
                width=95,
            ).pack(side="right", padx=6)

    def kill_connected_app(self, pid: int, name: str):
        try:
            psutil.Process(pid).terminate()
            self.status_label.configure(
                text=f"Terminated {name} (PID {pid}) and closed its network sockets.", text_color="#E67E22"
            )
            self.after(400, self.scan_network_connections)
        except Exception as e:
            self.status_label.configure(text=f"Could not terminate {name}: {e}", text_color="#E74C3C")