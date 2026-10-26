# app_uninstaller.py
import threading
import subprocess
import winreg
import customtkinter as ctk


class AppUninstallerView(ctk.CTkFrame):
    """Modular Installed Programs & Bloatware Uninstaller with live search filter."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.all_apps = []  # Stores dicts of installed applications

        # ==========================================
        # TOP SEARCH & REFRESH BAR
        # ==========================================
        top_bar = ctk.CTkFrame(self)
        top_bar.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(
            top_bar, text="🔎 Search Apps:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(15, 8), pady=12)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.filter_apps())

        self.search_entry = ctk.CTkEntry(
            top_bar,
            width=320,
            placeholder_text="Type app name or publisher (e.g. Chrome, Adobe, Microsoft)...",
            textvariable=self.search_var,
        )
        self.search_entry.pack(side="left", padx=5, pady=12, fill="x", expand=True)

        self.refresh_btn = ctk.CTkButton(
            top_bar,
            text="🔄 Scan Installed Apps",
            width=160,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.load_installed_apps,
        )
        self.refresh_btn.pack(side="right", padx=15, pady=12)

        # ==========================================
        # STATUS BAR
        # ==========================================
        self.status_label = ctk.CTkLabel(
            self,
            text="Click 'Scan Installed Apps' or switch to this tab to list programs.",
            text_color="gray",
        )
        self.status_label.grid(row=1, column=0, pady=(0, 6), sticky="w")

        # ==========================================
        # SCROLLABLE APP LIST
        # ==========================================
        self.apps_scroll = ctk.CTkScrollableFrame(self)
        self.apps_scroll.grid(row=2, column=0, sticky="nsew")

    def load_installed_apps(self):
        self.refresh_btn.configure(state="disabled", text="Scanning...")
        self.status_label.configure(text="Reading Windows Registry Uninstall keys...", text_color="#3B8ED0")
        threading.Thread(target=self._scan_registry_worker, daemon=True).start()

    def _scan_registry_worker(self):
        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        seen_names = set()
        apps = []

        for hive, path in reg_paths:
            try:
                with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as key:
                    subkey_count = winreg.QueryInfoKey(key)[0]
                    for i in range(subkey_count):
                        try:
                            sub_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, sub_name) as subkey:
                                name = self._get_reg_val(subkey, "DisplayName")
                                uninstall_cmd = self._get_reg_val(subkey, "UninstallString")
                                sys_component = self._get_reg_val(subkey, "SystemComponent")

                                if not name or not uninstall_cmd or sys_component == 1:
                                    continue

                                name_clean = str(name).strip()
                                if name_clean.lower() in seen_names:
                                    continue
                                seen_names.add(name_clean.lower())

                                version = str(self._get_reg_val(subkey, "DisplayVersion") or "Unknown")
                                publisher = str(self._get_reg_val(subkey, "Publisher") or "Unknown Publisher")

                                apps.append(
                                    {
                                        "name": name_clean,
                                        "version": version,
                                        "publisher": publisher,
                                        "uninstall": str(uninstall_cmd).strip(),
                                    }
                                )
                        except OSError:
                            continue
            except OSError:
                continue

        apps.sort(key=lambda x: x["name"].lower())
        self.all_apps = apps
        self.after(0, self._finish_load)

    @staticmethod
    def _get_reg_val(key, val_name):
        try:
            val, _ = winreg.QueryValueEx(key, val_name)
            return val
        except OSError:
            return None

    def _finish_load(self):
        self.refresh_btn.configure(state="normal", text="🔄 Scan Installed Apps")
        self.filter_apps()

    def filter_apps(self):
        for widget in self.apps_scroll.winfo_children():
            widget.destroy()

        query = self.search_var.get().strip().lower()
        filtered = [
            app
            for app in self.all_apps
            if query in app["name"].lower() or query in app["publisher"].lower()
        ]

        # Cap rendered widgets at 75 so scrolling stays buttery smooth
        display_list = filtered[:75]
        self.status_label.configure(
            text=f"Found {len(filtered)} matching programs (Showing top {len(display_list)}).",
            text_color="#2FA572",
        )

        for app in display_list:
            card = ctk.CTkFrame(self.apps_scroll)
            card.pack(fill="x", padx=5, pady=4)

            info_box = ctk.CTkFrame(card, fg_color="transparent")
            info_box.pack(side="left", fill="x", expand=True, padx=12, pady=8)

            ctk.CTkLabel(
                info_box,
                text=f"{app['name']}   (v{app['version']})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#3B8ED0",
            ).pack(anchor="w")

            ctk.CTkLabel(
                info_box,
                text=f"Publisher: {app['publisher']}",
                font=ctk.CTkFont(size=11),
                text_color="gray",
            ).pack(anchor="w")

            ctk.CTkButton(
                card,
                text="🗑️ Uninstall",
                width=105,
                height=30,
                fg_color="#C0392B",
                hover_color="#922B21",
                font=ctk.CTkFont(weight="bold"),
                command=lambda cmd=app["uninstall"], n=app["name"]: self.run_uninstaller(cmd, n),
            ).pack(side="right", padx=12, pady=8)

    def run_uninstaller(self, uninstall_cmd: str, app_name: str):
        try:
            subprocess.Popen(uninstall_cmd, shell=True)
            self.status_label.configure(
                text=f"Launched uninstaller for: {app_name}", text_color="#E67E22"
            )
        except Exception as e:
            self.status_label.configure(
                text=f"Failed to launch uninstaller for {app_name}: {e}", text_color="#E74C3C"
            )