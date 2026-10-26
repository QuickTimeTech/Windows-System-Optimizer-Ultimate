# winget_app_installer.py
import shutil
import threading
import subprocess
import customtkinter as ctk


class WingetAppInstallerView(ctk.CTkFrame):
    """Modular 1-Click Bulk Software Installer & Smart Updater (via Windows Winget)."""

    APP_CATALOG = {
        "🌐 Web Browsers & Communication": [
            ("Google Chrome", "Google.Chrome", "Fast, standard web browser"),
            ("Brave Privacy Browser", "Brave.Brave", "Built-in ad & tracker blocker"),
            ("Mozilla Firefox", "Mozilla.Firefox", "Open-source privacy browser"),
            ("Discord", "Discord.Discord", "Voice, video & gaming chat"),
            ("Zoom Workplace", "Zoom.Zoom", "Video meetings & screen sharing"),
        ],
        "🛠️ Essential Utilities & File Tools": [
            ("7-Zip Archiver", "7zip.7zip", "Essential .zip, .7z, and .rar extractor"),
            ("Notepad++", "Notepad++.Notepad++", "Fast code & text editor"),
            ("Everything Search", "voidtools.Everything", "Instant NTFS filename search engine"),
            ("Microsoft PowerToys", "Microsoft.PowerToys", "FancyZones, ColorPicker, PowerRename & more"),
            ("ShareX Screen Capture", "ShareX.ShareX", "Advanced screenshot & screen recorder"),
            ("WinDirStat", "WinDirStat.WinDirStat", "Visual disk space treemap analyzer"),
        ],
        "🎮 Gaming & Media": [
            ("VLC Media Player", "VideoLAN.VLC", "Plays any video or audio format"),
            ("Valve Steam", "Valve.Steam", "PC gaming store & library"),
            ("Epic Games Launcher", "EpicGames.EpicGamesLauncher", "Epic Games store & Unreal Engine"),
            ("OBS Studio", "OBSProject.OBSStudio", "Pro video recording & live streaming"),
            ("Spotify Music", "Spotify.Spotify", "Music & podcast streaming"),
            ("Audacity Audio Editor", "Audacity.Audacity", "Multi-track audio editor & recorder"),
        ],
        "🩺 Hardware Diagnostics, Security & Dev": [
            ("HWiNFO64", "REALiX.HWiNFO", "Deep motherboard, CPU & GPU sensor monitor"),
            ("CPUID CPU-Z", "CPUID.CPU-Z", "Processor, motherboard & RAM timings inspector"),
            ("TechPowerUp GPU-Z", "TechPowerUp.GPU-Z", "Graphics card BIOS & sensor utility"),
            ("Malwarebytes Anti-Malware", "Malwarebytes.Malwarebytes", "On-demand malware & spyware scanner"),
            ("Bitwarden Password Manager", "Bitwarden.Bitwarden", "Encrypted open-source password vault"),
            ("Visual Studio Code", "Microsoft.VisualStudioCode", "Lightweight code editor"),
            ("Python 3.12", "Python.Python.3.12", "Python runtime & pip package manager"),
        ],
    }

    TECH_ESSENTIALS_IDS = {
        "7zip.7zip",
        "Notepad++.Notepad++",
        "voidtools.Everything",
        "VideoLAN.VLC",
        "REALiX.HWiNFO",
        "Brave.Brave",
    }

    GAMER_PACK_IDS = {
        "Discord.Discord",
        "Valve.Steam",
        "OBSProject.OBSStudio",
        "7zip.7zip",
        "REALiX.HWiNFO",
        "TechPowerUp.GPU-Z",
    }

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)

        self.has_winget = shutil.which("winget") is not None
        # pkg_id -> {"var": BooleanVar, "name": str, "desc": str, "cb": CTkCheckBox, "badge": CTkLabel, "state": str}
        # state can be: "not_installed", "installed", "updatable"
        self.app_widgets = {}
        self.installing = False
        self.scanning = False
        self.initial_scan_done = False

        # ==========================================
        # TOP HEADER & QUICK PRESET BUNDLES
        # ==========================================
        top_card = ctk.CTkFrame(self)
        top_card.grid(row=0, column=0, pady=(0, 8), sticky="ew")

        row1 = ctk.CTkFrame(top_card, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(12, 6))

        ctk.CTkLabel(
            row1,
            text="📦 1-CLICK BULK SOFTWARE INSTALLER & SMART UPDATER",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(side="left")

        self.scan_status_btn = ctk.CTkButton(
            row1,
            text="🔄 Scan Installed Status",
            width=175,
            height=28,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.scan_installed_apps,
        )
        self.scan_status_btn.pack(side="right")

        row2 = ctk.CTkFrame(top_card, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(2, 12))

        ctk.CTkButton(
            row2,
            text="⚡ Tech Essentials",
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.apply_preset(self.TECH_ESSENTIALS_IDS),
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            row2,
            text="🎮 Gamer Pack",
            height=32,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.apply_preset(self.GAMER_PACK_IDS),
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            row2,
            text="🔄 Select All Updates",
            height=32,
            fg_color="#D35400",
            hover_color="#A04000",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.select_all_updates,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            row2,
            text="🧹 Clear",
            width=80,
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.apply_preset(set()),
        ).pack(side="left", padx=5)

        self.install_btn = ctk.CTkButton(
            row2,
            text="🚀 Install / Update Selected (0)",
            height=34,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.start_bulk_install,
        )
        self.install_btn.pack(side="right")

        # ==========================================
        # PROGRESS BAR
        # ==========================================
        self.progress_bar = ctk.CTkProgressBar(self, height=10, progress_color="#2FA572")
        self.progress_bar.grid(row=1, column=0, pady=(0, 8), sticky="ew")
        self.progress_bar.set(0)

        # ==========================================
        # SCROLLABLE 2-COLUMN APP CATALOG
        # ==========================================
        self.catalog_scroll = ctk.CTkScrollableFrame(self)
        self.catalog_scroll.grid(row=2, column=0, pady=(0, 8), sticky="nsew")
        self.catalog_scroll.grid_columnconfigure((0, 1), weight=1)

        self._build_catalog_cards()

        # ==========================================
        # LIVE INSTALLATION CONSOLE LOG
        # ==========================================
        self.log_box = ctk.CTkTextbox(self, height=130, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=3, column=0, sticky="ew")
        self.log_message(
            "Smart Winget Installer Ready. Scanning your PC to lock already-installed apps & detect available updates..."
        )

        # Automatically scan installed status when created
        self.after(300, self.scan_installed_apps)

    def _build_catalog_cards(self):
        for idx, (category_title, apps) in enumerate(self.APP_CATALOG.items()):
            card = ctk.CTkFrame(self.catalog_scroll)
            card.grid(row=idx // 2, column=idx % 2, padx=6, pady=6, sticky="nsew")

            ctk.CTkLabel(
                card,
                text=category_title,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#3B8ED0",
            ).pack(anchor="w", padx=14, pady=(10, 6))

            for app_name, pkg_id, desc in apps:
                var = ctk.BooleanVar(value=False)

                item_row = ctk.CTkFrame(card, fg_color="transparent")
                item_row.pack(fill="x", padx=14, pady=3)

                cb = ctk.CTkCheckBox(
                    item_row,
                    text=app_name,
                    variable=var,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    command=self.update_button_count,
                )
                cb.pack(side="left")

                badge = ctk.CTkLabel(
                    item_row,
                    text=desc,
                    font=ctk.CTkFont(size=11),
                    text_color="gray",
                )
                badge.pack(side="right")

                self.app_widgets[pkg_id] = {
                    "var": var,
                    "name": app_name,
                    "desc": desc,
                    "cb": cb,
                    "badge": badge,
                    "state": "not_installed",
                }

            ctk.CTkLabel(card, text="", height=4).pack()

    # ==========================================
    # INSTALLED & UPDATE SCANNER (WINGET LIST / UPGRADE)
    # ==========================================
    def scan_installed_apps(self):
        if not self.has_winget or self.scanning or self.installing:
            return

        self.scanning = True
        self.scan_status_btn.configure(state="disabled", text="⏳ Scanning PC...")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        installed_ids = set()
        upgradable_ids = set()

        try:
            # 1. Get all installed packages via winget list
            res_list = subprocess.run(
                ["winget", "list", "--accept-source-agreements"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=25,
            )
            out_list_lower = (res_list.stdout or "").lower()

            # 2. Get all packages with available updates via winget upgrade
            res_upg = subprocess.run(
                ["winget", "upgrade", "--accept-source-agreements"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=25,
            )
            out_upg_lower = (res_upg.stdout or "").lower()

            for pkg_id in self.app_widgets:
                pid_low = pkg_id.lower()
                if pid_low in out_list_lower:
                    installed_ids.add(pkg_id)
                if pid_low in out_upg_lower:
                    upgradable_ids.add(pkg_id)
        except Exception as e:
            self.after(0, lambda err=e: self.log_message(f"[!] Scan note: {err}"))

        self.after(0, lambda: self._apply_scan_results(installed_ids, upgradable_ids))

    def _apply_scan_results(self, installed_ids: set, upgradable_ids: set):
        self.scanning = False
        self.initial_scan_done = True
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(1.0)
        self.scan_status_btn.configure(state="normal", text="🔄 Scan Installed Status")

        installed_count = 0
        update_count = 0

        for pkg_id, item in self.app_widgets.items():
            cb = item["cb"]
            badge = item["badge"]
            var = item["var"]
            name = item["name"]
            desc = item["desc"]

            if pkg_id in upgradable_ids:
                # Installed, but has an update! Keep unlocked & offer update
                update_count += 1
                item["state"] = "updatable"
                cb.configure(
                    state="normal",
                    text=f"{name} (Update Ready)",
                    text_color="#F39C12",
                )
                badge.configure(
                    text="🔄 Update Available!",
                    text_color="#F39C12",
                    font=ctk.CTkFont(size=11, weight="bold"),
                )
            elif pkg_id in installed_ids:
                # Installed and up to date! Lock checkbox so user can't re-check it
                installed_count += 1
                item["state"] = "installed"
                var.set(False)
                cb.configure(
                    state="disabled",
                    text=name,
                    text_color="gray",
                )
                badge.configure(
                    text="✅ Installed (Up to Date)",
                    text_color="#2FA572",
                    font=ctk.CTkFont(size=11, weight="bold"),
                )
            else:
                # Not installed on this PC
                item["state"] = "not_installed"
                cb.configure(
                    state="normal",
                    text=name,
                    text_color=("gray10", "gray90"),
                )
                badge.configure(
                    text=desc,
                    text_color="gray",
                    font=ctk.CTkFont(size=11, weight="normal"),
                )

        self.update_button_count()
        self.log_message(
            f"[+] Scan Complete: {installed_count} app(s) already up-to-date (locked), "
            f"{update_count} app(s) have updates ready!"
        )

    # ==========================================
    # PRESET & SELECTION HELPERS
    # ==========================================
    def apply_preset(self, target_ids: set):
        if self.installing or self.scanning:
            return
        for pkg_id, item in self.app_widgets.items():
            # Never check an app that is locked/already up to date
            if item["state"] == "installed":
                item["var"].set(False)
            else:
                item["var"].set(pkg_id in target_ids)
        self.update_button_count()

    def select_all_updates(self):
        if self.installing or self.scanning:
            return
        count = 0
        for pkg_id, item in self.app_widgets.items():
            if item["state"] == "updatable":
                item["var"].set(True)
                count += 1
            else:
                item["var"].set(False)
        self.update_button_count()
        if count == 0:
            self.log_message("[i] All installed catalog apps are already up to date!")
        else:
            self.log_message(f"[+] Selected {count} outdated app(s) for silent upgrading.")

    def update_button_count(self):
        install_cnt = 0
        update_cnt = 0
        for item in self.app_widgets.values():
            if item["var"].get():
                if item["state"] == "updatable":
                    update_cnt += 1
                else:
                    install_cnt += 1

        total = install_cnt + update_cnt
        if update_cnt > 0 and install_cnt > 0:
            lbl = f"🚀 Install ({install_cnt}) & Update ({update_cnt})"
        elif update_cnt > 0:
            lbl = f"🔄 Update Selected Apps ({update_cnt})"
        else:
            lbl = f"🚀 Install Selected Apps ({total})"

        self.install_btn.configure(text=lbl)

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ==========================================
    # BULK INSTALL & UPGRADE WORKER
    # ==========================================
    def start_bulk_install(self):
        if not self.has_winget:
            self.log_message("[!] Error: Microsoft Winget is not installed on this Windows build.")
            return

        selected_items = [
            (pkg_id, item["name"], item["state"])
            for pkg_id, item in self.app_widgets.items()
            if item["var"].get() and item["state"] != "installed"
        ]
        if not selected_items:
            self.log_message("[!] Please check at least one uninstalled or updatable application first.")
            return

        self.installing = True
        self.install_btn.configure(state="disabled", text="⏳ Working...")
        self.scan_status_btn.configure(state="disabled")
        self.progress_bar.set(0)

        threading.Thread(target=self._install_worker, args=(selected_items,), daemon=True).start()

    def _install_worker(self, items: list[tuple[str, str, str]]):
        total = len(items)
        self.after(
            0,
            lambda: self.log_message(
                f"\n=== Starting Silent Winget Operation for {total} Application(s) ==="
            ),
        )

        success_count = 0
        for idx, (pkg_id, app_name, state) in enumerate(items, start=1):
            action_cmd = "upgrade" if state == "updatable" else "install"
            action_label = "Updating" if state == "updatable" else "Installing"

            self.after(
                0,
                lambda i=idx, t=total, act=action_label, n=app_name, p=pkg_id: self.log_message(
                    f"[{i}/{t}] {act} {n} ({p})..."
                ),
            )
            try:
                res = subprocess.run(
                    [
                        "winget",
                        action_cmd,
                        "--id",
                        pkg_id,
                        "-e",
                        "--silent",
                        "--accept-package-agreements",
                        "--accept-source-agreements",
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                out_lower = (res.stdout or "").lower()
                if (
                    res.returncode == 0
                    or "successfully installed" in out_lower
                    or "already installed" in out_lower
                    or "no applicable upgrade" in out_lower
                ):
                    success_count += 1
                    done_word = "Updated" if state == "updatable" else "Installed"
                    self.after(0, lambda dw=done_word, n=app_name: self.log_message(f"  ✅ {dw} {n} successfully!"))
                else:
                    lines = (res.stdout or res.stderr or "Installer exited").strip().splitlines()
                    err_snippet = lines[-1] if lines else "Finished"
                    self.after(
                        0,
                        lambda n=app_name, e=err_snippet: self.log_message(
                            f"  ⚠️ {n} note: {e[:90]}"
                        ),
                    )
            except Exception as e:
                self.after(0, lambda n=app_name, err=e: self.log_message(f"  ❌ Failed on {n}: {err}"))

            prog = idx / total
            self.after(0, lambda pr=prog: self.progress_bar.set(pr))

        self.installing = False
        self.after(
            0,
            lambda: (
                self.log_message(
                    f"=== Operation Complete! ({success_count}/{total} apps processed). Re-scanning status... ==="
                ),
                self.install_btn.configure(state="normal"),
                self.scan_installed_apps(),
            ),
        )