#define AppName      "Quan Ly Nguoi Nuoc Ngoai"
#define AppNameShort "QLNNN"
#define AppVersion   "1.0.0"
#define AppPublisher "Phong An ninh doi ngoai"
#define AppExeName   "QLNNN.exe"
#define SourceDir    "..\dist\QLNNN"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppVerName={#AppName} {#AppVersion}
DefaultDirName={autopf}\{#AppNameShort}
DefaultGroupName={#AppName}
DisableDirPage=no
OutputDir=..\dist\installer
OutputBaseFilename=QLNNN_Setup_v{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
SetupIconFile=..\assets\logo.ico
MinVersion=10.0
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
AllowNoIcons=yes
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Tao bieu tuong tren Desktop"; GroupDescription: "Bieu tuong tat:"
Name: "startmenuicon"; Description: "Tao bieu tuong trong Start Menu"; GroupDescription: "Bieu tuong tat:"
Name: "autostart"; Description: "Tu dong khoi dong cung Windows"; GroupDescription: "Tuy chon:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: startmenuicon
Name: "{group}\Go cai dat {#AppNameShort}"; Filename: "{uninstallexe}"
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: autostart

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Chay {#AppName} ngay bay gio"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\*.log"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvExampleSrc, EnvDest: String;
begin
  if CurStep = ssPostInstall then
  begin
    EnvDest := ExpandConstant('{app}\.env');
    EnvExampleSrc := ExpandConstant('{app}\.env.example');
    
    if not FileExists(EnvDest) then
    begin
      FileCopy(EnvExampleSrc, EnvDest, False);
    end;
  end;
end;

function InitializeUninstall(): Boolean;
var
  Response: Integer;
begin
  Response := MsgBox(
    'Ban co chac muon go cai dat QLNNN?' + #13#10 + #13#10 +
    'Luu y: Du lieu CSDL (file .db) se KHONG bi xoa.' + #13#10 +
    'Ban co the sao luu truoc khi tiep tuc.',
    mbConfirmation, MB_YESNO
  );
  Result := (Response = IDYES);
end;
