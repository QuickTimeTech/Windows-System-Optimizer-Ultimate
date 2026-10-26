# privacy_debloater.py
import subprocess
import winreg
import customtkinter as ctk
from backend_engine import SystemEngine


class PrivacyDebloaterView(ctk.CTkFrame):
    """Modular Windows 10/11 Privacy Shield & Debloater using Registry Switches."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Define registry tweaks:
        # (id, title, description, hive, reg_path, value_name, enabled_val, disabled_val, needs_admin)
        self.tweaks = [
            (
                "bing_search",
                "⚡ Disable Bing Web Search in Start Menu",
                "Makes Start Menu search instant by stopping Windows from querying Bing online for every keystroke.",
                winreg.HKEY_CURRENT_USER,
                r"Software\Policies\Microsoft\Windows\Explorer",
                "DisableSearchBoxSuggestions",
                1,
                0,
                False,
            ),
            (
                "ad_id",
                "🛡️ Disable Windows Advertising ID Tracking",
                "Prevents Windows and Microsoft Store apps from using your unique Advertising ID for targeted ads.",
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
                "Enabled",
                0,
                1,
                False,
            ),
            (
                "start_ads",
                "🚫 Block Start Menu & Settings 'Suggested' App Ads",
                "Disables silent promotional app suggestions and nag notifications inside Windows Content Delivery.",
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                "SubscribedContent-338389Enabled",
                0,
                1,
                False,
            ),
            (
                "lock_tips",
                "🔒 Disable Lock Screen Tips, Tricks & Ads",
                "Stops Windows from showing 'Fun facts, tips, and more' promotional overlays on your lock screen.",
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                "RotatingLockScreenOverlayEnabled",
                0,
                1,
                False,
            ),
            (
                "copilot",
                "🤖 Disable Windows Copilot Sidebar Integration",
                "Turns off Windows Copilot background hooks for a cleaner taskbar and lower memory usage.",
                winreg.HKEY_CURRENT_USER,
                r"Software\Policies\Microsoft\Windows\WindowsCopilot",
                "TurnOffWindowsCopilot",
                1,
                0,
                False,
            ),
            (
                "telemetry",
                "📡 Minimize Windows Diagnostic Telemetry (Requires Admin)",
                "Sets Windows Data Collection policy to Security/Minimum (0) to reduce background data uploads.",
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                "AllowTelemetry",
                0,
                1,
                True,
            ),
        ]

        self.switch_vars = {}

        # ==========================================
        # TOP ACTION BAR
        # ==========================================
        top_bar = ctk.CTkFrame(self)
        top_bar.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(
            top_bar,
            text="🕵️ Windows Privacy & Debloat Switches",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=15, pady=12)

        ctk.CTkButton(
            top_bar,
            text="🔄 Restart Explorer (Apply UI Changes)",
            fg_color="#D35400",
            hover_color="#A04000",
            font=ctk.CTkFont(weight="bold"),
            command=self.restart_explorer,
        ).pack(side="right", padx=15, pady=12)

        ctk.CTkButton(
            top_bar,
            text="🛡️ Enable All Privacy Shields",
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(weight="bold"),
            command=self.apply_all_shields,
        ).pack(side="right", padx=5, pady=12)

        # ==========================================
        # STATUS BAR
        # ==========================================
        self.status_label = ctk.CTkLabel(
            self,
            text="Toggle any switch below to immediately update your Windows Registry privacy settings.",
            text_color="gray",
        )
        self.status_label.grid(row=1, column=0, pady=(0, 6), sticky="w")

        # ==========================================
        # SCROLLABLE TWEAK CARDS
        # ==========================================
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=2, column=0, sticky="nsew")

        self.build_tweak_cards()
        self.sync_switches_with_registry()

    def build_tweak_cards(self):
        for tweak in self.tweaks:
            t_id, title, desc, hive, path, val_name, on_val, off_val, needs_admin = tweak

            card = ctk.CTkFrame(self.scroll)
            card.pack(fill="x", padx=5, pady=5)

            text_box = ctk.CTkFrame(card, fg_color="transparent")
            text_box.pack(side="left", fill="x", expand=True, padx=15, pady=10)

            ctk.CTkLabel(
                text_box,
                text=title,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#3B8ED0",
            ).pack(anchor="w")

            ctk.CTkLabel(
                text_box,
                text=desc,
                font=ctk.CTkFont(size=11),
                text_color="lightgray",
                wraplength=600,
                justify="left",
            ).pack(anchor="w", pady=(2, 0))

            var = ctk.BooleanVar(value=False)
            self.switch_vars[t_id] = var

            switch = ctk.CTkSwitch(
                card,
                text="Protected",
                variable=var,
                progress_color="#2FA572",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda t=tweak: self.on_switch_toggled(t),
            )
            switch.pack(side="right", padx=20, pady=10)

    def sync_switches_with_registry(self):
        """Reads current Windows Registry values so switches reflect live system state."""
        for tweak in self.tweaks:
            t_id, _, _, hive, path, val_name, on_val, _, _ = tweak
            current_val = self.read_reg_dword(hive, path, val_name)
            is_protected = current_val == on_val
            self.switch_vars[t_id].set(is_protected)

    @staticmethod
    def read_reg_dword(hive, path: str, val_name: str):
        try:
            with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, val_name)
                return val
        except OSError:
            return None

    @staticmethod
    def write_reg_dword(hive, path: str, val_name: str, value: int) -> tuple[bool, str]:
        try:
            with winreg.CreateKeyEx(hive, path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, val_name, 0, winreg.REG_DWORD, int(value))
            return True, "Successfully updated Registry."
        except PermissionError:
            return False, "Access Denied (Run app as Administrator for this setting)."
        except OSError as e:
            return False, f"Registry error: {e}"

    def on_switch_toggled(self, tweak: tuple):
        t_id, title, _, hive, path, val_name, on_val, off_val, needs_admin = tweak
        target_state = self.switch_vars[t_id].get()

        if needs_admin and not SystemEngine.is_admin():
            self.switch_vars[t_id].set(not target_state)
            self.status_label.configure(
                text=f"⚠️ '{title}' requires Administrator privileges.", text_color="#E74C3C"
            )
            return

        new_reg_val = on_val if target_state else off_val
        ok, msg = self.write_reg_dword(hive, path, val_name, new_reg_val)

        if ok:
            state_str = "ENABLED (Protected)" if target_state else "RESTORED to Windows Default"
            self.status_label.configure(text=f"✅ {title}: {state_str}", text_color="#2FA572")
        else:
            self.switch_vars[t_id].set(not target_state)
            self.status_label.configure(text=f"❌ {msg}", text_color="#E74C3C")

    def apply_all_shields(self):
        applied = 0
        for tweak in self.tweaks:
            t_id, _, _, hive, path, val_name, on_val, _, needs_admin = tweak
            if needs_admin and not SystemEngine.is_admin():
                continue
            ok, _ = self.write_reg_dword(hive, path, val_name, on_val)
            if ok:
                self.switch_vars[t_id].set(True)
                applied += 1

        self.status_label.configure(
            text=f"🛡️ Enabled {applied} privacy shields! Click 'Restart Explorer' for Start Menu changes to take effect.",
            text_color="#2FA572",
        )

    def restart_explorer(self):
        """Restarts explorer.exe so Start Menu and Taskbar registry tweaks apply immediately."""
        try:
            subprocess.run(
                ["taskkill", "/f", "/im", "explorer.exe"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )
            subprocess.Popen(["explorer.exe"])
            self.status_label.configure(
                text="🔄 Windows Explorer restarted! Start Menu & Taskbar tweaks are now live.",
                text_color="#3B8ED0",
            )
        except Exception as e:
            self.status_label.configure(text=f"Could not restart Explorer: {e}", text_color="#E74C3C")