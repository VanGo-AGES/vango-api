# Agrupa as subnets da rede
resource "aws_db_subnet_group" "rds" {
  name       = "vango-rds-subnet-group-${var.environment}" # <- Dinâmico
  subnet_ids = data.aws_subnets.default.ids

  tags = {
    Name = "vango-rds-subnet-group-${var.environment}"
  }
}

# O Banco de dados
resource "aws_db_instance" "postgres" {
  identifier        = "vango-db-${var.environment}" # <- Dinâmico
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = var.db_instance_class
  allocated_storage = 20

  parameter_group_name = aws_db_parameter_group.postgres_custom.name

  # O DB Name não aceita hífen (-), só underscore (_)
  db_name  = "vango_db_${var.environment}" 
  username = "vango_admin"
  password = var.db_password # <- Trazemos da variável pra não expor a senha no código!

  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  publicly_accessible = false
  
  skip_final_snapshot     = var.db_skip_final_snapshot
  deletion_protection     = var.db_deletion_protection
  backup_retention_period = var.db_backup_retention_period

  tags = {
    Name        = "vango-rds-postgres-${var.environment}"
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

resource "aws_db_parameter_group" "postgres_custom" {
  name   = "vango-postgres16-${var.environment}-params" # <- Dinâmico
  family = "postgres16" 

  # Loga queries lentas (mais de 500ms)
  parameter {
    name  = "log_min_duration_statement"
    value = "500"
  }

  # Loga alterações estruturais (CREATE, ALTER, DROP)
  parameter {
    name  = "log_statement"
    value = "ddl"
  }

  # Coleta estatísticas detalhadas do banco
  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  # Limite de conexões (pool_size * num_workers + margem)
  parameter {
    name  = "max_connections"
    value = "100" 
    apply_method = "pending-reboot"
  }
}