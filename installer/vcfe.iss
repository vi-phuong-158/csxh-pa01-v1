; ============================================================
; vcfe.iss  —  Inno Setup Script cho VCFE Database v2.0
; Chay: ISCC.exe installer\vcfe.iss  (tu thu muc goc du an)
; ============================================================

#define AppName      "VCFE Database"
#define AppVersion   "2.0.0"
#define AppPublisher "VCFE"
#define AppExeName   "Start.bat"
#define OutputName   "Setup_VCFE_v2.0"

[Setup]
AppId={{F3A2C8E1-4B7D-4F9A-A2E6-8D3C5B1F2E4A}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppVerName={#AppName} {#AppVersion}

; Thu muc mac dinh: Program Files (admin) hoac AppData\Local\Programs (user)
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}

; Cho phep ca admin va user thuong cai dat
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Output
OutputDir=dist\Output
OutputBaseFilename={#OutputName}

; Nen cao nhat — file .exe nho nhat
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; Giao dien
WizardStyle=modern
WizardSizePercent=120

; Doc file nguon tu thu muc goc du an (cha cua installer/)
SourceDir=..

; Icon cho file .exe installer va shortcut
SetupIconFile=frontend\static\img\logo.ico

; Khong cho phep chay nhieu phien ban dong thoi
AppMutex=VCFEDatabaseMutex

; Thong tin them
ChangesAssociations=no
DisableProgramGroupPage=yes

[Languages]
Name: "vi"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; \
    Description: "Tao shortcut tren Desktop"; \
    GroupDescription: "Shortcut:"; \
    Flags: checkedonce

[Files]
; ── Python runtime + tat ca goi da cai ──────────────────────────────────────
Source: "dist\python\*"; \
    DestDir: "{app}\python"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; ── Ma nguon ung dung ────────────────────────────────────────────────────────
Source: "dist\backend\*"; \
    DestDir: "{app}\backend"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

Source: "dist\frontend\*"; \
    DestDir: "{app}\frontend"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; ── File kho du lieu rong (tao san thu muc) ──────────────────────────────────
Source: "dist\data\uploads\.gitkeep"; \
    DestDir: "{app}\data\uploads"; \
    Flags: ignoreversion

; ── Trinh khoi dong va wizard lan dau ────────────────────────────────────────
Source: "dist\Start.bat";     DestDir: "{app}"; Flags: ignoreversion
Source: "dist\first_run.py";  DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Dam bao thu muc data ton tai va co quyen ghi
Name: "{app}\data";         Permissions: everyone-modify
Name: "{app}\data\uploads"; Permissions: everyone-modify
Name: "{app}\logs";         Permissions: everyone-modify

[Icons]
; Start Menu
Name: "{group}\{#AppName}"; \
    Filename: "{app}\{#AppExeName}"; \
    WorkingDir: "{app}"; \
    IconFilename: "{app}\frontend\static\img\logo.ico"; \
    Comment: "Mo VCFE Database"

Name: "{group}\Go cai dat {#AppName}"; \
    Filename: "{uninstallexe}"

; Desktop (neu chon task)
Name: "{autodesktop}\{#AppName}"; \
    Filename: "{app}\{#AppExeName}"; \
    WorkingDir: "{app}"; \
    IconFilename: "{app}\frontend\static\img\logo.ico"; \
    Tasks: desktopicon; \
    Comment: "Mo VCFE Database"

[Run]
; Sau khi cai xong: hoi co muon mo ung dung khong
Filename: "{app}\{#AppExeName}"; \
    Description: "Mo VCFE Database ngay bay gio"; \
    Flags: postinstall nowait skipifsilent shellexec

[UninstallDelete]
; Xoa ca file duoc tao trong qua trinh su dung
Type: files;     Name: "{app}\.env"
Type: files;     Name: "{app}\security_profile.db"
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\backend\__pycache__"
Type: filesandordirs; Name: "{app}\backend\routes\__pycache__"
Type: filesandordirs; Name: "{app}\backend\services\__pycache__"
