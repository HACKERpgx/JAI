#define MyAppName "JAI Voice Assistant"
#define MyAppVersion "1.0"
#define MyAppPublisher "JAI Technologies"
#define MyAppExeName "run_jai.bat"

[Setup]
AppId={{JAI-VOICE-ASSISTANT}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=JAI_Voice_Installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "*.*"; Excludes: "*.iss,*.log,*.pyc,__pycache__"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  PythonVersion: string;
  PythonPath: string;
  I: Integer;
  Versions: TArrayOfString;
  PythonFound: Boolean;
  ResultCode: Integer;
begin
  PythonFound := False;
  
  // Check for Python 3.x in the registry (HKLM)
  if RegGetSubkeyNames(HKLM, 'SOFTWARE\Python\PythonCore', Versions) then
  begin
    for I := 0 to GetArrayLength(Versions) - 1 do
    begin
      PythonVersion := Versions[I];
      if (Pos('3.', PythonVersion) = 1) then
      begin
        // Found a Python 3.x installation
        if RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\' + PythonVersion + '\InstallPath', '', PythonPath) then
        begin
          PythonFound := True;
          break;
        end;
      end;
    end;
  end;
  
  // Check for Python 3.x in the registry (HKCU - for user installations)
  if not PythonFound and RegGetSubkeyNames(HKCU, 'SOFTWARE\Python\PythonCore', Versions) then
  begin
    for I := 0 to GetArrayLength(Versions) - 1 do
    begin
      PythonVersion := Versions[I];
      if (Pos('3.', PythonVersion) = 1) then
      begin
        if RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\' + PythonVersion + '\InstallPath', '', PythonPath) then
        begin
          PythonFound := True;
          break;
        end;
      end;
    end;
  end;
  
  // Check if Python is in PATH
  if not PythonFound then
  begin
    if Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    begin
      PythonFound := True;
    end;
  end;
  
  if not PythonFound then
  begin
    if MsgBox('Python 3.x is required but was not found. Would you like to open the Python download page?', 
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      ShellExec('open', 'https://www.python.org/downloads/', '', '', SW_SHOW, ewNoWait, ResultCode);
    end;
    Result := False;
  end
  else
  begin
    Result := True;
  end;
end;

function FindPythonExecutable(): String;
var
  PythonVersion: string;
  PythonPath: string;
  I: Integer;
  Versions: TArrayOfString;
begin
  Result := '';
  
  // Check for Python 3.x in the registry (HKLM)
  if RegGetSubkeyNames(HKLM, 'SOFTWARE\Python\PythonCore', Versions) then
  begin
    for I := 0 to GetArrayLength(Versions) - 1 do
    begin
      PythonVersion := Versions[I];
      if (Pos('3.', PythonVersion) = 1) then
      begin
        if RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\' + PythonVersion + '\InstallPath', '', PythonPath) then
        begin
          Result := AddBackslash(PythonPath) + 'python.exe';
          if FileExists(Result) then Exit;
        end;
      end;
    end;
  end;
  
  // Check for Python 3.x in the registry (HKCU - for user installations)
  if RegGetSubkeyNames(HKCU, 'SOFTWARE\Python\PythonCore', Versions) then
  begin
    for I := 0 to GetArrayLength(Versions) - 1 do
    begin
      PythonVersion := Versions[I];
      if (Pos('3.', PythonVersion) = 1) then
      begin
        if RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\' + PythonVersion + '\InstallPath', '', PythonPath) then
        begin
          Result := AddBackslash(PythonPath) + 'python.exe';
          if FileExists(Result) then Exit;
        end;
      end;
    end;
  end;
  
  // Check if Python is in PATH
  if Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, I) then
  begin
    Result := 'python';
  end;
end;

procedure InstallPythonPackages();
var
  PythonExe: String;
  ResultCode: Integer;
  PythonDir: String;
  PipPath: String;
begin
  PythonExe := FindPythonExecutable();
  
  if PythonExe = '' then
  begin
    MsgBox('Could not find Python executable. Please install Python 3.x and try again.', mbError, MB_OK);
    Exit;
  end;
  
  // Get the directory containing python.exe
  PythonDir := ExtractFileDir(PythonExe);
  PipPath := AddBackslash(PythonDir) + 'pip.exe';
  
  // Install required packages
  if not FileExists(PipPath) then
  begin
    // If pip.exe doesn't exist, try to install it
    if not Exec(PythonExe, '-m ensurepip --default-pip', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    begin
      MsgBox('Failed to install pip. Please install pip manually and try again.', mbError, MB_OK);
      Exit;
    end;
  end;
  
  // Upgrade pip
  if not Exec(PythonExe, '-m pip install --upgrade pip', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    MsgBox('Failed to upgrade pip. Some features might not work correctly.', mbError, MB_OK);
  end;
  
  // Install required packages
  if not Exec(PythonExe, '-m pip install pyttsx3 pywin32 comtypes pycaw', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    MsgBox('Failed to install required Python packages. Please install them manually using: pip install pyttsx3 pywin32 comtypes pycaw', mbError, MB_OK);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Install required Python packages
    InstallPythonPackages();
  end;
end;
