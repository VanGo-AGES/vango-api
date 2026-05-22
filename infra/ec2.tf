# --- 1. IAM Role (O "crachá" da máquina para acessar o S3) ---
resource "aws_iam_role" "ec2_role" {
  name = "vango-ec2-role-staging"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# Define as regras exatas do que a máquina pode fazer no S3
resource "aws_iam_policy" "s3_access" {
  name        = "vango-s3-access-policy-staging"
  description = "Permite a EC2 acessar o bucket S3 do projeto"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.bucket_name}",
          "arn:aws:s3:::${var.bucket_name}/*"
        ]
      }
    ]
  })
}

# Anexa as regras ao crachá de segurança
resource "aws_iam_role_policy_attachment" "ec2_s3_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.s3_access.arn
}

# Perfil que será de fato pendurado na instância EC2
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "vango-ec2-profile-staging"
  role = aws_iam_role.ec2_role.name
}

# --- 2. Busca o Sistema Operacional correto (AL2023 para processadores Intel/AMD x86_64) ---
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"] # Garante a compatibilidade com t3.micro
  }
}

# --- 3. A Máquina EC2 ---
resource "aws_instance" "api" {
  ami                  = data.aws_ami.amazon_linux_2023.id
  instance_type        = var.instance_type
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name # Associa o crachá do S3

  vpc_security_group_ids = [aws_security_group.ec2.id] # Associa o firewall da EC2

  # Script de inicialização automática (User Data) compilado para x86_64
  user_data = <<-EOF
    #!/bin/bash
    # Atualiza todos os pacotes do sistema operacional
    dnf update -y
    
    # Instala o Docker e o Git
    dnf install -y docker git
    systemctl enable --now docker
    usermod -aG docker ec2-user
    
    # Instala o Docker Compose (Versão x86_64 correta para T3)
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Instala o GitLab Runner (Versão AMD64/x86_64 correta para T3)
    curl -L "https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64" -o /usr/local/bin/gitlab-runner
    chmod +x /usr/local/bin/gitlab-runner
    useradd --comment 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash
    gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
    systemctl enable --now gitlab-runner
    
    # Adiciona o runner ao grupo do docker para evitar erros de permissão de deploy
    usermod -aG docker gitlab-runner
    
    # Registra o Runner temporário no GitLab do projeto
    gitlab-runner register \
      --non-interactive \
      --url "https://gitlab.com/" \
      --registration-token "${var.gitlab_runner_token}" \
      --executor "shell" \
      --description "vango-staging-runner" \
      --tag-list "staging,vango-ec2"
  EOF

  tags = {
    Name        = "vango-ec2-staging"
    Environment = var.environment
  }
}

# --- 4. Elastic IP (IP Fixo da Máquina) ---
resource "aws_eip" "api_ip" {
  instance = aws_instance.api.id
  domain   = "vpc"

  tags = {
    Name        = "vango-eip-staging"
    Environment = var.environment
  }
}