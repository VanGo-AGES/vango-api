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

resource "aws_iam_role_policy_attachment" "ec2_s3_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.s3_access.arn
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "vango-ec2-profile-staging"
  role = aws_iam_role.ec2_role.name
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_instance" "api" {
  ami                  = data.aws_ami.amazon_linux_2023.id
  instance_type        = var.instance_type
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  vpc_security_group_ids = [aws_security_group.ec2.id]

  user_data = <<-EOF
    #!/bin/bash
    dnf update -y

    dnf install -y docker git
    systemctl enable --now docker
    usermod -aG docker ec2-user

    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    curl -L "https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64" -o /usr/local/bin/gitlab-runner
    chmod +x /usr/local/bin/gitlab-runner
    useradd --comment 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash
    gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
    systemctl enable --now gitlab-runner

    usermod -aG docker gitlab-runner

    # CORRIGIDO: Alterado para o novo padrao do GitLab (--token com fluxo GLRT)
    gitlab-runner register \
      --non-interactive \
      --url "https://gitlab.com/" \
      --token "${var.gitlab_runner_token}" \
      --executor "shell" \
      --description "vango-staging-runner" \
      --tag-list "staging,vango-ec2"
  EOF

  tags = {
    Name        = "vango-ec2-staging"
    Environment = var.environment
  }
}

resource "aws_eip" "api_ip" {
  instance = aws_instance.api.id
  domain   = "vpc"

  tags = {
    Name        = "vango-eip-staging"
    Environment = var.environment
  }
}
