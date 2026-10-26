# update_center.py
import os
import re
import json
import shutil
import threading
import subprocess
import psutil
import customtkinter as ctk


class UpdateCenterView(ctk.CTkFrame):
    """Smart Winget Software Update Center with Auto-Process Closing, Force-Install Fallback & Package Pinning."""

    IGNORE_UPDATES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ignored_updates.json")

    # Known self-updating or retired packages that fail standard Winget upgrades
    KNOWN_QUIRKS = {
        "ElectronicArts.Origin": "⚠️ Retired by EA (404 Dead Server) — Recommend Ignore or Uninstall",
        "Cfx.re.FiveM": "⚠️ Self-Updating Client (Hash Mismatch in Admin Mode) — Recommend Ignore",
        "SharkLabs.ClownfishVoiceChanger": "⚠️ Legacy Installer (Reports 'Unknown' Version to Registry) — Recommend Ignore",
        "espeak.espeak": "⚠️ Legacy Installer (Reports 'Unknown' Version to Registry) — Recommend Ignore",
    }

    # Map package IDs to process names that lock files during upgrade (Exit Code 6)
    PROCESS_LOCKS = {
        "OBSProject.OBSStudio": ["obs64.exe", "obs32.exe", "obs-ffmpeg-mux.exe"],
        "dev47apps.DroidCamOBSPlugin": ["obs64.exe", "DroidCamApp.exe"],
        "Audacity.Audacity": ["Audacity.exe"],
        "Discord.Discord": ["Discord.exe"],
        "Spotify.Spotify": ["Spotify.exe"],
        "Brave.Brave": ["brave.exe"],
        "Google.Chrome": ["chrome.exe"],
        "Mozilla.Firefox": ["firefox.exe"],
    }

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)

        self.has_winget = shutil.which("winget") is not None
        self.ignored_pkgs = self.load_ignored_packages()
        self.outdated_list = []
        self.busy = False

        # ==========================================
        # TOP CONTROL BAR
        # ==========================================
        top_card = ctk.CTkFrame(self)
        top_card.grid(row=0, column=0, pady=(0, 8), sticky="ew")

        row1 = ctk.CTkFrame(top_card, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(12, 6))

        ctk.CTkLabel(
            row1,
            text="🔄 SMART SOFTWARE UPDATE & PATCH REMEDIATION CENTER",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0",
        ).pack(side="left")

        self.badge_lbl = ctk.CTkLabel(
            row1,
            text="Click 'Scan for Updates' to inspect installed packages.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray",
        )
        self.badge_lbl.pack(side="right")

        row2 = ctk.CTkFrame(top_card, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(2, 12))

        self.scan_btn = ctk.CTkButton(
            row2,
            text="🔍 Scan for Updates",
            width=165,
            height=34,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(weight="bold"),
            command=self.scan_updates,
        )
        self.scan_btn.pack(side="left", padx=(0, 6))

        self.update_all_btn = ctk.CTkButton(
            row2,
            text="🚀 Smart-Update All Valid Apps",
            width=225,
            height=34,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(weight="bold"),
            command=self.smart_update_all,
        )
        self.update_all_btn.pack(side="left", padx=6)

        self.mute_ghosts_btn = ctk.CTkButton(
            row2,
            text="🔇 Auto-Mute 'Unknown' / Broken Loops",
            width=245,
            height=34,
            fg_color="#D35400",
            hover_color="#A04000",
            font=ctk.CTkFont(weight="bold"),
            command=self.auto_mute_quirky_packages,
        )
        self.mute_ghosts_btn.pack(side="left", padx=6)

        self.reset_pins_btn = ctk.CTkButton(
            row2,
            text="🔓 Unmute All",
            width=115,
            height=34,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(weight="bold"),
            command=self.clear_ignored_packages,
        )
        self.reset_pins_btn.pack(side="right")

        # ==========================================
        # PROGRESS BAR
        # ==========================================
        self.progress = ctk.CTkProgressBar(self, height=10, progress_color="#2FA572")
        self.progress.grid(row=1, column=0, pady=(0, 8), sticky="ew")
        self.progress.set(0)

        # ==========================================
        # SCROLLABLE INTERACTIVE PACKAGE CARDS
        # ==========================================
        self.pkg_scroll = ctk.CTkScrollableFrame(self)
        self.pkg_scroll.grid(row=2, column=0, pady=(0, 8), sticky="nsew")

        # ==========================================
        # LIVE DIAGNOSTIC LOG CONSOLE
        # ==========================================
        self.log_box = ctk.CTkTextbox(self, height=135, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=3, column=0, sticky="ew")
        self.log_message(
            "Smart Software Update Center Ready.\n"
            "• Automatically closes locked apps (like OBS), bypasses 'Different Install Tech' blocks, and lets you mute 'Unknown' version loops."
        )

        self.after(300, self.scan_updates)

    # ==========================================
    # PERSISTENT IGNORE / PIN LIST
    # ==========================================
    @classmethod
    def load_ignored_packages(cls) -> set:
        if os.path.exists(cls.IGNORE_UPDATES_FILE):
            try:
                with open(cls.IGNORE_UPDATES_FILE, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                pass
        return set()

    def save_ignored_packages(self):
        try:
            with open(self.IGNORE_UPDATES_FILE, "w", encoding="utf-8") as f:
                json.dump(list(self.ignored_pkgs), f)
        except Exception:
            pass

    def log_message(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ==========================================
    # WINGET UPGRADE TABLE PARSER
    # ==========================================
    def scan_updates(self):
        if self.busy or not self.has_winget:
            return
        self.busy = True
        self.scan_btn.configure(state="disabled", text="⏳ Scanning...")
        self.update_all_btn.configure(state="disabled")
        self.progress.configure(mode="indeterminate")
        self.progress.start()

        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        self.after(0, lambda: self.log_message("\n--- Scanning Installed Software for Updates (winget upgrade) ---"))
        parsed = []
        try:
            res = subprocess.run(
                ["winget", "upgrade", "--accept-source-agreements"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=30,
            )
            out = res.stdout or ""
            lines = [ln.rstrip() for ln in out.splitlines() if ln.strip()]

            # Locate header and separator line "---"
            sep_idx = -1
            for i, ln in enumerate(lines):
                if "---" in ln and len(ln.strip()) > 15:
                    sep_idx = i
                    break

            if sep_idx > 0:
                for ln in lines[sep_idx + 1 :]:
                    clean_ln = ln.strip()
                    low = clean_ln.lower()
                    if (
                        "upgrades available" in low
                        or "upgrade available" in low
                        or low.startswith("the following")
                        or "package(s) have" in low
                    ):
                        continue

                    # Parse columns using 2+ spaces or tail token splitting
                    tokens = clean_ln.split()
                    if len(tokens) >= 4:
                        source = tokens[-1]
                        avail_ver = tokens[-2]
                        cur_ver = tokens[-3]
                        pkg_id = tokens[-4]
                        name = " ".join(tokens[:-4]).strip()
                        if not name:
                            name = pkg_id

                        if pkg_id not in self.ignored_pkgs:
                            parsed.append(
                                {
                                    "name": name,
                                    "id": pkg_id,
                                    "current": cur_ver,
                                    "available": avail_ver,
                                    "source": source,
                                }
                            )
        except Exception as e:
            self.after(0, lambda err=e: self.log_message(f"[!] Scan error: {err}"))

        self.outdated_list = parsed
        self.busy = False
        self.after(0, self._render_package_cards)

    def _render_package_cards(self):
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(1.0)
        self.scan_btn.configure(state="normal", text="🔍 Scan for Updates")
        self.update_all_btn.configure(state="normal")

        for w in self.pkg_scroll.winfo_children():
            w.destroy()

        count = len(self.outdated_list)
        muted_cnt = len(self.ignored_pkgs)
        if count == 0:
            self.badge_lbl.configure(
                text=f"✅ All Active Software Up to Date! ({muted_cnt} Muted)",
                text_color="#2FA572",
            )
            ctk.CTkLabel(
                self.pkg_scroll,
                text="🎉 Zero pending software updates! Your PC's applications are completely up to date.",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#2FA572",
            ).pack(pady=35)
            self.log_message(f"=== Scan Complete: 0 active updates needed ({muted_cnt} muted packages hidden) ===")
            return

        self.badge_lbl.configure(
            text=f"⚠️ {count} Update(s) Available ({muted_cnt} Muted)",
            text_color="#E67E22",
        )
        self.log_message(f"=== Found {count} active package update(s). Use the cards above to update or mute ===")

        for pkg in self.outdated_list:
            pkg_id = pkg["id"]
            is_unknown = pkg["current"].lower() == "unknown"
            quirk_note = self.KNOWN_QUIRKS.get(pkg_id, "")
            if is_unknown and not quirk_note:
                quirk_note = "⚠️ Reports 'Unknown' Installed Version — May loop endlessly unless muted after update."

            card_bg = ("#FEF9E7", "#3A2E18") if (quirk_note or is_unknown) else ("gray85", "gray17")
            card = ctk.CTkFrame(self.pkg_scroll, fg_color=card_bg)
            card.pack(fill="x", padx=5, pady=4)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=14, pady=8)

            ctk.CTkLabel(
                left,
                text=f"📦 {pkg['name']}   ({pkg_id})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#3B8ED0",
            ).pack(anchor="w")

            ver_txt = f"Installed: {pkg['current']}   ➔   Available: {pkg['available']}"
            if quirk_note:
                ver_txt += f"   |   {quirk_note}"

            ctk.CTkLabel(
                left,
                text=ver_txt,
                font=ctk.CTkFont(size=11),
                text_color="#F39C12" if quirk_note else "lightgray",
            ).pack(anchor="w")

            btn_box = ctk.CTkFrame(card, fg_color="transparent")
            btn_box.pack(side="right", padx=10, pady=8)

            ctk.CTkButton(
                btn_box,
                text="🚀 Smart Update",
                width=125,
                height=28,
                fg_color="#2FA572",
                hover_color="#1D7A52",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda p=pkg: self.update_single_package(p),
            ).pack(side="right", padx=4)

            ctk.CTkButton(
                btn_box,
                text="🔇 Mute / Ignore",
                width=120,
                height=28,
                fg_color="#34495E",
                hover_color="#2C3E50",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda p=pkg: self.mute_package(p["id"], p["name"]),
            ).pack(side="right", padx=4)

    # ==========================================
    # SMART REMEDIATION ENGINE
    # ==========================================
    def _close_locking_processes(self, pkg_id: str):
        """Closes running processes (like obs64.exe) so Winget doesn't fail with Exit Code 6."""
        targets = [n.lower() for n in self.PROCESS_LOCKS.get(pkg_id, [])]
        if not targets:
            return
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pname = (proc.info["name"] or "").lower()
                if pname in targets:
                    self.after(
                        0,
                        lambda n=proc.info["name"]: self.log_message(
                            f"  [🔓 Auto-Unlock] Closing running {n} so installer can overwrite files..."
                        ),
                    )
                    proc.terminate()
                    proc.wait(timeout=3)
            except Exception:
                pass

    def _smart_upgrade_pkg_sync(self, pkg: dict) -> bool:
        """Upgrades a single package with process unlocking & force-install fallback for tech changes."""
        pkg_id = pkg["id"]
        name = pkg["name"]

        # 1. Close known locking processes first
        self._close_locking_processes(pkg_id)

        # 2. Run standard winget upgrade
        cmd = [
            "winget",
            "upgrade",
            "--id",
            pkg_id,
            "-e",
            "--silent",
            "--include-unknown",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ]
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        out = (res.stdout or "") + "\n" + (res.stderr or "")
        out_low = out.lower()

        if res.returncode == 0 or "successfully installed" in out_low or "no applicable upgrade" in out_low:
            # If the package had "Unknown" version before, auto-mute it so it doesn't loop forever!
            if pkg["current"].lower() == "unknown":
                self.ignored_pkgs.add(pkg_id)
                self.save_ignored_packages()
                self.after(
                    0,
                    lambda n=name: self.log_message(
                        f"  ✅ {n} installed! Auto-muted '{pkg_id}' so its 'Unknown' registry version stops looping."
                    ),
                )
            else:
                self.after(0, lambda n=name: self.log_message(f"  ✅ Successfully updated {n}!"))
            return True

        # 3. Handle "different install technology" block (e.g. Audacity 3.7 -> 4.0 or Epic Online Services)
        if "different install technology" in out_low or "uninstall each package" in out_low:
            self.after(
                0,
                lambda n=name: self.log_message(
                    f"  [⚡ Tech Migration] {n} changed installer technology. Running fresh 'winget install --force'..."
                ),
            )
            res2 = subprocess.run(
                [
                    "winget",
                    "install",
                    "--id",
                    pkg_id,
                    "-e",
                    "--silent",
                    "--force",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if res2.returncode == 0 or "successfully installed" in (res2.stdout or "").lower():
                self.ignored_pkgs.add(pkg_id)
                self.save_ignored_packages()
                self.after(
                    0,
                    lambda n=name: self.log_message(
                        f"  ✅ Fresh-installed {n} & muted old side-by-side stub!"
                    ),
                )
                return True

        # 4. Handle 404 Dead Server (Origin) or Admin Hash Mismatch (FiveM)
        if "0x80190194" in out_low or "not found (404)" in out_low or "hash does not match" in out_low:
            self.ignored_pkgs.add(pkg_id)
            self.save_ignored_packages()
            self.after(
                0,
                lambda n=name, p=pkg_id: self.log_message(
                    f"  🔇 Auto-muted '{n}' ({p}) due to broken upstream server (404 / Hash Mismatch)."
                ),
            )
            return False

        # 5. Handle Exit Code 6 (Files in use)
        if "exit code: 6" in out_low or "currently in use" in out_low:
            self.after(
                0,
                lambda n=name: self.log_message(
                    f"  ⚠️ {n} files are locked by another open app (e.g. Browser/Discord using OBS Virtual Camera). Close open apps and retry."
                ),
            )
            return False

        last_line = [ln.strip() for ln in out.splitlines() if ln.strip()][-1:]
        note = last_line[0] if last_line else f"Exit code {res.returncode}"
        self.after(0, lambda n=name, m=note: self.log_message(f"  ⚠️ {n}: {m[:90]}"))
        return False

    def update_single_package(self, pkg: dict):
        if self.busy:
            return
        self.busy = True
        self.progress.set(0.2)
        self.log_message(f"\n--- Smart-Updating {pkg['name']} ({pkg['id']}) ---")

        def worker():
            self._smart_upgrade_pkg_sync(pkg)
            self.busy = False
            self.after(200, self.scan_updates)

        threading.Thread(target=worker, daemon=True).start()

    def smart_update_all(self):
        if self.busy or not self.outdated_list:
            return
        self.busy = True
        self.update_all_btn.configure(state="disabled", text="⏳ Updating Apps...")
        self.scan_btn.configure(state="disabled")
        self.progress.set(0)

        targets = list(self.outdated_list)

        def worker():
            total = len(targets)
            self.after(
                0,
                lambda: self.log_message(f"\n=== Running Smart Remediation Upgrade for {total} Package(s) ==="),
            )
            for idx, pkg in enumerate(targets, start=1):
                self.after(
                    0,
                    lambda i=idx, t=total, n=pkg["name"]: self.log_message(
                        f"[{i}/{t}] Processing {n} ({pkg['current']} ➔ {pkg['available']})..."
                    ),
                )
                self._smart_upgrade_pkg_sync(pkg)
                self.after(0, lambda p=idx / total: self.progress.set(p))

            self.busy = False
            self.after(200, self.scan_updates)

        threading.Thread(target=worker, daemon=True).start()

    def mute_package(self, pkg_id: str, pkg_name: str):
        self.ignored_pkgs.add(pkg_id)
        self.save_ignored_packages()

        # Also attempt native winget pin add in background so winget CLI ignores it too
        def pin_worker():
            try:
                subprocess.run(
                    ["winget", "pin", "add", "--id", pkg_id, "-e"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=6,
                )
            except Exception:
                pass

        threading.Thread(target=pin_worker, daemon=True).start()
        self.log_message(
            f"[🔇 Muted] '{pkg_name}' ({pkg_id}) added to ignore list & pinned. It will no longer lower your Health Score!"
        )
        self.outdated_list = [p for p in self.outdated_list if p["id"] != pkg_id]
        self._render_package_cards()

    def auto_mute_quirky_packages(self):
        """1-Click button to mute Unknown-version loops, 404 Origin, and FiveM."""
        muted_now = []
        for pkg in list(self.outdated_list):
            pid = pkg["id"]
            if pid in self.KNOWN_QUIRKS or pkg["current"].lower() == "unknown":
                self.ignored_pkgs.add(pid)
                muted_now.append(pkg["name"])

        self.save_ignored_packages()
        self.outdated_list = [p for p in self.outdated_list if p["id"] not in self.ignored_pkgs]
        self._render_package_cards()

        if muted_now:
            self.log_message(
                f"[🔇 Auto-Muted {len(muted_now)} Quirky Packages] {', '.join(muted_now)} — Health Scorecard synced!"
            )
        else:
            self.log_message("[i] No 'Unknown' version loops or known dead packages found in current list.")

    def clear_ignored_packages(self):
        self.ignored_pkgs.clear()
        self.save_ignored_packages()

        def unpin_worker():
            try:
                subprocess.run(
                    ["winget", "pin", "reset", "--force"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=6,
                )
            except Exception:
                pass

        threading.Thread(target=unpin_worker, daemon=True).start()
        self.log_message("[🔓 Unmuted] Cleared all ignored software update rules. Re-scanning...")
        self.scan_updates()