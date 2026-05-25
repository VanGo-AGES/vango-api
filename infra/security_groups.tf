data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "ec2" {
  name        = "vango-sg-ec2-staging"
  description = "Firewall para a instancia EC2 de staging"
  vpc_id      = data.aws_vpc.default.id

  # Regra de Entrada 1: Acesso SSH Restrito
  ingress {
    description = "Acesso SSH restrito"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidrs # CORRIGIDO: Vinculado a lista restrita
  }

  ingress {
    description = "Acesso a API"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

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

resource "aws_security_group" "rds" {
  name        = "vango-sg-rds-staging"
  description = "Firewall para o RDS de staging"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "Acesso ao Postgres restrito a EC2"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

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
