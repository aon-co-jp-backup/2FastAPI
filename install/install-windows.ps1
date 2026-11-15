# 2FastAPI installer for Windows / Windows 用インストーラー
# Usage:  powershell -ExecutionPolicy Bypass -File install-windows.ps1 [-NoOpenEasyWeb] [-DryRun] [-Uninstall]
#   Installs 2FastAPI into %LOCALAPPDATA%\2FastAPI (own Python venv), puts "2FastAPI" (GUI) and "2FastAPI (Web)" icons on the
#   Desktop and Start menu, and - unless -NoOpenEasyWeb is given - installs open-easy-web too when it is not installed yet (default: ON).
param(
    [switch]$NoOpenEasyWeb,
    [switch]$DryRun,
    [switch]$Uninstall,
    [switch]$OewOnly   # used by the .exe installer: only (re)install open-easy-web
)
$ErrorActionPreference = 'Stop'
$AppDir = Join-Path $env:LOCALAPPDATA '2FastAPI'
$OewDir = Join-Path $env:LOCALAPPDATA 'open-easy-web'
$Src = 'https://github.com/aon-co-jp/2FastAPI/archive/refs/heads/main.zip'
$OewApi = 'https://api.github.com/repos/aon-co-jp/open-easy-web/releases/latest'

function Step($m) { Write-Host ("==> " + $m) }
function Run($desc, [scriptblock]$sb) { Step $desc; if (-not $DryRun) { & $sb } }

function Remove-Shortcuts {
    $desk = [Environment]::GetFolderPath('Desktop'); $prog = [Environment]::GetFolderPath('Programs')
    foreach ($n in '2FastAPI.lnk', '2FastAPI (Web).lnk') { foreach ($d in $desk, $prog) { $p = Join-Path $d $n; if (Test-Path $p) { Remove-Item $p -Force } } }
}

if ($Uninstall) {
    Run 'Remove shortcuts / ショートカットを削除' { Remove-Shortcuts }
    Run ("Remove " + $AppDir + " / アプリを削除") { if (Test-Path $AppDir) { Remove-Item $AppDir -Recurse -Force } }
    Step ('open-easy-web is left in place (remove ' + $OewDir + ' by hand if unneeded). / open-easy-web は残します。')
    exit 0
}

if (-not $OewOnly) {
# 1. Python 3.9-3.13 (libcst, the conversion library, has wheels up to 3.13 / libcst の対応は 3.13 まで)
$py = $null
foreach ($v in '3.12', '3.13', '3.11', '3.10') {
    try { $o = & py "-$v" -c "import sys;print(sys.version_info[0])" 2>$null; if ($o -eq '3') { $py = $v; break } } catch {}
}
if (-not $py) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Run 'Install Python 3.12 with winget / winget で Python 3.12 を導入' { winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements }
        $py = '3.12'
    } else {
        Write-Host 'Python 3.10-3.13 is required. Install it from https://www.python.org/downloads/ and run this again. / Python 3.10〜3.13 が必要です。'
        exit 1
    }
}
Step ("Using Python " + $py)

# 2. 2FastAPI into its own venv
Run ("Create venv in " + $AppDir) { New-Item -ItemType Directory -Force $AppDir | Out-Null; & py "-$py" -m venv (Join-Path $AppDir 'venv') }
Run 'Install 2FastAPI and libcst / 2FastAPI と libcst を導入' {
    $vpy = Join-Path $AppDir 'venv\Scripts\python.exe'
    & $vpy -m pip install --quiet --upgrade pip
    & $vpy -m pip install --quiet libcst
    & $vpy -m pip install --quiet --force-reinstall --no-deps $Src
}

}
# 3. open-easy-web: install when missing (default on)
$oewInstalled = (Test-Path (Join-Path $OewDir 'open-easy-web-server.exe')) -or [bool](Get-Command open-easy-web-server -ErrorAction SilentlyContinue)
if ($oewInstalled) {
    Step 'open-easy-web is already installed - skipped / open-easy-web は導入済みのためスキップ'
} elseif ($NoOpenEasyWeb) {
    Step 'open-easy-web not installed and -NoOpenEasyWeb given - skipped / 導入しません'
} else {
    Run 'Install open-easy-web (latest release, windows x86_64) / open-easy-web を導入' {
        $rel = Invoke-RestMethod $OewApi
        $asset = $rel.assets | Where-Object { $_.name -like '*windows*x86_64*.zip' } | Select-Object -First 1
        if (-not $asset) { throw 'open-easy-web Windows release asset not found' }
        $zip = Join-Path $env:TEMP $asset.name
        Invoke-WebRequest $asset.browser_download_url -OutFile $zip
        New-Item -ItemType Directory -Force $OewDir | Out-Null
        Expand-Archive $zip -DestinationPath $OewDir -Force
        Remove-Item $zip -Force
    }
}

if (-not $OewOnly) {
# 4. Shortcuts with the 2FastAPI icon (GUI + Web wizard)
Run 'Create Desktop / Start menu shortcuts / ショートカットを作成' {
    $vpyw = Join-Path $AppDir 'venv\Scripts\pythonw.exe'
    $vpy = Join-Path $AppDir 'venv\Scripts\python.exe'
    $ico = (& $vpy -c "import os,tofastapi;print(os.path.join(os.path.dirname(tofastapi.__file__),'2fastapi.ico'))").Trim()
    $s = New-Object -ComObject WScript.Shell
    $desk = [Environment]::GetFolderPath('Desktop'); $prog = [Environment]::GetFolderPath('Programs')
    foreach ($d in $desk, $prog) {
        $l = $s.CreateShortcut((Join-Path $d '2FastAPI.lnk')); $l.TargetPath = $vpyw; $l.Arguments = '-m tofastapi gui'
        $l.IconLocation = $ico; $l.Description = '2FastAPI - Flask/Django to FastAPI/MFastAPI'; $l.Save()
        $w = $s.CreateShortcut((Join-Path $d '2FastAPI (Web).lnk')); $w.TargetPath = $vpyw; $w.Arguments = '-m tofastapi web'
        $w.IconLocation = $ico; $w.Description = '2FastAPI in the browser (this PC only)'; $w.Save()
    }
}
}
Step 'Done. Double-click the 2FastAPI icon. / 完了。デスクトップの 2FastAPI アイコンをダブルクリックしてください。'
