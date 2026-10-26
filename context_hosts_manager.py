# context_hosts_manager.py
import os
import shutil
import subprocess
import winreg
import customtkinter as ctk
from backend_engine import SystemEngine


class ContextHostsManagerView(ctk.CTkFrame):
    """Modular Windows 11 Classic Context Menu Switcher, God Mode Creator & Hosts File Shield."""

    CLSID_KEY = r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32"
    HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
    HOSTS_BACKUP = r"C:\Windows\System32\drivers\etc\hosts.pcoptimizer.bak"

    # Safe, well-known Microsoft Telemetry & Ad-Tracking domains to sinkhole to 0.0.0.0
    TELEMETRY_DOMAINS = [
        "vortex.data.microsoft.com",
        "vortex-win.data.microsoft.com",
        "telecommand.telemetry.microsoft.com",
        "oca.telemetry.microsoft.com",
        "sqm.telemetry.microsoft.com",
        "watson.telemetry.microsoft.com",
        "redir.metaservices.microsoft.com",
        "choice.microsoft.com",
        "df.telemetry.microsoft.com",
        "reports.wes.df.telemetry.microsoft.com",
        "wes.df.telemetry.microsoft.com",
        "services.wes.df.telemetry.microsoft.com",
        "sqm.df.telemetry.microsoft.com",
        "telemetry.microsoft.com",
        "watson.ppe.telemetry.microsoft.com",
        "telemetry.appex.bing.net",
        "telemetry.urs.microsoft.com",
        "settings-sandbox.data.microsoft.com",
        "vortex-sandbox.data.microsoft.com",
        "survey.watson.microsoft.com",
        "watson.live.com",
        "watson.microsoft.com",
        "statsfe2.ws.microsoft.com",
        "corpext.msitadfs.glbdns2.microsoft.com",
        "compatexchange.cloudapp.net",
        "cs1.wpc.v0cdn.net",
        "a-0001.a-msedge.net",
        "statsfe2.update.microsoft.com.akadns.net",
        "diagnostics.support.microsoft.com",
        "corp.sts.microsoft.com",
        "statsfe1.ws.microsoft.com",
        "pre.footprintpredict.com",
        "i1.services.social.microsoft.com",
        "feedback.windows.com",
        "feedback.microsoft-hohm.com",
        "feedback.search.microsoft.com",
        "rad.msn.com",
        "preview.msn.com",
        "ad.doubleclick.net",
        "ads.msn.com",
        "adnexus.net",
        "adnxs.com",
    ]

    BLOCK_START_TAG = "# === BEGIN PC OPTIMIZER TELEMETRY SHIELD ==="
    BLOCK_END_TAG = "# === END PC OPTIMIZER TELEMETRY SHIELD ==="

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ==========================================
        # CARD 1: WIN 11 CONTEXT MENU & GOD MODE
        # ==========================================
        ui_card = ctk.CTkFrame(self)
        ui_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            ui_card,
            text="🖱️ WINDOWS 11 SHELL & GOD MODE TWEAKS",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        self.ctx_status_lbl = ctk.CTkLabel(
            ui_card,
            text="Right-Click Menu Style: Checking...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2FA572",
        )
        self.ctx_status_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        self.btn_classic_ctx = ctk.CTkButton(
            ui_card,
            text="⚡ Enable Classic Full Right-Click Menu (Win 10 Style)",
            height=34,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(weight="bold"),
            command=self.enable_classic_context_menu,
        )
        self.btn_classic_ctx.pack(fill="x", padx=15, pady=4)

        self.btn_modern_ctx = ctk.CTkButton(
            ui_card,
            text="🔄 Restore Default Windows 11 Compact Menu",
            height=34,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(weight="bold"),
            command=self.restore_win11_context_menu,
        )
        self.btn_modern_ctx.pack(fill="x", padx=15, pady=4)

        self.btn_godmode = ctk.CTkButton(
            ui_card,
            text="🛠️ Create 'Windows God Mode' Control Panel on Desktop",
            height=34,
            fg_color="#8E44AD",
            hover_color="#6C3483",
            font=ctk.CTkFont(weight="bold"),
            command=self.create_god_mode_folder,
        )
        self.btn_godmode.pack(fill="x", padx=15, pady=(4, 15))

        # ==========================================
        # CARD 2: OS HOSTS FILE TELEMETRY SHIELD
        # ==========================================
        hosts_card = ctk.CTkFrame(self)
        hosts_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            hosts_card,
            text="🛡️ OS HOSTS FILE TELEMETRY & AD SHIELD",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#E67E22",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        self.hosts_status_lbl = ctk.CTkLabel(
            hosts_card,
            text="Hosts Shield Status: Checking...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray",
        )
        self.hosts_status_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        self.btn_inject_hosts = ctk.CTkButton(
            hosts_card,
            text=f"🛡️ Block {len(self.TELEMETRY_DOMAINS)} Telemetry & Ad Domains in Hosts (Admin)",
            height=34,
            fg_color="#D35400",
            hover_color="#A04000",
            font=ctk.CTkFont(weight="bold"),
            command=self.apply_hosts_shield,
        )
        self.btn_inject_hosts.pack(fill="x", padx=15, pady=4)

        self.btn_clean_hosts = ctk.CTkButton(
            hosts_card,
            text="🧹 Remove Shield & Restore Clean Hosts File (Admin)",
            height=34,
            fg_color="#C0392B",
            hover_color="#922B21",
            font=ctk.CTkFont(weight="bold"),
            command=self.remove_hosts_shield,
        )
        self.btn_clean_hosts.pack(fill="x", padx=15, pady=4)

        self.btn_open_hosts = ctk.CTkButton(
            hosts_card,
            text="📄 Open Raw Hosts File in Notepad",
            height=34,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: subprocess.Popen(["notepad.exe", self.HOSTS_PATH]),
        )
        self.btn_open_hosts.pack(fill="x", padx=15, pady=(4, 15))

        # ==========================================
        # STATUS & LIVE HOSTS VIEWER
        # ==========================================
        self.status_bar = ctk.CTkLabel(
            self,
            text="Ready to customize Windows Shell and inspect C:\\Windows\\System32\\drivers\\etc\\hosts.",
            text_color="gray",
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, pady=(0, 4), sticky="w")

        self.hosts_viewer = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.hosts_viewer.grid(row=2, column=0, columnspan=2, sticky="nsew")

        self.refresh_state()

    def refresh_state(self):
        # 1. Check Classic Context Menu Registry Key
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.CLSID_KEY, 0, winreg.KEY_READ):
                self.ctx_status_lbl.configure(
                    text="Right-Click Menu: ✅ Classic Full Menu Active (Win 10 Style)",
                    text_color="#2FA572",
                )
        except OSError:
            self.ctx_status_lbl.configure(
                text="Right-Click Menu: Standard Windows 11 Compact Menu",
                text_color="#3B8ED0",
            )

        # 2. Read Hosts File
        self.hosts_viewer.configure(state="normal")
        self.hosts_viewer.delete("1.0", "end")
        try:
            if os.path.exists(self.HOSTS_PATH):
                with open(self.HOSTS_PATH, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self.hosts_viewer.insert("end", content)
                if self.BLOCK_START_TAG in content:
                    self.hosts_status_lbl.configure(
                        text=f"Hosts Shield: ✅ PROTECTED ({len(self.TELEMETRY_DOMAINS)} Telemetry Domains Blocked)",
                        text_color="#2FA572",
                    )
                else:
                    self.hosts_status_lbl.configure(
                        text="Hosts Shield: ⏸️ Standard Unfiltered Hosts File",
                        text_color="gray",
                    )
            else:
                self.hosts_viewer.insert("end", "# Hosts file not found.")
        except Exception as e:
            self.hosts_viewer.insert("end", f"# Error reading hosts file: {e}")
        self.hosts_viewer.configure(state="disabled")

    def enable_classic_context_menu(self):
        try:
            with winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER, self.CLSID_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                # Setting the default "(Default)" value to an empty string activates the classic menu
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "")
            self.restart_explorer()
            self.refresh_state()
            self.status_bar.configure(
                text="✅ Enabled Classic Right-Click Context Menu and restarted Windows Explorer!",
                text_color="#2FA572",
            )
        except Exception as e:
            self.status_bar.configure(text=f"❌ Failed to set context menu: {e}", text_color="#E74C3C")

    def restore_win11_context_menu(self):
        parent_key = r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}"
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, self.CLSID_KEY)
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, parent_key)
        except OSError:
            pass
        self.restart_explorer()
        self.refresh_state()
        self.status_bar.configure(
            text="🔄 Restored default Windows 11 right-click menu and restarted Explorer.",
            text_color="#3B8ED0",
        )

    def create_god_mode_folder(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        god_folder = os.path.join(desktop, "GodMode.{ED7BA470-8E54-465E-825C-99712043E01C}")
        try:
            os.makedirs(god_folder, exist_ok=True)
            self.status_bar.configure(
                text="🛠️ Created 'GodMode' Master Control Panel on your Desktop! Opening now...",
                text_color="#2FA572",
            )
            subprocess.Popen(["explorer.exe", god_folder])
        except Exception as e:
            self.status_bar.configure(text=f"❌ Could not create God Mode folder: {e}", text_color="#E74C3C")

    def apply_hosts_shield(self):
        if not SystemEngine.is_admin():
            self.status_bar.configure(
                text="⚠️ Modifying C:\\Windows\\System32\\drivers\\etc\\hosts requires Administrator Mode.",
                text_color="#E74C3C",
            )
            return

        try:
            if os.path.exists(self.HOSTS_PATH) and not os.path.exists(self.HOSTS_BACKUP):
                shutil.copy2(self.HOSTS_PATH, self.HOSTS_BACKUP)

            content = ""
            if os.path.exists(self.HOSTS_PATH):
                with open(self.HOSTS_PATH, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

            if self.BLOCK_START_TAG in content:
                self.status_bar.configure(
                    text="✅ Telemetry & Ad Shield is already active in your hosts file.",
                    text_color="#2FA572",
                )
                return

            block_lines = ["\n" + self.BLOCK_START_TAG]
            for dom in self.TELEMETRY_DOMAINS:
                block_lines.append(f"0.0.0.0 {dom}")
            block_lines.append(self.BLOCK_END_TAG + "\n")

            with open(self.HOSTS_PATH, "a", encoding="utf-8") as f:
                f.write("\n".join(block_lines))

            subprocess.run(["ipconfig", "/flushdns"], creationflags=subprocess.CREATE_NO_WINDOW)
            self.refresh_state()
            self.status_bar.configure(
                text=f"🛡️ Added {len(self.TELEMETRY_DOMAINS)} telemetry & ad-tracker blocks to Windows hosts file!",
                text_color="#2FA572",
            )
        except Exception as e:
            self.status_bar.configure(text=f"❌ Could not update hosts file: {e}", text_color="#E74C3C")

    def remove_hosts_shield(self):
        if not SystemEngine.is_admin():
            self.status_bar.configure(
                text="⚠️ Modifying the Windows hosts file requires Administrator Mode.",
                text_color="#E74C3C",
            )
            return

        try:
            if not os.path.exists(self.HOSTS_PATH):
                return
            with open(self.HOSTS_PATH, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            if self.BLOCK_START_TAG in content and self.BLOCK_END_TAG in content:
                before = content.split(self.BLOCK_START_TAG)[0].rstrip()
                after = content.split(self.BLOCK_END_TAG)[-1].lstrip()
                cleaned = before + ("\n\n" + after if after else "\n")
                with open(self.HOSTS_PATH, "w", encoding="utf-8") as f:
                    f.write(cleaned)

            subprocess.run(["ipconfig", "/flushdns"], creationflags=subprocess.CREATE_NO_WINDOW)
            self.refresh_state()
            self.status_bar.configure(
                text="🧹 Removed PC Optimizer Telemetry Shield from hosts file and flushed DNS.",
                text_color="#3B8ED0",
            )
        except Exception as e:
            self.status_bar.configure(text=f"❌ Error cleaning hosts file: {e}", text_color="#E74C3C")

    @staticmethod
    def restart_explorer():
        try:
            subprocess.run(
                ["taskkill", "/f", "/im", "explorer.exe"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )
            subprocess.Popen(["explorer.exe"])
        except Exception:
            pass