# Windows-System-Optimizer-Ultimate
Windows System Optimizer Ultimate is a portable, 34-in-1 IT maintenance, hardware diagnostic, and gaming suite built in Python. It features 1-click Autopilot cleanup, RAM &amp; service tuning, an in-game HUD, laptop dGPU sleep protection, and deep GPU, network, and monitor diagnostics—all packed into a single, zero-bloat executable.

# ⚡ Windows System Optimizer Ultimate — IT Maintenance & Gaming Suite

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011%20(64--bit)-0078D6?style=for-the-badge&logo=windows)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![UI](https://img.shields.io/badge/GUI-CustomTkinter%20Dark-2FA572?style=for-the-badge)
![Tools](https://img.shields.io/badge/Integrated%20Tools-34%20Modules-8E44AD?style=for-the-badge)

**Windows System Optimizer Ultimate** is a portable, commercial-grade IT maintenance, hardware diagnostic, and gaming optimization suite built in Python. Designed to replace bloated commercial cleaners, driver updaters, and heavy OEM utilities, it consolidates **34 specialized system administration tools** into a single, zero-install executable (`PC_Optimizer_Ultimate.exe`).

---

## 🌟 Key Architectural Highlights

* **⚡ Lazy-Loading Zero-Overhead Engine:** Modules are dynamically imported on demand (`importlib`) and cached. Background UI redraws pause automatically when minimized to the System Tray (`0.0%` idle CPU overhead).
* **🔋 NVIDIA Advanced Optimus Laptop Sleep Guard:** Automatically detects laptop batteries and prevents background `nvidia-smi` polling from waking dedicated RTX GPUs out of `D3cold` (0W) sleep unless the user is actively viewing the *GPU Performance Center* tab.
* **🧠 Smart Energy Report Translator (`powercfg /energy`):** Automatically decodes cryptic Windows hardware `VID/PID` hex strings and Device Manager error codes (such as `0x16` / Code 22 on sleeping Bluetooth controllers or Logitech LIGHTSPEED 1000Hz receivers) into plain English while flagging genuine CPU timer locks like `LightingService.exe`.
* **⌨️ Global Win32 In-Game Hotkeys & Tray Super-Menu:** Control RAM trimming (`Ctrl + Shift + B`) and toggle the translucent **Floating Gaming HUD** (`Ctrl + Shift + H`) directly inside fullscreen games without Alt-Tabbing.
* **🤖 Headless Task Scheduler CLI (`--silent-autopilot`):** Run full system cleanups, working-set RAM trims, and DNS flushes silently in the background via command-line flags with zero GUI windows.

---

## 🧰 Complete 34-Tool Module Breakdown

### 1. Quick Start & Audit
| Tool | Module File | Description |
| :--- | :--- | :--- |
| **🤖 1-Click Autopilot** | `autopilot_maintenance.py` | Runs an 8-stage automated maintenance pipeline (Temp/Browser/Shader caches, RAM trim, Registry audit, Winget audit, DNS flush, Defender update, SSD TRIM) and opens a dark-mode HTML Master Report. |
| **📋 PC Health Scorecard** | `pc_health_scorecard.py` | Audits 10 weighted system health metrics on a **0–100 scale** (`Grade A+` to `D`) with intelligent filtering for disabled/sleeping peripherals and exportable HTML certificates. |
| **📌 Tray Auto-RAM Guard** | `tray_ram_guard.py` | System Tray daemon (`pystray`) with a right-click Super-Menu, configurable auto-RAM trim slider, and global Win32 hotkey listener. |

### 2. Performance & Tuning
| Tool | Module File | Description |
| :--- | :--- | :--- |
| **🎯 Floating Gaming HUD** | `hud_overlay.py` | Translucent, always-on-top, draggable pill overlay showing live `CPU %`, `RAM %`, `GPU % (°C)`, and `Ping ms` with 1-click RAM boost. |
| **🧠 CPU & RAM Tuner** | `cpu_ram_tuner.py` | Per-core utilization monitor, Win32 `EmptyWorkingSet` memory trimmer, and virtual memory (pagefile) configurator. |
| **⚙️ Services & Power Tamer** | `services_optimizer.py` | Curated Windows & ASUS service optimizer, **ASUS Laptop Eco Mode** (stops `LightingService.exe` 1ms timer locks), live custom service search, and **Smart Energy Report Translator**. |
| **📈 GPU Performance Center** | `gpu_performance_center.py` | Live GPU sensor telemetry, DirectX/NVIDIA/AMD 3D shader cache purger, and Hardware-Accelerated GPU Scheduling (`HAGS`) toggle. |
| **⏱ CPU & Disk Benchmark** | `thermal_stress_bench.py` | Multi-core CPU floating-point stress test and sequential NVMe/SSD Read/Write speed benchmark (`MB/s`). |
| **🎮 Gaming & Power Plans** | `gaming_booster.py` | Unlocks and switches between *Balanced*, *High Performance*, and the hidden Windows *Ultimate Performance* power scheme. |
| **📊 Process Manager** | `main.py` *(Built-in)* | Lists the Top 15 memory-consuming processes with instant task termination. |
| **🚀 Startup Apps Manager** | `main.py` *(Built-in)* | Audits and removes unnecessary `HKCU` and `HKLM` Registry `Run` startup programs. |

### 3. Storage & Cleanup
| Tool | Module File | Description |
| :--- | :--- | :--- |
| **🧹 Junk & Quick Clean** | `main.py` *(Built-in)* | Cleans `%TEMP%`, `Windows\Temp`, `Prefetch`, Chrome/Brave/Edge caches, and the Recycle Bin. |
| **💿 Disk SMART & Space** | `disk_health_analyzer.py` | Reads physical disk S.M.A.R.T. health, temperature, wear indicators, and partition space bars. |
| **📦 Large File Finder** | `large_file_finder.py` | Multi-threaded scanner that locates oversized files (`>100 MB` to `>5 GB`) across any drive or folder. |
| **📑 Duplicate File Finder** | `duplicate_finder.py` | Two-pass size + **SHA-256 cryptographic hash** scanner to find and remove 100% identical duplicate files. |
| **🔥 File Shredder & Unlocker** | `file_shredder_unlock.py` | Overwrites sensitive files with random cryptographic bytes (`os.urandom`) and zeros before deletion. |
| **🚮 App Uninstaller** | `app_uninstaller.py` | Fast registry-powered uninstaller for 64-bit, 32-bit, and user-installed applications. |

### 4. Updates & Recovery
| Tool | Module File | Description |
| :--- | :--- | :--- |
| **📥 1-Click App Installer** | `winget_app_installer.py` | Bulk silent installer for essential browsers, gaming launchers, media tools, and developer utilities via `winget`. |
| **🔄 Software Update Center** | `update_center.py` | Scans for outdated software, runs batch silent upgrades with `--force` fallback, and supports muting apps (`ignored_updates.json`). |
| **⏪ Restore & Scheduler** | `restore_scheduler.py` | Creates Windows System Restore Points (`vssadmin` / `Checkpoint-Computer`) and schedules weekly maintenance tasks. |
| **🔧 Windows Repair & Battery** | `system_repair.py` | Automates `SFC /scannow`, `DISM /RestoreHealth`, `CHKDSK`, Winsock/IP resets, and `powercfg /batteryreport`. |
| **🚨 Crash & Event Logs** | `crash_inspector.py` | Inspects `C:\Windows\Minidump` BSOD `.dmp` files and critical Windows Event Logs (`Kernel-Power 41`, `WHEA`, App Crashes). |

### 5. Privacy & Customization
| Tool | Module File | Description |
| :--- | :--- | :--- |
| **🔒 Privacy & Debloater** | `privacy_debloater.py` | Disables Windows telemetry, Advertising ID, Copilot/Cortana bloat, and removes pre-installed AppX packages. |
| **🎛 Input & Explorer Tweaks** | `win11_ui_customizer.py` | Enables **1:1 Raw Mouse Input** (disables pointer acceleration), disables Sticky Keys popups, shows file extensions/hidden files, and disables Start Menu Bing search. |
| **⚡ Shell & Hosts Shield** | `context_hosts_manager.py` | Restores the **Classic Windows 10 Full Right-Click Context Menu** on Windows 11 and blocks telemetry domains via the `hosts` file. |

### 6. Network & Security
| Tool | Module File | Description |
| :--- | :--- | :--- |
| **📡 LAN Ping Sweep Scanner** | `lan_network_scanner.py` | Multi-threaded local subnet scanner that discovers active IPs, MAC addresses (`arp -a`), and device hostnames. |
| **🔑 Wi-Fi Vault & DNS** | `wifi_vault_dns.py` | Recovers saved Wi-Fi SSIDs and cleartext passwords, benchmarks DNS ping latency, and switches between Cloudflare, Google, and Quad9 DNS. |
| **🌐 Speed & Ping Test** | `network_speedtest.py` | Measures live download speed (`Mbps`), jitter, and gaming ping latency. |
| **🔰 Security & Open Ports** | `security_port_scanner.py` | Audits Defender/Firewall shields and maps all active TCP/UDP `LISTENING` and `ESTABLISHED` ports to their PIDs. |

### 7. Hardware & Drivers
| Tool | Module File | Description |
| :--- | :--- | :--- |
| **🏷 Product Key & BIOS/TPM** | `product_key_bios.py` | Recovers OEM BIOS/Registry Windows Product Keys and verifies Secure Boot and TPM 2.0 status. |
| **💻 Full Hardware Specs** | `main.py` *(Built-in)* | Complete WMI/Registry hardware inventory including **all GPU adapters** (true 64-bit VRAM, VBIOS, PCIe lanes, clocks, watts) and **all Wired + Wireless network interfaces** (SSID, Wi-Fi standard, signal %, band, channel, IPv4/v6, MAC, link speed, gateway, DNS) with `.TXT` export. |
| **🖥 Display & Pixel Tester** | `display_monitor_tester.py` | Decodes raw monitor EDID firmware (Vendor, Panel ID, Serial, Physical Inches, Date) and launches a **9-Color Fullscreen Dead-Pixel & OLED Uniformity Tester**. |
| **🔌 Driver Backup Center** | `driver_backup_center.py` | Audits PnP drivers for errors (with mute/ignore support via `ignored_devices.json`) and exports third-party drivers via `DISM`. |
| **🎧 Connected Devices** | `connected_devices.py` | Lists all active USB controllers, audio endpoints, HID gaming peripherals, and Bluetooth devices. |

---

## ⌨️ Global Shortcuts & Command-Line Flags

| Shortcut / Flag | Action |
| :--- | :--- |
| **`Ctrl + Shift + B`** | Triggers an instant background RAM Working-Set Trim (works inside fullscreen games). |
| **`Ctrl + Shift + H`** | Toggles the **Floating Gaming HUD** overlay on or off from anywhere in Windows. |
| **`--silent-autopilot`** | Runs junk cleanup, browser cache cleanup, RAM optimization, and DNS flush silently with zero GUI windows (`PC_Optimizer_Ultimate.exe --silent-autopilot`). |

---

## 🚀 Installation & Running from Source

### Prerequisites
* **OS:** Windows 10 or Windows 11 (64-bit)
* **Python:** Python 3.11+ (Run as Administrator for full service, registry, and `powercfg` access)

### 1. Install Dependencies
```bash
pip install customtkinter psutil pillow pystray pyinstaller
