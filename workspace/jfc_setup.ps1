<#
CLARIPHY - one-shot setup for the JFC agentic-analysis exercise (native Windows).

Windows counterpart of jfc_setup.sh: Step 1 of the "Launch the Agent" lesson.
It does Parts 1-4 of the JFC exercise for you (each is explained in the
"Check In on the Agent" lesson):
  1. installs Claude Code and Pixi (skipped if they are already installed)
  2. writes a workshop-only Claude Code config that points at NRP
  3. downloads the two repositories and the CMS Open Data samples
  4. stages the fast-path analysis directory
and creates start-agent.cmd, which launches the agent (Step 2 / Part 5).

Usage, from PowerShell (no Administrator needed):

  powershell -ExecutionPolicy Bypass -File .\jfc_setup.ps1

"-ExecutionPolicy Bypass" applies to that one run only; it changes no settings.
The script asks for your NRP LLM token (https://nrp.ai/llmtoken). To skip the
prompt, set it first:   $env:NRP_LLM_TOKEN = "<your-token>"

Safe to re-run: finished steps are skipped and an interrupted download resumes.
It never edits %USERPROFILE%\.claude or your PowerShell profile. Everything
lives under %USERPROFILE%\jfc-exercise, apart from the claude and pixi binaries
(%USERPROFILE%\.local\bin and %USERPROFILE%\.pixi\bin).

If you have WSL, running jfc_setup.sh inside WSL is the better-trodden path.

Optional environment overrides: JFC_WORK, NRP_MODEL, NRP_CONTEXT.
#>

# Keep this file pure ASCII: Windows PowerShell 5.1 reads BOM-less scripts as
# Windows-1252, where the bytes of some UTF-8 characters turn into quote marks.

$ErrorActionPreference = 'Continue'     # failures are checked explicitly below
$ProgressPreference = 'SilentlyContinue' # the PS 5.1 progress bar makes web requests crawl
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch { }

if ($env:OS -ne 'Windows_NT') {
    Write-Host 'This script is for Windows. On macOS, Linux or WSL run:  bash jfc_setup.sh'
    exit 1
}

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
$UserHome = $env:USERPROFILE
$Work     = if ($env:JFC_WORK)     { $env:JFC_WORK }     else { Join-Path $UserHome 'jfc-exercise' }
$Model    = if ($env:NRP_MODEL)    { $env:NRP_MODEL }    else { 'gpt-oss' }
$Context  = if ($env:NRP_CONTEXT)  { $env:NRP_CONTEXT }  else { '131072' }
$NrpUrl   = if ($env:JFC_NRP_URL)  { $env:JFC_NRP_URL }  else { 'https://ellm.nrp-nautilus.io' }
$DataUrl  = if ($env:JFC_DATA_URL) { $env:JFC_DATA_URL } else { 'https://s3-west.nrp-nautilus.io/transfer-bucket/h4l-data.tgz' }

$ClaudeCfg  = Join-Path $Work 'claude-config'
$Rogue      = Join-Path $Work 'jfc\analyses\h4l_rogue'
$EnvCmd     = Join-Path $Work 'nrp-env.cmd'
$StartCmd   = Join-Path $Work 'start-agent.cmd'
$LocalBin   = Join-Path $UserHome '.local\bin'
$PixiBin    = Join-Path $UserHome '.pixi\bin'
$SysTar     = Join-Path $env:SystemRoot 'System32\tar.exe'
$SysCurl    = Join-Path $env:SystemRoot 'System32\curl.exe'
$PsExe      = (Get-Process -Id $PID).Path
$env:Path   = "$LocalBin;$PixiBin;$env:Path"

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
function Step($msg) { Write-Host ''; Write-Host "==> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "  [ok] $msg" -ForegroundColor Green }
function Note($msg) { Write-Host "       $msg" }
function Warn($msg) { Write-Host "  [!]  $msg" -ForegroundColor Yellow }
function Die {
    Write-Host ''
    Write-Host "  [x]  $($args[0])" -ForegroundColor Red
    for ($i = 1; $i -lt $args.Count; $i++) { Write-Host "       $($args[$i])" }
    Write-Host ''
    Write-Host '       Fix that and re-run - finished steps are skipped. Still stuck? Try the'
    Write-Host '       JupyterHub backup notebook, or ask an instructor.'
    exit 1
}
function Have($name) { [bool](Get-Command $name -ErrorAction SilentlyContinue) }
function Write-Utf8($path, $text) {
    [IO.File]::WriteAllText($path, $text, (New-Object Text.UTF8Encoding($false)))
}
function Invoke-Nrp {
    param([string]$Uri, [hashtable]$Headers, [string]$Method = 'GET', [string]$Body = '', [int]$TimeoutSec = 30)
    $p = @{ Uri = $Uri; Headers = $Headers; Method = $Method; TimeoutSec = $TimeoutSec; UseBasicParsing = $true; ErrorAction = 'Stop' }
    if ($Body) { $p.Body = $Body; $p.ContentType = 'application/json' }
    try {
        $r = Invoke-WebRequest @p
        return @{ Code = [int]$r.StatusCode; Body = [string]$r.Content }
    } catch {
        $resp = $_.Exception.Response
        if ($resp) { return @{ Code = [int]$resp.StatusCode; Body = '' } }
        return @{ Code = 0; Body = $_.Exception.Message }
    }
}
function Has-Content($dir) {
    (Test-Path $dir) -and [bool](Get-ChildItem -Force -Path $dir -ErrorAction SilentlyContinue | Select-Object -First 1)
}

# ---------------------------------------------------------------------------
# 0. Preflight
# ---------------------------------------------------------------------------
Step 'Checking this machine'

$arch = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
if ($PSVersionTable.PSVersion.Major -lt 5) { Die 'PowerShell 5.1 or newer is required.' }
Ok "Windows $([Environment]::OSVersion.Version) on $arch, PowerShell $($PSVersionTable.PSVersion)"

if (-not (Test-Path $SysTar) -or -not (Test-Path $SysCurl)) {
    Die 'tar.exe or curl.exe is missing - both ship with Windows 10 (1803) and later.' `
        'Update Windows, or use WSL or the JupyterHub backup notebook.'
}
Ok 'curl.exe and tar.exe available'

$HaveGit = Have 'git'
if ($HaveGit) {
    Ok 'Git for Windows available'
} else {
    Warn 'Git for Windows not found - Claude Code will run shell commands through PowerShell instead of Git Bash.'
    Note 'Recommended:  winget install --id Git.Git -e   then open a new PowerShell window and re-run.'
}

try {
    $memGb = [math]::Round((Get-CimInstance Win32_ComputerSystem -ErrorAction Stop).TotalPhysicalMemory / 1GB)
    if ($memGb -lt 7) { Warn "Only ~$memGb GB of RAM - the lesson recommends 8 GB. Watch for out-of-memory failures." }
    else { Ok "~$memGb GB RAM, $([Environment]::ProcessorCount) CPU cores" }
} catch { }

New-Item -ItemType Directory -Force -Path $Work -ErrorAction SilentlyContinue | Out-Null
if (-not (Test-Path $Work)) { Die "Could not create $Work" }
if (-not (Test-Path (Join-Path $Work 'data'))) {
    try {
        $freeMb = [math]::Floor((Get-Item $Work).PSDrive.Free / 1MB)
        if ($freeMb -lt 2500) {
            Die "Not enough free disk space for ${Work}: $freeMb MiB free, ~2500 MiB needed." `
                'Free some space, or pick another folder:  $env:JFC_WORK = "D:\jfc-exercise"'
        }
        Ok "$freeMb MiB free for $Work"
    } catch { }
}

