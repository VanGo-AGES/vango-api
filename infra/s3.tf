resource "aws_s3_bucket" "app_bucket" {
  bucket        = var.bucket_name
  force_destroy = var.s3_force_destroy

  tags = {
    Name        = "vango-s3-staging"
    Environment = var.environment
  }
}

# Ativa versionamento
resource "aws_s3_bucket_versioning" "app_bucket_versioning" {
  bucket = aws_s3_bucket.app_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Ativa criptografia exigida na task
resource "aws_s3_bucket_server_side_encryption_configuration" "app_bucket_crypto" {
  bucket = aws_s3_bucket.app_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Bloqueia acesso público (Os 4 flags da task)
resource "aws_s3_bucket_public_access_block" "app_bucket_privacy" {
  bucket = aws_s3_bucket.app_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}