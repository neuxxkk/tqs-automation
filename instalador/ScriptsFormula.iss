; Inno Setup script - Scripts Formula
[Setup]
AppId={{8B380ABE-A4E5-4D7E-B5FA-A3BFB9E1E615}
AppName=Scripts Formula
AppVersion=1.0.0
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
Source: "..\arquivos\*"; DestDir: "{app}\arquivos"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\codigo_fonte\*"; DestDir: "{app}\codigo_fonte"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\executaveis\*"; DestDir: "{app}\executaveis"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "instalar_completo.bat"; DestDir: "{app}\instalador"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Scripts Formula"; Filename: "{app}\executaveis\Scripts.bat"; WorkingDir: "{app}\executaveis"; IconFilename: "{app}\arquivos\imgs\engenharia_formula_logo.ico"
Name: "{autodesktop}\Scripts Formula"; Filename: "{app}\executaveis\Scripts.bat"; WorkingDir: "{app}\executaveis"; IconFilename: "{app}\arquivos\imgs\engenharia_formula_logo.ico"

[Run]
Filename: "{app}\instalador\instalar_completo.bat"; Description: "Executar configuracao inicial agora"; Flags: postinstall waituntilterminated
