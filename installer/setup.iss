; Inno Setup script - Scripts Formula
[Setup]
AppId={{8B380ABE-A4E5-4D7E-B5FA-A3BFB9E1E615}
AppName=Scripts Formula
AppVersion=2.0.0
AppPublisher=Vitor Neuenschwander
DefaultDirName={autopf}\Scripts Formula
DefaultGroupName=Scripts Formula
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=Scripts-Formula-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
SetupLogging=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "..\assets\*";    DestDir: "{app}\assets";    Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\src\*";       DestDir: "{app}\src";       Excludes: "__pycache__\*,*\__pycache__\*,*.pyc"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\launchers\*"; DestDir: "{app}\launchers"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\audit\*";     DestDir: "{app}\audit";     Flags: recursesubdirs createallsubdirs ignoreversion
Source: "post_install.bat";     DestDir: "{app}\installer"; Flags: ignoreversion
Source: "post_install_gui.pyw"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "..\version.txt"; DestDir: "{app}";           Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Scripts Formula"; Filename: "{app}\launchers\Scripts Formula.bat"; WorkingDir: "{app}\launchers"; IconFilename: "{app}\assets\imgs\engenharia_formula_logo.ico"
Name: "{autodesktop}\Scripts Formula";  Filename: "{app}\launchers\Scripts Formula.bat"; WorkingDir: "{app}\launchers"; IconFilename: "{app}\assets\imgs\engenharia_formula_logo.ico"

[Run]
Filename: "{app}\installer\post_install.bat"; Description: "Executar configuracao inicial agora"; Flags: postinstall waituntilterminated
