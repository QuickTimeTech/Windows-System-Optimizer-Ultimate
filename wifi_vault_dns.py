# wifi_vault_dns.py
import re
import socket
import threading
import subprocess
import psutil
import customtkinter as ctk
from backend_engine import SystemEngine


class WifiVaultDnsView(ctk.CTkFrame):
    """Modular Saved Wi-Fi Password Recovery Vault & 1-Click DNS Changer."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.wifi_profiles = []
        self.active_adapters = self.get_up_adapters()

        # ==========================================
        # CARD 1: 1-CLICK DNS SERVER SWITCHER
        # ==========================================
        dns_card = ctk.CTkFrame(self)
        dns_card.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        top_dns_row = ctk.CTkFrame(dns_card, fg_color="transparent")
        top_dns_row.pack(fill="x", padx=15, pady=(12, 6))

        ctk.CTkLabel(
            top_dns_row,
            text="🌐 1-CLICK DNS SERVER SWITCHER (ADMIN)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(side="left")

        ctk.CTkLabel(top_dns_row, text="Target Adapter:", font=ctk.CTkFont(weight="bold")).pack(
            side="left", padx=(25, 6)
        )

        self.adapter_menu = ctk.CTkOptionMenu(
            top_dns_row,
            values=self.active_adapters if self.active_adapters else ["Wi-Fi", "Ethernet"],
            width=190,
        )
        self.adapter_menu.pack(side="left", padx=4)

        self.dns_status_lbl = ctk.CTkLabel(
            top_dns_row,
            text="Select a DNS provider below to apply.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray",
        )
        self.dns_status_lbl.pack(side="right")

        btn_dns_row = ctk.CTkFrame(dns_card, fg_color="transparent")
        btn_dns_row.pack(fill="x", padx=15, pady=(4, 14))

        self.btn_cf = ctk.CTkButton(
            btn_dns_row,
            text="⚡ Cloudflare (1.1.1.1 - Fastest)",
            height=34,
            fg_color="#D35400",
            hover_color="#A04000",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.apply_dns("Cloudflare", ["1.1.1.1", "1.0.0.1"]),
        )
        self.btn_cf.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_quad9 = ctk.CTkButton(
            btn_dns_row,
            text="🛡️ Quad9 (9.9.9.9 - Malware Block)",
            height=34,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.apply_dns("Quad9 Security", ["9.9.9.9", "149.112.112.112"]),
        )
        self.btn_quad9.pack(side="left", expand=True, fill="x", padx=5)

        self.btn_google = ctk.CTkButton(
            btn_dns_row,
            text="🌍 Google DNS (8.8.8.8)",
            height=34,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.apply_dns("Google Public DNS", ["8.8.8.8", "8.8.4.4"]),
        )
        self.btn_google.pack(side="left", expand=True, fill="x", padx=5)

        self.btn_dhcp = ctk.CTkButton(
            btn_dns_row,
            text="🔄 Reset to Automatic (ISP Default)",
            height=34,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.apply_dns("Automatic (DHCP)", []),
        )
        self.btn_dhcp.pack(side="right", expand=True, fill="x", padx=(5, 0))

        # ==========================================
        # CARD 2: WI-FI PASSWORD VAULT SEARCH BAR
        # ==========================================
        wifi_bar = ctk.CTkFrame(self)
        wifi_bar.grid(row=1, column=0, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(
            wifi_bar, text="🔑 Saved Wi-Fi Vault:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(15, 5), pady=12)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_wifi_cards())

        self.search_entry = ctk.CTkEntry(
            wifi_bar,
            placeholder_text="Search saved Wi-Fi SSID name...",
            textvariable=self.search_var,
        )
        self.search_entry.pack(side="left", padx=8, pady=12, fill="x", expand=True)

        self.scan_wifi_btn = ctk.CTkButton(
            wifi_bar,
            text="🔍 Reveal Saved Wi-Fi Passwords",
            width=215,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(weight="bold"),
            command=self.scan_saved_wifi,
        )
        self.scan_wifi_btn.pack(side="right", padx=15, pady=12)

        # ==========================================
        # STATUS BAR & SCROLLABLE WI-FI VAULT
        # ==========================================
        self.status_label = ctk.CTkLabel(
            self,
            text="Click 'Reveal Saved Wi-Fi Passwords' to extract SSIDs and cleartext keys stored on this PC.",
            text_color="gray",
        )
        self.status_label.grid(row=2, column=0, pady=(0, 4), sticky="w")

        self.wifi_scroll = ctk.CTkScrollableFrame(self)
        self.wifi_scroll.grid(row=3, column=0, sticky="nsew")

    @staticmethod
    def get_up_adapters() -> list[str]:
        """Returns active physical network interface names."""
        up_list = []
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            for name, iface_addrs in addrs.items():
                if name in stats and stats[name].isup:
                    has_ipv4 = any(
                        a.family == socket.AF_INET and not a.address.startswith("127.")
                        for a in iface_addrs
                    )
                    if has_ipv4:
                        up_list.append(name)
        except Exception:
            pass
        return up_list

    # ==========================================
    # 1-CLICK DNS SWITCHER LOGIC
    # ==========================================
    def apply_dns(self, label: str, servers: list[str]):
        if not SystemEngine.is_admin():
            self.dns_status_lbl.configure(
                text="⚠️ Admin Mode Required to change adapter DNS!", text_color="#E74C3C"
            )
            return

        adapter = self.adapter_menu.get().replace("'", "''")
        self.dns_status_lbl.configure(text=f"Applying {label} to '{adapter}'...", text_color="#3B8ED0")

        def worker():
            try:
                if servers:
                    srv_str = ",".join([f"'{s}'" for s in servers])
                    ps_cmd = (
                        f"Set-DnsClientServerAddress -InterfaceAlias '{adapter}' "
                        f"-ServerAddresses ({srv_str}) -ErrorAction Stop; ipconfig /flushdns | Out-Null"
                    )
                else:
                    ps_cmd = (
                        f"Set-DnsClientServerAddress -InterfaceAlias '{adapter}' "
                        f"-ResetServerAddresses -ErrorAction Stop; ipconfig /flushdns | Out-Null"
                    )

                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=8,
                )
                if res.returncode == 0:
                    dns_disp = ", ".join(servers) if servers else "DHCP Automatic"
                    self.after(
                        0,
                        lambda: self.dns_status_lbl.configure(
                            text=f"✅ Active DNS: {label} ({dns_disp})", text_color="#2FA572"
                        ),
                    )
                else:
                    self.after(
                        0,
                        lambda: self.dns_status_lbl.configure(
                            text="❌ Failed to update DNS (Check adapter name)", text_color="#E74C3C"
                        ),
                    )
            except Exception as e:
                self.after(
                    0,
                    lambda err=e: self.dns_status_lbl.configure(
                        text=f"❌ DNS Error: {err}", text_color="#E74C3C"
                    ),
                )

        threading.Thread(target=worker, daemon=True).start()

    # ==========================================
    # SAVED WI-FI PASSWORD EXTRACTOR
    # ==========================================
    def scan_saved_wifi(self):
        self.scan_wifi_btn.configure(state="disabled", text="Decrypting Profiles...")
        self.status_label.configure(
            text="Reading WLAN profiles from Windows Wireless AutoConfig (wlansvc)...",
            text_color="#3B8ED0",
        )
        threading.Thread(target=self._wifi_worker, daemon=True).start()

    def _wifi_worker(self):
        profiles = []
        try:
            out = subprocess.check_output(
                ["netsh", "wlan", "show", "profiles"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=6,
            )
            ssids = [
                line.split(":", 1)[1].strip()
                for line in out.splitlines()
                if "All User Profile" in line and ":" in line
            ]

            for ssid in ssids:
                if not ssid:
                    continue
                try:
                    detail = subprocess.check_output(
                        ["netsh", "wlan", "show", "profile", f"name={ssid}", "key=clear"],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=4,
                    )
                    pwd_match = re.search(r"Key Content\s*:\s*(.+)", detail)
                    auth_match = re.search(r"Authentication\s*:\s*(.+)", detail)

                    password = pwd_match.group(1).strip() if pwd_match else "[Open / No Password Stored]"
                    auth = auth_match.group(1).strip() if auth_match else "WPA2/WPA3"

                    profiles.append({"ssid": ssid, "password": password, "auth": auth})
                except Exception:
                    continue
        except Exception:
            pass

        profiles.sort(key=lambda x: x["ssid"].lower())
        self.wifi_profiles = profiles
        self.after(0, self._finish_wifi_scan)

    def _finish_wifi_scan(self):
        self.scan_wifi_btn.configure(state="normal", text="🔍 Reveal Saved Wi-Fi Passwords")
        self.render_wifi_cards()

    def render_wifi_cards(self):
        for widget in self.wifi_scroll.winfo_children():
            widget.destroy()

        query = self.search_var.get().strip().lower()
        filtered = [p for p in self.wifi_profiles if query in p["ssid"].lower()]

        self.status_label.configure(
            text=f"Recovered {len(filtered)} saved Wi-Fi network profile(s).",
            text_color="#2FA572",
        )

        if not filtered:
            ctk.CTkLabel(
                self.wifi_scroll,
                text="No saved Wi-Fi profiles found (or PC does not have a Wi-Fi adapter).",
                text_color="gray",
            ).pack(pady=25)
            return

        for item in filtered:
            card = ctk.CTkFrame(self.wifi_scroll)
            card.pack(fill="x", padx=5, pady=4)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=14, pady=8)

            ctk.CTkLabel(
                left,
                text=f"📶 {item['ssid']}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#3B8ED0",
            ).pack(anchor="w")

            ctk.CTkLabel(
                left,
                text=f"Security: {item['auth']}",
                font=ctk.CTkFont(size=11),
                text_color="gray",
            ).pack(anchor="w")

            # Copy Password Button
            ctk.CTkButton(
                card,
                text="📋 Copy Key",
                width=95,
                height=28,
                fg_color="#34495E",
                hover_color="#2C3E50",
                command=lambda p=item["password"], s=item["ssid"]: self.copy_password(p, s),
            ).pack(side="right", padx=12, pady=8)

            # Password Badge
            ctk.CTkLabel(
                card,
                text=f"🔑 {item['password']}",
                font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                text_color="#2FA572",
            ).pack(side="right", padx=15, pady=8)

    def copy_password(self, password: str, ssid: str):
        self.clipboard_clear()
        self.clipboard_append(password)
        self.status_label.configure(
            text=f"✅ Copied password for '{ssid}' to clipboard!", text_color="#2FA572"
        )