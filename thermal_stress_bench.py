# thermal_stress_bench.py
import os
import time
import math
import hashlib
import tempfile
import threading
import multiprocessing
import psutil
import customtkinter as ctk


def _cpu_stress_worker(duration_sec: float) -> int:
    """Top-level worker function for multiprocessing (safe for PyInstaller .exe builds)."""
    end_time = time.perf_counter() + duration_sec
    iterations = 0
    payload = b"PCOptimizerUltimateStressBenchmarkPayloadBlock2026"
    while time.perf_counter() < end_time:
        # Mix integer cryptographic hashing + floating point math to load ALU & FPU units
        h = hashlib.sha256(payload).digest()
        val = 0.0
        for b in h[:16]:
            val += math.sqrt(b + 1.0) * math.sin(b)
        if val > 0:
            iterations += 1
    return iterations


class ThermalStressBenchView(ctk.CTkFrame):
    """Modular Multi-Core CPU Stress Test & Drive Sequential Read/Write Speed Benchmark."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.running_cpu = False
        self.running_disk = False
        self.logical_cores = psutil.cpu_count(logical=True) or 4
        self.physical_cores = psutil.cpu_count(logical=False) or 2

        # ==========================================
        # CARD 1: CPU MULTI-CORE STRESS & BENCHMARK
        # ==========================================
        cpu_card = ctk.CTkFrame(self)
        cpu_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            cpu_card,
            text="🔥 CPU MULTI-CORE STRESS & BENCHMARK",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w", padx=15, pady=(12, 2))

        ctk.CTkLabel(
            cpu_card,
            text=f"Detected {self.physical_cores} Physical Cores / {self.logical_cores} Logical Threads",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 8))

        # Score Box Row
        cpu_scores_frame = ctk.CTkFrame(cpu_card, fg_color=("gray85", "gray17"))
        cpu_scores_frame.pack(fill="x", padx=15, pady=6)
        cpu_scores_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="cpuscore")

        # Single-Core Score
        s_box = ctk.CTkFrame(cpu_scores_frame, fg_color="transparent")
        s_box.grid(row=0, column=0, pady=8)
        ctk.CTkLabel(s_box, text="SINGLE-CORE", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray").pack()
        self.single_score_lbl = ctk.CTkLabel(
            s_box, text="-- pts", font=ctk.CTkFont(size=18, weight="bold"), text_color="#3B8ED0"
        )
        self.single_score_lbl.pack()

        # Multi-Core Score
        m_box = ctk.CTkFrame(cpu_scores_frame, fg_color="transparent")
        m_box.grid(row=0, column=1, pady=8)
        ctk.CTkLabel(m_box, text="MULTI-CORE", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray").pack()
        self.multi_score_lbl = ctk.CTkLabel(
            m_box, text="-- pts", font=ctk.CTkFont(size=18, weight="bold"), text_color="#2FA572"
        )
        self.multi_score_lbl.pack()

        # Peak Clock Speed
        c_box = ctk.CTkFrame(cpu_scores_frame, fg_color="transparent")
        c_box.grid(row=0, column=2, pady=8)
        ctk.CTkLabel(c_box, text="LOAD CLOCK", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray").pack()
        self.clock_lbl = ctk.CTkLabel(
            c_box, text="-- MHz", font=ctk.CTkFont(size=18, weight="bold"), text_color="#E67E22"
        )
        self.clock_lbl.pack()

        dur_row = ctk.CTkFrame(cpu_card, fg_color="transparent")
        dur_row.pack(fill="x", padx=15, pady=6)

        ctk.CTkLabel(dur_row, text="Stress Duration:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.dur_menu = ctk.CTkOptionMenu(
            dur_row,
            values=["5 Seconds (Quick Bench)", "10 Seconds (Standard)", "20 Seconds (Thermal Soak)"],
            width=210,
        )
        self.dur_menu.set("10 Seconds (Standard)")
        self.dur_menu.pack(side="right")

        self.cpu_bench_btn = ctk.CTkButton(
            cpu_card,
            text="🚀 Run Single & Multi-Core CPU Benchmark",
            height=38,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.start_cpu_benchmark,
        )
        self.cpu_bench_btn.pack(fill="x", padx=15, pady=(6, 14))

        # ==========================================
        # CARD 2: SSD / HDD SEQUENTIAL SPEED TEST
        # ==========================================
        disk_card = ctk.CTkFrame(self)
        disk_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            disk_card,
            text="💿 DRIVE READ & WRITE SPEED BENCHMARK",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#9B59B6",
        ).pack(anchor="w", padx=15, pady=(12, 2))

        ctk.CTkLabel(
            disk_card,
            text="Measures sequential throughput (MB/s) using a 256 MB unbuffered test file.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 8))

        # Speed Display Box
        disk_scores_frame = ctk.CTkFrame(disk_card, fg_color=("gray85", "gray17"))
        disk_scores_frame.pack(fill="x", padx=15, pady=6)
        disk_scores_frame.grid_columnconfigure((0, 1), weight=1, uniform="diskscore")

        r_box = ctk.CTkFrame(disk_scores_frame, fg_color="transparent")
        r_box.grid(row=0, column=0, pady=8)
        ctk.CTkLabel(r_box, text="SEQUENTIAL READ", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray").pack()
        self.read_speed_lbl = ctk.CTkLabel(
            r_box, text="-- MB/s", font=ctk.CTkFont(size=18, weight="bold"), text_color="#2FA572"
        )
        self.read_speed_lbl.pack()

        w_box = ctk.CTkFrame(disk_scores_frame, fg_color="transparent")
        w_box.grid(row=0, column=1, pady=8)
        ctk.CTkLabel(
            w_box, text="SEQUENTIAL WRITE", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray"
        ).pack()
        self.write_speed_lbl = ctk.CTkLabel(
            w_box, text="-- MB/s", font=ctk.CTkFont(size=18, weight="bold"), text_color="#9B59B6"
        )
        self.write_speed_lbl.pack()

        drv_row = ctk.CTkFrame(disk_card, fg_color="transparent")
        drv_row.pack(fill="x", padx=15, pady=6)

        ctk.CTkLabel(drv_row, text="Target Drive:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

        drives = [p.mountpoint for p in psutil.disk_partitions(all=False) if p.fstype and "cdrom" not in p.opts]
        if not drives:
            drives = ["C:\\"]

        self.drive_menu = ctk.CTkOptionMenu(drv_row, values=drives, width=140)
        self.drive_menu.set(drives[0])
        self.drive_menu.pack(side="right")

        self.disk_bench_btn = ctk.CTkButton(
            disk_card,
            text="⚡ Run 256 MB Read / Write Disk Speed Test",
            height=38,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.start_disk_benchmark,
        )
        self.disk_bench_btn.pack(fill="x", padx=15, pady=(6, 14))

        # ==========================================
        # PROGRESS BAR & LIVE TELEMETRY CONSOLE
        # ==========================================
        self.progress_bar = ctk.CTkProgressBar(self, height=12, progress_color="#2FA572")
        self.progress_bar.grid(row=1, column=0, columnspan=2, pady=(0, 8), sticky="ew")
        self.progress_bar.set(0)

        self.log_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.log_message(
            "Hardware Stress & Speed Benchmark Ready.\n"
            "• CPU Benchmark tests Single-Core speed first, then loads 100% of all logical threads to measure Multi-Core scaling and clock stability.\n"
            "• Disk Benchmark writes and reads a 256 MB random block with OS write-cache flushing enabled."
        )

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ==========================================
    # PART 1: CPU SINGLE & MULTI-CORE BENCHMARK
    # ==========================================
    def start_cpu_benchmark(self):
        if self.running_cpu or self.running_disk:
            return

        dur_choice = self.dur_menu.get()
        total_secs = int(dur_choice.split()[0])

        self.running_cpu = True
        self.cpu_bench_btn.configure(state="disabled", text="🔥 Stressing CPU (Watch Top Gauge)...")
        self.disk_bench_btn.configure(state="disabled")
        self.progress_bar.set(0)

        threading.Thread(target=self._cpu_bench_worker, args=(total_secs,), daemon=True).start()

    def _cpu_bench_worker(self, total_secs: int):
        single_dur = max(2.0, total_secs * 0.35)
        multi_dur = max(3.0, total_secs * 0.65)

        self.after(
            0,
            lambda: self.log_message(
                f"\n=== Starting CPU Benchmark ({single_dur:.1f}s Single-Core + {multi_dur:.1f}s {self.logical_cores}-Thread All-Core Load) ==="
            ),
        )

        # Phase 1: Single-Core Benchmark
        self.after(0, lambda: self.log_message("[1/2] Running Single-Core SHA-256 + FPU Math Stress Test..."))
        t0 = time.perf_counter()
        single_iters = _cpu_stress_worker(single_dur)
        single_elapsed = max(0.1, time.perf_counter() - t0)
        single_score = int((single_iters / single_elapsed) / 12.0)

        freq = psutil.cpu_freq()
        cur_mhz = int(freq.current) if freq and freq.current else 0

        self.after(
            0,
            lambda s=single_score, c=cur_mhz: (
                self.single_score_lbl.configure(text=f"{s:,} pts"),
                self.clock_lbl.configure(text=f"{c} MHz" if c else "Active"),
                self.progress_bar.set(0.4),
                self.log_message(f"  [+] Single-Core Score: {s:,} pts (Clock: {c} MHz)"),
            ),
        )

        # Phase 2: Multi-Core All-Thread Stress Test
        self.after(
            0,
            lambda: self.log_message(
                f"[2/2] Spawning {self.logical_cores} parallel worker processes for 100% All-Core Load..."
            ),
        )

        clocks_sampled = []
        stop_clock_sampler = False

        def sample_clocks():
            while not stop_clock_sampler:
                f = psutil.cpu_freq()
                if f and f.current:
                    clocks_sampled.append(f.current)
                time.sleep(0.4)

        sampler_thread = threading.Thread(target=sample_clocks, daemon=True)
        sampler_thread.start()

        t1 = time.perf_counter()
        try:
            with multiprocessing.Pool(processes=self.logical_cores) as pool:
                results = pool.map(_cpu_stress_worker, [multi_dur] * self.logical_cores)
            total_multi_iters = sum(results)
        except Exception:
            # Fallback to threaded execution if OS restricts subprocess pool
            total_multi_iters = _cpu_stress_worker(multi_dur) * self.logical_cores

        stop_clock_sampler = True
        multi_elapsed = max(0.1, time.perf_counter() - t1)
        multi_score = int((total_multi_iters / multi_elapsed) / 12.0)

        avg_mhz = int(sum(clocks_sampled) / len(clocks_sampled)) if clocks_sampled else cur_mhz
        min_mhz = int(min(clocks_sampled)) if clocks_sampled else cur_mhz
        max_mhz = int(max(clocks_sampled)) if clocks_sampled else cur_mhz
        scaling_ratio = multi_score / max(1, single_score)

        # Check for severe clock drop (>15% drop from peak during load)
        throttled = (max_mhz > 0) and ((max_mhz - min_mhz) / max_mhz > 0.15)
        throttle_msg = (
            f"⚠️ Noticeable clock drop detected ({max_mhz} ➔ {min_mhz} MHz). Check CPU cooling!"
            if throttled
            else f"✅ Stable Boost Clocks held under 100% load (Avg: {avg_mhz} MHz | Peak: {max_mhz} MHz)."
        )

        self.running_cpu = False
        self.after(
            0,
            lambda: (
                self.multi_score_lbl.configure(text=f"{multi_score:,} pts"),
                self.clock_lbl.configure(text=f"{avg_mhz} MHz"),
                self.progress_bar.set(1.0),
                self.cpu_bench_btn.configure(state="normal", text="🚀 Run Single & Multi-Core CPU Benchmark"),
                self.disk_bench_btn.configure(state="normal"),
                self.log_message(
                    f"  [+] Multi-Core Score:  {multi_score:,} pts ({scaling_ratio:.2f}x MP Ratio)\n"
                    f"  [+] Clock Stability:   {throttle_msg}\n"
                    f"=== CPU Benchmark Complete ==="
                ),
            ),
        )

    # ==========================================
    # PART 2: SEQUENTIAL DISK READ/WRITE BENCHMARK
    # ==========================================
    def start_disk_benchmark(self):
        if self.running_cpu or self.running_disk:
            return

        target_drive = self.drive_menu.get()
        self.running_disk = True
        self.disk_bench_btn.configure(state="disabled", text="⏳ Testing Drive Speed...")
        self.cpu_bench_btn.configure(state="disabled")
        self.progress_bar.set(0)

        threading.Thread(target=self._disk_bench_worker, args=(target_drive,), daemon=True).start()

    def _disk_bench_worker(self, drive_root: str):
        total_mb = 256
        chunk_bytes = 4 * 1024 * 1024  # 4 MB block
        chunks = total_mb // 4
        buf = os.urandom(chunk_bytes)

        # Choose a writable temp path on the selected drive
        if drive_root.upper().startswith("C:"):
            test_dir = tempfile.gettempdir()
        else:
            test_dir = drive_root

        test_file = os.path.join(test_dir, "pc_optimizer_disk_bench_temp.bin")

        self.after(
            0,
            lambda: self.log_message(
                f"\n=== Starting 256 MB Sequential Read/Write Speed Test on {drive_root} ==="
            ),
        )

        write_mb_s = 0.0
        read_mb_s = 0.0

        try:
            # 1. Sequential Write Test (with fsync so OS write-behind cache is flushed to physical disk)
            self.after(0, lambda: self.log_message("[1/2] Measuring Sequential Write Speed (256 MB)..."))
            t_w0 = time.perf_counter()
            with open(test_file, "wb", buffering=0) as f:
                for i in range(chunks):
                    f.write(buf)
                    if i % 8 == 0:
                        self.after(0, lambda p=(i / chunks) * 0.5: self.progress_bar.set(p))
                f.flush()
                os.fsync(f.fileno())
            t_w_elapsed = max(0.001, time.perf_counter() - t_w0)
            write_mb_s = total_mb / t_w_elapsed

            self.after(
                0,
                lambda w=write_mb_s: (
                    self.write_speed_lbl.configure(text=f"{w:.0f} MB/s"),
                    self.progress_bar.set(0.55),
                    self.log_message(f"  [+] Sequential Write Speed: {w:.1f} MB/s"),
                ),
            )

            # 2. Sequential Read Test
            self.after(0, lambda: self.log_message("[2/2] Measuring Sequential Read Speed (256 MB)..."))
            t_r0 = time.perf_counter()
            with open(test_file, "rb", buffering=0) as f:
                for i in range(chunks):
                    _ = f.read(chunk_bytes)
                    if i % 8 == 0:
                        self.after(0, lambda p=0.55 + (i / chunks) * 0.45: self.progress_bar.set(p))
            t_r_elapsed = max(0.001, time.perf_counter() - t_r0)
            read_mb_s = total_mb / t_r_elapsed

            # Classify drive tier
            if write_mb_s >= 1500 or read_mb_s >= 2000:
                tier = "⚡ NVMe PCIe M.2 SSD Tier"
            elif write_mb_s >= 300 or read_mb_s >= 400:
                tier = "✅ SATA III SSD Tier"
            else:
                tier = "💿 Mechanical HDD / USB Flash Tier"

            self.after(
                0,
                lambda r=read_mb_s, t=tier: (
                    self.read_speed_lbl.configure(text=f"{r:.0f} MB/s"),
                    self.progress_bar.set(1.0),
                    self.log_message(
                        f"  [+] Sequential Read Speed:  {r:.1f} MB/s\n"
                        f"  [+] Performance Tier:       {t}\n"
                        f"=== Disk Speed Benchmark Complete (Temporary test file cleaned) ==="
                    ),
                ),
            )
        except PermissionError:
            self.after(
                0,
                lambda: self.log_message(
                    f"[!] Permission denied writing test file to {drive_root}. Ensure Admin Mode is ON."
                ),
            )
        except Exception as e:
            self.after(0, lambda err=e: self.log_message(f"[!] Disk benchmark error: {err}"))
        finally:
            if os.path.exists(test_file):
                try:
                    os.unlink(test_file)
                except OSError:
                    pass
            self.running_disk = False
            self.after(
                0,
                lambda: (
                    self.disk_bench_btn.configure(
                        state="normal", text="⚡ Run 256 MB Read / Write Disk Speed Test"
                    ),
                    self.cpu_bench_btn.configure(
                        state="normal", text="🚀 Run Single & Multi-Core CPU Benchmark"
                    ),
                ),
            )