# hud_overlay.py
import re
import shutil
import threading
import subprocess
import psutil
import customtkinter as ctk
from backend_engine import SystemEngine


class HudOverlayView(ctk.CTkFrame):
    """Modular Floating Always-On-Top Gaming & Hardware Telemetry Mini-HUD Controller."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = master

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.hud_window = None
        self.hud_active = False
        self.has_nvidia_smi = shutil.which("nvidia-smi") is not None

        # Drag offset state for borderless window
        self._drag_x = 0
        self._drag_y = 0

        # Cached async telemetry for HUD
        self.hud_gpu_txt = "GPU: --%"
        self.hud_ping_txt = "Ping: --ms"
        self._hud_async_busy = False

        # Config Variables
        self.var_show_cpu = ctk.BooleanVar(value=True)
        self.var_show_ram = ctk.BooleanVar(value=True)
        self.var_show_gpu = ctk.BooleanVar(value=True)
        self.var_show_ping = ctk.BooleanVar(value=True)
        self.opacity_val = 0.88

        # ==========================================
        # CARD 1: HUD LAUNCHER & APPEARANCE
        # ==========================================
        ctrl_card = ctk.CTkFrame(self)
        ctrl_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            ctrl_card,
            text="🎯 FLOATING ALWAYS-ON-TOP MINI HUD",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w", padx=15, pady=(12, 2))

        ctk.CTkLabel(
            ctrl_card,
            text="Displays a draggable, translucent hardware & ping bar over games and apps.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 10))

        self.toggle_hud_btn = ctk.CTkButton(
            ctrl_card,
            text="🚀 Launch Floating Mini-HUD Overlay",
            height=38,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.toggle_hud,
        )
        self.toggle_hud_btn.pack(fill="x", padx=15, pady=6)

        self.hide_main_btn = ctk.CTkButton(
            ctrl_card,
            text="🔽 Launch HUD & Minimize Main Window to Tray",
            height=34,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.launch_hud_and_minimize,
        )
        self.hide_main_btn.pack(fill="x", padx=15, pady=4)

        # Opacity Slider
        self.op_lbl = ctk.CTkLabel(
            ctrl_card,
            text=f"HUD Background Opacity: {int(self.opacity_val * 100)}%",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.op_lbl.pack(anchor="w", padx=15, pady=(10, 2))

        self.op_slider = ctk.CTkSlider(
            ctrl_card,
            from_=0.40,
            to=1.00,
            number_of_steps=30,
            command=self.on_opacity_changed,
        )
        self.op_slider.set(self.opacity_val)
        self.op_slider.pack(fill="x", padx=15, pady=(0, 14))

        # ==========================================
        # CARD 2: SENSORS & SCREEN SNAP POSITION
        # ==========================================
        cfg_card = ctk.CTkFrame(self)
        cfg_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            cfg_card,
            text="⚙️ HUD METRICS & SCREEN CORNER SNAP",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#9B59B6",
        ).pack(anchor="w", padx=15, pady=(12, 6))

        chk_grid = ctk.CTkFrame(cfg_card, fg_color="transparent")
        chk_grid.pack(fill="x", padx=15, pady=4)
        chk_grid.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkCheckBox(chk_grid, text="Show CPU Load %", variable=self.var_show_cpu).grid(
            row=0, column=0, pady=4, sticky="w"
        )
        ctk.CTkCheckBox(chk_grid, text="Show RAM Usage %", variable=self.var_show_ram).grid(
            row=0, column=1, pady=4, sticky="w"
        )
        ctk.CTkCheckBox(chk_grid, text="Show GPU Load & Temp", variable=self.var_show_gpu).grid(
            row=1, column=0, pady=4, sticky="w"
        )
        ctk.CTkCheckBox(chk_grid, text="Show Live Game Ping (ms)", variable=self.var_show_ping).grid(
            row=1, column=1, pady=4, sticky="w"
        )

        ctk.CTkLabel(
            cfg_card, text="Quick Snap Position:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 4))

        snap_row = ctk.CTkFrame(cfg_card, fg_color="transparent")
        snap_row.pack(fill="x", padx=15, pady=(0, 14))

        for label, pos in [
            ("↖ Top-Left", "tl"),
            ("↗ Top-Right", "tr"),
            ("↙ Bot-Left", "bl"),
            ("↘ Bot-Right", "br"),
        ]:
            ctk.CTkButton(
                snap_row,
                text=label,
                height=30,
                fg_color="#34495E",
                hover_color="#2C3E50",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda p=pos: self.snap_hud_position(p),
            ).pack(side="left", expand=True, fill="x", padx=2)

        # ==========================================
        # INSTRUCTIONS & TELEMETRY LOG
        # ==========================================
        self.log_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.log_message(
            "Floating Mini-HUD Ready.\n"
            "• Click and drag anywhere on the floating HUD pill to reposition it on your monitor.\n"
            "• Click the '⚡' button on the HUD to trigger an instant background RAM trim without leaving your game.\n"
            "• Click the '×' button on the HUD to close the overlay."
        )

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def on_opacity_changed(self, val):
        self.opacity_val = float(val)
        self.op_lbl.configure(text=f"HUD Background Opacity: {int(self.opacity_val * 100)}%")
        if self.hud_window is not None and self.hud_window.winfo_exists():
            self.hud_window.attributes("-alpha", self.opacity_val)

    # ==========================================
    # FLOATING TOPMOST PILL WINDOW
    # ==========================================
    def toggle_hud(self):
        if self.hud_active and self.hud_window is not None and self.hud_window.winfo_exists():
            self.close_hud()
        else:
            self.open_hud()

    def launch_hud_and_minimize(self):
        if not self.hud_active:
            self.open_hud()
        if hasattr(self.app, "view_trayguard") and getattr(self.app.view_trayguard, "tray_running", False):
            self.app.view_trayguard.hide_to_tray()
        else:
            self.app.iconify()

    def open_hud(self):
        if self.hud_window is not None and self.hud_window.winfo_exists():
            return

        self.hud_window = ctk.CTkToplevel(self)
        self.hud_window.overrideredirect(True)  # Borderless floating pill
        self.hud_window.attributes("-topmost", True)
        self.hud_window.attributes("-alpha", self.opacity_val)
        self.hud_window.configure(fg_color="#0F172A")

        # Default position: Top-Right corner with 20px margin
        screen_w = self.winfo_screenwidth()
        self.hud_window.geometry(f"+{screen_w - 540}+20")

        pill_frame = ctk.CTkFrame(
            self.hud_window,
            fg_color="#0F172A",
            border_width=2,
            border_color="#3B8ED0",
            corner_radius=8,
        )
        pill_frame.pack(fill="both", expand=True)

        # Drag bindings
        pill_frame.bind("<ButtonPress-1>", self._start_drag)
        pill_frame.bind("<B1-Motion>", self._on_drag)

        self.hud_text_lbl = ctk.CTkLabel(
            pill_frame,
            text="⚡ Initializing Telemetry...",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color="#F8FAFC",
        )
        self.hud_text_lbl.pack(side="left", padx=(12, 8), pady=6)
        self.hud_text_lbl.bind("<ButtonPress-1>", self._start_drag)
        self.hud_text_lbl.bind("<B1-Motion>", self._on_drag)

        # Quick 1-Click RAM Boost Button right on the HUD
        boost_btn = ctk.CTkButton(
            pill_frame,
            text="⚡",
            width=26,
            height=22,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._hud_quick_ram_trim,
        )
        boost_btn.pack(side="left", padx=2, pady=4)

        # Close HUD Button
        close_btn = ctk.CTkButton(
            pill_frame,
            text="×",
            width=26,
            height=22,
            fg_color="#C0392B",
            hover_color="#922B21",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.close_hud,
        )
        close_btn.pack(side="right", padx=(2, 8), pady=4)

        self.hud_active = True
        self.toggle_hud_btn.configure(
            text="❌ Close Floating Mini-HUD Overlay",
            fg_color="#C0392B",
            hover_color="#922B21",
        )
        self.log_message("[+] Launched Floating Always-On-Top Mini-HUD.")
        self._update_hud_loop()

    def close_hud(self):
        self.hud_active = False
        if self.hud_window is not None and self.hud_window.winfo_exists():
            self.hud_window.destroy()
        self.hud_window = None
        self.toggle_hud_btn.configure(
            text="🚀 Launch Floating Mini-HUD Overlay",
            fg_color="#2FA572",
            hover_color="#1D7A52",
        )
        self.log_message("[-] Closed Floating Mini-HUD.")

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        if self.hud_window is not None and self.hud_window.winfo_exists():
            x = self.hud_window.winfo_x() + (event.x - self._drag_x)
            y = self.hud_window.winfo_y() + (event.y - self._drag_y)
            self.hud_window.geometry(f"+{x}+{y}")

    def snap_hud_position(self, corner: str):
        if not self.hud_active or self.hud_window is None or not self.hud_window.winfo_exists():
            self.open_hud()
        self.hud_window.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = max(420, self.hud_window.winfo_width())
        h = max(38, self.hud_window.winfo_height())

        coords = {
            "tl": (20, 20),
            "tr": (sw - w - 20, 20),
            "bl": (20, sh - h - 60),
            "br": (sw - w - 20, sh - h - 60),
        }
        x, y = coords.get(corner, (20, 20))
        self.hud_window.geometry(f"+{x}+{y}")

    def _hud_quick_ram_trim(self):
        def worker():
            SystemEngine.optimize_ram(lambda _: None)
            self.after(0, lambda: self.log_message("[⚡ HUD Quick Boost] Trimmed background process RAM!"))

        threading.Thread(target=worker, daemon=True).start()

    # ==========================================
    # LIGHTWEIGHT HUD TELEMETRY LOOP
    # ==========================================
    def _poll_hud_async_sensors(self):
        if self._hud_async_busy:
            return
        self._hud_async_busy = True

        def worker():
            try:
                if self.var_show_gpu.get() and self.has_nvidia_smi:
                    out = subprocess.check_output(
                        [
                            "nvidia-smi",
                            "--query-gpu=utilization.gpu,temperature.gpu",
                            "--format=csv,noheader,nounits",
                        ],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        text=True,
                        timeout=2,
                    ).strip()
                    if out:
                        parts = [p.strip() for p in out.splitlines()[0].split(",")]
                        if len(parts) >= 2:
                            self.hud_gpu_txt = f"GPU: {parts[0]}% ({parts[1]}°C)"

                if self.var_show_ping.get():
                    res = subprocess.run(
                        ["ping", "-n", "1", "-w", "600", "1.1.1.1"],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=1.5,
                    )
                    m = re.search(r"time[=<](\d+)\s*ms", res.stdout or "", re.IGNORECASE)
                    self.hud_ping_txt = f"Ping: {m.group(1)}ms" if m else "Ping: --"
            except Exception:
                pass
            finally:
                self._hud_async_busy = False

        threading.Thread(target=worker, daemon=True).start()

    def _update_hud_loop(self):
        if not self.hud_active or self.hud_window is None or not self.hud_window.winfo_exists():
            return

        segments = []
        if self.var_show_cpu.get():
            cpu_p = psutil.cpu_percent(interval=None)
            segments.append(f"CPU: {cpu_p:.0f}%")

        if self.var_show_ram.get():
            ram = psutil.virtual_memory()
            segments.append(f"RAM: {ram.percent:.0f}%")

        if self.var_show_gpu.get() or self.var_show_ping.get():
            self._poll_hud_async_sensors()

        if self.var_show_gpu.get():
            segments.append(self.hud_gpu_txt)

        if self.var_show_ping.get():
            segments.append(self.hud_ping_txt)

        line = "  |  ".join(segments) if segments else "⚡ PC Optimizer HUD"
        self.hud_text_lbl.configure(text=line)
        self.hud_window.lift()

        self.after(2000, self._update_hud_loop)