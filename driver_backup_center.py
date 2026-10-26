# driver_backup_center.py
import os
import json
import threading
import subprocess
from tkinter import filedialog
import customtkinter as ctk
from backend_engine import SystemEngine


class DriverBackupCenterView(ctk.CTkFrame):
    """Modular Hardware Driver Health Scanner, Ghost Device Uninstaller & PnPUtil Backup Center."""

    IGNORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ignored_devices.json")

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.all_drivers = []
        self.problem_devices = []
        self.ignored_ids = self.load_ignored_devices()

        # ==========================================
        # CARD 1: DRIVER BACKUP & HEALTH BANNER
        # ==========================================
        top_card = ctk.CTkFrame(self)
        top_card.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        header_row = ctk.CTkFrame(top_card, fg_color="transparent")
        header_row.pack(fill="x", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            header_row,
            text="🔌 HARDWARE DRIVER INSPECTOR & BACKUP CENTER",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(side="left")

        self.backup_btn = ctk.CTkButton(
            header_row,
            text="💾 Export All Drivers Backup",
            width=215,
            height=32,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(weight="bold"),
            command=self.export_drivers_backup,
        )
        self.backup_btn.pack(side="right", padx=(6, 0))

        self.bt_settings_btn = ctk.CTkButton(
            header_row,
            text="📲 Bluetooth Settings",
            width=165,
            height=32,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: subprocess.Popen(["explorer.exe", "ms-settings:bluetooth"]),
        )
        self.bt_settings_btn.pack(side="right", padx=6)

        self.devmgmt_btn = ctk.CTkButton(
            header_row,
            text="🔧 Device Manager",
            width=155,
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: subprocess.Popen(["mmc", "devmgmt.msc"]),
        )
        self.devmgmt_btn.pack(side="right", padx=6)

        self.health_badge = ctk.CTkLabel(
            top_card,
            text="Device Manager Status: Click 'Scan Drivers' to check for hardware errors.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray",
        )
        self.health_badge.pack(anchor="w", padx=15, pady=(0, 12))

        # ==========================================
        # CARD 2: SEARCH & FILTER BAR
        # ==========================================
        filter_bar = ctk.CTkFrame(self)
        filter_bar.grid(row=1, column=0, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(
            filter_bar, text="🔎 Filter Drivers:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(15, 5), pady=12)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_driver_list())

        self.search_entry = ctk.CTkEntry(
            filter_bar,
            width=240,
            placeholder_text="Search by device name, provider (NVIDIA, Intel, AMD, Realtek)...",
            textvariable=self.search_var,
        )
        self.search_entry.pack(side="left", padx=5, pady=12, fill="x", expand=True)

        self.var_hide_microsoft = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            filter_bar,
            text="Hide Standard Microsoft Drivers",
            variable=self.var_hide_microsoft,
            command=self.render_driver_list,
        ).pack(side="left", padx=12, pady=12)

        self.scan_btn = ctk.CTkButton(
            filter_bar,
            text="🔄 Scan Drivers",
            width=140,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.scan_drivers,
        )
        self.scan_btn.pack(side="right", padx=15, pady=12)

        # ==========================================
        # STATUS BAR
        # ==========================================
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready to scan installed PnP drivers and check for Device Manager error codes.",
            text_color="gray",
        )
        self.status_label.grid(row=2, column=0, pady=(0, 4), sticky="w")

        # ==========================================
        # SCROLLABLE DRIVER LIST
        # ==========================================
        self.driver_scroll = ctk.CTkScrollableFrame(self)
        self.driver_scroll.grid(row=3, column=0, sticky="nsew")

    @classmethod
    def load_ignored_devices(cls) -> set:
        if os.path.exists(cls.IGNORE_FILE):
            try:
                with open(cls.IGNORE_FILE, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                pass
        return set()

    def save_ignored_devices(self):
        try:
            with open(self.IGNORE_FILE, "w", encoding="utf-8") as f:
                json.dump(list(self.ignored_ids), f)
        except Exception:
            pass

    # ==========================================
    # DRIVER HEALTH & INVENTORY SCANNER
    # ==========================================
    def scan_drivers(self):
        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.status_label.configure(
            text="Querying Windows WMI PnP Drivers & checking Device Manager error codes...",
            text_color="#3B8ED0",
        )
        threading.Thread(target=self._driver_scan_worker, daemon=True).start()

    def _driver_scan_worker(self):
        ps_cmd = (
            "$errs = @(Get-CimInstance Win32_PnPEntity | "
            "Where-Object { $_.ConfigManagerErrorCode -ne 0 -and $_.ConfigManagerErrorCode -ne 22 } | "
            "Select-Object Name, DeviceID, ConfigManagerErrorCode, Status); "
            "$drvs = @(Get-CimInstance Win32_PnPSignedDriver | Where-Object { $_.DeviceName -ne $null } | "
            "Select-Object DeviceName, DriverVersion, DriverProviderName, DeviceClass, InfName); "
            "@{errors=$errs; drivers=$drvs} | ConvertTo-Json -Compress"
        )
        errors = []
        drivers = []
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=12,
            ).strip()
            if out:
                data = json.loads(out)
                raw_errs = data.get("errors") or []
                raw_drvs = data.get("drivers") or []
                errors = [raw_errs] if isinstance(raw_errs, dict) else raw_errs
                drivers = [raw_drvs] if isinstance(raw_drvs, dict) else raw_drvs
        except Exception:
            pass

        errors = [e for e in errors if (e.get("DeviceID") or "") not in self.ignored_ids]

        seen = set()
        clean_drivers = []
        for d in drivers:
            name = (d.get("DeviceName") or "").strip()
            ver = (d.get("DriverVersion") or "Unknown").strip()
            provider = (d.get("DriverProviderName") or "Unknown").strip()
            dev_class = (d.get("DeviceClass") or "System").strip()
            inf = (d.get("InfName") or "").strip()

            if not name:
                continue
            key = f"{name.lower()}|{ver}"
            if key in seen:
                continue
            seen.add(key)

            clean_drivers.append(
                {
                    "name": name,
                    "version": ver,
                    "provider": provider,
                    "class": dev_class,
                    "inf": inf,
                }
            )

        clean_drivers.sort(key=lambda x: x["name"].lower())
        self.problem_devices = errors
        self.all_drivers = clean_drivers
        self.after(0, self._finish_scan)

    def _finish_scan(self):
        self.scan_btn.configure(state="normal", text="🔄 Scan Drivers")

        if self.problem_devices:
            count = len(self.problem_devices)
            self.health_badge.configure(
                text=f"⚠️ Warning: {count} device(s) reporting errors! Click 'Force Uninstall Subtree' or 'Disable & Mute' below.",
                text_color="#E74C3C",
            )
        else:
            self.health_badge.configure(
                text="✅ All Hardware Devices Working Properly (0 Active Error Codes)",
                text_color="#2FA572",
            )

        self.render_driver_list()

    def render_driver_list(self):
        for widget in self.driver_scroll.winfo_children():
            widget.destroy()

        for err in self.problem_devices:
            err_card = ctk.CTkFrame(self.driver_scroll, fg_color=("#FADBD8", "#4A1C1C"))
            err_card.pack(fill="x", padx=5, pady=4)

            dev_name = err.get("Name") or "Unknown Hardware Device"
            dev_id = err.get("DeviceID") or ""
            err_code = err.get("ConfigManagerErrorCode")

            info_col = ctk.CTkFrame(err_card, fg_color="transparent")
            info_col.pack(side="left", fill="x", expand=True, padx=12, pady=8)

            ctk.CTkLabel(
                info_col,
                text=f"⚠️ HARDWARE ERROR: {dev_name}  (Error Code {err_code})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#E74C3C",
            ).pack(anchor="w")

            ctk.CTkLabel(
                info_col,
                text=f"ID: {dev_id}",
                font=ctk.CTkFont(family="Consolas", size=10),
                text_color="lightgray",
            ).pack(anchor="w")

            if dev_id:
                btn_box = ctk.CTkFrame(err_card, fg_color="transparent")
                btn_box.pack(side="right", padx=10, pady=8)

                ctk.CTkButton(
                    btn_box,
                    text="🚮 Force Uninstall Subtree",
                    width=180,
                    height=28,
                    fg_color="#C0392B",
                    hover_color="#922B21",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    command=lambda did=dev_id, dn=dev_name: self.force_uninstall_device(did, dn),
                ).pack(side="right", padx=4)

                ctk.CTkButton(
                    btn_box,
                    text="🔇 Disable & Mute",
                    width=140,
                    height=28,
                    fg_color="#D35400",
                    hover_color="#A04000",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    command=lambda did=dev_id, dn=dev_name: self.disable_and_mute_device(did, dn),
                ).pack(side="right", padx=4)

        query = self.search_var.get().strip().lower()
        hide_ms = self.var_hide_microsoft.get()

        filtered = []
        for d in self.all_drivers:
            if hide_ms and d["provider"].lower() in ("microsoft", "standard system devices"):
                continue
            if query:
                haystack = f"{d['name']} {d['provider']} {d['class']} {d['version']}".lower()
                if query not in haystack:
                    continue
            filtered.append(d)

        display_list = filtered[:75]
        self.status_label.configure(
            text=f"Showing {len(display_list)} of {len(filtered)} matching drivers.",
            text_color="#2FA572",
        )

        for drv in display_list:
            card = ctk.CTkFrame(self.driver_scroll)
            card.pack(fill="x", padx=5, pady=3)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=12, pady=8)

            ctk.CTkLabel(
                left,
                text=f"🔌 {drv['name']}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#3B8ED0",
            ).pack(anchor="w")

            sub_text = f"Provider: {drv['provider']}   |   Class: {drv['class']}"
            if drv["inf"]:
                sub_text += f"   |   INF: {drv['inf']}"

            ctk.CTkLabel(
                left,
                text=sub_text,
                font=ctk.CTkFont(size=11),
                text_color="gray",
            ).pack(anchor="w")

            ctk.CTkLabel(
                card,
                text=f"v{drv['version']}",
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                text_color="lightgray",
            ).pack(side="right", padx=15, pady=8)

    def force_uninstall_device(self, device_id: str, device_name: str):
        if not SystemEngine.is_admin():
            self.status_label.configure(
                text="⚠️ Force-uninstalling a device requires Administrator Mode.",
                text_color="#E74C3C",
            )
            return

        self.status_label.configure(
            text=f"🚮 Force-uninstalling '{device_name}' subtree ({device_id})...",
            text_color="#3B8ED0",
        )

        def worker():
            try:
                safe_id = device_id.replace("'", "''")
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f"Disable-PnpDevice -InstanceId '{safe_id}' -Confirm:$false -ErrorAction SilentlyContinue",
                    ],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=8,
                )

                res = subprocess.run(
                    ["pnputil", "/remove-device", device_id, "/subtree"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10,
                )

                if res.returncode != 0:
                    res = subprocess.run(
                        ["pnputil", "/remove-device", device_id],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=10,
                    )

                out_msg = (res.stdout or res.stderr or "").strip().replace("\n", " ")
                self.ignored_ids.add(device_id)
                self.save_ignored_devices()

                self.after(
                    0,
                    lambda m=out_msg: self.status_label.configure(
                        text=f"✅ Uninstalled '{device_name}' ({m[:70]}). Refreshing...",
                        text_color="#2FA572",
                    ),
                )
                self.after(400, self.scan_drivers)
            except Exception as e:
                self.after(
                    0,
                    lambda err=e: self.status_label.configure(
                        text=f"❌ Error removing device: {err}", text_color="#E74C3C"
                    ),
                )

        threading.Thread(target=worker, daemon=True).start()

    def disable_and_mute_device(self, device_id: str, device_name: str):
        if not SystemEngine.is_admin():
            self.status_label.configure(
                text="⚠️ Disabling a device requires Administrator Mode.",
                text_color="#E74C3C",
            )
            return

        self.status_label.configure(
            text=f"🔇 Disabling stuck ghost device '{device_name}'...",
            text_color="#3B8ED0",
        )

        def worker():
            safe_id = device_id.replace("'", "''")
            ps_cmd = f"Disable-PnpDevice -InstanceId '{safe_id}' -Confirm:$false -ErrorAction Stop"
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=8,
                )
            except Exception:
                pass

            self.ignored_ids.add(device_id)
            self.save_ignored_devices()

            self.after(
                0,
                lambda: self.status_label.configure(
                    text=f"✅ Disabled & muted '{device_name}'. Saved to persistent ignore list.",
                    text_color="#2FA572",
                ),
            )
            self.after(300, self.scan_drivers)

        threading.Thread(target=worker, daemon=True).start()

    # ==========================================
    # 1-CLICK DRIVER BACKUP (PNPUTIL)
    # ==========================================
    def export_drivers_backup(self):
        if not SystemEngine.is_admin():
            self.status_label.configure(
                text="⚠️ Exporting third-party drivers requires Administrator privileges.",
                text_color="#E74C3C",
            )
            return

        dest_dir = filedialog.askdirectory(title="Select Folder to Save Driver Backup")
        if not dest_dir:
            return

        backup_folder = os.path.join(os.path.normpath(dest_dir), "Windows_Drivers_Backup")
        os.makedirs(backup_folder, exist_ok=True)

        self.backup_btn.configure(state="disabled", text="Exporting Drivers...")
        self.status_label.configure(
            text=f"Exporting all third-party drivers to {backup_folder}... Please wait (takes 30-90 seconds).",
            text_color="#3B8ED0",
        )

        def worker():
            try:
                res = subprocess.run(
                    ["pnputil", "/export-driver", "*", backup_folder],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                if res.returncode == 0:
                    self.after(
                        0,
                        lambda: self.status_label.configure(
                            text=f"✅ Driver Backup Complete! Saved to: {backup_folder}",
                            text_color="#2FA572",
                        ),
                    )
                    subprocess.Popen(["explorer", backup_folder])
                else:
                    self.after(
                        0,
                        lambda: self.status_label.configure(
                            text=f"Driver export finished with message: {res.stdout.strip()[:80]}",
                            text_color="#E67E22",
                        ),
                    )
            except Exception as e:
                self.after(
                    0,
                    lambda err=e: self.status_label.configure(
                        text=f"❌ Failed to export drivers: {err}", text_color="#E74C3C"
                    ),
                )
            finally:
                self.after(
                    0,
                    lambda: self.backup_btn.configure(
                        state="normal", text="💾 Export All Drivers Backup"
                    ),
                )

        threading.Thread(target=worker, daemon=True).start()