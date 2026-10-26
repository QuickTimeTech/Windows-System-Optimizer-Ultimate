# win11_ui_customizer.py
import winreg
import subprocess
import customtkinter as ctk


class Win11UiCustomizerView(ctk.CTkFrame):
    """Modular Windows 10/11 Explorer, Start Menu & Raw Gaming Input Customizer."""

    EXPLORER_ADV_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
    EXPLORER_POL_KEY = r"Software\Policies\Microsoft\Windows\Explorer"
    MOUSE_KEY = r"Control Panel\Mouse"
    STICKY_KEY = r"Control Panel\Accessibility\StickyKeys"

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Switch Variables
        self.var_raw_mouse = ctk.BooleanVar(value=False)
        self.var_no_sticky = ctk.BooleanVar(value=False)
        self.var_show_ext = ctk.BooleanVar(value=False)
        self.var_show_hidden = ctk.BooleanVar(value=False)
        self.var_launch_thispc = ctk.BooleanVar(value=False)
        self.var_no_bing = ctk.BooleanVar(value=False)

        # ==========================================
        # CARD 1: GAMING INPUT & ACCESSIBILITY TWEAKS
        # ==========================================
        input_card = ctk.CTkFrame(self)
        input_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            input_card,
            text="🎯 GAMING INPUT & KEYBOARD TWEAKS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2FA572",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            input_card,
            text="Eliminates Windows pointer acceleration curve and accidental key popups.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 10))

        self._create_tweak_row(
            input_card,
            "Disable Mouse Acceleration (Raw 1:1 Gaming Aim)",
            "Turns off 'Enhance Pointer Precision' in Control Panel\\Mouse.",
            self.var_raw_mouse,
            self.toggle_raw_mouse,
        )

        self._create_tweak_row(
            input_card,
            "Disable 'Sticky Keys' Shift-Spam Popup",
            "Stops Windows from minimizing games when pressing Shift 5 times.",
            self.var_no_sticky,
            self.toggle_sticky_keys,
        )

        btn_preset_row = ctk.CTkFrame(input_card, fg_color="transparent")
        btn_preset_row.pack(fill="x", padx=15, pady=(14, 14))

        ctk.CTkButton(
            btn_preset_row,
            text="⚡ Apply All Recommended Pro Tweaks",
            height=34,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(weight="bold"),
            command=self.apply_all_pro_tweaks,
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        ctk.CTkButton(
            btn_preset_row,
            text="🔄 Restart Explorer",
            width=140,
            height=34,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(weight="bold"),
            command=self.restart_explorer,
        ).pack(side="right", padx=(4, 0))

        # ==========================================
        # CARD 2: FILE EXPLORER & START MENU TWEAKS
        # ==========================================
        exp_card = ctk.CTkFrame(self)
        exp_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            exp_card,
            text="📁 FILE EXPLORER & START MENU CUSTOMIZER",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            exp_card,
            text="Unlocks hidden file extensions, system folders, and fast local Start search.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 10))

        self._create_tweak_row(
            exp_card,
            "Always Show File Extensions (.exe, .dll, .txt)",
            "Prevents malware from disguising executable files as PDFs or images.",
            self.var_show_ext,
            self.toggle_file_extensions,
        )

        self._create_tweak_row(
            exp_card,
            "Show Hidden Files & Folders (AppData, ProgramData)",
            "Makes hidden system and configuration directories visible in Explorer.",
            self.var_show_hidden,
            self.toggle_hidden_files,
        )

        self._create_tweak_row(
            exp_card,
            "Open File Explorer to 'This PC' Instead of 'Home'",
            "Skips the recent files view and opens directly to your hard drives.",
            self.var_launch_thispc,
            self.toggle_launch_to_thispc,
        )

        self._create_tweak_row(
            exp_card,
            "Disable Bing Web Search in Windows Start Menu",
            "Makes Start Menu search 100% local and instant (Restart Explorer to apply).",
            self.var_no_bing,
            self.toggle_disable_bing,
        )

        # ==========================================
        # STATUS & REGISTRY CHANGE LOG
        # ==========================================
        self.status_lbl = ctk.CTkLabel(
            self,
            text="All switches are synced with your live Windows Registry.",
            text_color="#2FA572",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.status_lbl.grid(row=1, column=0, columnspan=2, pady=(0, 4), sticky="w")

        self.log_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.log_message("Windows Input & Explorer Customizer Ready. Reading current registry states...")

        self.sync_from_registry()

    def _create_tweak_row(self, parent, title: str, subtitle: str, var: ctk.BooleanVar, cmd):
        row = ctk.CTkFrame(parent, fg_color=("gray85", "gray17"))
        row.pack(fill="x", padx=15, pady=4)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=12, pady=6)

        ctk.CTkLabel(left, text=title, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left, text=subtitle, font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w")

        sw = ctk.CTkSwitch(
            row,
            text="",
            width=46,
            variable=var,
            progress_color="#2FA572",
            command=cmd,
        )
        sw.pack(side="right", padx=12, pady=6)

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ==========================================
    # REGISTRY SYNC & HANDLERS
    # ==========================================
    def sync_from_registry(self):
        # 1. Mouse Acceleration
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.MOUSE_KEY, 0, winreg.KEY_READ) as k:
                mspeed, _ = winreg.QueryValueEx(k, "MouseSpeed")
                self.var_raw_mouse.set(str(mspeed) == "0")
        except OSError:
            pass

        # 2. Sticky Keys
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.STICKY_KEY, 0, winreg.KEY_READ) as k:
                flags, _ = winreg.QueryValueEx(k, "Flags")
                self.var_no_sticky.set(str(flags) in ("506", "26"))
        except OSError:
            pass

        # 3. Explorer Advanced (Extensions, Hidden, LaunchTo)
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.EXPLORER_ADV_KEY, 0, winreg.KEY_READ) as k:
                try:
                    hide_ext, _ = winreg.QueryValueEx(k, "HideFileExt")
                    self.var_show_ext.set(int(hide_ext) == 0)
                except OSError:
                    pass
                try:
                    hidden, _ = winreg.QueryValueEx(k, "Hidden")
                    self.var_show_hidden.set(int(hidden) == 1)
                except OSError:
                    pass
                try:
                    launch_to, _ = winreg.QueryValueEx(k, "LaunchTo")
                    self.var_launch_thispc.set(int(launch_to) == 1)
                except OSError:
                    pass
        except OSError:
            pass

        # 4. Bing Start Menu Search
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.EXPLORER_POL_KEY, 0, winreg.KEY_READ) as k:
                no_bing, _ = winreg.QueryValueEx(k, "DisableSearchBoxSuggestions")
                self.var_no_bing.set(int(no_bing) == 1)
        except OSError:
            self.var_no_bing.set(False)

    def toggle_raw_mouse(self):
        raw = self.var_raw_mouse.get()
        try:
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, self.MOUSE_KEY, 0, winreg.KEY_SET_VALUE) as k:
                if raw:
                    winreg.SetValueEx(k, "MouseSpeed", 0, winreg.REG_SZ, "0")
                    winreg.SetValueEx(k, "MouseThreshold1", 0, winreg.REG_SZ, "0")
                    winreg.SetValueEx(k, "MouseThreshold2", 0, winreg.REG_SZ, "0")
                    self.log_message("[+] Enabled Raw 1:1 Mouse Input (MouseSpeed=0, Thresholds=0).")
                else:
                    winreg.SetValueEx(k, "MouseSpeed", 0, winreg.REG_SZ, "1")
                    winreg.SetValueEx(k, "MouseThreshold1", 0, winreg.REG_SZ, "6")
                    winreg.SetValueEx(k, "MouseThreshold2", 0, winreg.REG_SZ, "10")
                    self.log_message("[-] Restored default Windows Pointer Precision curve.")
        except Exception as e:
            self.log_message(f"[!] Error setting mouse registry: {e}")

    def toggle_sticky_keys(self):
        disable_popup = self.var_no_sticky.get()
        try:
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, self.STICKY_KEY, 0, winreg.KEY_SET_VALUE) as k:
                val = "506" if disable_popup else "510"
                winreg.SetValueEx(k, "Flags", 0, winreg.REG_SZ, val)
                self.log_message(
                    f"[+] Set StickyKeys Flags = {val} ({'Popup Disabled' if disable_popup else 'Default Popup Enabled'})."
                )
        except Exception as e:
            self.log_message(f"[!] Error setting StickyKeys registry: {e}")

    def toggle_file_extensions(self):
        show = self.var_show_ext.get()
        try:
            with winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER, self.EXPLORER_ADV_KEY, 0, winreg.KEY_SET_VALUE
            ) as k:
                winreg.SetValueEx(k, "HideFileExt", 0, winreg.REG_DWORD, 0 if show else 1)
                self.log_message(
                    f"[+] File Extensions: {'VISIBLE (HideFileExt=0)' if show else 'HIDDEN (HideFileExt=1)'}."
                )
        except Exception as e:
            self.log_message(f"[!] Error updating HideFileExt: {e}")

    def toggle_hidden_files(self):
        show = self.var_show_hidden.get()
        try:
            with winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER, self.EXPLORER_ADV_KEY, 0, winreg.KEY_SET_VALUE
            ) as k:
                winreg.SetValueEx(k, "Hidden", 0, winreg.REG_DWORD, 1 if show else 2)
                self.log_message(
                    f"[+] Hidden Files & Folders: {'VISIBLE (Hidden=1)' if show else 'HIDDEN (Hidden=2)'}."
                )
        except Exception as e:
            self.log_message(f"[!] Error updating Hidden files setting: {e}")

    def toggle_launch_to_thispc(self):
        this_pc = self.var_launch_thispc.get()
        try:
            with winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER, self.EXPLORER_ADV_KEY, 0, winreg.KEY_SET_VALUE
            ) as k:
                winreg.SetValueEx(k, "LaunchTo", 0, winreg.REG_DWORD, 1 if this_pc else 2)
                self.log_message(
                    f"[+] Explorer Default Startup View: {'This PC (Drives)' if this_pc else 'Quick Access / Home'}."
                )
        except Exception as e:
            self.log_message(f"[!] Error updating LaunchTo setting: {e}")

    def toggle_disable_bing(self):
        no_bing = self.var_no_bing.get()
        try:
            with winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER, self.EXPLORER_POL_KEY, 0, winreg.KEY_SET_VALUE
            ) as k:
                winreg.SetValueEx(k, "DisableSearchBoxSuggestions", 0, winreg.REG_DWORD, 1 if no_bing else 0)
                self.log_message(
                    f"[+] Start Menu Bing Web Search: {'DISABLED (Local Search Only)' if no_bing else 'ENABLED'}."
                )
        except Exception as e:
            self.log_message(f"[!] Error updating Start Menu Bing policy: {e}")

    def apply_all_pro_tweaks(self):
        self.var_raw_mouse.set(True)
        self.toggle_raw_mouse()
        self.var_no_sticky.set(True)
        self.toggle_sticky_keys()
        self.var_show_ext.set(True)
        self.toggle_file_extensions()
        self.var_show_hidden.set(True)
        self.toggle_hidden_files()
        self.var_launch_thispc.set(True)
        self.toggle_launch_to_thispc()
        self.var_no_bing.set(True)
        self.toggle_disable_bing()
        self.log_message("=== Applied All 6 Recommended Pro Gamer & Power-User Tweaks! ===")

    def restart_explorer(self):
        try:
            subprocess.run(
                ["taskkill", "/f", "/im", "explorer.exe"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )
            subprocess.Popen(["explorer.exe"])
            self.log_message("[🔄] Restarted Windows Explorer shell to apply UI changes immediately.")
        except Exception as e:
            self.log_message(f"[!] Could not restart Explorer: {e}")