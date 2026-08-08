[CmdletBinding()]
param(
    [string]$Version,
    [int]$BuildNumber = 1,
    [switch]$SkipTests,
    [switch]$Clean,
    [string]$CertificateThumbprint,
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$flet = Join-Path $projectRoot ".venv\Scripts\flet.exe"
$appBundle = Join-Path $projectRoot "build\windows"
$distDir = Join-Path $projectRoot "dist"
$installerScript = Join-Path $projectRoot "installer\InsightForge.iss"

if (-not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath $flet)) {
    throw "Create the project virtual environment and install .[dev] before building."
}

if (-not $Version) {
    $Version = & $python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"
}
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Version must use semantic x.y.z format. Received: $Version"
}

$isccCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 7\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 7\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 7\ISCC.exe")
)
$iscc = $isccCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $iscc) {
    throw "Inno Setup 7 is required. Install it with: winget install --id JRSoftware.InnoSetup -e -s winget -i"
}

Push-Location $projectRoot
try {
    # serious_python invokes the bundled runtime's pip as a child process. Keep
    # release builds non-interactive and fail promptly if an index is unavailable
    # instead of waiting indefinitely for credentials or a network timeout.
    $env:PIP_NO_INPUT = "1"
    $env:PIP_DEFAULT_TIMEOUT = "20"
    $env:PIP_RETRIES = "1"
    $env:PIP_KEYRING_PROVIDER = "disabled"
    $env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
    $env:PIP_PROGRESS_BAR = "off"
    $env:PYTHONUNBUFFERED = "1"
    $env:FLET_CLI_NO_RICH_OUTPUT = "1"

    if ($Clean) {
        & $flet clean .
        if ($LASTEXITCODE -ne 0) { throw "Flet clean failed." }
    }

    if (-not $SkipTests) {
        $testTemp = Join-Path $projectRoot ".tmp\installer-tests"
        New-Item -ItemType Directory -Force $testTemp | Out-Null
        $env:TEMP = $testTemp
        $env:TMP = $testTemp
        & $python -m pytest -q
        if ($LASTEXITCODE -ne 0) { throw "Tests failed; installer build stopped." }
        & $python -m ruff check insightforge tests main.py
        if ($LASTEXITCODE -ne 0) { throw "Ruff failed; installer build stopped." }
    }

    & $python scripts\generate_brand_assets.py
    if ($LASTEXITCODE -ne 0) { throw "Brand asset generation failed." }

    # Recreate the generated target rather than overlaying a previous bundle.
    # This prevents stale files from surviving when exclusion rules change.
    if (Test-Path -LiteralPath $appBundle) {
        $resolvedBundle = (Resolve-Path -LiteralPath $appBundle).Path
        $expectedBundle = [System.IO.Path]::GetFullPath($appBundle)
        if ($resolvedBundle -ne $expectedBundle -or $resolvedBundle -notlike "$projectRoot\build\windows") {
            throw "Refusing to clean unexpected application bundle path: $resolvedBundle"
        }
        Remove-Item -LiteralPath $resolvedBundle -Recurse -Force
    }

    & $flet build windows . --output $appBundle --build-version $Version --build-number $BuildNumber --python-version 3.14 --no-rich-output --yes
    if ($LASTEXITCODE -ne 0) { throw "Flet Windows bundle build failed." }

    $appExe = Join-Path $appBundle "InsightForge.exe"
    if (-not (Test-Path -LiteralPath $appExe)) {
        throw "Expected application executable was not created: $appExe"
    }

    $forbiddenBundlePaths = @(
        (Join-Path $appBundle "app\.env"),
        (Join-Path $appBundle "app\.flet"),
        (Join-Path $appBundle "app\data")
    )
    $embeddedPrivateData = $forbiddenBundlePaths | Where-Object { Test-Path -LiteralPath $_ }
    if ($embeddedPrivateData) {
        throw "Release bundle contains private development data: $($embeddedPrivateData -join ', ')"
    }

    $isccArgs = @(
        "/DMyAppVersion=$Version",
        "/DSourceDir=$appBundle",
        "/DOutputDir=$distDir"
    )

    if ($CertificateThumbprint) {
        $signTool = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Filter signtool.exe -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match '\\x64\\signtool\.exe$' } |
            Sort-Object FullName -Descending |
            Select-Object -First 1 -ExpandProperty FullName
        if (-not $signTool) { throw "signtool.exe was not found in the Windows SDK." }

        & $signTool sign /sha1 $CertificateThumbprint /fd SHA256 /tr $TimestampUrl /td SHA256 $appExe
        if ($LASTEXITCODE -ne 0) { throw "Application signing failed." }

        $signCommand = '"{0}" sign /sha1 {1} /fd SHA256 /tr {2} /td SHA256 $f' -f $signTool, $CertificateThumbprint, $TimestampUrl
        $isccArgs += "/SInsightForgeSign=$signCommand"
        $isccArgs += "/DSignedBuild=1"
    }

    New-Item -ItemType Directory -Force $distDir | Out-Null
    & $iscc @isccArgs $installerScript
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup compilation failed." }

    $installer = Join-Path $distDir "InsightForge-$Version-Setup.exe"
    if (-not (Test-Path -LiteralPath $installer)) {
        throw "Expected installer was not created: $installer"
    }
    $checksum = (Get-FileHash -Algorithm SHA256 -LiteralPath $installer).Hash.ToLowerInvariant()
    Set-Content -LiteralPath "$installer.sha256" -Value "$checksum  $(Split-Path -Leaf $installer)" -Encoding utf8NoBOM
    Write-Host "Installer ready: $installer"
    Write-Host "SHA256: $checksum"
}
finally {
    Pop-Location
}
