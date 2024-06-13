param(
   [string]$inputFile = "file_with_crlf.txt",
   [string]$outputFile = "file_with_lf.txt"
)

$fileContent = Get-Content -Raw -Path $inputFile
$fileContent = $fileContent -replace "`r`n", "`n"
Set-Content -Path $outputFile -Value $fileCOntent -NoNewline