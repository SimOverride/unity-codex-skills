param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$ErrorActionPreference = 'Stop'

function Test-UnityProjectRoot {
    param([string]$Candidate)

    return (Test-Path -LiteralPath (Join-Path $Candidate 'Assets') -PathType Container) -and
        (Test-Path -LiteralPath (Join-Path $Candidate 'ProjectSettings') -PathType Container)
}

function Find-UnityProjectRoot {
    param(
        [string]$StartPath,
        [int]$MaxDepth = 3
    )

    $resolvedStart = (Resolve-Path -LiteralPath $StartPath).Path
    if (Test-UnityProjectRoot -Candidate $resolvedStart) {
        return $resolvedStart
    }

    $queue = [System.Collections.Generic.Queue[object]]::new()
    $queue.Enqueue([pscustomobject]@{ Path = $resolvedStart; Depth = 0 })

    while ($queue.Count -gt 0) {
        $current = $queue.Dequeue()
        if ($current.Depth -ge $MaxDepth) {
            continue
        }

        foreach ($directory in Get-ChildItem -LiteralPath $current.Path -Directory -Force -ErrorAction SilentlyContinue) {
            if (Test-UnityProjectRoot -Candidate $directory.FullName) {
                return $directory.FullName
            }

            if ($directory.Name -notin @('Library', 'Temp', 'Logs', 'obj', '.git')) {
                $queue.Enqueue([pscustomobject]@{
                    Path = $directory.FullName
                    Depth = $current.Depth + 1
                })
            }
        }
    }

    return $null
}

function Get-LineEndingKind {
    param([string]$FilePath)

    $content = [System.IO.File]::ReadAllText($FilePath)
    $hasCrLf = $content.Contains("`r`n")
    $hasLfOnly = [System.Text.RegularExpressions.Regex]::IsMatch($content, '(?<!\r)\n')

    if ($hasCrLf -and $hasLfOnly) {
        return 'Mixed'
    }
    if ($hasLfOnly) {
        return 'LF'
    }
    if ($hasCrLf) {
        return 'CRLF'
    }
    return 'NoNewline'
}

$sourceRoot = (Resolve-Path -LiteralPath $Path).Path
$unityRoot = Find-UnityProjectRoot -StartPath $sourceRoot
if ($null -eq $unityRoot) {
    throw "在 $sourceRoot 的三层目录范围内未找到 Unity 项目。"
}

$csharpFiles = @(Get-ChildItem -LiteralPath (Join-Path $unityRoot 'Assets') -Recurse -File -Filter '*.cs' -ErrorAction SilentlyContinue)
$lineEndingSummary = [ordered]@{
    CRLF = 0
    LF = 0
    Mixed = 0
    NoNewline = 0
}
foreach ($file in $csharpFiles) {
    $kind = Get-LineEndingKind -FilePath $file.FullName
    $lineEndingSummary[$kind]++
}

$searchRoots = @($sourceRoot, $unityRoot) | Select-Object -Unique
$agentsFiles = @()
$docsDirectories = @()
$hasCodeGraph = $false
foreach ($root in $searchRoots) {
    $agentsFiles += @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter 'AGENTS.md' -Depth 2 -ErrorAction SilentlyContinue | ForEach-Object FullName)
    $docsDirectories += @(Get-ChildItem -LiteralPath $root -Directory -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ieq 'docs' } |
        ForEach-Object FullName)
    if (Test-Path -LiteralPath (Join-Path $root '.codegraph') -PathType Container) {
        $hasCodeGraph = $true
    }
}

$gitRoot = $null
$dirtyFiles = $null
if (Get-Command git -ErrorAction SilentlyContinue) {
    $gitRootResult = & git -C $sourceRoot rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0) {
        $gitRoot = ($gitRootResult | Select-Object -First 1)
        $dirtyFiles = @(& git -C $gitRoot status --porcelain=v1).Count
    }
}

$projectVersionFile = Join-Path $unityRoot 'ProjectSettings\ProjectVersion.txt'
$unityVersion = $null
if (Test-Path -LiteralPath $projectVersionFile) {
    $versionLine = Get-Content -LiteralPath $projectVersionFile |
        Where-Object { $_ -match '^m_EditorVersion:\s*(.+)$' } |
        Select-Object -First 1
    if ($versionLine -match '^m_EditorVersion:\s*(.+)$') {
        $unityVersion = $Matches[1]
    }
}

$result = [ordered]@{
    sourceRoot = $sourceRoot
    unityProjectRoot = $unityRoot
    unityVersion = $unityVersion
    gitRoot = $gitRoot
    dirtyFileCount = $dirtyFiles
    agentsFiles = @($agentsFiles | Sort-Object -Unique)
    docsDirectories = @($docsDirectories | Sort-Object -Unique)
    hasCodeGraph = $hasCodeGraph
    csharpFileCount = $csharpFiles.Count
    assemblyDefinitionCount = @(Get-ChildItem -LiteralPath (Join-Path $unityRoot 'Assets') -Recurse -File -Filter '*.asmdef' -ErrorAction SilentlyContinue).Count
    testFileCount = @($csharpFiles | Where-Object { $_.FullName -match '[\\/]Tests?[\\/]' }).Count
    csharpLineEndings = $lineEndingSummary
}

$result | ConvertTo-Json -Depth 5
