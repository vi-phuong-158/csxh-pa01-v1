#define MyAppName "VCFE Database"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "CSDLNNN"
#define MyAppExeName "VCFE_Database.exe"

[Setup]
AppId={{5D01115F-9883-42D0-9DF8-662C5B422AA1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
; Chỉ định icon cho trình cài đặt (sử dụng icon đã convert)
SetupIconFile=..\assets\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
OutputDir=..\dist
OutputBaseFilename=VCFE_Database_Setup
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy toàn bộ thư mục VCFE_Database được build ở One Folder mode
Source: "..\dist\VCFE_Database\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Đưa file .env.example ra thư mục gốc để người dùng dễ thấy và cấu hình
Source: "..\dist\VCFE_Database\_internal\.env.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\logo.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
; Tạo shortcut ở Start Menu và Desktop. CHÚ Ý: IconFilename trỏ thẳng đến file logo.ico để đảm bảo chất lượng hình ảnh sắc nét.
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\logo.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
