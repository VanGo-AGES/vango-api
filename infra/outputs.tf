output "ec2_public_ip" {
  description = "IP Publico da instancia EC2"
  value       = aws_eip.api_ip.public_ip
}

output "rds_endpoint" {
  description = "Endpoint de conexao do banco de dados RDS"
  value       = aws_db_instance.postgres.endpoint
}

output "s3_bucket_name" {
  description = "Nome do bucket S3 criado"
  value       = aws_s3_bucket.app_bucket.bucket
}