# ---------------------------------------------------------------------------
# 1. NRP token
# ---------------------------------------------------------------------------
Step 'Your NRP LLM token'

$Interactive = [Environment]::UserInteractive -and -not [Console]::IsInputRedirected
function Read-Token {
    if (-not $Interactive) {
        Die 'No token found and no console to ask for one.' 'Set it first:  $env:NRP_LLM_TOKEN = "<your-token>"'
    }
    $sec = Read-Host -AsSecureString '  Paste your token from https://nrp.ai/llmtoken (input is hidden)'
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

$Token = ''; $TokenSource = ''
if ($env:NRP_LLM_TOKEN) {
    $Token = $env:NRP_LLM_TOKEN; $TokenSource = 'NRP_LLM_TOKEN'
} elseif ($env:OPENAI_API_KEY) {
    $Token = $env:OPENAI_API_KEY; $TokenSource = 'OPENAI_API_KEY'
} elseif (Test-Path $EnvCmd) {
    $m = Select-String -Path $EnvCmd -Pattern '^set "OPENAI_API_KEY=(.*)"\s*$' | Select-Object -First 1
    if ($m) { $Token = $m.Matches[0].Groups[1].Value.Replace('%%', '%'); $TokenSource = "$EnvCmd (previous run)" }
}

if (-not $Token) {
    $Token = Read-Token
} elseif ($Interactive) {
    if ($Token.StartsWith('sk-')) {
        Warn "The token in $TokenSource starts with 'sk-' - that looks like an OpenAI key, not an NRP token."
    }
    $prefix = $Token.Substring(0, [math]::Min(6, $Token.Length))
    $reply = Read-Host "  Found a token in $TokenSource ($prefix...). Use it? [Y/n]"
    if ($reply -match '^[nN]') { $Token = Read-Token }
}

# Tidy up common paste accidents: whitespace, surrounding quotes, "Bearer ".
$Token = $Token -replace '\s', ''
if ($Token.StartsWith('Bearer')) { $Token = $Token.Substring(6) }
$Token = $Token.Trim('"', "'")
if (-not $Token) { Die 'The token is empty.' }
if ($Token -match '^<.*>$') { Die 'That is the placeholder, not a token.' 'Get yours at https://nrp.ai/llmtoken' }
if ($Token.Contains('"')) { Die 'The token contains a double quote, which this script cannot store safely.' }

# /v1/models answers even without a token, so check with a one-token chat request instead.
$probe = '{"model":"gemma-small","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}'
$r = Invoke-Nrp -Uri "$NrpUrl/v1/chat/completions" -Method 'POST' -Body $probe -TimeoutSec 60 `
        -Headers @{ Authorization = "Bearer $Token" }
if ($r.Code -eq 200) {
    Ok "Token accepted by $NrpUrl"
} elseif ($r.Code -eq 401 -or $r.Code -eq 403) {
    Die "NRP rejected the token (HTTP $($r.Code))." `
        'Get a fresh one at https://nrp.ai/llmtoken, and make sure your account is in a' `
        'namespace with LLM access (see the Setup page).'
} elseif ($r.Code -eq 0) {
    Die "Could not reach $NrpUrl." 'Check your internet connection, VPN or proxy.' $r.Body
} else {
    Warn "Unexpected answer from $NrpUrl (HTTP $($r.Code)) - continuing, but the agent may not work."
}

# ---------------------------------------------------------------------------
# 2. Claude Code and Pixi
# ---------------------------------------------------------------------------
Step 'Installing Claude Code and Pixi'

# Official installers run in a child PowerShell so an `exit` inside them cannot end this script.
function Run-Installer($url, $name) {
    Note "Running the official installer ($url)..."
    & $PsExe -NoProfile -ExecutionPolicy Bypass -Command "Invoke-RestMethod '$url' | Invoke-Expression"
    if ($LASTEXITCODE -ne 0) { Die "The $name installer failed (exit code $LASTEXITCODE)." }
}

if (Have 'claude') {
    Ok "Claude Code already installed: $((& claude --version | Select-Object -First 1)) - leaving it as is"
} else {
    Run-Installer 'https://claude.ai/install.ps1' 'Claude Code'
    if (-not (Have 'claude')) { Die "Claude Code installed, but claude.exe is not in $LocalBin as expected." }
    Ok "Claude Code installed: $((& claude --version | Select-Object -First 1))"
}
if (-not ((& claude --help | Out-String) -match '"auto"')) {
    Warn 'This Claude Code is too old for --permission-mode auto. Update it with:  claude update'
}

if (Have 'pixi') {
    Ok "Pixi already installed: $(& pixi --version) - leaving it as is"
} else {
    $env:PIXI_NO_PATH_UPDATE = '1'       # do not touch the user's PATH settings
    Run-Installer 'https://pixi.sh/install.ps1' 'Pixi'
    Remove-Item Env:\PIXI_NO_PATH_UPDATE -ErrorAction SilentlyContinue
    if (-not (Have 'pixi')) { Die "Pixi installed, but pixi.exe is not in $PixiBin as expected." }
    Ok "Pixi installed: $(& pixi --version)"
}

# ---------------------------------------------------------------------------
# 3. Workshop-only Claude Code config + launch files
# ---------------------------------------------------------------------------
Step "Pointing Claude Code at NRP (in $ClaudeCfg - your .claude folder is not touched)"

# Claude Code reads its user settings from CLAUDE_CONFIG_DIR when that is set,
# which only happens through nrp-env.cmd / start-agent.cmd.
New-Item -ItemType Directory -Force -Path $ClaudeCfg -ErrorAction SilentlyContinue | Out-Null
$tokJson = $Token.Replace('\', '\\').Replace('"', '\"')
$settings = @"
{
  "env": {
    "ANTHROPIC_BASE_URL": "$NrpUrl/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "$tokJson",
    "ANTHROPIC_MODEL": "$Model",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "$Model",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "$Model",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "$Model",
    "CLAUDE_CODE_SUBAGENT_MODEL": "$Model",
    "ENABLE_TOOL_SEARCH": "false",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "$Context",
    "CLAUDE_CODE_EFFORT_LEVEL": "max",
    "CLAUDE_STREAM_IDLE_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_ENABLE_TELEMETRY": "0",
    "DISABLE_TELEMETRY": "1",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_MAX_RETRIES": "10"
  },
  "permissions": {
    "deny": ["WebSearch"]
  }
}
"@
try {
    Write-Utf8 (Join-Path $ClaudeCfg 'settings.json') $settings
} catch { Die "Could not write $ClaudeCfg\settings.json" $_.Exception.Message }

function CmdValue($s) { $s.Replace('%', '%%') }
$envLines = @(
    '@echo off',
    'rem NRP settings for the CLARIPHY JFC exercise (written by jfc_setup.ps1).',
    'rem Load them into a Command Prompt with:  call "<this file>"',
    'rem Note that claude in that window then uses the NRP config, not your usual .claude folder.',
    "set `"OPENAI_API_BASE=$(CmdValue "$NrpUrl/v1")`"",
    "set `"OPENAI_API_KEY=$(CmdValue $Token)`"",
    "set `"WORK=$(CmdValue $Work)`"",
    "set `"ROGUE=$(CmdValue $Rogue)`"",
    "set `"CLAUDE_CONFIG_DIR=$(CmdValue $ClaudeCfg)`"",
    'set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.pixi\bin;%PATH%"'
)
# The prompt is passed as an argument rather than piped in, so the interactive
# terminal UI keeps the console as its input on Windows.
$startLines = @(
    '@echo off',
    'rem Launches the JFC fast-path agent (Step 2 of the Launch the Agent lesson). Written by jfc_setup.ps1.',
    'call "%~dp0nrp-env.cmd"',
    'cd /d "%ROGUE%"',
    'echo Launching the JFC agent in %ROGUE% ...',
    'claude --permission-mode auto "Read prompt.md in this directory. It is your task: carry out the analysis it describes."',
    'pause'
)
try {
    Write-Utf8 $EnvCmd (($envLines -join "`r`n") + "`r`n")
    Write-Utf8 $StartCmd (($startLines -join "`r`n") + "`r`n")
} catch { Die "Could not write the launch files in $Work" $_.Exception.Message }
Ok "Claude Code config: $ClaudeCfg\settings.json (model: $Model)"
Ok "Launcher:           $StartCmd"

