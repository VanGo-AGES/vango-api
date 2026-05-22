# Agrupa as subnets da rede
resource "aws_db_subnet_group" "rds" {
  name       = "vango-rds-subnet-group-staging"
  subnet_ids = data.aws_subnets.default.ids

  tags = {
    Name = "vango-rds-subnet-group-staging"
  }
}

# O Banco de dados
resource "aws_db_instance" "postgres" {
  identifier        = "vango-db-staging"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = var.db_instance_class
  allocated_storage = 20

  db_name  = "vango_staging_db"
  username = "vango_admin"
  password = "SenhaStagingSegura123!" # Segredos reais ficam na Pipeline

  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id] # <- Trava a segurança com a EC2

  publicly_accessible = false
  skip_final_snapshot = true
  deletion_protection = var.db_deletion_protection

  tags = {
    Name        = "vango-rds-postgres-staging"
    Environment = var.environment
  }
}

# Busca a rede
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}