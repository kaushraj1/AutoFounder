terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0.0"
    }
  }
}

variable "endpoint_url" {
  type        = string
  description = "LocalStack endpoint URL"
}

variable "bucket_name" {
  type        = string
  description = "S3 bucket to create"
}

provider "aws" {
  region                      = "ap-south-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3 = var.endpoint_url
  }

  s3_use_path_style = true
}

resource "aws_s3_bucket" "test" {
  bucket = var.bucket_name
}

output "bucket_id" {
  value = aws_s3_bucket.test.id
}