Note "Checking that $Model answers through the Anthropic-compatible endpoint..."
$body = '{"model":"' + $Model + '","max_tokens":1000,"messages":[{"role":"user","content":"Reply with exactly: NRP OK"}]}'
$r = Invoke-Nrp -Uri "$NrpUrl/anthropic/v1/messages" -Method 'POST' -Body $body -TimeoutSec 180 `
        -Headers @{ 'x-api-key' = $Token; 'anthropic-version' = '2023-06-01' }
if ($r.Code -eq 200 -and $r.Body -match '"type"\s*:\s*"text"') {
    Ok "$Model replied through $NrpUrl/anthropic"
} elseif ($r.Code -eq 200) {
    Warn "$Model answered but returned no text (probably spent its budget reasoning) - usually fine."
} else {
    Warn "The Anthropic-compatible endpoint answered HTTP $($r.Code) for model $Model."
    Note 'The agent may not start. Try another model:  $env:NRP_MODEL = "glm-5"  then re-run this script.'
    Note 'Current model status: https://nrp.ai/llm-status/'
}

# ---------------------------------------------------------------------------
# 4. Repositories
# ---------------------------------------------------------------------------
Step 'Getting the JFC framework and the H4l tutorial context'

function Fetch-Repo($name, $repo, $branch) {
    $dest = Join-Path $Work $name
    $tmp = Join-Path $Work ".$name.partial"
    if (Has-Content $dest) { Ok "$name already present - leaving it as is"; return }
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
    if ($HaveGit) {
        & git clone -q --depth 1 -b $branch "https://github.com/$repo.git" $tmp
        if ($LASTEXITCODE -ne 0) {
            Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
            Die "git clone of $repo failed." 'Check your connection and re-run.'
        }
    } else {
        New-Item -ItemType Directory -Force -Path $tmp | Out-Null
        $archive = Join-Path $Work ".$name.tgz"
        & $SysCurl -fsSL --retry 3 -o $archive "https://codeload.github.com/$repo/tar.gz/refs/heads/$branch"
        if ($LASTEXITCODE -ne 0) { Die "Downloading $repo failed." 'Check your connection and re-run.' }
        & $SysTar -xzf $archive -C $tmp --strip-components=1
        if ($LASTEXITCODE -ne 0) {
            # Usually symlinks, which Windows will not create without extra privileges.
            Warn "tar reported problems unpacking $repo (often harmless symlink warnings)."
        }
        Remove-Item -Force $archive -ErrorAction SilentlyContinue
        if (-not (Has-Content $tmp)) { Die "Unpacking $repo failed." }
    }
    if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
    Move-Item $tmp $dest
    Ok "$name ($repo, branch $branch)"
}
Fetch-Repo 'h4l_agent_test' 'violatingcp/h4l_agent_test' 'main'
Fetch-Repo 'jfc' 'violatingcp/jfc' 'jfc_lite'

# ---------------------------------------------------------------------------
# 5. CMS Open Data samples
# ---------------------------------------------------------------------------
Step 'Getting the CMS Open Data samples (~860 MiB)'

$dataDir = Join-Path $Work 'data'
if (Has-Content $dataDir) {
    Ok 'data already present - skipping download'
} else {
    $tgz = Join-Path $Work 'data.tgz'
    $part = "$tgz.part"
    $expected = $null
    try {
        $h = Invoke-WebRequest -Uri $DataUrl -Method Head -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop
        $expected = [int64](@($h.Headers['Content-Length'])[0])
    } catch { }
    function SizeOf($p) { if (Test-Path $p) { (Get-Item $p).Length } else { -1 } }

    if ((Test-Path $tgz) -and ((-not $expected) -or (SizeOf $tgz) -eq $expected)) {
        Ok 'data.tgz already downloaded'
    } else {
        if (-not ($expected -and (SizeOf $part) -eq $expected)) {
            if (Test-Path $part) { Note 'Resuming the previous download...' } else { Note 'Downloading - a few minutes on a good connection...' }
            & $SysCurl -fL -C - --retry 5 --retry-delay 5 --progress-bar -o $part $DataUrl
            if ($LASTEXITCODE -ne 0) { Die 'The download stopped.' 'Re-run the script to resume it.' }
        }
        if ($expected -and (SizeOf $part) -ne $expected) {
            Die "Downloaded $(SizeOf $part) bytes, expected $expected." 'Re-run the script to resume it.'
        }
        Move-Item -Force $part $tgz
        Ok 'Downloaded data.tgz'
    }

    # Extract beside the final location, then move into place, so an interrupted
    # extraction never leaves a half-filled data folder that looks finished.
    Note 'Extracting...'
    $ext = Join-Path $Work '.data-extract'
    if (Test-Path $ext) { Remove-Item -Recurse -Force $ext }
    New-Item -ItemType Directory -Force -Path $ext | Out-Null
    & $SysTar -xzf $tgz -C $ext
    if ($LASTEXITCODE -ne 0) {
        Remove-Item -Recurse -Force $ext -ErrorAction SilentlyContinue
        Remove-Item -Force $tgz -ErrorAction SilentlyContinue
        Die 'Extracting data.tgz failed (corrupt download, or the disk filled up).' `
            'The tarball was removed; re-run the script to download it again.'
    }
    if (Test-Path (Join-Path $ext 'data')) {
        Move-Item (Join-Path $ext 'data') $dataDir
        Remove-Item -Recurse -Force $ext
    } else {
        Move-Item $ext $dataDir
    }
    Remove-Item -Force $tgz
    Ok "Samples extracted to $dataDir"
}

