provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "package_history" {
  bucket = "yum-package-history-shared"
}

resource "aws_s3_bucket_versioning" "package_history" {
  bucket = aws_s3_bucket.package_history.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "package_history" {
  bucket = aws_s3_bucket.package_history.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "package_history" {
  bucket = aws_s3_bucket.package_history.id

  rule {
    id     = "transition_old_versions"
    status = "Enabled"

    filter {}

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = 90
      storage_class   = "GLACIER"
    }
  }
}

output "bucket_name" {
  value = aws_s3_bucket.package_history.bucket
}

output "bucket_arn" {
  value = aws_s3_bucket.package_history.arn
}
