param([Parameter(Mandatory=$true)][string]$InputFile,[Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$sourcePath = (Resolve-Path -LiteralPath $InputFile).Path
$outputPath = [System.IO.Path]::GetFullPath($OutputDirectory)
[System.IO.Directory]::CreateDirectory($outputPath) | Out-Null
$pdfPath = Join-Path $outputPath ([System.IO.Path]::GetFileNameWithoutExtension($sourcePath) + '.pdf')
$wordApplication = New-Object -ComObject Word.Application
$wordApplication.Visible = $false
$wordApplication.DisplayAlerts = 0
$wordApplication.AutomationSecurity = 3
try {
    $document = $wordApplication.Documents.Open($sourcePath, $false, $true)
    try {
        $document.Repaginate()
        $document.ExportAsFixedFormat($pdfPath, 17)
        Write-Output ('Pages: ' + $document.ComputeStatistics(2))
        Write-Output $pdfPath
    } finally { $document.Close(0) }
} finally { $wordApplication.Quit() }
