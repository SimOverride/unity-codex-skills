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

function Get-Matches {
    param(
        [System.IO.FileInfo[]]$Files,
        [string]$Pattern,
        [string]$Label
    )

    $matches = @()
    foreach ($file in $Files) {
        foreach ($match in Select-String -LiteralPath $file.FullName -Pattern $Pattern -AllMatches -ErrorAction SilentlyContinue) {
            $matches += [pscustomobject][ordered]@{
                label = $Label
                path = $file.FullName
                line = $match.LineNumber
                text = $match.Line.Trim()
            }
        }
    }
    return $matches
}

$startRoot = (Resolve-Path -LiteralPath $Path).Path
$unityRoot = Find-UnityProjectRoot -StartPath $startRoot
if ($null -eq $unityRoot) {
    throw "在 $startRoot 的三层目录范围内未找到 Unity 项目。"
}

$assetsRoot = Join-Path $unityRoot 'Assets'
$allFiles = @(Get-ChildItem -LiteralPath $assetsRoot -Recurse -File -ErrorAction SilentlyContinue)
$shaderFiles = @($allFiles | Where-Object { $_.Extension -in @('.shader', '.hlsl', '.cginc', '.shadergraph') })
$yamlFiles = @($allFiles | Where-Object {
    $_.Extension -in @('.mat', '.prefab', '.asset', '.unity', '.meta') -and $_.Length -lt 10MB
})
$textFiles = @($shaderFiles + $yamlFiles | Sort-Object FullName -Unique)

$patterns = @(
    @{ Label = 'MainLightWithShadowCoordinates'; Pattern = 'GetMainLight\s*\(\s*TransformWorldToShadowCoord' },
    @{ Label = 'ShadowAttenuation'; Pattern = 'shadowAttenuation' },
    @{ Label = 'ShadowCasterPass'; Pattern = 'ShadowCaster' },
    @{ Label = 'DepthOnlyPass'; Pattern = 'DepthOnly' },
    @{ Label = 'DepthNormalsPass'; Pattern = 'DepthNormals' },
    @{ Label = 'TransparentQueue'; Pattern = 'Queue[^\\r\\n]*Transparent|RenderType[^\\r\\n]*Transparent' },
    @{ Label = 'AlphaBlend'; Pattern = 'Blend\s+SrcAlpha\s+OneMinusSrcAlpha' },
    @{ Label = 'ZWriteOff'; Pattern = 'ZWrite\s+Off' },
    @{ Label = 'Stencil'; Pattern = '\bStencil\b' },
    @{ Label = 'MeshNotReadable'; Pattern = 'isReadable:\s*0' },
    @{ Label = 'ReceiveShadowsDisabled'; Pattern = 'm_ReceiveShadows:\s*0' },
    @{ Label = 'CastShadows'; Pattern = 'm_CastShadows:' },
    @{ Label = 'RendererFeature'; Pattern = 'ScriptableRendererFeature|m_RendererFeatures:' }
)

$findings = @()
foreach ($entry in $patterns) {
    $findings += @(Get-Matches -Files $textFiles -Pattern $entry.Pattern -Label $entry.Label)
}

$shaderNames = @()
foreach ($file in $shaderFiles | Where-Object { $_.Extension -eq '.shader' }) {
    $match = Select-String -LiteralPath $file.FullName -Pattern '^\s*Shader\s+"([^"]+)"' | Select-Object -First 1
    if ($match -and $match.Matches.Count -gt 0) {
        $shaderNames += [pscustomobject][ordered]@{
            name = $match.Matches[0].Groups[1].Value
            path = $file.FullName
        }
    }
}

$summaryByLabel = [ordered]@{}
foreach ($group in $findings | Group-Object label | Sort-Object Name) {
    $summaryByLabel[$group.Name] = $group.Count
}

$result = [ordered]@{
    unityProjectRoot = $unityRoot
    shaderFileCount = $shaderFiles.Count
    materialFileCount = @($allFiles | Where-Object Extension -eq '.mat').Count
    rendererDataCandidates = @($allFiles | Where-Object {
        $_.Extension -eq '.asset' -and $_.Name -match 'Renderer|Pipeline'
    } | ForEach-Object FullName)
    shaders = $shaderNames
    findingCounts = $summaryByLabel
    findings = $findings
}

$result | ConvertTo-Json -Depth 6
