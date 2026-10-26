# display_monitor_tester.py
import math
import json
import ctypes
import threading
import subprocess
import customtkinter as ctk


class DisplayMonitorTesterView(ctk.CTkFrame):
    """Modular Monitor EDID Firmware Inspector, Dead-Pixel/OLED Tester & Calibration Center."""

    # Standard 3-Letter PnP EDID Manufacturer IDs
    PNP_VENDORS = {
        "ACI": "ASUS (ASUSTeK Computer Inc.)",
        "AUS": "ASUS (ASUSTeK Computer Inc.)",
        "AUO": "AU Optronics (Laptop/Gaming Panel)",
        "BOE": "BOE Technology (OLED/IPS Panel)",
        "CMN": "Innolux / Chimei (Display Panel)",
        "CSO": "China Star Optoelectronics (CSOT)",
        "DEL": "Dell Inc.",
        "ENC": "Eizo Nanao Corporation",
        "GSM": "LG Electronics (GoldStar)",
        "LGD": "LG Display (OLED/IPS Panel)",
        "HWP": "HP (Hewlett-Packard)",
        "LEN": "Lenovo Group Limited",
        "MSI": "MSI (Micro-Star International)",
        "PHL": "Philips Consumer Electronics",
        "SAM": "Samsung Electric Company",
        "SDC": "Samsung Display Corp (QD-OLED/AMOLED)",
        "SHP": "Sharp Corporation (IGZO Panel)",
        "SNY": "Sony Corporation",
        "VSC": "ViewSonic Corporation",
        "ACR": "Acer Technologies",
        "BNQ": "BenQ Corporation (ZOWIE)",
        "GBT": "Gigabyte Technology",
    }

    # VideoOutputTechnology mapping from WmiMonitorConnectionParams
    OUTPUT_TECH = {
        -2: "Uninitialized",
        -1: "Other / Unknown",
        0: "VGA (HD15 Analog)",
        4: "DVI (Digital)",
        5: "HDMI",
        10: "DisplayPort (External)",
        11: "Embedded DisplayPort (eDP Internal Laptop Panel)",
        2147483648: "Internal Laptop Display Connection",
    }

    TEST_COLORS = [
        ("#000000", "#FFFFFF", "1/9: PURE BLACK — Inspect for glowing stuck sub-pixels or IPS backlight bleed"),
        ("#FFFFFF", "#000000", "2/9: PURE WHITE — Inspect for dark dead pixels, dust, or color tinting"),
        ("#FF0000", "#FFFFFF", "3/9: PURE RED — Inspect for dead/dark Red sub-pixels or stuck Green/Blue"),
        ("#00FF00", "#000000", "4/9: PURE GREEN — Inspect for dead/dark Green sub-pixels or stuck Red/Blue"),
        ("#0000FF", "#FFFFFF", "5/9: PURE BLUE — Inspect for dead/dark Blue sub-pixels or stuck Red/Green"),
        ("#00FFFF", "#000000", "6/9: CYAN (Green + Blue) — Inspect secondary sub-pixel saturation"),
        ("#FF00FF", "#FFFFFF", "7/9: MAGENTA (Red + Blue) — Inspect secondary sub-pixel saturation"),
        ("#FFFF00", "#000000", "8/9: YELLOW (Red + Green) — Inspect secondary sub-pixel saturation"),
        ("#222222", "#FFFFFF", "9/9: DARK GRAY (12%) — Inspect for OLED vertical banding or dirty screen effect"),
    ]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)

        self.tester_win = None
        self.color_idx = 0
        self.hint_lbl = None
        self.var_show_hint = ctk.BooleanVar(value=True)

        # ==========================================
        # CARD 1: DEAD-PIXEL & OLED UNIFORMITY TESTER
        # ==========================================
        pixel_card = ctk.CTkFrame(self)
        pixel_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 8), sticky="nsew")

        ctk.CTkLabel(
            pixel_card,
            text="🖥 FULLSCREEN DEAD-PIXEL & OLED UNIFORMITY TESTER",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2FA572",
        ).pack(anchor="w", padx=15, pady=(12, 2))

        ctk.CTkLabel(
            pixel_card,
            text="Cycles 9 pure solid colors across your screen to spot dead pixels, stuck sub-pixels & banding.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 8))

        ctk.CTkButton(
            pixel_card,
            text="🚀 Launch Fullscreen Dead-Pixel & OLED Tester",
            height=38,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.launch_pixel_tester(0),
        ).pack(fill="x", padx=15, pady=4)

        # Quick-launch specific color buttons
        quick_row = ctk.CTkFrame(pixel_card, fg_color="transparent")
        quick_row.pack(fill="x", padx=15, pady=6)

        for idx, (hex_col, txt_col, short_lbl) in [
            (0, ("#111111", "#FFFFFF", "⬛ Black")),
            (1, ("#EAEAEA", "#000000", "⬜ White")),
            (2, ("#C0392B", "#FFFFFF", "🟥 Red")),
            (3, ("#27AE60", "#FFFFFF", "🟩 Green")),
            (4, ("#2980B9", "#FFFFFF", "🟦 Blue")),
            (8, ("#34495E", "#FFFFFF", "🌫 OLED Gray")),
        ]:
            ctk.CTkButton(
                quick_row,
                text=short_lbl,
                height=28,
                fg_color=hex_col,
                text_color=txt_col,
                hover_color="#555555",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda i=idx: self.launch_pixel_tester(i),
            ).pack(side="left", expand=True, fill="x", padx=2)

        ctk.CTkCheckBox(
            pixel_card,
            text="Show brief instruction banner when switching colors (auto-hides after 2.5s)",
            variable=self.var_show_hint,
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=15, pady=(4, 12))

        # ==========================================
        # CARD 2: WINDOWS HDR, COLOR & CLEARTYPE TOOLS
        # ==========================================
        cal_card = ctk.CTkFrame(self)
        cal_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 8), sticky="nsew")

        ctk.CTkLabel(
            cal_card,
            text="🎨 WINDOWS DISPLAY, HDR & COLOR CALIBRATION",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w", padx=15, pady=(12, 2))

        ctk.CTkLabel(
            cal_card,
            text="Direct 1-click launchers for Windows hardware color profiles, HDR, and font rendering.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=15, pady=(0, 8))

        btn_grid = ctk.CTkFrame(cal_card, fg_color="transparent")
        btn_grid.pack(fill="x", padx=15, pady=4)
        btn_grid.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_grid,
            text="✨ Windows HDR Settings",
            height=32,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._open_tool("ms-settings:display-advancedgraphics", "Windows Advanced Display / HDR"),
        ).grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        ctk.CTkButton(
            btn_grid,
            text="⚡ Refresh Rate (Hz) Settings",
            height=32,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._open_tool("ms-settings:display-advanced", "Windows Advanced Display & Hz"),
        ).grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        ctk.CTkButton(
            btn_grid,
            text="🔤 ClearType Text Tuner",
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._run_exe("cttune.exe", "ClearType Text Tuner"),
        ).grid(row=1, column=0, padx=4, pady=4, sticky="ew")

        ctk.CTkButton(
            btn_grid,
            text="🎯 Display Color Wizard",
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._run_exe("dccw.exe", "Display Color Calibration Wizard"),
        ).grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        ctk.CTkButton(
            btn_grid,
            text="🌈 ICC Color Profiles (colorcpl)",
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._run_exe("colorcpl.exe", "Windows ICC Color Management"),
        ).grid(row=2, column=0, padx=4, pady=4, sticky="ew")

        ctk.CTkButton(
            btn_grid,
            text="🔄 Rescan Monitor EDID Info",
            height=32,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.scan_monitors_edid,
        ).grid(row=2, column=1, padx=4, pady=4, sticky="ew")

        # ==========================================
        # PROGRESS BAR
        # ==========================================
        self.progress = ctk.CTkProgressBar(self, height=10, progress_color="#3B8ED0")
        self.progress.grid(row=1, column=0, columnspan=2, pady=(0, 8), sticky="ew")
        self.progress.set(0)

        # ==========================================
        # MONITOR EDID HARDWARE CARDS
        # ==========================================
        self.mon_scroll = ctk.CTkScrollableFrame(self)
        self.mon_scroll.grid(row=2, column=0, columnspan=2, pady=(0, 8), sticky="nsew")
        self.mon_scroll.grid_columnconfigure((0, 1), weight=1)

        # ==========================================
        # CONSOLE LOG
        # ==========================================
        self.log_box = ctk.CTkTextbox(self, height=115, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.log_message(
            "Display, Monitor EDID & Dead-Pixel Inspector Ready.\n"
            "• Click '🚀 Launch Fullscreen Dead-Pixel & OLED Tester' to inspect your screen.\n"
            "• Left-Click or press SPACE / RIGHT ARROW to cycle colors. Press ESC or Right-Click to exit."
        )

        self.after(250, self.scan_monitors_edid)

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _open_tool(self, uri: str, label: str):
        try:
            subprocess.Popen(["cmd", "/c", "start", "", uri], creationflags=subprocess.CREATE_NO_WINDOW)
            self.log_message(f"[+] Opened {label}.")
        except Exception as e:
            self.log_message(f"[!] Could not open {label}: {e}")

    def _run_exe(self, exe_name: str, label: str):
        try:
            subprocess.Popen([exe_name])
            self.log_message(f"[+] Launched {label} ({exe_name}).")
        except Exception as e:
            self.log_message(f"[!] Could not launch {exe_name}: {e}")

    # ==========================================
    # FULLSCREEN DEAD-PIXEL & UNIFORMITY TESTER
    # ==========================================
    def launch_pixel_tester(self, start_index: int = 0):
        if self.tester_win is not None and self.tester_win.winfo_exists():
            self.tester_win.destroy()

        self.color_idx = start_index % len(self.TEST_COLORS)
        self.tester_win = ctk.CTkToplevel(self)
        self.tester_win.title("Fullscreen Dead-Pixel Tester")
        self.tester_win.attributes("-topmost", True)
        self.tester_win.overrideredirect(True)

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.tester_win.geometry(f"{sw}x{sh}+0+0")
        self.tester_win.focus_force()

        # Hide mouse cursor after 1 second or keep clean
        self.tester_win.config(cursor="crosshair")

        self.hint_lbl = ctk.CTkLabel(
            self.tester_win,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            corner_radius=8,
            padx=18,
            pady=10,
        )

        # Bind mouse & keyboard controls
        self.tester_win.bind("<Button-1>", lambda _: self._step_color(1))
        self.tester_win.bind("<Button-3>", lambda _: self.close_pixel_tester())
        self.tester_win.bind("<space>", lambda _: self._step_color(1))
        self.tester_win.bind("<Right>", lambda _: self._step_color(1))
        self.tester_win.bind("<Left>", lambda _: self._step_color(-1))
        self.tester_win.bind("<Escape>", lambda _: self.close_pixel_tester())

        self._apply_current_test_color()

    def _step_color(self, delta: int):
        self.color_idx = (self.color_idx + delta) % len(self.TEST_COLORS)
        self._apply_current_test_color()

    def _apply_current_test_color(self):
        if self.tester_win is None or not self.tester_win.winfo_exists():
            return

        bg_hex, fg_hex, desc = self.TEST_COLORS[self.color_idx]
        self.tester_win.configure(fg_color=bg_hex)

        if self.var_show_hint.get() and self.hint_lbl is not None:
            self.hint_lbl.configure(
                text=f"{desc}\n[Left-Click / Space: Next Color  •  Left Arrow: Previous  •  Right-Click / ESC: Exit]",
                fg_color="#0F172A",
                text_color="#F8FAFC",
            )
            self.hint_lbl.place(relx=0.5, rely=0.06, anchor="center")
            self.tester_win.after(2400, self._hide_hint_banner)

    def _hide_hint_banner(self):
        if self.hint_lbl is not None and self.hint_lbl.winfo_exists():
            self.hint_lbl.place_forget()

    def close_pixel_tester(self):
        if self.tester_win is not None and self.tester_win.winfo_exists():
            self.tester_win.destroy()
        self.tester_win = None

    # ==========================================
    # RAW WMI MONITOR EDID FIRMWARE SCANNER
    # ==========================================
    def scan_monitors_edid(self):
        for w in self.mon_scroll.winfo_children():
            w.destroy()

        self.progress.configure(mode="indeterminate")
        self.progress.start()
        threading.Thread(target=self._edid_worker, daemon=True).start()

    def _edid_worker(self):
        ps_cmd = (
            "$ids = @(Get-CimInstance -Namespace root\\wmi -ClassName WmiMonitorID -ErrorAction SilentlyContinue); "
            "$params = @(Get-CimInstance -Namespace root\\wmi -ClassName WmiMonitorBasicDisplayParams -ErrorAction SilentlyContinue); "
            "$conn = @(Get-CimInstance -Namespace root\\wmi -ClassName WmiMonitorConnectionParams -ErrorAction SilentlyContinue); "
            "$vc = @(Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | Select-Object Name, CurrentHorizontalResolution, CurrentVerticalResolution, CurrentRefreshRate, MinRefreshRate, MaxRefreshRate, CurrentBitsPerPixel); "
            "$out = @(); "
            "for ($i=0; $i -lt $ids.Count; $i++) { "
            "  $m = $ids[$i]; "
            "  $mfg = if ($m.ManufacturerName) { [System.Text.Encoding]::ASCII.GetString(($m.ManufacturerName | Where-Object {$_ -ne 0})) } else { '' }; "
            "  $name = if ($m.UserFriendlyName) { [System.Text.Encoding]::ASCII.GetString(($m.UserFriendlyName | Where-Object {$_ -ne 0})) } else { '' }; "
            "  $ser = if ($m.SerialNumberID) { [System.Text.Encoding]::ASCII.GetString(($m.SerialNumberID | Where-Object {$_ -ne 0})) } else { '' }; "
            "  $pcode = if ($m.ProductCodeID) { [System.Text.Encoding]::ASCII.GetString(($m.ProductCodeID | Where-Object {$_ -ne 0})) } else { '' }; "
            "  $w_cm = if ($i -lt $params.Count) { $params[$i].MaxHorizontalImageSize } else { 0 }; "
            "  $h_cm = if ($i -lt $params.Count) { $params[$i].MaxVerticalImageSize } else { 0 }; "
            "  $tech = if ($i -lt $conn.Count) { $conn[$i].VideoOutputTechnology } else { -1 }; "
            "  $out += @{Mfg=$mfg; Name=$name; Serial=$ser; ProdCode=$pcode; Year=$m.YearOfManufacture; Week=$m.WeekOfManufacture; Wcm=$w_cm; Hcm=$h_cm; Tech=$tech; Instance=$m.InstanceName} "
            "}; "
            "@{Monitors=$out; VC=$vc} | ConvertTo-Json -Compress -Depth 3"
        )

        monitors = []
        vc_list = []
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=8,
            ).strip()
            if out:
                data = json.loads(out)
                raw_m = data.get("Monitors") or []
                monitors = [raw_m] if isinstance(raw_m, dict) else raw_m
                raw_vc = data.get("VC") or []
                vc_list = [raw_vc] if isinstance(raw_vc, dict) else raw_vc
        except Exception:
            pass

        # Query Windows DPI Scaling Factor
        try:
            dpi = ctypes.windll.user32.GetDpiForSystem()
            dpi_scale_str = f"{int(round((dpi / 96.0) * 100))}% ({dpi} DPI)"
        except Exception:
            dpi_scale_str = "100% (96 DPI)"

        self.after(0, lambda: self._render_monitor_cards(monitors, vc_list, dpi_scale_str))

    def _render_monitor_cards(self, monitors: list, vc_list: list, dpi_scale_str: str):
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(1.0)

        primary_vc = vc_list[0] if vc_list else {}
        h_res = primary_vc.get("CurrentHorizontalResolution") or self.winfo_screenwidth()
        v_res = primary_vc.get("CurrentVerticalResolution") or self.winfo_screenheight()
        cur_hz = primary_vc.get("CurrentRefreshRate") or 60
        max_hz = primary_vc.get("MaxRefreshRate") or cur_hz
        min_hz = primary_vc.get("MinRefreshRate") or cur_hz
        gpu_name = primary_vc.get("Name") or "Primary Graphics Adapter"

        if not monitors:
            monitors = [
                {
                    "Mfg": "STD",
                    "Name": "Primary Display Panel",
                    "Serial": "Internal",
                    "ProdCode": "Default",
                    "Year": 2025,
                    "Week": 1,
                    "Wcm": 34,
                    "Hcm": 21,
                    "Tech": 11,
                    "Instance": "Default_Monitor",
                }
            ]

        for idx, m in enumerate(monitors, start=1):
            mfg_code = (m.get("Mfg") or "UNK").strip().upper()
            vendor_full = self.PNP_VENDORS.get(mfg_code, f"Panel Vendor ({mfg_code})")
            prod_code = (m.get("ProdCode") or "Panel").strip()
            friendly_name = (m.get("Name") or "").strip() or f"{mfg_code}{prod_code} Display Panel"
            serial = (m.get("Serial") or "").strip()
            if not serial or serial == "0":
                serial = f"{mfg_code}-{prod_code} (Embedded EDID)"

            year = m.get("Year") or "N/A"
            week = m.get("Week") or 0
            w_cm = int(m.get("Wcm") or 0)
            h_cm = int(m.get("Hcm") or 0)

            if w_cm > 0 and h_cm > 0:
                diag_cm = math.hypot(w_cm, h_cm)
                diag_in = diag_cm / 2.54
                size_str = f'{diag_in:.1f}" Diagonal ({w_cm} cm × {h_cm} cm)'
            else:
                size_str = "Dynamic / Internal Panel"

            tech_id = int(m.get("Tech") if m.get("Tech") is not None else -1)
            conn_str = self.OUTPUT_TECH.get(tech_id, f"Digital Interface ({tech_id})")

            card = ctk.CTkFrame(self.mon_scroll)
            card.grid(row=(idx - 1) // 2, column=(idx - 1) % 2, padx=8, pady=8, sticky="nsew")

            ctk.CTkLabel(
                card,
                text=f"🖥 Display #{idx}: {friendly_name}",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="#3B8ED0",
            ).pack(anchor="w", padx=15, pady=(12, 6))

            specs = {
                "Panel Manufacturer": f"{vendor_full} [{mfg_code}]",
                "Hardware Panel ID": f"{mfg_code}{prod_code}",
                "EDID Serial Number": serial,
                "Connection Interface": conn_str,
                "Physical Screen Size": size_str,
                "Manufacture Date": f"Week {week}, {year}" if week else str(year),
                "Active Resolution & Refresh": f"{h_res} × {v_res} @ {cur_hz} Hz",
                "Supported Refresh Range": f"{min_hz} Hz – {max_hz} Hz",
                "Windows UI DPI Scaling": dpi_scale_str,
                "Driven By GPU": gpu_name,
            }

            for k, v in specs.items():
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=2)
                ctk.CTkLabel(row, text=f"{k}:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
                ctk.CTkLabel(row, text=str(v), font=ctk.CTkFont(size=12), text_color="lightgray").pack(
                    side="right"
                )

            ctk.CTkLabel(card, text="", height=6).pack()

        self.log_message(f"[+] Decoded EDID firmware for {len(monitors)} connected display(s).")