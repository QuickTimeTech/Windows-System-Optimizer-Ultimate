# tray_ram_guard.py
import os
import time
import ctypes
from ctypes import wintypes
import threading
import subprocess
import psutil
import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray
from backend_engine import SystemEngine


class TrayRamGuardView(ctk.CTkFrame):
    """System Tray Background Daemon, Auto-RAM Guard, Super-Menu & Global Win32 Hotkey Listener."""

    # Win32 Global Hotkey Constants
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_NOREPEAT = 0x4000
    WM_HOTKEY = 0x0312
    HK_BOOST_RAM = 101  # Ctrl + Shift + B (0x42)
    HK_TOGGLE_HUD = 102  # Ctrl + Shift + H (0x48)

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = master

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.tray_icon = None
        self.tray_running = False
        self.guard_running = True
        self.hotkeys_enabled = True
        self._hotkey_thread_id = None

        self.var_auto_guard = ctk.BooleanVar(value=True)
        self.var_close_to_tray = ctk.BooleanVar(value=True)
        self.var_global_hotkeys = ctk.BooleanVar(value=True)
        self.threshold_pct = 85

        self.trim_count = 0
        self.total_freed_mb = 0.0

        # ==========================================
        # CARD 1: SYSTEM TRAY & AUTO-RAM GUARD
        # ==========================================
        left_card = ctk.CTkFrame(self)
        left_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            left_card,
            text="📌 SYSTEM TRAY DAEMON & AUTO-RAM GUARD",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            left_card,
            text="Monitors memory in the background and provides a right-click Tray Super-Menu.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 10))

        ctk.CTkSwitch(
            left_card,
            text="Enable Automatic RAM Guard (Auto-Trim when RAM is high)",
            variable=self.var_auto_guard,
            progress_color="#2FA572",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=15, pady=6)

        ctk.CTkSwitch(
            left_card,
            text="Minimize to System Tray when clicking Window 'X' Close",
            variable=self.var_close_to_tray,
            progress_color="#3B8ED0",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=15, pady=6)

        self.thresh_lbl = ctk.CTkLabel(
            left_card,
            text=f"Auto-Trim Trigger Threshold: {self.threshold_pct}% RAM Usage",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.thresh_lbl.pack(anchor="w", padx=15, pady=(10, 2))

        self.thresh_slider = ctk.CTkSlider(
            left_card,
            from_=65,
            to=95,
            number_of_steps=30,
            command=self._on_slider_change,
        )
        self.thresh_slider.set(self.threshold_pct)
        self.thresh_slider.pack(fill="x", padx=15, pady=(0, 10))

        btn_row = ctk.CTkFrame(left_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(4, 14))

        ctk.CTkButton(
            btn_row,
            text="🔽 Minimize to System Tray Now",
            height=34,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.hide_to_tray,
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        ctk.CTkButton(
            btn_row,
            text="🚀 Manual Trim Now",
            height=34,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(weight="bold"),
            command=self.manual_trim_now,
        ).pack(side="right", expand=True, fill="x", padx=(4, 0))

        # ==========================================
        # CARD 2: GLOBAL IN-GAME HOTKEYS & CLI MODE
        # ==========================================
        right_card = ctk.CTkFrame(self)
        right_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            right_card,
            text="⌨️ GLOBAL IN-GAME HOTKEYS & SILENT CLI",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#9B59B6",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            right_card,
            text="Trigger instant optimizations while inside fullscreen games without Alt-Tabbing.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 8))

        hk_box1 = ctk.CTkFrame(right_card, fg_color=("gray85", "gray17"))
        hk_box1.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(
            hk_box1, text="⚡ Instant Background RAM Boost:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=12, pady=8)
        ctk.CTkLabel(
            hk_box1,
            text="Ctrl + Shift + B",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color="#2FA572",
        ).pack(side="right", padx=12, pady=8)

        hk_box2 = ctk.CTkFrame(right_card, fg_color=("gray85", "gray17"))
        hk_box2.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(
            hk_box2, text="🎯 Toggle Floating Gaming HUD:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=12, pady=8)
        ctk.CTkLabel(
            hk_box2,
            text="Ctrl + Shift + H",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color="#3B8ED0",
        ).pack(side="right", padx=12, pady=8)

        hk_box3 = ctk.CTkFrame(right_card, fg_color=("gray85", "gray17"))
        hk_box3.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(
            hk_box3, text="🤖 Headless Scheduled CLI Flag:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=12, pady=8)
        ctk.CTkLabel(
            hk_box3,
            text="--silent-autopilot",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#F39C12",
        ).pack(side="right", padx=12, pady=8)

        self.stats_lbl = ctk.CTkLabel(
            right_card,
            text="Session Auto-Trims: 0  |  Total RAM Reclaimed: 0.0 MB",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2FA572",
        )
        self.stats_lbl.pack(anchor="w", padx=15, pady=(8, 12))

        # ==========================================
        # LIVE GUARD & HOTKEY LOG
        # ==========================================
        self.log_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.log_message(
            "System Tray Super-Menu & Global Hotkeys Active!\n"
            "• Right-click the ⚡ icon in your Windows System Tray for 1-click Junk Clean, RAM Boost, HUD Toggle, ASUS Eco Mode & DNS Flush.\n"
            "• Press Ctrl+Shift+B anywhere to boost RAM, or Ctrl+Shift+H to toggle the Floating Gaming HUD."
        )

        # Start System Tray Icon, Auto-RAM Guard Loop & Global Hotkey Listener
        self._start_tray_icon()
        self._start_hotkey_listener()
        self.after(4000, self._auto_guard_loop)

    def _on_slider_change(self, val):
        self.threshold_pct = int(float(val))
        self.thresh_lbl.configure(text=f"Auto-Trim Trigger Threshold: {self.threshold_pct}% RAM Usage")

    def log_message(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{ts}] {msg}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ==========================================
    # GLOBAL WIN32 HOTKEY LISTENER (CTRL+SHIFT+B / CTRL+SHIFT+H)
    # ==========================================
    def _start_hotkey_listener(self):
        def hotkey_worker():
            user32 = ctypes.windll.user32
            self._hotkey_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

            mods = self.MOD_CONTROL | self.MOD_SHIFT | self.MOD_NOREPEAT
            user32.RegisterHotKey(None, self.HK_BOOST_RAM, mods, 0x42)  # 'B'
            user32.RegisterHotKey(None, self.HK_TOGGLE_HUD, mods, 0x48)  # 'H'

            msg = wintypes.MSG()
            while self.guard_running:
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret <= 0:
                    break
                if msg.message == self.WM_HOTKEY:
                    if msg.wParam == self.HK_BOOST_RAM:
                        self.app.after(0, self._on_hotkey_boost_ram)
                    elif msg.wParam == self.HK_TOGGLE_HUD:
                        self.app.after(0, self._on_hotkey_toggle_hud)
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

            user32.UnregisterHotKey(None, self.HK_BOOST_RAM)
            user32.UnregisterHotKey(None, self.HK_TOGGLE_HUD)

        threading.Thread(target=hotkey_worker, daemon=True).start()

    def _on_hotkey_boost_ram(self):
        self.log_message("⌨️ [Global Hotkey Ctrl+Shift+B] Triggering instant background RAM boost...")
        self.manual_trim_now()

    def _on_hotkey_toggle_hud(self):
        self.log_message("⌨️ [Global Hotkey Ctrl+Shift+H] Toggling Floating Gaming HUD...")
        hud_view = self.app.get_lazy_view("hud_overlay", "HudOverlayView")
        if hasattr(hud_view, "toggle_hud"):
            hud_view.toggle_hud()

    # ==========================================
    # SYSTEM TRAY SUPER-MENU
    # ==========================================
    @staticmethod
    def _create_bolt_image():
        img = Image.new("RGBA", (64, 64), (15, 23, 42, 255))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((2, 2, 62, 62), radius=14, outline=(56, 189, 248, 255), width=4)
        bolt = [(36, 10), (16, 36), (30, 36), (26, 54), (48, 26), (34, 26)]
        draw.polygon(bolt, fill=(47, 165, 114, 255))
        return img

    def _start_tray_icon(self):
        if self.tray_running:
            return

        menu = pystray.Menu(
            pystray.MenuItem("📊 Open PC Optimizer Dashboard", self._tray_restore_window, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("🚀 Quick Boost RAM (Ctrl+Shift+B)", self._tray_boost_ram),
            pystray.MenuItem("🧹 Silent Quick Junk Clean", self._tray_quick_clean),
            pystray.MenuItem("🎯 Toggle Gaming HUD (Ctrl+Shift+H)", self._tray_toggle_hud),
            pystray.MenuItem("🔋 ASUS Laptop Eco Mode (Stop RGB Drain)", self._tray_asus_eco),
            pystray.MenuItem("🌐 Flush DNS Cache", self._tray_flush_dns),
            pystray.MenuItem("🤖 Run 1-Click Autopilot & HTML Report", self._tray_run_autopilot),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Exit PC Optimizer Completely", self._tray_exit_app),
        )

        self.tray_icon = pystray.Icon(
            "PCOptimizerUltimate",
            self._create_bolt_image(),
            "PC Optimizer Ultimate (Ctrl+Shift+B: Boost RAM)",
            menu,
        )
        self.tray_running = True
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_to_tray(self):
        self.app.withdraw()
        self.log_message("Window minimized to System Tray (0% UI CPU sleep mode active).")

    def _tray_restore_window(self, icon=None, item=None):
        self.app.after(0, lambda: (self.app.deiconify(), self.app.lift(), self.app.focus_force()))

    def _tray_boost_ram(self, icon=None, item=None):
        self.app.after(0, self.manual_trim_now)

    def _tray_quick_clean(self, icon=None, item=None):
        def worker():
            targets = SystemEngine.get_target_folders(
                user_temp=True, win_temp=True, prefetch=False, chrome=True, edge=True
            )
            SystemEngine.clean_junk(targets, True, lambda _: None)
            self.app.after(0, lambda: self.log_message("🧹 [Tray Quick Clean] Cleaned Temp & Browser Caches silently!"))

        threading.Thread(target=worker, daemon=True).start()

    def _tray_toggle_hud(self, icon=None, item=None):
        self.app.after(0, self._on_hotkey_toggle_hud)

    def _tray_asus_eco(self, icon=None, item=None):
        def worker():
            for svc in ["LightingService", "AsusROGLSLService", "ArmouryCrateService"]:
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f"Stop-Service -Name '{svc}' -Force -ErrorAction SilentlyContinue; "
                        f"Set-Service -Name '{svc}' -StartupType Manual -ErrorAction SilentlyContinue",
                    ],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=6,
                )
            self.app.after(0, lambda: self.log_message("🔋 [Tray ASUS Eco] Stopped LightingService & ROG timer drain!"))

        threading.Thread(target=worker, daemon=True).start()

    def _tray_flush_dns(self, icon=None, item=None):
        threading.Thread(
            target=lambda: (
                SystemEngine.flush_dns(lambda _: None),
                self.app.after(0, lambda: self.log_message("🌐 [Tray DNS] Flushed Windows DNS Resolver Cache.")),
            ),
            daemon=True,
        ).start()

    def _tray_run_autopilot(self, icon=None, item=None):
        def launch():
            self.app.deiconify()
            self.app.show_autopilot_view()
            ap = self.app.get_lazy_view("autopilot_maintenance", "AutopilotMaintenanceView")
            if hasattr(ap, "start_autopilot"):
                ap.start_autopilot()

        self.app.after(0, launch)

    def _tray_exit_app(self, icon=None, item=None):
        self.stop_tray()
        self.app.after(0, self.app.destroy)

    def stop_tray(self):
        self.guard_running = False
        self.tray_running = False
        if self._hotkey_thread_id:
            try:
                ctypes.windll.user32.PostThreadMessageW(self._hotkey_thread_id, 0x0012, 0, 0)  # WM_QUIT
            except Exception:
                pass
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass

    # ==========================================
    # AUTO-RAM GUARD LOOP
    # ==========================================
    def manual_trim_now(self):
        def worker():
            before = psutil.virtual_memory().used
            SystemEngine.optimize_ram(lambda _: None)
            time.sleep(0.3)
            after = psutil.virtual_memory().used
            freed_mb = max(0.0, (before - after) / (1024 * 1024))
            self.trim_count += 1
            self.total_freed_mb += freed_mb
            self.app.after(
                0,
                lambda f=freed_mb: (
                    self.stats_lbl.configure(
                        text=f"Session Auto-Trims: {self.trim_count}  |  Total RAM Reclaimed: {self.total_freed_mb:.0f} MB"
                    ),
                    self.log_message(f"🚀 RAM Working Sets Trimmed — Reclaimed {f:.1f} MB!"),
                ),
            )

        threading.Thread(target=worker, daemon=True).start()

    def _auto_guard_loop(self):
        if not self.guard_running:
            return
        if self.var_auto_guard.get():
            mem = psutil.virtual_memory()
            if mem.percent >= self.threshold_pct:
                self.log_message(
                    f"⚠️ RAM reached {mem.percent:.1f}% (Threshold: {self.threshold_pct}%). Auto-trimming..."
                )
                self.manual_trim_now()
        self.after(12000, self._auto_guard_loop)