# network_speedtest.py
import time
import socket
import threading
import subprocess
import urllib.request
import psutil
import customtkinter as ctk


class NetworkSpeedtestView(ctk.CTkFrame):
    """Modular Network Speed, Ping Latency, and Adapter Inspector view."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ==========================================
        # TOP METRIC CARDS (DOWNLOAD & PING)
        # ==========================================
        # Download Speed Card
        self.dl_card = ctk.CTkFrame(self)
        self.dl_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            self.dl_card, text="⬇️ DOWNLOAD SPEED", font=ctk.CTkFont(size=13, weight="bold"), text_color="gray"
        ).pack(pady=(15, 2))

        self.dl_value_label = ctk.CTkLabel(
            self.dl_card, text="-- Mbps", font=ctk.CTkFont(size=32, weight="bold"), text_color="#3B8ED0"
        )
        self.dl_value_label.pack(pady=5)

        self.dl_bar = ctk.CTkProgressBar(self.dl_card, height=10, progress_color="#3B8ED0")
        self.dl_bar.pack(padx=25, pady=(5, 15), fill="x")
        self.dl_bar.set(0)

        # Ping Latency Card
        self.ping_card = ctk.CTkFrame(self)
        self.ping_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            self.ping_card, text="⚡ PING LATENCY (Cloudflare 1.1.1.1)", font=ctk.CTkFont(size=13, weight="bold"), text_color="gray"
        ).pack(pady=(15, 2))

        self.ping_value_label = ctk.CTkLabel(
            self.ping_card, text="-- ms", font=ctk.CTkFont(size=32, weight="bold"), text_color="#2FA572"
        )
        self.ping_value_label.pack(pady=5)

        self.status_label = ctk.CTkLabel(
            self.ping_card, text="Click 'Run Speed & Ping Test' below to start", font=ctk.CTkFont(size=12), text_color="gray"
        )
        self.status_label.pack(pady=(2, 15))

        # ==========================================
        # ACTION BUTTONS BAR
        # ==========================================
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky="ew")

        self.test_btn = ctk.CTkButton(
            btn_frame,
            text="🚀 Run Speed & Ping Test",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3B8ED0",
            command=self.start_full_test,
        )
        self.test_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))

        self.ping_only_btn = ctk.CTkButton(
            btn_frame,
            text="📡 Quick Multi-Server Ping",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#8E44AD",
            hover_color="#6C3483",
            command=self.start_ping_only,
        )
        self.ping_only_btn.pack(side="right", expand=True, fill="x", padx=(8, 0))

        # ==========================================
        # BOTTOM SPLIT: LOG CONSOLE & ADAPTER INFO
        # ==========================================
        self.log_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=2, column=0, padx=(0, 8), sticky="nsew")
        self.log_message("Network Tester Ready.\nUses Cloudflare CDN (25MB payload) for accurate download speed measurement.")

        self.adapters_scroll = ctk.CTkScrollableFrame(self, label_text="Active Network Interfaces")
        self.adapters_scroll.grid(row=2, column=1, padx=(8, 0), sticky="nsew")
        self.populate_adapters()

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def populate_adapters(self):
        """Lists active network interfaces and their IPv4 addresses."""
        for widget in self.adapters_scroll.winfo_children():
            widget.destroy()

        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        for iface_name, iface_addrs in addrs.items():
            if iface_name in stats and not stats[iface_name].isup:
                continue

            ipv4 = next((a.address for a in iface_addrs if a.family == socket.AF_INET), None)
            if not ipv4 or ipv4.startswith("127."):
                continue

            speed_mbps = stats[iface_name].speed if iface_name in stats else 0
            card = ctk.CTkFrame(self.adapters_scroll)
            card.pack(fill="x", padx=5, pady=5)

            ctk.CTkLabel(
                card, text=iface_name, font=ctk.CTkFont(size=13, weight="bold"), text_color="#3B8ED0"
            ).pack(anchor="w", padx=12, pady=(8, 2))

            ctk.CTkLabel(
                card,
                text=f"IPv4: {ipv4}   |   Link Speed: {speed_mbps} Mbps",
                font=ctk.CTkFont(size=11),
                text_color="lightgray",
            ).pack(anchor="w", padx=12, pady=(0, 8))

    def set_buttons_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.test_btn.configure(state=state)
        self.ping_only_btn.configure(state=state)

    def start_full_test(self):
        self.set_buttons_state(False)
        self.dl_bar.set(0)
        threading.Thread(target=self.run_full_test_worker, daemon=True).start()

    def start_ping_only(self):
        self.set_buttons_state(False)
        threading.Thread(target=self.run_ping_worker, daemon=True).start()

    def measure_ping(self, host: str) -> float:
        """Runs a single Windows ping command and extracts latency in ms."""
        try:
            output = subprocess.check_output(
                ["ping", "-n", "2", "-w", "1500", host],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
            )
            for line in output.splitlines():
                if "Average =" in line:
                    avg_part = line.split("Average =")[-1].strip()
                    return float(avg_part.replace("ms", "").strip())
        except Exception:
            pass
        return -1.0

    def run_ping_worker(self):
        self.log_message("\n--- Pinging Global DNS Servers ---")
        servers = [
            ("Cloudflare DNS", "1.1.1.1"),
            ("Google Public DNS", "8.8.8.8"),
            ("Quad9 Security DNS", "9.9.9.9"),
        ]

        for name, ip in servers:
            self.after(0, lambda n=name: self.status_label.configure(text=f"Pinging {n}..."))
            ms = self.measure_ping(ip)
            if ms >= 0:
                self.log_message(f"[+] {name} ({ip}): {ms:.0f} ms")
                if ip == "1.1.1.1":
                    self.after(0, lambda m=ms: self.ping_value_label.configure(text=f"{m:.0f} ms"))
            else:
                self.log_message(f"[!] {name} ({ip}): Request Timed Out")

        self.after(0, lambda: self.status_label.configure(text="Ping test finished."))
        self.after(0, lambda: self.set_buttons_state(True))

    def run_full_test_worker(self):
        # Step 1: Ping Test
        self.run_ping_worker()
        self.after(0, lambda: self.set_buttons_state(False))

        # Step 2: Download Speed Test (25 MB stream from Cloudflare Speedtest)
        self.log_message("\n--- Starting Download Speed Test (25 MB) ---")
        self.after(0, lambda: self.status_label.configure(text="Downloading test payload..."))

        url = "https://speed.cloudflare.com/__down?bytes=25000000"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

        total_bytes = 25_000_000
        downloaded = 0
        chunk_size = 64 * 1024  # 64 KB chunks

        try:
            start_time = time.perf_counter()
            with urllib.request.urlopen(req, timeout=15) as response:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    elapsed = time.perf_counter() - start_time
                    if elapsed > 0:
                        # Convert bytes/sec to Megabits/sec (Mbps)
                        current_mbps = (downloaded * 8) / (elapsed * 1_000_000)
                        progress = min(1.0, downloaded / total_bytes)
                        self.after(
                            0,
                            lambda m=current_mbps, p=progress: (
                                self.dl_value_label.configure(text=f"{m:.1f} Mbps"),
                                self.dl_bar.set(p),
                            ),
                        )

            total_elapsed = time.perf_counter() - start_time
            final_mbps = (downloaded * 8) / (total_elapsed * 1_000_000)
            self.log_message(f"[+] Downloaded 25 MB in {total_elapsed:.2f} seconds.")
            self.log_message(f"=== Final Download Speed: {final_mbps:.2f} Mbps ===")
            self.after(0, lambda: self.status_label.configure(text="Speedtest Complete!"))

        except Exception as e:
            self.log_message(f"[!] Download speed test failed: {e}")
            self.after(0, lambda: self.status_label.configure(text="Test failed (Check connection)"))

        self.after(0, lambda: self.set_buttons_state(True))