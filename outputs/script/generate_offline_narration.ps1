$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$storyboardPath = Join-Path $PSScriptRoot "storyboard-proposal.json"
$audioDirectory = Join-Path $projectRoot "outputs\the-next-page-film\outputs\audio"

if (-not (Test-Path -LiteralPath $storyboardPath -PathType Leaf)) {
    throw "Storyboard proposal not found: $storyboardPath"
}

$storyboard = Get-Content -LiteralPath $storyboardPath -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Force -Path $audioDirectory | Out-Null
Add-Type -AssemblyName System.Speech

$synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $synthesizer.SelectVoice("Microsoft Zira Desktop")
    $synthesizer.Rate = -1
    $synthesizer.Volume = 82

    foreach ($shot in $storyboard.shots) {
        $output = Join-Path $audioDirectory ($shot.id + "-narration.wav")
        $synthesizer.SetOutputToWaveFile($output)
        $synthesizer.Speak($shot.narration)
        $synthesizer.SetOutputToNull()
    }
}
finally {
    $synthesizer.Dispose()
}

Write-Output "Generated offline narration WAVs in $audioDirectory"
