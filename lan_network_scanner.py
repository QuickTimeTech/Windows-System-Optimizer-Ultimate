# lan_network_scanner.py
import re
import time
import socket
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import customtkinter as ctk


class LanNetworkScannerView(ctk.CTkFrame):
    """Modular Multi-Threaded LAN Ping Sweep, ARP MAC Inspector & Device Port Prober."""

    # Common MAC OUI prefixes to help identify device manufacturers without external APIs
    COMMON_OUIS = {
        "00-1A-11": "Google",
        "3C-5A-B4": "Google",
        "F4-F5-D8": "Google",
        "B8-27-EB": "Raspberry Pi",
        "DC-A6-32": "Raspberry Pi",
        "E4-5F-01": "Raspberry Pi",
        "28-CD-C1": "Raspberry Pi",
        "00-15-5D": "Microsoft Hyper-V",
        "00-50-56": "VMware",
        "08-00-27": "VirtualBox",
        "00-1B-63": "Apple",
        "AC-BC-32": "Apple",
        "F0-18-98": "Apple",
        "3C-22-FB": "Apple",
        "A4-83-E7": "Apple",
        "00-26-BB": "Apple",
        "FC-EC-DA": "Ubiquiti",
        "78-8A-20": "Ubiquiti",
        "24-5A-4C": "Ubiquiti",
        "B0-BE-76": "TP-Link",
        "50-C7-BF": "TP-Link",
        "98-DA-C4": "TP-Link",
        "C0-56-27": "Belkin / Linksys",
        "00-14-BF": "Linksys",
        "A0-04-60": "Netgear",
        "28-80-88": "Netgear",
        "04-D4-C4": "ASUS",
        "2C-FD-A1": "ASUS",
        "F0-79-59": "ASUS",
        "3C-97-0E": "Wistron / Intel",
        "00-1E-67": "Intel",
        "A4-34-D9": "Intel",
        "F8-75-A4": "LCFC / Lenovo",
        "00-E0-4C": "Realtek",
        "70-85-C2": "ASRock / Realtek",
        "D8-BB-C1": "Micro-Star (MSI)",
        "18-C0-4D": "Gigabyte",
        "E0-D5-5E": "Gigabyte",
        "00-12-FB": "Samsung",
        "8C-77-12": "Samsung",
        "50-01-BB": "Samsung",
        "44-65-0D": "Amazon (Echo/Fire)",
        "F0-D2-F1": "Amazon (Echo/Fire)",
    }

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.local_ip, self.subnet_prefix = self.detect_local_subnet()
        self.discovered_devices = []

        # ==========================================
        # CARD 1: SUBNET CONFIG & PING SWEEP CONTROLS
        # ==========================================
        top_card = ctk.CTkFrame(self)
        top_card.grid(row=0, column=0, pady=(0, 8), sticky="ew")

        row1 = ctk.CTkFrame(top_card, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(12, 8))

        ctk.CTkLabel(
            row1,
            text="📡 LAN PING SWEEP & NETWORK DEVICE SCANNER",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(side="left")

        ctk.CTkLabel(
            row1,
            text=f"Your Local IP: {self.local_ip}",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#2FA572",
        ).pack(side="right")

        row2 = ctk.CTkFrame(top_card, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(
            row2, text="Subnet Prefix (/24):", font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(0, 6))

        self.subnet_entry = ctk.CTkEntry(row2, width=130, font=ctk.CTkFont(family="Consolas", size=13))
        self.subnet_entry.insert(0, self.subnet_prefix)
        self.subnet_entry.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(row2, text=".1  to  .254", text_color="gray").pack(side="left", padx=(0, 15))

        self.var_resolve_names = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            row2,
            text="Resolve Device Hostnames (Reverse DNS)",
            variable=self.var_resolve_names,
        ).pack(side="left", padx=10)

        self.scan_btn = ctk.CTkButton(
            row2,
            text="🚀 Start Ping Sweep (1-254)",
            width=210,
            height=36,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(weight="bold"),
            command=self.start_ping_sweep,
        )
        self.scan_btn.pack(side="right")

        # ==========================================
        # PROGRESS BAR & STATUS BAR
        # ==========================================
        self.progress_bar = ctk.CTkProgressBar(self, height=12, progress_color="#3B8ED0")
        self.progress_bar.grid(row=1, column=0, pady=(0, 6), sticky="ew")
        self.progress_bar.set(0)

        self.status_lbl = ctk.CTkLabel(
            self,
            text=f"Ready to sweep {self.subnet_prefix}.1 - {self.subnet_prefix}.254 across 64 parallel threads.",
            text_color="gray",
        )
        self.status_lbl.grid(row=2, column=0, pady=(0, 4), sticky="w")

        # ==========================================
        # SCROLLABLE DISCOVERED DEVICES LIST
        # ==========================================
        self.dev_scroll = ctk.CTkScrollableFrame(self)
        self.dev_scroll.grid(row=3, column=0, sticky="nsew")

    @staticmethod
    def detect_local_subnet() -> tuple[str, str]:
        """Finds the primary outbound local IPv4 address and its /24 prefix."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1.0)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            parts = local_ip.split(".")
            if len(parts) == 4:
                return local_ip, f"{parts[0]}.{parts[1]}.{parts[2]}"
        except Exception:
            pass
        return "192.168.1.100", "192.168.1"

    def start_ping_sweep(self):
        prefix = self.subnet_entry.get().strip().rstrip(".")
        if len(prefix.split(".")) != 3:
            self.status_lbl.configure(
                text="⚠️ Invalid Subnet Prefix! Enter the first 3 octets (e.g., 192.168.1 or 10.0.0).",
                text_color="#E74C3C",
            )
            return

        self.scan_btn.configure(state="disabled", text="⏳ Sweeping Subnet...")
        self.progress_bar.set(0)
        for w in self.dev_scroll.winfo_children():
            w.destroy()

        self.status_lbl.configure(
            text=f"Pinging {prefix}.1 to {prefix}.254 (64 concurrent threads)...",
            text_color="#3B8ED0",
        )
        threading.Thread(
            target=self._sweep_worker, args=(prefix, self.var_resolve_names.get()), daemon=True
        ).start()

    @staticmethod
    def _ping_single_ip(ip: str) -> tuple[str, bool, int]:
        """Pings a single IPv4 with a fast 450ms timeout. Returns (ip, alive, latency_ms)."""
        try:
            res = subprocess.run(
                ["ping", "-n", "1", "-w", "450", ip],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=1.5,
            )
            out = res.stdout
            if "TTL=" in out.upper():
                match = re.search(r"time[=<](\d+)\s*ms", out, re.IGNORECASE)
                ms = int(match.group(1)) if match else 1
                return ip, True, ms
        except Exception:
            pass
        return ip, False, -1

    @staticmethod
    def _parse_arp_table(prefix: str) -> dict[str, str]:
        """Reads Windows ARP cache (arp -a) to map IP -> MAC address."""
        arp_map = {}
        try:
            out = subprocess.check_output(
                ["arp", "-a"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=4,
            )
            for line in out.splitlines():
                line = line.strip()
                if line.startswith(prefix + "."):
                    parts = line.split()
                    if len(parts) >= 2:
                        ip_addr = parts[0]
                        mac = parts[1].upper().replace(":", "-")
                        # Ignore broadcast FF-FF-FF-FF-FF-FF and incomplete 00-00-00-00-00-00
                        if len(mac) == 17 and mac != "FF-FF-FF-FF-FF-FF" and not mac.startswith("00-00-00"):
                            arp_map[ip_addr] = mac
        except Exception:
            pass
        return arp_map

    def _lookup_vendor(self, mac: str) -> str:
        if not mac or len(mac) < 8:
            return ""
        oui = mac[:8].upper()
        return self.COMMON_OUIS.get(oui, "")

    def _sweep_worker(self, prefix: str, resolve_names: bool):
        start_t = time.perf_counter()
        ips = [f"{prefix}.{i}" for i in range(1, 255)]
        alive_ping = {}

        # Step 1: Parallel Ping Sweep across all 254 IPs
        completed = 0
        with ThreadPoolExecutor(max_workers=64) as pool:
            futures = {pool.submit(self._ping_single_ip, ip): ip for ip in ips}
            for fut in as_completed(futures):
                completed += 1
                ip, is_up, ms = fut.result()
                if is_up:
                    alive_ping[ip] = ms
                if completed % 16 == 0 or completed == 254:
                    prog = (completed / 254.0) * 0.80
                    self.after(0, lambda p=prog: self.progress_bar.set(p))

        # Step 2: Read ARP table (catches firewalled devices that answered ARP but dropped ICMP)
        self.after(
            0,
            lambda: self.status_lbl.configure(
                text="Reading Windows ARP MAC table & resolving device hostnames...",
                text_color="#3B8ED0",
            ),
        )
        arp_map = self._parse_arp_table(prefix)

        # Combine Ping-Alive IPs + ARP-Active IPs (plus our own local IP)
        all_found_ips = set(alive_ping.keys()) | set(arp_map.keys())
        if self.local_ip.startswith(prefix + "."):
            all_found_ips.add(self.local_ip)

        # Filter out .255 subnet broadcast if present
        all_found_ips = {ip for ip in all_found_ips if not ip.endswith(".255")}

        sorted_ips = sorted(all_found_ips, key=lambda x: int(x.split(".")[-1]))

        # Step 3: Resolve hostnames in parallel
        hostnames = {}
        if resolve_names and sorted_ips:
            def _resolve(target_ip: str) -> tuple[str, str]:
                if target_ip == self.local_ip:
                    return target_ip, f"{socket.gethostname()} (This PC)"
                try:
                    name, _, _ = socket.gethostbyaddr(target_ip)
                    return target_ip, name
                except Exception:
                    return target_ip, "Unknown / Private Device"

            with ThreadPoolExecutor(max_workers=32) as name_pool:
                for ip_addr, hname in name_pool.map(_resolve, sorted_ips):
                    hostnames[ip_addr] = hname

        devices = []
        for ip_addr in sorted_ips:
            mac = arp_map.get(ip_addr, "Local Interface" if ip_addr == self.local_ip else "MAC Hidden")
            vendor = self._lookup_vendor(mac)
            ms = alive_ping.get(ip_addr, 0 if ip_addr == self.local_ip else -1)
            hname = hostnames.get(
                ip_addr,
                f"{socket.gethostname()} (This PC)" if ip_addr == self.local_ip else "Active LAN Node",
            )
            is_gateway = ip_addr.endswith(".1") or ip_addr.endswith(".254")

            devices.append(
                {
                    "ip": ip_addr,
                    "mac": mac,
                    "vendor": vendor,
                    "ms": ms,
                    "hostname": hname,
                    "is_self": ip_addr == self.local_ip,
                    "is_gateway": is_gateway and ip_addr != self.local_ip,
                }
            )

        elapsed = time.perf_counter() - start_t
        self.discovered_devices = devices
        self.after(0, lambda: self._finish_sweep(elapsed))

    def _finish_sweep(self, elapsed: float):
        self.progress_bar.set(1.0)
        self.scan_btn.configure(state="normal", text="🚀 Start Ping Sweep (1-254)")
        self.status_lbl.configure(
            text=f"✅ Sweep Complete in {elapsed:.1f}s! Discovered {len(self.discovered_devices)} active devices on your network.",
            text_color="#2FA572",
        )

        if not self.discovered_devices:
            ctk.CTkLabel(
                self.dev_scroll, text="No active devices found on this subnet.", text_color="gray"
            ).pack(pady=25)
            return

        for dev in self.discovered_devices:
            card = ctk.CTkFrame(
                self.dev_scroll,
                fg_color=("#E8F8F5", "#1A362D") if dev["is_self"] else ("gray85", "gray17"),
            )
            card.pack(fill="x", padx=5, pady=4)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=14, pady=8)

            # Role Icon & IP + Hostname
            if dev["is_self"]:
                icon, tag = "💻", " [THIS PC]"
            elif dev["is_gateway"]:
                icon, tag = "🌐", " [Router / Gateway]"
            else:
                icon, tag = "📱", ""

            vendor_str = f"  •  {dev['vendor']}" if dev["vendor"] else ""

            ctk.CTkLabel(
                left,
                text=f"{icon}  {dev['ip']}   —   {dev['hostname']}{tag}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#2FA572" if dev["is_self"] else "#3B8ED0",
            ).pack(anchor="w")

            ping_txt = f"{dev['ms']} ms (ICMP Reply)" if dev["ms"] >= 0 else "ARP Responder (Ping Firewalled)"
            sub_lbl = ctk.CTkLabel(
                left,
                text=f"MAC Address: {dev['mac']}{vendor_str}   |   Response: {ping_txt}",
                font=ctk.CTkFont(family="Consolas", size=11),
                text_color="lightgray",
            )
            sub_lbl.pack(anchor="w")

            # Action Buttons on Right
            btn_box = ctk.CTkFrame(card, fg_color="transparent")
            btn_box.pack(side="right", padx=12, pady=8)

            ctk.CTkButton(
                btn_box,
                text="📋 Copy IP",
                width=90,
                height=28,
                fg_color="#34495E",
                hover_color="#2C3E50",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda ip=dev["ip"]: self.copy_ip(ip),
            ).pack(side="right", padx=4)

            ctk.CTkButton(
                btn_box,
                text="🔎 Probe Ports",
                width=115,
                height=28,
                fg_color="#8E44AD",
                hover_color="#6C3483",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda ip=dev["ip"], lbl=sub_lbl: self.probe_device_ports(ip, lbl),
            ).pack(side="right", padx=4)

    def copy_ip(self, ip: str):
        self.clipboard_clear()
        self.clipboard_append(ip)
        self.status_lbl.configure(text=f"✅ Copied {ip} to clipboard!", text_color="#2FA572")

    def probe_device_ports(self, ip: str, target_label: ctk.CTkLabel):
        """Checks common service ports on a discovered LAN device."""
        ports_to_check = [
            (22, "SSH"),
            (53, "DNS"),
            (80, "HTTP Web"),
            (135, "RPC"),
            (139, "NetBIOS"),
            (443, "HTTPS"),
            (445, "SMB File Share"),
            (3389, "Remote Desktop"),
            (8080, "Web Admin"),
        ]
        self.status_lbl.configure(text=f"🔎 Probing common ports on {ip}...", text_color="#3B8ED0")

        def worker():
            open_services = []
            for port, name in ports_to_check:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(0.25)
                        if s.connect_ex((ip, port)) == 0:
                            open_services.append(f"{port} ({name})")
                except Exception:
                    continue

            ports_str = ", ".join(open_services) if open_services else "None (All Common Ports Closed/Stealthed)"
            current_txt = target_label.cget("text").split("   |   Open Ports:")[0]
            self.after(
                0,
                lambda: (
                    target_label.configure(
                        text=f"{current_txt}   |   Open Ports: {ports_str}",
                        text_color="#F1C40F" if open_services else "lightgray",
                    ),
                    self.status_lbl.configure(
                        text=f"✅ Port probe for {ip} complete: {ports_str}",
                        text_color="#2FA572",
                    ),
                ),
            )

        threading.Thread(target=worker, daemon=True).start()