@echo off
title Building Standalone Single-File PC_Optimizer_Ultimate.exe...

echo [1/3] Checking & installing required Python packages...
python3.11 -m pip install pyinstaller customtkinter psutil pillow pystray

echo.
echo [2/3] Generating custom app_icon.ico...
python3.11 icon_generator.py

echo.
echo [3/3] Packing all 32 tools into a single standalone .exe file...
python3.11 -m PyInstaller --noconsole --onefile --uac-admin --clean ^
    --collect-all customtkinter ^
    --collect-all pystray ^
    --icon="app_icon.ico" ^
    --add-data "app_icon.ico;." ^
    --hidden-import=backend_engine ^
    --hidden-import=icon_generator ^
    --hidden-import=autopilot_maintenance ^
    --hidden-import=pc_health_scorecard ^
    --hidden-import=tray_ram_guard ^
    --hidden-import=hud_overlay ^
    --hidden-import=winget_app_installer ^
    --hidden-import=update_center ^
    --hidden-import=cpu_ram_tuner ^
    --hidden-import=gpu_performance_center ^
    --hidden-import=thermal_stress_bench ^
    --hidden-import=restore_scheduler ^
    --hidden-import=gaming_booster ^
    --hidden-import=privacy_debloater ^
    --hidden-import=win11_ui_customizer ^
    --hidden-import=context_hosts_manager ^
    --hidden-import=disk_health_analyzer ^
    --hidden-import=large_file_finder ^
    --hidden-import=duplicate_finder ^
    --hidden-import=file_shredder_unlock ^
    --hidden-import=app_uninstaller ^
    --hidden-import=product_key_bios ^
    --hidden-import=driver_backup_center ^
    --hidden-import=connected_devices ^
    --hidden-import=lan_network_scanner ^
    --hidden-import=wifi_vault_dns ^
    --hidden-import=network_speedtest ^
    --hidden-import=security_port_scanner ^
    --hidden-import=crash_inspector ^
    --hidden-import=system_repair ^
    --name "PC_Optimizer_Ultimate" main.py

echo.
echo ==========================================================
echo  Single-File Build Complete!
echo  Share this single file: dist\PC_Optimizer_Ultimate.exe
echo ==========================================================
explorer dist
pause