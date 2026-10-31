@echo off
setlocal
chcp 65001 >nul
set "MARVOI_DOWNLOADER=%~f0"
powershell.exe -NoLogo -NoProfile -Command "$ErrorActionPreference='Stop'; $text=Get-Content -LiteralPath $env:MARVOI_DOWNLOADER -Raw -Encoding UTF8; $marker='# MARVOI_POWERSHELL'; & ([scriptblock]::Create($text.Substring($text.LastIndexOf($marker))))"
if errorlevel 1 (
  echo.
  echo 下載未完成，請查看上方訊息。也可使用 GitHub 發行頁的手動下載方式。
  pause
  exit /b 1
)
pause
exit /b 0
# MARVOI_POWERSHELL
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[void][Reflection.Assembly]::LoadWithPartialName('System.IO.Compression.FileSystem')
$baseUrl = 'https://github.com/yo20ywork-max/MarVoiReflex/releases/download/v0.1.0-preview-20261031'
$archiveName = 'MarVoiReflex-App-CPU-Windows-x64-20261031.zip'
$archiveHash = '754673e81d6d8a50198a4bed45618b82992328bd7f9b1ec319ee42faf1f5bc58'
$modelName = 'MiniCPM5-2B-Q4_K_M.gguf'
$modelHash = 'ec2d5801640099e97d8d7e8003ad4d81f336e757811f03a26173dddf386602fd'
$exeHash = '6d6c2d79890254f402e12792fda957f5f43924201b18e8ce48a3def8ee0d1faf'
$destination = $env:MARVOI_INSTALL_DIR
if ([string]::IsNullOrWhiteSpace($destination)) {
    $destination = Join-Path $env:USERPROFILE 'Downloads\MarVoiReflex-20261031'
}
$destination = [IO.Path]::GetFullPath($destination)
$appRoot = Join-Path $destination 'MarVoiReflex'
$exe = Join-Path $appRoot 'MarVoiReflex.exe'
$modelTarget = Join-Path $appRoot ('assets\models\' + $modelName)

function Test-Hash([string]$Path, [string]$Expected) {
    if (-not [IO.File]::Exists($Path)) { return $false }
    $stream = [IO.File]::OpenRead($Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        $actual = [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant()
        return $actual -eq $Expected
    } finally {
        $stream.Dispose()
        $algorithm.Dispose()
    }
}

function Receive-Asset([string]$Name, [string]$Expected) {
    $cached = Join-Path $cache $Name
    if (Test-Path -LiteralPath $cached) {
        if (Test-Hash $cached $Expected) {
            Write-Host ('已核對：' + $Name)
            return $cached
        }
        throw ('下載資料夾內已有不同內容的檔案，請先移至其他位置：' + $cached)
    }
    $partial = $cached + '.partial'
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            Write-Host ('下載中（' + $attempt + '/3）：' + $Name)
            $client = [Net.WebClient]::new()
            try {
                $client.Headers['User-Agent'] = 'MarVoiReflex-Downloader/0.1.0'
                $client.DownloadFile(($baseUrl + '/' + $Name), $partial)
            } finally {
                $client.Dispose()
            }
            if (-not (Test-Hash $partial $Expected)) {
                throw ('檔案校驗失敗：' + $Name)
            }
            [IO.File]::Move($partial, $cached)
            return $cached
        } catch {
            if ($attempt -eq 3) { throw }
            Write-Host '下載中斷，正在重試。'
        }
    }
}

try {
    if (Test-Path -LiteralPath $appRoot) {
        if ((Test-Hash $exe $exeHash) -and (Test-Hash $modelTarget $modelHash)) {
            Write-Host ('App 已存在，可直接開啟：' + $exe)
            exit 0
        }
        throw ('目的地已有資料夾，請保留現有資料，改用其他位置或依手動下載說明補齊檔案：' + $appRoot)
    }
    [void][IO.Directory]::CreateDirectory($destination)
    $cache = Join-Path $destination 'downloads'
    [void][IO.Directory]::CreateDirectory($cache)
    Write-Host ('儲存位置：' + $destination)
    $archive = Receive-Asset $archiveName $archiveHash
    $model = Receive-Asset $modelName $modelHash
    Write-Host '檔案校驗通過，正在解壓縮。'
    [IO.Compression.ZipFile]::ExtractToDirectory($archive, $destination)
    if (-not (Test-Hash $exe $exeHash)) { throw '執行檔校驗失敗，請保留訊息並回報。' }
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($modelTarget)) | Out-Null
    [IO.File]::Move($model, $modelTarget)
    if (-not (Test-Hash $modelTarget $modelHash)) { throw '模型校驗失敗，請保留訊息並回報。' }
    Write-Host ''
    Write-Host '下載與解壓縮完成。請開啟下列程式：'
    Write-Host $exe
    Write-Host 'App 需有 WebView2 與 .NET Framework 4.8；使用語音回覆需 Windows 中文朗讀語音。'
    exit 0
} catch {
    Write-Host ('未完成：' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
