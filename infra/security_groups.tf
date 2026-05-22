# Busca a VPC padrão da sua conta na região de Ohio
data "aws_vpc" "default" {
  default = true
}

# --- Security Group da EC2 (A Aplicação) ---
resource "aws_security_group" "ec2" {
  name        = "vango-sg-ec2-staging"
  description = "Firewall para a instancia EC2 de staging"
  vpc_id      = data.aws_vpc.default.id

  # Regra de Entrada 1: Acesso SSH (Porta 22)
  # A task pede para restringir ao CIDR do time. 
  # Troque o "0.0.0.0/0" pelo IP do escritório/VPN se tiverem, senão deixe assim para testes.
  ingress {
    description = "Acesso SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Regra de Entrada 2: Tráfego da API (Ex: Porta 80 / HTTP)
  ingress {
    description = "Acesso a API"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Regra de Saída: Liberado para a EC2 poder baixar pacotes e conectar na internet
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "vango-sg-ec2-staging"
    Environment = var.environment
  }
}

# --- Security Group do RDS (O Banco de Dados) ---
resource "aws_security_group" "rds" {
  name        = "vango-sg-rds-staging"
  description = "Firewall para o RDS de staging"
  vpc_id      = data.aws_vpc.default.id

  # Regra de Entrada: A REGRA DE OURO (SG-to-SG)
  # Aceita tráfego na porta 5432 APENAS se vier da EC2
  ingress {
    description     = "Acesso ao Postgres restrito a EC2"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id] # <- O segredo está aqui!
  }

  # Regra de Saída padrão
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "vango-sg-rds-staging"
    Environment = var.environment
  }
}