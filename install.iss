; VRChat 翻译悬浮字幕 - Inno Setup 安装脚本
; 使用方法：用 Inno Setup 编译器打开此文件，编译生成安装包
; 前提：先运行 build_exe.bat 打包出 dist\VRC_Translate.exe

#define MyAppName "VRChat 翻译悬浮字幕"
#define MyAppVersion "2.3.0"
#define MyAppPublisher "VRC Translate"
#define MyAppExeName "VRC_Translate.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/vrc-translate/vrc_trans
AppSupportURL=https://github.com/vrc-translate/vrc_trans/issues
AppUpdatesURL=https://github.com/vrc-translate/vrc_trans/releases
DefaultDirName={autopf}\VRC Translate
DefaultGroupName=VRC Translate
AllowNoIcons=yes
LicenseFile=
OutputDir=installer
OutputBaseFilename=VRC_Translate_Setup_{#MyAppVersion}
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
SetupIconFile=app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
AppCopyright=Copyright (C) 2026 VRC Translate

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; 主程序
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 图标文件
Source: "app.ico"; DestDir: "{app}"; Flags: ignoreversion
; 说明文档
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
; 注意：模型和 FFmpeg 由程序首次运行时自动下载，不打包

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时删除配置文件（可选，注释掉则保留用户配置）
; Type: filesandordirs; Name: "{userappdata}\vrc_trans"

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  ; 检查是否有旧版本在运行（通过 tasklist 查找进程）
  Exec(ExpandConstant('{cmd}'), '/C tasklist /FI "IMAGENAME eq VRC_Translate.exe" | find /I "VRC_Translate.exe"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  if ResultCode = 0 then
  begin
    if MsgBox('检测到 VRChat 翻译悬浮字幕正在运行，请先关闭程序再继续安装。' + #13#10 + #13#10 + '是否现在关闭程序？', mbConfirmation, MB_YESNO) = IDYES then
    begin
      Exec('taskkill', '/F /IM VRC_Translate.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end
    else
    begin
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    ; 安装完成后可以在这里做额外初始化
  end;
end;
