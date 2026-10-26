# pc_health_scorecard.py
import os
import sys
import json
import time
import shutil
import threading
import subprocess
import webbrowser
from datetime import datetime
import psutil
import customtkinter as ctk
from backend_engine import SystemEngine


def get_persistent_data_dir() -> str:
    """Returns a persistent directory next to the .exe or script (never a temporary _MEIPASS folder)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class PcHealthScorecardView(ctk.CTkFrame):
    """Modular 10-Point (0-100%) PC Health Scorecard & Styled HTML Technician Report Generator."""

    IGNORE_DEVICES_FILE = os.path.join(get_persistent_data_dir(), "ignored_devices.json")
    IGNORE_UPDATES_FILE = os.path.join(get_persistent_data_dir(), "ignored_updates.json")

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.last_audit = None

        # ==========================================
        # TOP SCORE HERO BANNER
        # ==========================================
        self.hero_card = ctk.CTkFrame(self)
        self.hero_card.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        score_box = ctk.CTkFrame(self.hero_card, fg_color=("gray85", "gray17"), width=155, height=105)
        score_box.pack(side="left", padx=18, pady=14)
        score_box.pack_propagate(False)

        ctk.CTkLabel(
            score_box, text="OVERALL SCORE", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray"
        ).pack(pady=(12, 0))

        self.score_num_lbl = ctk.CTkLabel(
            score_box, text="-- / 100", font=ctk.CTkFont(size=28, weight="bold"), text_color="#3B8ED0"
        )
        self.score_num_lbl.pack(pady=2)

        self.grade_lbl = ctk.CTkLabel(
            score_box, text="Not Audited", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray"
        )
        self.grade_lbl.pack()

        # Center Summary & Progress Bar
        mid_box = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        mid_box.pack(side="left", fill="x", expand=True, padx=10, pady=14)

        ctk.CTkLabel(
            mid_box,
            text="📋 10-POINT PC HEALTH SCORECARD & TECHNICIAN AUDIT",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#3B8ED0",
        ).pack(anchor="w")

        self.summary_lbl = ctk.CTkLabel(
            mid_box,
            text="Click 'Re-Run Health Audit' to inspect 10 hardware, security, software update, and hygiene metrics.",
            font=ctk.CTkFont(size=12),
            text_color="lightgray",
        )
        self.summary_lbl.pack(anchor="w", pady=(4, 8))

        self.score_bar = ctk.CTkProgressBar(mid_box, height=14, progress_color="#2FA572")
        self.score_bar.pack(fill="x", pady=(2, 4))
        self.score_bar.set(0)

        # Action Buttons on Right
        btn_col = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        btn_col.pack(side="right", padx=18, pady=14)

        self.audit_btn = ctk.CTkButton(
            btn_col,
            text="🔄 Re-Run Health Audit",
            width=220,
            height=38,
            fg_color="#3B8ED0",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.run_health_audit,
        )
        self.audit_btn.pack(pady=(0, 6))

        self.html_btn = ctk.CTkButton(
            btn_col,
            text="🌐 Export HTML Report",
            width=220,
            height=38,
            fg_color="#2FA572",
            hover_color="#1D7A52",
            font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled",
            command=self.export_html_report,
        )
        self.html_btn.pack()

        # ==========================================
        # STATUS BAR
        # ==========================================
        self.status_lbl = ctk.CTkLabel(
            self,
            text="Ready to perform 10-point diagnostic audit.",
            text_color="gray",
        )
        self.status_lbl.grid(row=1, column=0, pady=(0, 4), sticky="w")

        # ==========================================
        # SCROLLABLE AUDIT BREAKDOWN CARDS
        # ==========================================
        self.cards_scroll = ctk.CTkScrollableFrame(self)
        self.cards_scroll.grid(row=2, column=0, sticky="nsew")

    # ==========================================
    # SHARED IGNORE FILE LOADERS
    # ==========================================
    @classmethod
    def load_ignored_devices(cls) -> set:
        paths_to_check = [
            cls.IGNORE_DEVICES_FILE,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "ignored_devices.json"),
        ]
        ignored = set()
        for p in paths_to_check:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        ignored.update(json.load(f))
                except Exception:
                    pass
        return ignored

    @classmethod
    def load_ignored_updates(cls) -> set:
        paths_to_check = [
            cls.IGNORE_UPDATES_FILE,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "ignored_updates.json"),
        ]
        ignored = set()
        for p in paths_to_check:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        ignored.update(x.lower() for x in json.load(f))
                except Exception:
                    pass
        return ignored

    @classmethod
    def _count_outdated_winget_apps(cls) -> int:
        """Counts outdated Winget apps while excluding muted/ignored packages from ignored_updates.json."""
        if not shutil.which("winget"):
            return 0

        ignored_pkgs = cls.load_ignored_updates()

        try:
            res = subprocess.run(
                ["winget", "upgrade", "--accept-source-agreements"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=16,
            )
            out = res.stdout or ""
            lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
            sep_idx = -1
            for idx, ln in enumerate(lines):
                if "---" in ln and len(ln) > 15:
                    sep_idx = idx
                    break
            if sep_idx != -1:
                active_count = 0
                for ln in lines[sep_idx + 1 :]:
                    low = ln.lower()
                    if (
                        "upgrades available" in low
                        or "upgrade available" in low
                        or low.startswith("the following")
                        or "package(s) have" in low
                    ):
                        continue
                    tokens = ln.split()
                    if len(tokens) >= 4:
                        pkg_id = tokens[-4].lower()
                        if pkg_id not in ignored_pkgs:
                            active_count += 1
                return active_count
        except Exception:
            pass
        return 0

    @staticmethod
    def _estimate_temp_junk_bytes() -> int:
        """Quickly samples User Temp, Windows Temp, and Browser Cache folders."""
        targets = SystemEngine.get_target_folders(
            user_temp=True, win_temp=True, prefetch=False, chrome=True, edge=True
        )
        total = 0
        for path in targets.values():
            if not path or not os.path.exists(path):
                continue
            try:
                for root, _, files in os.walk(path):
                    for f in files:
                        try:
                            total += os.path.getsize(os.path.join(root, f))
                        except OSError:
                            continue
            except OSError:
                continue
        return total

    # ==========================================
    # 10-POINT AUDIT ENGINE
    # ==========================================
    def run_health_audit(self):
        self.audit_btn.configure(state="disabled", text="⏳ Auditing 10 Metrics...")
        self.html_btn.configure(state="disabled")
        self.status_lbl.configure(
            text="Running 10-point diagnostic: Disk, SMART, Defender, Firewall, Outdated Apps, RAM, Drivers, Temp Junk, Startup & BSODs...",
            text_color="#3B8ED0",
        )
        for w in self.cards_scroll.winfo_children():
            w.destroy()

        threading.Thread(target=self._audit_worker, daemon=True).start()

    def _audit_worker(self):
        checks = []
        total_score = 0

        # ---------------------------------------------------------
        # 1. Primary Drive Free Space (12 pts)
        # ---------------------------------------------------------
        try:
            disk = psutil.disk_usage("C:\\")
            free_pct = 100.0 - disk.percent
            free_gb = disk.free / (1024**3)
            if free_pct >= 20:
                pts, status = 12, "Optimal"
                rec = f"Drive C: has plenty of breathing room ({free_gb:.1f} GB / {free_pct:.1f}% free)."
            elif free_pct >= 10:
                pts, status = 7, "Moderate"
                rec = f"Drive C: has {free_gb:.1f} GB ({free_pct:.1f}%) free. Run Junk Cleaner & Large File Finder."
            else:
                pts, status = 2, "Critical Low Space"
                rec = f"Drive C: is critically full ({free_gb:.1f} GB free)! SSD performance will degrade."
        except Exception:
            pts, status, rec = 10, "Checked", "Drive C: online."

        total_score += pts
        checks.append(
            {
                "title": "1. Primary Drive Free Space (SSD Breathing Room)",
                "points": pts,
                "max": 12,
                "status": status,
                "detail": rec,
            }
        )

        # ---------------------------------------------------------
        # Combined PowerShell Check (SMART, Defender, Firewall, Drivers)
        # ---------------------------------------------------------
        ps_cmd = (
            "$unhealthy = @(Get-PhysicalDisk -ErrorAction SilentlyContinue | Where-Object { $_.HealthStatus -ne 'Healthy' }).Count; "
            "$mp = Get-MpComputerStatus -ErrorAction SilentlyContinue | Select-Object RealTimeProtectionEnabled; "
            "$fwOff = @(Get-NetFirewallProfile -ErrorAction SilentlyContinue | Where-Object { $_.Enabled -eq $false }).Count; "
            "$errDevs = @(Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue | "
            "Where-Object { $_.ConfigManagerErrorCode -ne 0 -and $_.ConfigManagerErrorCode -ne 22 -and "
            "-not ($_.ConfigManagerErrorCode -eq 10 -and ($_.DeviceID -like 'BTH*' -or $_.Name -like '*Bluetooth*')) } | "
            "Select-Object -ExpandProperty DeviceID); "
            "@{unhealthy=$unhealthy; rtp=$mp.RealTimeProtectionEnabled; fwOff=$fwOff; errDevs=$errDevs} | ConvertTo-Json -Compress"
        )
        unhealthy_disks = 0
        rtp_enabled = True
        fw_disabled_count = 0
        driver_errors = 0
        ignored_ids = self.load_ignored_devices()

        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                timeout=9,
            ).strip()
            if out:
                d = json.loads(out)
                unhealthy_disks = int(d.get("unhealthy") or 0)
                if d.get("rtp") is False:
                    rtp_enabled = False
                fw_disabled_count = int(d.get("fwOff") or 0)
                raw_err_devs = d.get("errDevs") or []
                if isinstance(raw_err_devs, str):
                    raw_err_devs = [raw_err_devs]
                active_errs = [dev_id for dev_id in raw_err_devs if dev_id not in ignored_ids]
                driver_errors = len(active_errs)
        except Exception:
            pass

        # ---------------------------------------------------------
        # 2. Physical Disk S.M.A.R.T. Reliability (12 pts)
        # ---------------------------------------------------------
        if unhealthy_disks == 0:
            s_pts, s_stat, s_rec = 12, "Healthy", "All physical SSD/HDD drives report Healthy S.M.A.R.T. status."
        else:
            s_pts, s_stat, s_rec = (
                0,
                "Warning",
                f"{unhealthy_disks} physical drive(s) reported S.M.A.R.T. warnings! Back up data immediately.",
            )
        total_score += s_pts
        checks.append(
            {
                "title": "2. Physical Disk S.M.A.R.T. Reliability",
                "points": s_pts,
                "max": 12,
                "status": s_stat,
                "detail": s_rec,
            }
        )

        # ---------------------------------------------------------
        # 3. Antivirus & Real-Time Security Shield (12 pts)
        # ---------------------------------------------------------
        if rtp_enabled:
            a_pts, a_stat, a_rec = 12, "Protected", "Windows Defender Real-Time Protection is active and monitoring."
        else:
            a_pts, a_stat, a_rec = (
                2,
                "Vulnerable",
                "Real-Time Antivirus Protection appears disabled! Enable Windows Defender.",
            )
        total_score += a_pts
        checks.append(
            {
                "title": "3. Antivirus & Real-Time Security Shield",
                "points": a_pts,
                "max": 12,
                "status": a_stat,
                "detail": a_rec,
            }
        )

        # ---------------------------------------------------------
        # 4. Windows Network Firewall Profiles (10 pts)
        # ---------------------------------------------------------
        if fw_disabled_count == 0:
            fw_pts, fw_stat, fw_rec = 10, "All Active", "Domain, Private, and Public Windows Firewall shields are active."
        else:
            fw_pts = max(2, 10 - (fw_disabled_count * 4))
            fw_stat = f"{fw_disabled_count} Profile(s) Off"
            fw_rec = f"{fw_disabled_count} Windows Firewall profile(s) are turned off. Open 'Security & Open Ports' to review."
        total_score += fw_pts
        checks.append(
            {
                "title": "4. Windows Network Firewall Protection",
                "points": fw_pts,
                "max": 10,
                "status": fw_stat,
                "detail": fw_rec,
            }
        )

        # ---------------------------------------------------------
        # 5. Outdated Software & Patch Hygiene (12 pts)
        # ---------------------------------------------------------
        outdated_apps = self._count_outdated_winget_apps()
        if outdated_apps == 0:
            up_pts, up_stat = 12, "Up to Date"
            up_rec = "All active Winget-tracked applications on this PC are running their latest versions."
        elif outdated_apps <= 2:
            up_pts, up_stat = 10, f"{outdated_apps} Minor Update(s)"
            up_rec = f"{outdated_apps} installed app(s) have updates available. Open 'Software Update Center' to patch or mute."
        elif outdated_apps <= 6:
            up_pts, up_stat = 7, f"{outdated_apps} Outdated Apps"
            up_rec = f"{outdated_apps} installed programs are out of date. Run 'Software Update Center' to update or mute loops."
        else:
            up_pts, up_stat = 3, f"{outdated_apps} Outdated Apps"
            up_rec = f"Found {outdated_apps} outdated applications! Open 'Software Update Center' to smart-update or mute."
        total_score += up_pts
        checks.append(
            {
                "title": "5. Software Update & Patch Hygiene (Winget Audit)",
                "points": up_pts,
                "max": 12,
                "status": up_stat,
                "detail": up_rec,
            }
        )

        # ---------------------------------------------------------
        # 6. Physical Memory (RAM) Headroom (10 pts)
        # ---------------------------------------------------------
        mem = psutil.virtual_memory()
        if mem.percent <= 75:
            m_pts, m_stat = 10, "Healthy"
            m_rec = f"RAM usage is comfortable at {mem.percent:.1f}% ({SystemEngine.format_bytes(mem.available)} free)."
        elif mem.percent <= 88:
            m_pts, m_stat = 6, "Elevated"
            m_rec = f"RAM usage is {mem.percent:.1f}%. Use 'Boost RAM' or 'Tray Auto-RAM Guard' to free working sets."
        else:
            m_pts, m_stat = 2, "High Pressure"
            m_rec = f"RAM usage is critically high ({mem.percent:.1f}%). Close heavy apps or enable Auto-RAM Guard."
        total_score += m_pts
        checks.append(
            {
                "title": "6. Physical Memory (RAM) Headroom",
                "points": m_pts,
                "max": 10,
                "status": m_stat,
                "detail": m_rec,
            }
        )

        # ---------------------------------------------------------
        # 7. Hardware & Driver Integrity (10 pts)
        # ---------------------------------------------------------
        if driver_errors == 0:
            d_pts, d_stat, d_rec = 10, "Optimal", "0 active hardware devices reporting Device Manager error codes."
        else:
            d_pts = max(2, 10 - (driver_errors * 4))
            d_stat = f"{driver_errors} Error(s)"
            d_rec = f"{driver_errors} device(s) have driver errors. Open 'Driver Backup Center' to inspect or mute."
        total_score += d_pts
        checks.append(
            {
                "title": "7. Hardware & Driver Integrity",
                "points": d_pts,
                "max": 10,
                "status": d_stat,
                "detail": d_rec,
            }
        )

        # ---------------------------------------------------------
        # 8. Temp Junk & Browser Cache Clutter (8 pts)
        # ---------------------------------------------------------
        junk_bytes = self._estimate_temp_junk_bytes()
        junk_mb = junk_bytes / (1024 * 1024)
        junk_fmt = SystemEngine.format_bytes(junk_bytes)
        if junk_mb <= 500:
            j_pts, j_stat = 8, "Clean"
            j_rec = f"Only {junk_fmt} of temporary cache files detected across system & browser temp folders."
        elif junk_mb <= 2048:
            j_pts, j_stat = 5, f"{junk_fmt} Junk"
            j_rec = f"Found {junk_fmt} of temporary clutter. Run 'Junk & Quick Clean' or '1-Click Autopilot' to reclaim space."
        else:
            j_pts, j_stat = 2, f"{junk_fmt} Bloat"
            j_rec = f"Heavy cache accumulation ({junk_fmt} of temp junk)! Run 'Junk & Quick Clean' to free SSD space."
        total_score += j_pts
        checks.append(
            {
                "title": "8. Temporary Junk & Browser Cache Hygiene",
                "points": j_pts,
                "max": 8,
                "status": j_stat,
                "detail": j_rec,
            }
        )

        # ---------------------------------------------------------
        # 9. Boot & Startup Program Bloat (7 pts)
        # ---------------------------------------------------------
        startup_apps = SystemEngine.get_startup_apps()
        st_count = len(startup_apps)
        if st_count <= 8:
            st_pts, st_stat = 7, f"Fast Boot ({st_count} Apps)"
            st_rec = f"Only {st_count} registry startup program(s) configured to launch at Windows boot."
        elif st_count <= 14:
            st_pts, st_stat = 4, f"Moderate ({st_count} Apps)"
            st_rec = f"{st_count} programs launch automatically at boot. Review 'Startup Apps Manager' to speed up login."
        else:
            st_pts, st_stat = 2, f"Heavy Bloat ({st_count} Apps)"
            st_rec = f"{st_count} startup apps are slowing down Windows boot time and eating background RAM!"
        total_score += st_pts
        checks.append(
            {
                "title": "9. Boot Speed & Startup Program Hygiene",
                "points": st_pts,
                "max": 7,
                "status": st_stat,
                "detail": st_rec,
            }
        )

        # ---------------------------------------------------------
        # 10. Crash History & Reboot Hygiene (7 pts)
        # ---------------------------------------------------------
        uptime_days = (time.time() - psutil.boot_time()) / 86400.0
        minidump_dir = r"C:\Windows\Minidump"
        dumps = 0
        if os.path.exists(minidump_dir):
            try:
                dumps = len([f for f in os.listdir(minidump_dir) if f.lower().endswith(".dmp")])
            except Exception:
                pass

        if dumps == 0 and uptime_days <= 10:
            u_pts, u_stat = 7, "Stable"
            u_rec = f"0 BSOD crash dumps found; clean system uptime of {uptime_days:.1f} days."
        elif dumps > 0:
            u_pts, u_stat = 2, f"{dumps} BSOD Dump(s)"
            u_rec = f"Found {dumps} minidump crash file(s) in C:\\Windows\\Minidump. Check 'Crash & Event Logs'."
        else:
            u_pts, u_stat = 4, "Reboot Due"
            u_rec = f"PC has been running for {uptime_days:.1f} days without a restart. Reboot to clear kernel pools."
        total_score += u_pts
        checks.append(
            {
                "title": "10. Crash History & System Uptime Hygiene",
                "points": u_pts,
                "max": 7,
                "status": u_stat,
                "detail": u_rec,
            }
        )

        self.last_audit = {
            "score": total_score,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "checks": checks,
        }

        self.after(0, self._render_audit_results)

    def _render_audit_results(self):
        self.audit_btn.configure(state="normal", text="🔄 Re-Run Health Audit")
        self.html_btn.configure(state="normal")

        score = self.last_audit["score"]
        if score >= 90:
            grade, color = "Grade A+ (Excellent)", "#2FA572"
        elif score >= 75:
            grade, color = "Grade B (Good)", "#3B8ED0"
        elif score >= 60:
            grade, color = "Grade C (Fair - Tune-Up Recommended)", "#E67E22"
        else:
            grade, color = "Grade D (Maintenance Required)", "#E74C3C"

        self.score_num_lbl.configure(text=f"{score} / 100", text_color=color)
        self.grade_lbl.configure(text=grade, text_color=color)
        self.score_bar.configure(progress_color=color)
        self.score_bar.set(score / 100.0)

        self.summary_lbl.configure(
            text=f"10-Point Audit completed at {self.last_audit['timestamp']}. Click 'Export HTML Report' for a printable certificate.",
            text_color="lightgray",
        )
        self.status_lbl.configure(
            text=f"10-Point Health Audit Complete — Overall Score: {score}/100 ({grade})", text_color=color
        )

        for item in self.last_audit["checks"]:
            card = ctk.CTkFrame(self.cards_scroll)
            card.pack(fill="x", padx=5, pady=4)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=14, pady=(8, 2))

            ctk.CTkLabel(
                top,
                text=item["title"],
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#3B8ED0",
            ).pack(side="left")

            is_full = item["points"] == item["max"]
            badge_col = (
                "#2FA572"
                if is_full
                else ("#E67E22" if item["points"] >= item["max"] * 0.5 else "#E74C3C")
            )

            ctk.CTkLabel(
                top,
                text=f"{item['status']}  ({item['points']} / {item['max']} pts)",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=badge_col,
            ).pack(side="right")

            ctk.CTkLabel(
                card,
                text=item["detail"],
                font=ctk.CTkFont(size=12),
                text_color="lightgray",
                wraplength=760,
                justify="left",
            ).pack(anchor="w", padx=14, pady=(0, 8))

    def export_html_report(self):
        if not self.last_audit:
            return

        specs = SystemEngine.get_detailed_specs()
        score = self.last_audit["score"]
        ts = self.last_audit["timestamp"]
        badge_color = "#2FA572" if score >= 85 else ("#E67E22" if score >= 65 else "#E74C3C")

        check_rows = ""
        for c in self.last_audit["checks"]:
            check_rows += f"""
            <tr>
                <td><strong>{c['title']}</strong><br><span style="color:#94a3b8;font-size:13px;">{c['detail']}</span></td>
                <td style="text-align:center;font-weight:bold;">{c['status']}</td>
                <td style="text-align:right;font-weight:bold;color:#38bdf8;">{c['points']} / {c['max']}</td>
            </tr>
            """

        spec_cards_html = ""
        for cat, items in specs.items():
            rows_html = "".join(
                [
                    f"<div style='display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #1e293b;'><span>{k}</span><strong style='color:#e2e8f0;'>{v}</strong></div>"
                    for k, v in items.items()
                ]
            )
            spec_cards_html += f"""
            <div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:14px;">
                <h3 style="margin:0 0 10px 0;color:#38bdf8;font-size:15px;">{cat}</h3>
                {rows_html}
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>PC Health & Maintenance Audit Report</title>
<style>
    body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #020617; color: #f8fafc; margin: 0; padding: 30px; }}
    .container {{ max-width: 960px; margin: auto; background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 28px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
    .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #1e293b; padding-bottom: 20px; margin-bottom: 24px; }}
    .score-badge {{ background: {badge_color}; color: #fff; padding: 14px 26px; border-radius: 10px; font-size: 28px; font-weight: bold; text-align: center; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 28px; }}
    th, td {{ padding: 12px; border-bottom: 1px solid #1e293b; text-align: left; }}
    th {{ color: #38bdf8; font-size: 13px; text-transform: uppercase; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <h1 style="margin:0;color:#38bdf8;">⚡ 10-Point PC Health & Technician Audit Report</h1>
            <p style="margin:5px 0 0 0;color:#94a3b8;">Generated on {ts} by Windows System Optimizer Ultimate</p>
        </div>
        <div class="score-badge">{score} / 100</div>
    </div>
    <h2>10-Point Diagnostic Scorecard Breakdown</h2>
    <table>
        <thead><tr><th>Diagnostic Check</th><th style="text-align:center;">Status</th><th style="text-align:right;">Points</th></tr></thead>
        <tbody>{check_rows}</tbody>
    </table>
    <h2>Complete Hardware & System Profile</h2>
    <div class="grid">{spec_cards_html}</div>
</div>
</body>
</html>"""

        report_path = os.path.join(os.path.expanduser("~"), "PC_Health_Audit_Report.html")
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            self.status_lbl.configure(
                text=f"✅ Saved & opened 10-point HTML report: {report_path}", text_color="#2FA572"
            )
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
        except Exception as e:
            self.status_lbl.configure(text=f"❌ Could not save HTML report: {e}", text_color="#E74C3C")