$ErrorActionPreference = 'Continue'
$root = "C:\Users\PA535HZ\Documents\PROJECT-1-AutoFounder-AI\backend\app\agents\devops\terraform_templates"
$logFile = "C:\Users\PA535HZ\Documents\PROJECT-1-AutoFounder-AI\scripts\tf-validate.log"
if (Test-Path $logFile) { Remove-Item $logFile }
$dirs = @('_shared','networking','ecs','data-layer','alb')
foreach ($d in $dirs) {
  Set-Location "$root\$d"
  "==================== MODULE: $d ====================" | Tee-Object -FilePath $logFile -Append | Write-Host
  "-- fmt --" | Tee-Object -FilePath $logFile -Append | Write-Host
  $fmt = terraform fmt -check -recursive 2>&1 | Out-String
  "exit=$LASTEXITCODE`n$($fmt.Trim())" | Tee-Object -FilePath $logFile -Append | Write-Host
  "-- init --" | Tee-Object -FilePath $logFile -Append | Write-Host
  $init = terraform init -backend=false -input=false -no-color 2>&1 | Out-String
  "exit=$LASTEXITCODE`n$($init.Trim())" | Tee-Object -FilePath $logFile -Append | Write-Host
  "-- validate --" | Tee-Object -FilePath $logFile -Append | Write-Host
  $validate = terraform validate -no-color 2>&1 | Out-String
  "exit=$LASTEXITCODE`n$($validate.Trim())" | Tee-Object -FilePath $logFile -Append | Write-Host
}
Set-Location $root
"DONE" | Tee-Object -FilePath $logFile -Append | Write-Host
