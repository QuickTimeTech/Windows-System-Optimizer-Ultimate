# product_key_bios.py
import json
import threading
import subprocess
from tkinter import messagebox
import customtkinter as ctk
from backend_engine import SystemEngine


class ProductKeyBiosView(ctk.CTkFrame):
    """Modular Windows OEM/Registry Product Key Extractor, UEFI/BIOS, TPM 2.0 & RAM Slot Inspector."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.oem_key = ""
        self.reg_key = ""
        self.keys_revealed = False
        self.bios_data = {}

        # ==========================================
        # TOP CARD: WINDOWS PRODUCT KEY VAULT
        # ==========================================
        key_card = ctk.CTkFrame(self)
        key_card.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="ew")

        hdr_row = ctk.CTkFrame(key_card, fg_color="transparent")
        hdr_row.pack(fill="x", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            hdr_row,
            text="🔑 WINDOWS PRODUCT KEY & LICENSING VAULT",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(side="left")

        self.scan_btn = ctk.CTkButton(
            hdr_row,
            text="🔄 Scan Keys & Firmware",
            width=175,
            height=30,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.scan_all_firmware,
        )
        self.scan_btn.pack(side="right", padx=(6, 0))

        self.uefi_reboot_btn = ctk.CTkButton(
            hdr_row,
            text="⚡ Reboot to UEFI BIOS Setup",
            width=205,
            height=30,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.reboot_to_uefi_bios,
        )
        self.uefi_reboot_btn.pack(side="right", padx=6)

        # Key Display Bar
        key_bar = ctk.CTkFrame(key_card, fg_color=("gray85", "gray17"))
        key_bar.pack(fill="x", padx=15, pady=(4, 12))

        left_key_col = ctk.CTkFrame(key_bar, fg_color="transparent")
        left_key_col.pack(side="left", fill="x", expand=True, padx=14, pady=10)

        self.edition_lbl = ctk.CTkLabel(
            left_key_col,
            text="Windows Edition: Scanning...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="lightgray",
        )
        self.edition_lbl.pack(anchor="w")

        self.key_display_lbl = ctk.CTkLabel(
            left_key_col,
            text="Product Key: •••••-•••••-•••••-•••••-•••••",
            font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
            text_color="#2FA572",
        )
        self.key_display_lbl.pack(anchor="w", pady=(2, 0))

        key_btns = ctk.CTkFrame(key_bar, fg_color="transparent")
        key_btns.pack(side="right", padx=14, pady=10)

        self.reveal_btn = ctk.CTkButton(
            key_btns,
            text="👁️ Reveal Key",
            width=120,
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.toggle_reveal_keys,
        )
        self.reveal_btn.pack(side="left", padx=4)

        self.copy_key_btn = ctk.CTkButton(
            key_btns,
            text="📋 Copy Key",
            width=120,
            height=32,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.copy_product_key,
        )
        self.copy_key_btn.pack(side="left", padx=4)

        # ==========================================
        # MIDDLE ROW: 4 COMPLIANCE BADGES (UEFI, SECURE BOOT, TPM 2.0, XMP/RAM)
        # ==========================================
        badge_frame = ctk.CTkFrame(self)
        badge_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky="ew")
        badge_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="badges")

        self.badge_uefi = self._create_status_badge(badge_frame, 0, "FIRMWARE MODE", "Checking...")
        self.badge_secboot = self._create_status_badge(badge_frame, 1, "SECURE BOOT", "Checking...")
        self.badge_tpm = self._create_status_badge(badge_frame, 2, "TPM 2.0 MODULE", "Checking...")
        self.badge_ram_slots = self._create_status_badge(badge_frame, 3, "DIMM RAM SLOTS", "Checking...")

        # ==========================================
        # BOTTOM ROW: MOTHERBOARD/BIOS SPECS & PHYSICAL RAM STICKS
        # ==========================================
        # Left Card: Motherboard & BIOS Details
        mb_card = ctk.CTkFrame(self)
        mb_card.grid(row=2, column=0, padx=(0, 8), sticky="nsew")

        ctk.CTkLabel(
            mb_card,
            text="🎛️ MOTHERBOARD & BIOS FIRMWARE DETAILS",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w", padx=15, pady=(12, 6))

        self.mb_info_box = ctk.CTkScrollableFrame(mb_card, fg_color="transparent")
        self.mb_info_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Right Card: Physical RAM DIMM Slots & Speeds
        ram_card = ctk.CTkFrame(self)
        ram_card.grid(row=2, column=1, padx=(8, 0), sticky="nsew")

        ctk.CTkLabel(
            ram_card,
            text="⚡ PHYSICAL RAM DIMM STICKS & XMP/DOCP SPEED",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#9B59B6",
        ).pack(anchor="w", padx=15, pady=(12, 6))

        self.ram_sticks_box = ctk.CTkScrollableFrame(ram_card, fg_color="transparent")
        self.ram_sticks_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Auto-scan on creation
        self.after(250, self.scan_all_firmware)

    def _create_status_badge(self, parent, col: int, title: str, initial_val: str) -> ctk.CTkLabel:
        box = ctk.CTkFrame(parent, fg_color=("gray85", "gray17"))
        box.grid(row=0, column=col, padx=8, pady=10, sticky="nsew")
        ctk.CTkLabel(box, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color="gray").pack(
            pady=(8, 2)
        )
        val_lbl = ctk.CTkLabel(
            box, text=initial_val, font=ctk.CTkFont(size=15, weight="bold"), text_color="#3B8ED0"
        )
        val_lbl.pack(pady=(0, 8))
        return val_lbl

    # ==========================================
    # WMI FIRMWARE, KEY & TPM SCANNER
    # ==========================================
    def scan_all_firmware(self):
        self.scan_btn.configure(state="disabled", text="⏳ Scanning...")
        threading.Thread(target=self._firmware_worker, daemon=True).start()

    def _firmware_worker(self):
        ps_cmd = (
            "$sls = Get-CimInstance SoftwareLicensingService -ErrorAction SilentlyContinue | Select-Object OA3xOriginalProductKey; "
            "$lp = Get-CimInstance SoftwareLicensingProduct -ErrorAction SilentlyContinue | "
            "Where-Object { $_.PartialProductKey -ne $null -and $_.Name -like 'Windows*' } | "
            "Select-Object -First 1 Name, Description, PartialProductKey, LicenseStatus; "
            "$nt = Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SoftwareProtectionPlatform' -ErrorAction SilentlyContinue; "
            "$cur = Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion' -ErrorAction SilentlyContinue; "
            "$bios = Get-CimInstance Win32_BIOS -ErrorAction SilentlyContinue | Select-Object Manufacturer, SMBIOSBIOSVersion, ReleaseDate, SerialNumber; "
            "$board = Get-CimInstance Win32_BaseBoard -ErrorAction SilentlyContinue | Select-Object Manufacturer, Product, Version, SerialNumber; "
            "$tpm = Get-Tpm -ErrorAction SilentlyContinue | Select-Object TpmPresent, TpmReady, TpmEnabled; "
            "$sb = try { Confirm-SecureBootUEFI -ErrorAction Stop } catch { $null }; "
            "$pe = (Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control' -Name PEFirmwareType -ErrorAction SilentlyContinue).PEFirmwareType; "
            "$memArr = Get-CimInstance Win32_PhysicalMemoryArray -ErrorAction SilentlyContinue | Measure-Object -Property MemoryDevices -Sum | Select-Object -ExpandProperty Sum; "
            "$sticks = @(Get-CimInstance Win32_PhysicalMemory -ErrorAction SilentlyContinue | "
            "Select-Object BankLabel, DeviceLocator, Capacity, ConfiguredClockSpeed, Speed, Manufacturer, PartNumber); "
            "@{oemKey=$sls.OA3xOriginalProductKey; backupKey=$nt.BackupProductKeyDefault; "
            "edName=$cur.ProductName; displayVer=$cur.DisplayVersion; partial=$lp.PartialProductKey; licDesc=$lp.Description; "
            "bios=$bios; board=$board; tpm=$tpm; sb=$sb; pe=$pe; totalSlots=$memArr; sticks=$sticks} | ConvertTo-Json -Compress -Depth 3"
        )
        data = {}
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=12,
            ).strip()
            if out:
                data = json.loads(out)
        except Exception:
            pass

        self.bios_data = data
        self.oem_key = (data.get("oemKey") or "").strip()
        self.reg_key = (data.get("backupKey") or "").strip()
        self.after(0, self._render_firmware_ui)

    def _render_firmware_ui(self):
        self.scan_btn.configure(state="normal", text="🔄 Scan Keys & Firmware")
        d = self.bios_data

        # 1. Windows Edition & Product Key
        ed_name = d.get("edName") or "Windows OS"
        disp_ver = d.get("displayVer") or ""
        lic_desc = d.get("licDesc") or "Retail / OEM Channel"
        partial = d.get("partial") or ""
        self.edition_lbl.configure(
            text=f"OS Edition: {ed_name} ({disp_ver})   |   Channel: {lic_desc}"
        )
        self._update_key_label(partial)

        # 2. Top 4 Compliance Badges
        pe_type = d.get("pe")
        if pe_type == 2:
            self.badge_uefi.configure(text="✅ UEFI Mode", text_color="#2FA572")
        elif pe_type == 1:
            self.badge_uefi.configure(text="⚠️ Legacy BIOS", text_color="#E67E22")
        else:
            self.badge_uefi.configure(text="UEFI / Standard", text_color="#3B8ED0")

        sb = d.get("sb")
        if sb is True:
            self.badge_secboot.configure(text="✅ Enabled (Active)", text_color="#2FA572")
        elif sb is False:
            self.badge_secboot.configure(text="❌ Disabled", text_color="#E74C3C")
        else:
            self.badge_secboot.configure(text="⚠️ Unsupported / Off", text_color="#E67E22")

        tpm = d.get("tpm") or {}
        if tpm.get("TpmReady") or tpm.get("TpmEnabled"):
            self.badge_tpm.configure(text="✅ TPM 2.0 Ready", text_color="#2FA572")
        elif tpm.get("TpmPresent"):
            self.badge_tpm.configure(text="⚠️ Present (Not Ready)", text_color="#E67E22")
        else:
            self.badge_tpm.configure(text="⚠️ Admin Required / Off", text_color="#E67E22")

        raw_sticks = d.get("sticks") or []
        sticks = [raw_sticks] if isinstance(raw_sticks, dict) else raw_sticks
        total_slots = int(d.get("totalSlots") or max(len(sticks), 2))
        self.badge_ram_slots.configure(
            text=f"{len(sticks)} of {total_slots} Slots Used",
            text_color="#9B59B6",
        )

        # 3. Motherboard & BIOS Details List
        for w in self.mb_info_box.winfo_children():
            w.destroy()

        board = d.get("board") or {}
        bios = d.get("bios") or {}

        # Format WMI ReleaseDate if present
        raw_date = str(bios.get("ReleaseDate") or "Unknown")
        if len(raw_date) >= 8 and raw_date[:8].isdigit():
            raw_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"

        mb_rows = [
            ("Motherboard Vendor", board.get("Manufacturer") or "Unknown"),
            ("Motherboard Model", board.get("Product") or "Unknown"),
            ("Board Revision", board.get("Version") or "Standard"),
            ("Board Serial Number", board.get("SerialNumber") or "Default"),
            ("BIOS Vendor", bios.get("Manufacturer") or "Unknown"),
            ("BIOS Version", bios.get("SMBIOSBIOSVersion") or "Unknown"),
            ("BIOS Release Date", raw_date),
            ("OEM Key in Firmware", "✅ Embedded in BIOS" if self.oem_key else "Digital License / Retail"),
        ]

        for k, v in mb_rows:
            row = ctk.CTkFrame(self.mb_info_box, fg_color=("gray85", "gray17"))
            row.pack(fill="x", padx=4, pady=3)
            ctk.CTkLabel(row, text=f"{k}:", font=ctk.CTkFont(size=12, weight="bold")).pack(
                side="left", padx=12, pady=7
            )
            ctk.CTkLabel(row, text=str(v), font=ctk.CTkFont(size=12), text_color="#3B8ED0").pack(
                side="right", padx=12, pady=7
            )

        # 4. Physical RAM Sticks & XMP Speeds
        for w in self.ram_sticks_box.winfo_children():
            w.destroy()

        if not sticks:
            ctk.CTkLabel(self.ram_sticks_box, text="No physical DIMM data returned.", text_color="gray").pack(
                pady=15
            )
        else:
            for idx, st in enumerate(sticks, start=1):
                cap_bytes = int(st.get("Capacity") or 0)
                cap_gb = cap_bytes / (1024**3) if cap_bytes else 0
                clk = st.get("ConfiguredClockSpeed") or st.get("Speed") or "Unknown"
                vendor = (st.get("Manufacturer") or "RAM Vendor").strip()
                part = (st.get("PartNumber") or "Generic DIMM").strip()
                slot_lbl = (st.get("DeviceLocator") or st.get("BankLabel") or f"Slot {idx}").strip()

                scard = ctk.CTkFrame(self.ram_sticks_box, fg_color=("gray85", "gray17"))
                scard.pack(fill="x", padx=4, pady=4)

                top_r = ctk.CTkFrame(scard, fg_color="transparent")
                top_r.pack(fill="x", padx=12, pady=(8, 2))

                ctk.CTkLabel(
                    top_r,
                    text=f"⚡ {slot_lbl}: {cap_gb:.0f} GB @ {clk} MHz",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#2FA572",
                ).pack(side="left")

                ctk.CTkLabel(
                    top_r,
                    text=vendor,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color="#9B59B6",
                ).pack(side="right")

                ctk.CTkLabel(
                    scard,
                    text=f"Part Number: {part}",
                    font=ctk.CTkFont(family="Consolas", size=11),
                    text_color="gray",
                ).pack(anchor="w", padx=12, pady=(0, 8))

    # ==========================================
    # PRODUCT KEY MASKING, COPY & UEFI REBOOT
    # ==========================================
    def _get_best_key(self) -> tuple[str, str]:
        if self.oem_key:
            return self.oem_key, "UEFI Motherboard OEM Key"
        if self.reg_key:
            return self.reg_key, "Installed Registry Key"
        partial = (self.bios_data.get("partial") or "").strip()
        if partial:
            return f"XXXXX-XXXXX-XXXXX-XXXXX-{partial}", "Digital License (Partial Key)"
        return "Digital Entitlement Active", "Microsoft Account Digital License"

    def _update_key_label(self, partial: str = ""):
        best_key, key_source = self._get_best_key()
        if self.keys_revealed:
            self.key_display_lbl.configure(text=f"{key_source}:  {best_key}")
            self.reveal_btn.configure(text="🙈 Hide Key")
        else:
            tail = best_key[-5:] if len(best_key) >= 5 else (partial or "•••••")
            self.key_display_lbl.configure(
                text=f"{key_source}:  •••••-•••••-•••••-•••••-{tail}"
            )
            self.reveal_btn.configure(text="👁️ Reveal Key")

    def toggle_reveal_keys(self):
        self.keys_revealed = not self.keys_revealed
        self._update_key_label()

    def copy_product_key(self):
        best_key, _ = self._get_best_key()
        self.clipboard_clear()
        self.clipboard_append(best_key)
        self.copy_key_btn.configure(text="✅ Copied!")
        self.after(1800, lambda: self.copy_key_btn.configure(text="📋 Copy Key"))

    def reboot_to_uefi_bios(self):
        if not SystemEngine.is_admin():
            messagebox.showwarning(
                "Administrator Required",
                "Rebooting directly into UEFI Firmware Settings requires Administrator privileges.",
            )
            return

        confirm = messagebox.askyesno(
            "Reboot Directly Into UEFI BIOS Setup?",
            "Your PC will restart in 3 seconds and boot straight into your motherboard's UEFI/BIOS Setup screen.\n\n"
            "Save any open work before clicking Yes. Proceed?",
        )
        if confirm:
            subprocess.Popen(
                ["shutdown", "/r", "/fw", "/t", "3"],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )