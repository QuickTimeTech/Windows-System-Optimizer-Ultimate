; installer_setup.iss - Inno Setup Script for PC Optimizer Ultimate
[Setup]
AppId={{8F9B3A1D-4C2E-47A9-9D12-7E6B5C8A2F01}
AppName=Windows System Optimizer Ultimate
AppVersion=2.0.0
AppPublisher=PC Optimizer IT Suite
DefaultDirName={autopf}\PC Optimizer Ultimate
DefaultGroupName=PC Optimizer Ultimate
PrivilegesRequired=admin
OutputDir=installer_output
OutputBaseFilename=PC_Optimizer_Ultimate_Setup_v2.0
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\PC_Optimizer_Ultimate.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\PC_Optimizer_Ultimate.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PC Optimizer Ultimate"; Filename: "{app}\PC_Optimizer_Ultimate.exe"; IconFilename: "{app}\app_icon.ico"
Name: "{group}\Uninstall PC Optimizer Ultimate"; Filename: "{uninstallexe}"
Name: "{autodesktop}\PC Optimizer Ultimate"; Filename: "{app}\PC_Optimizer_Ultimate.exe"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\PC_Optimizer_Ultimate.exe"; Description: "{cm:LaunchProgram,Windows System Optimizer Ultimate}"; Flags: nowait postinstall skipifsilent shellexec