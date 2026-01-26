param(
  [string]$ProjectRoot = "C:\dev\fagouflow"
)

$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host $msg }

# 0) BACKUP
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $ProjectRoot "backup_$timestamp"
Write-Info "[0] Backup -> $backupDir"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
Get-ChildItem -Path $ProjectRoot -Force | Where-Object { $_.Name -ne '.venv' -and $_.Name -notlike 'backup_*' } |
  ForEach-Object { Copy-Item -Path $_.FullName -Destination $backupDir -Recurse -Force }

# helper: UTF-8 no BOM writer
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

# 1) Fix encoding for templates
Write-Info "[1] Fix UTF-8 encoding in templates"
$templatesDir = Join-Path $ProjectRoot "templates"
$fixedEncoding = @()
if (Test-Path $templatesDir) {
  $htmlFiles = Get-ChildItem -Path $templatesDir -Recurse -Filter *.html -File
  foreach ($file in $htmlFiles) {
    $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
    $needsFix = $false
    try {
      [System.Text.Encoding]::UTF8.GetString($bytes) | Out-Null
    } catch {
      $needsFix = $true
    }
    if ($needsFix) {
      $text = [System.Text.Encoding]::GetEncoding(1252).GetString($bytes)
      [System.IO.File]::WriteAllText($file.FullName, $text, $utf8NoBom)
      $fixedEncoding += $file.FullName
    }
  }
}

# 2) Add {% load static %} where needed
Write-Info "[2] Ensure {% load static %}"
$staticFixed = @()
if (Test-Path $templatesDir) {
  $htmlFiles = Get-ChildItem -Path $templatesDir -Recurse -Filter *.html -File
  foreach ($file in $htmlFiles) {
    $content = Get-Content -Raw $file.FullName
    if ($content -match "\{\%\s*static\b") {
      if ($content -notmatch "\{\%\s*load\s+static\s*\%\}") {
        if ($content -match "^\{\%\s*extends\b") {
          $content = $content -replace "^(\{\%\s*extends[^\n]*\%\})", '$1' + "`r`n{% load static %}"
        } else {
          $content = "{% load static %}`r`n" + $content
        }
        [System.IO.File]::WriteAllText($file.FullName, $content, $utf8NoBom)
        $staticFixed += $file.FullName
      }
    }
  }
}

# 3) Safe avatar rendering
Write-Info "[3] Replace direct .avatar.url in templates"
$avatarFixed = @()
if (Test-Path $templatesDir) {
  $htmlFiles = Get-ChildItem -Path $templatesDir -Recurse -Filter *.html -File
  foreach ($file in $htmlFiles) {
    $content = Get-Content -Raw $file.FullName
    $original = $content

    # Replace direct avatar.url occurrences in template variables
    $content = $content -replace "\{\{\s*request\.user\.avatar\.url\s*\}\}", "{{ request.user|avatar_url }}"
    $content = $content -replace "\{\{\s*user\.avatar\.url\s*\}\}", "{{ user|avatar_url }}"
    $content = $content -replace "\{\{\s*msg\.author\.avatar\.url\s*\}\}", "{{ msg.author|avatar_url }}"

    if ($content -ne $original) {
      # ensure load avatar tag
      if ($content -notmatch "\{\%\s*load\s+avatar\s*\%\}") {
        if ($content -match "^\{\%\s*extends\b") {
          $content = $content -replace "^(\{\%\s*extends[^\n]*\%\})", '$1' + "`r`n{% load avatar %}"
        } else {
          $content = "{% load avatar %}`r`n" + $content
        }
      }
      [System.IO.File]::WriteAllText($file.FullName, $content, $utf8NoBom)
      $avatarFixed += $file.FullName
    }
  }
}

# Ensure placeholder avatar exists
$avatarPlaceholder = Join-Path $ProjectRoot "core\static\img\avatar-default.png"
if (-not (Test-Path $avatarPlaceholder)) {
  Write-Info "Creating placeholder avatar: $avatarPlaceholder"
  New-Item -ItemType Directory -Force -Path (Split-Path $avatarPlaceholder) | Out-Null
  $png = [Convert]::FromBase64String('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=')
  [System.IO.File]::WriteAllBytes($avatarPlaceholder, $png)
}

# Report
Write-Info "\n=== Summary ==="
Write-Info "Encoding fixed:"; $fixedEncoding | ForEach-Object { Write-Info "  - $_" }
Write-Info "Static tag added:"; $staticFixed | ForEach-Object { Write-Info "  - $_" }
Write-Info "Avatar url replaced:"; $avatarFixed | ForEach-Object { Write-Info "  - $_" }
