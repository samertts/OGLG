; Inno Setup script for the Correspondence System.
;
; Build from environment variables:
;   APP_VERSION  — version string (e.g. "1.0.0")
;   SOURCE_DIR   — path to PyInstaller one-folder output
;   OUTPUT_DIR   — path for the generated installer
;   PROJECT_ROOT — project root directory
;
; Usage:
;   set APP_VERSION=1.0.0
;   set SOURCE_DIR=C:\path\to\build\pyinstaller_dist\OfflineCorrespondenceSystem
;   set OUTPUT_DIR=C:\path\to\dist
;   iscc build\setup.iss

#define MyAppName "Offline Correspondence System"
#define MyAppShortName "OGLG"
#define MyAppVersion GetEnv("APP_VERSION")
#define MyAppPublisher "Iraq Ministry of Health"
#define MyAppURL "https://github.com/iraq-moh/oglg"
#define MyAppExeName "OfflineCorrespondenceSystem.exe"

#define SourceDir GetEnv("SOURCE_DIR")
#define OutputDir GetEnv("OUTPUT_DIR")
#define ProjectRoot GetEnv("PROJECT_ROOT")

[Setup]
AppId={{B8F4A3D2-1C5E-4A7B-9D0F-6E2C8A1B3D4F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppShortName}
DefaultGroupName={#MyAppShortName}
DisableProgramGroupPage=yes
OutputBaseFilename=OfflineCorrespondenceSystem_Setup_{#MyAppVersion}
OutputDir={#OutputDir}
SetupIconFile={#ProjectRoot}\app\assets\icons\app.ico
Compression=lzma2/max
SolidCompression=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableWelcomePage=no
DisableDirPage=auto
AllowNoIcons=yes
CloseApplications=no
RestartApplications=no

; Windows compatibility — supports Windows 7 through 11
MinVersion=6.1

; Data preservation flags
; NEVER delete user data directories during uninstall
[InstallDelete]
Type: files; Name: "{app}\temp\*.*"
Type: filesandordirs; Name: "{app}\temp"

[UninstallDelete]
; NOT deleting: {app}\data, {app}\database, {app}\archives, {app}\backups, {app}\logs
; User data MUST be preserved during uninstall
Type: files; Name: "{app}\temp\*.*"
Type: filesandordirs; Name: "{app}\temp"

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce
Name: "portablemode"; Description: "&Portable mode (store data in application directory)"; GroupDescription: "Installation mode:"; Flags: checkedonce

[Dirs]
; Application runtime directories (created during install)
Name: "{app}\runtime"
Name: "{app}\assets\fonts"
Name: "{app}\assets\icons"
Name: "{app}\assets\templates"
Name: "{app}\config"
Name: "{app}\migrations"
Name: "{app}\plugins"

; User data directories (created on first run, preserved on uninstall)
Name: "{app}\data\database"
Name: "{app}\data\archives"
Name: "{app}\data\backups"
Name: "{app}\data\logs"
Name: "{app}\data\temp"
Name: "{app}\data\attachments"
Name: "{app}\data\generated_letters"

[Files]
; Main executable and runtime
Source: "{#SourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "data"

; Assets
Source: "{#ProjectRoot}\app\assets\fonts\*"; DestDir: "{app}\assets\fonts"; Flags: ignoreversion recursesubdirs
Source: "{#ProjectRoot}\app\assets\icons\*"; DestDir: "{app}\assets\icons"; Flags: ignoreversion recursesubdirs
Source: "{#ProjectRoot}\app\assets\templates\*"; DestDir: "{app}\assets\templates"; Flags: ignoreversion recursesubdirs

; Configuration defaults
Source: "{#ProjectRoot}\app\config\defaults.json"; DestDir: "{app}\config"; Flags: ignoreversion

; Alembic migrations
Source: "{#ProjectRoot}\app\database\migrations\alembic.ini"; DestDir: "{app}\migrations"; Flags: ignoreversion
Source: "{#ProjectRoot}\app\database\migrations\env.py"; DestDir: "{app}\migrations"; Flags: ignoreversion
Source: "{#ProjectRoot}\app\database\migrations\script.py.mako"; DestDir: "{app}\migrations"; Flags: ignoreversion
Source: "{#ProjectRoot}\app\database\migrations\versions\*"; DestDir: "{app}\migrations\versions"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]

var
  PortableModePage: TInputOptionWizardPage;

procedure InitializeWizard;
begin
  PortableModePage := CreateInputOptionPage(
    wpSelectTasks,
    'Installation Mode',
    'Choose how the application stores its data.',
    'Standard mode stores data in your AppData folder (recommended).' + #13#10 +
    'Portable mode stores data alongside the application (useful for USB drives).',
    True, False
  );
  PortableModePage.Add('&Standard installation (data in AppData)');
  PortableModePage.Add('&Portable installation (data in application directory)');
  PortableModePage.SelectedValueIndex := 0;
end;

{ The portable.txt marker file tells the application to use portable mode }
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if PortableModePage.SelectedValueIndex = 1 then
    begin
      SaveStringToFile(ExpandConstant('{app}\portable.txt'), 'OGLG Portable Mode' + #13#10, False);
    end;
  end;
end;

{ Preserve user data on uninstall — ask user before removing data }
function InitializeUninstall: Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox(
      'Do you want to remove your personal data (database, archives, backups)?' + #13#10 + #13#10 +
      'Select "No" to keep your data for a future installation.',
      mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
    begin
      DelTree(ExpandConstant('{app}\data'), True, True, True);
    end;
  end;
end;
