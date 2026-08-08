#define MyAppName "InsightForge"
#define MyAppAuthor "Harshit Garg"
#define MyAppPublisher "Harshit Garg Inc."
#define MyAppEmail "harshit.garg@harshit-garg.com"
#define MyAppWebsite "https://harshit-garg.com"
#define MyAppSupportURL "mailto:harshit.garg@harshit-garg.com"
#define MyAppSupportPhone "+1 301-525-7100"
#define MyAppCopyright "Copyright (c) 2026 Harshit Garg. All rights reserved."
#define MyAppDescription "Local-first Excel analytics workspace by Harshit Garg"
#define MyAppExeName "InsightForge.exe"
#define MyAppId "{{1F02C7A2-C781-4C45-92A3-B6B0A39D60EF}"

#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\build\windows"
#endif
#ifndef OutputDir
  #define OutputDir "..\dist"
#endif

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppWebsite}
AppSupportURL={#MyAppSupportURL}
AppSupportPhone={#MyAppSupportPhone}
AppUpdatesURL={#MyAppWebsite}
AppContact={#MyAppAuthor} <{#MyAppEmail}>
AppCopyright={#MyAppCopyright}
AppComments={#MyAppDescription}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={#OutputDir}
OutputBaseFilename=InsightForge-{#MyAppVersion}-Setup
SetupIconFile={#SourcePath}\..\assets\icon.ico
LicenseFile={#SourcePath}\EULA.txt
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
WizardBackColor=#F6F7FC
WizardImageBackColor=#151D2F
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupArchitecture=x64
MinVersion=10.0.17763
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
UsePreviousTasks=yes
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoCopyright={#MyAppCopyright}
VersionInfoDescription={#MyAppDescription}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
#ifdef SignedBuild
SignTool=InsightForgeSign
SignedUninstaller=yes
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourcePath}\EULA.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
