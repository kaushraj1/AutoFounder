<#
.SYNOPSIS
  Bootstrap the Terraform remote-state backend for an environment (Windows).
  Creates the versioned, encrypted, private S3 state bucket and the shared
  DynamoDB lock table. Idempotent — safe to re-run.

.EXAMPLE
  .\bootstrap-state.ps1 -Environment staging
  .\bootstrap-state.ps1 -Environment production -Region ap-south-1

.NOTES
  Requires: AWS CLI v2, credentials with S3 + DynamoDB create permissions.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("staging", "production")]
  [string]$Environment,

  [string]$Region = "ap-south-1"
)

$ErrorActionPreference = "Stop"
$LockTable = "autofounder-ai-tfstate-lock"
$Bucket = "autofounder-ai-tfstate-$Environment"

Write-Host "==> Region: $Region  Bucket: $Bucket  Lock table: $LockTable"

# --- S3 state bucket -------------------------------------------------------
$bucketExists = $false
try { aws s3api head-bucket --bucket $Bucket --region $Region 2>$null; if ($?) { $bucketExists = $true } } catch {}

if ($bucketExists) {
  Write-Host "==> Bucket $Bucket already exists."
}
else {
  Write-Host "==> Creating bucket $Bucket..."
  if ($Region -eq "us-east-1") {
    aws s3api create-bucket --bucket $Bucket --region $Region
  }
  else {
    aws s3api create-bucket --bucket $Bucket --region $Region --create-bucket-configuration "LocationConstraint=$Region"
  }
}

Write-Host "==> Enabling versioning, encryption, and public-access block..."
aws s3api put-bucket-versioning --bucket $Bucket --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket $Bucket --server-side-encryption-configuration '{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":{\"SSEAlgorithm\":\"AES256\"},\"BucketKeyEnabled\":true}]}'
aws s3api put-public-access-block --bucket $Bucket --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-lifecycle-configuration --bucket $Bucket --lifecycle-configuration '{\"Rules\":[{\"ID\":\"expire-noncurrent-state\",\"Status\":\"Enabled\",\"Filter\":{\"Prefix\":\"\"},\"NoncurrentVersionExpiration\":{\"NoncurrentDays\":90}}]}'

# Deny any non-TLS access to the state bucket (CIS S3.5). Written to a temp file
# to sidestep Windows JSON-escaping issues. A Deny/Principal:* policy does not
# grant public access, so it is permitted under the public-access-block above.
$denyPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyInsecureTransport",
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": ["arn:aws:s3:::$Bucket", "arn:aws:s3:::$Bucket/*"],
    "Condition": {"Bool": {"aws:SecureTransport": "false"}}
  }]
}
"@
$policyFile = New-TemporaryFile
Set-Content -Path $policyFile.FullName -Value $denyPolicy -Encoding utf8
aws s3api put-bucket-policy --bucket $Bucket --policy "file://$($policyFile.FullName)"
Remove-Item $policyFile.FullName -Force

# --- DynamoDB lock table ---------------------------------------------------
$tableExists = $false
try { aws dynamodb describe-table --table-name $LockTable --region $Region 2>$null | Out-Null; if ($?) { $tableExists = $true } } catch {}

if ($tableExists) {
  Write-Host "==> Lock table $LockTable already exists."
}
else {
  Write-Host "==> Creating DynamoDB lock table $LockTable..."
  aws dynamodb create-table --table-name $LockTable --attribute-definitions AttributeName=LockID,AttributeType=S --key-schema AttributeName=LockID,KeyType=HASH --billing-mode PAY_PER_REQUEST --sse-specification Enabled=true,SSEType=KMS --region $Region
  aws dynamodb wait table-exists --table-name $LockTable --region $Region
  # Point-in-time recovery so a corrupted lock table is recoverable.
  aws dynamodb update-continuous-backups --table-name $LockTable --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true --region $Region
}

Write-Host "==> Done. Initialize Terraform with:"
Write-Host "    terraform init -backend-config=env/$Environment.backend.hcl"
