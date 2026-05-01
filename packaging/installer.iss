#define AppName      "VCFE Database"
#define AppNameShort "VCFE"
#define AppVersion   "2.0.0"
#define AppPublisher "PA01"
#define AppExeName   "VCFE.exe"
#define SourceDir    "..\dist\VCFE"

[Setup]
AppId={{4f96a524-b684-412e-900b-32fd016608cd}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppVerName={#AppName} {#AppVersion}
DefaultDirName={autopf}\{#AppNameShort}
DefaultGroupName={#AppName}
DisableDirPage=no
OutputDir=..\dist\installer
OutputBaseFilename={#AppNameShort}_Setup_v{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
SetupIconFile=..\assets\logo.ico
MinVersion=10.0
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
AllowNoIcons=yes
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Tao bieu tuong tren Desktop"; GroupDescription: "Bieu tuong tat:"
Name: "startmenuicon"; Description: "Tao bieu tuong trong Start Menu"; GroupDescription: "Bieu tuong tat:"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\logo.ico"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\logo.ico"; WorkingDir: "{app}"; Tasks: startmenuicon
Name: "{group}\Go cai dat {#AppNameShort}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Chay {#AppName} ngay bay gio"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\*.log"

[Code]
function InitializeUninstall(): Boolean;
var
  Response: Integer;
begin
  Response := MsgBox(
    'Ban co chac muon go cai dat ' + '{#AppName}' + '?' + #13#10 + #13#10 +
    'Luu y: Du lieu CSDL se KHONG bi xoa.' + #13#10 +
    'Ban co the sao luu truoc khi tiep tuc.',
    mbConfirmation, MB_YESNO
  );
  Result := (Response = IDYES);
end;