# ---------------------------------------------------------------------------
# 6. Stage the fast-path analysis
# ---------------------------------------------------------------------------
Step "Staging the fast-path analysis in $Rogue"

New-Item -ItemType Directory -Force -Path $Rogue -ErrorAction SilentlyContinue | Out-Null
if (-not (Test-Path $Rogue)) { Die "Could not create $Rogue" }
$link = Join-Path $Rogue 'data'
if (-not (Test-Path $link)) {
    # A junction needs no special privileges, unlike a symbolic link.
    New-Item -ItemType Junction -Path $link -Target $dataDir -ErrorAction SilentlyContinue | Out-Null
    if (-not (Test-Path $link)) { Die "Could not link $link to $dataDir" }
}
# Only add what is missing, so a re-run never overwrites anything the agent changed.
foreach ($item in @('prompt.md', 'h4l_ntuplize.py', 'docs', '.claude')) {
    $dst = Join-Path $Rogue $item
    if (-not (Test-Path $dst)) {
        Copy-Item -Recurse -Force -Path (Join-Path $Work "h4l_agent_test\$item") -Destination $dst
        if (-not (Test-Path $dst)) { Die "Could not copy $item into $Rogue" }
    }
}
Ok 'prompt.md, docs, h4l_ntuplize.py, .claude and a data link are in place'

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host '==> All set.' -ForegroundColor Cyan -NoNewline
Write-Host ' Launch the agent (Step 2 of the lesson) - double-click start-agent.cmd in'
Write-Host "    $Work, or run:"
Write-Host ''
Write-Host "    & `"$StartCmd`""
Write-Host ''
Write-Host 'Then leave that window open and carry on with the tutorial.'
Write-Host ''
Write-Host 'Your own Claude Code settings (.claude) and PowerShell profile were not modified.'
Write-Host "To remove everything after the workshop, delete the folder $Work"
