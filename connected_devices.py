# connected_devices.py
import json
import threading
import subprocess
import customtkinter as ctk


class ConnectedDevicesView(ctk.CTkFrame):
    """Modular Connected Peripherals, USB, Monitor, Audio & Printer Inspector."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.all_devices = []

        # ==========================================
        # TOP FILTER & SEARCH BAR
        # ==========================================
        top_bar = ctk.CTkFrame(self)
        top_bar.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(
            top_bar, text="🔌 Category:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(15, 5), pady=12)

        self.cat_menu = ctk.CTkOptionMenu(
            top_bar,
            values=[
                "All Connected Devices",
                "USB Controllers & Drives",
                "Monitors & Displays",
                "Audio & Microphones",
                "Keyboards, Mice & HID",
                "Printers & Scanners",
                "Bluetooth & Network",
            ],
            width=210,
            command=lambda _: self.render_devices(),
        )
        self.cat_menu.set("All Connected Devices")
        self.cat_menu.pack(side="left", padx=5, pady=12)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_devices())

        self.search_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="Search device name, manufacturer, or Hardware ID...",
            textvariable=self.search_var,
        )
        self.search_entry.pack(side="left", padx=8, pady=12, fill="x", expand=True)

        self.scan_btn = ctk.CTkButton(
            top_bar,
            text="🔄 Refresh Peripherals",
            width=160,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.scan_peripherals,
        )
        self.scan_btn.pack(side="right", padx=15, pady=12)

        # ==========================================
        # STATUS BAR
        # ==========================================
        self.status_label = ctk.CTkLabel(
            self,
            text="Click 'Refresh Peripherals' to list all active USB devices, monitors, audio gear, and printers.",
            text_color="gray",
        )
        self.status_label.grid(row=1, column=0, pady=(0, 6), sticky="w")

        # ==========================================
        # SCROLLABLE DEVICE CARDS
        # ==========================================
        self.dev_scroll = ctk.CTkScrollableFrame(self)
        self.dev_scroll.grid(row=2, column=0, sticky="nsew")

    def scan_peripherals(self):
        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.status_label.configure(
            text="Enumerating active PnP peripherals, USB hubs, displays, and audio endpoints...",
            text_color="#3B8ED0",
        )
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        ps_cmd = (
            "$devs = @(Get-CimInstance Win32_PnPEntity | Where-Object { $_.Present -eq $true -and $_.Name -ne $null } | "
            "Select-Object Name, PNPClass, Manufacturer, Status, DeviceID); "
            "$devs | ConvertTo-Json -Compress"
        )
        devices = []
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=10,
            ).strip()
            if out:
                raw = json.loads(out)
                devices = [raw] if isinstance(raw, dict) else raw
        except Exception:
            pass

        # Filter out noisy internal motherboard system bridges so real peripherals stand out
        ignored_classes = {"system", "legacydriver", "volume", "volumeshadowcopy", "softwarecomponent"}
        cleaned = []
        for d in devices:
            pnp_class = (d.get("PNPClass") or "Other").strip()
            if pnp_class.lower() in ignored_classes:
                continue
            cleaned.append(
                {
                    "name": (d.get("Name") or "Unknown Device").strip(),
                    "class": pnp_class,
                    "manufacturer": (d.get("Manufacturer") or "Standard Hardware").strip(),
                    "status": (d.get("Status") or "OK").strip(),
                    "id": (d.get("DeviceID") or "").strip(),
                }
            )

        cleaned.sort(key=lambda x: (x["class"].lower(), x["name"].lower()))
        self.all_devices = cleaned
        self.after(0, self._finish_scan)

    def _finish_scan(self):
        self.scan_btn.configure(state="normal", text="🔄 Refresh Peripherals")
        self.render_devices()

    @staticmethod
    def _matches_category(pnp_class: str, dev_id: str, category: str) -> bool:
        c = pnp_class.lower()
        did = dev_id.lower()
        if category == "All Connected Devices":
            return True
        if category == "USB Controllers & Drives":
            return "usb" in c or "diskdrive" in c or "wpd" in c or did.startswith("usb\\")
        if category == "Monitors & Displays":
            return c in ("monitor", "display", "image", "camera")
        if category == "Audio & Microphones":
            return "audio" in c or "media" in c or "sound" in c
        if category == "Keyboards, Mice & HID":
            return c in ("keyboard", "mouse", "hidclass")
        if category == "Printers & Scanners":
            return "print" in c or "scan" in c
        if category == "Bluetooth & Network":
            return "bluetooth" in c or "net" in c or "bth" in did
        return True

    def render_devices(self):
        for widget in self.dev_scroll.winfo_children():
            widget.destroy()

        cat = self.cat_menu.get()
        query = self.search_var.get().strip().lower()

        filtered = []
        for d in self.all_devices:
            if not self._matches_category(d["class"], d["id"], cat):
                continue
            if query:
                haystack = f"{d['name']} {d['class']} {d['manufacturer']} {d['id']}".lower()
                if query not in haystack:
                    continue
            filtered.append(d)

        display_list = filtered[:80]
        self.status_label.configure(
            text=f"Found {len(filtered)} connected devices in '{cat}' (Showing top {len(display_list)}).",
            text_color="#2FA572",
        )

        if not display_list:
            ctk.CTkLabel(
                self.dev_scroll, text="No connected devices matched this filter.", text_color="gray"
            ).pack(pady=25)
            return

        for dev in display_list:
            card = ctk.CTkFrame(self.dev_scroll)
            card.pack(fill="x", padx=5, pady=3)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=12, pady=8)

            ctk.CTkLabel(
                left,
                text=f"🔹 [{dev['class']}]  {dev['name']}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#3B8ED0",
            ).pack(anchor="w")

            ctk.CTkLabel(
                left,
                text=f"Manufacturer: {dev['manufacturer']}   |   ID: {dev['id'][:65]}",
                font=ctk.CTkFont(size=11),
                text_color="gray",
            ).pack(anchor="w")

            ok = dev["status"].upper() == "OK"
            ctk.CTkLabel(
                card,
                text=f"{'✅' if ok else '⚠️'} {dev['status']}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#2FA572" if ok else "#E74C3C",
            ).pack(side="right", padx=15, pady=8)