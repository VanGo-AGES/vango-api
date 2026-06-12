variable "aws_region" {
  description = "Regiao da AWS"
  type        = string
  default     = "us-east-2" # Atualizado para Ohio
}

variable "environment" {
  description = "Ambiente da infraestrutura"
  type        = string
  default     = "staging"
}

variable "instance_type" {
  description = "Tipo de instancia da EC2"
  type        = string
  default     = "t3.micro" # Mantido o padrão t3 pedido na task
}

variable "gitlab_runner_token" {
  description = "Token do GitLab Runner"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "Tamanho do Banco de Dados"
  type        = string
  default     = "db.t3.micro"
}

variable "bucket_name" {
  description = "Nome do bucket da aplicacao"
  type        = string
}

variable "db_deletion_protection" {
  description = "Protecao contra exclusao do RDS"
  type        = bool
  default     = false
}

variable "s3_force_destroy" {
  description = "Forcar exclusao do bucket no destroy"
  type        = bool
  default     = true
}

variable "db_password" {
  description = "Senha do banco de dados RDS"
  type        = string
  sensitive   = true # Isso impede que a senha apareça nos logs do terminal
}

variable "allowed_ssh_cidrs" {
  description = "Lista de IPs com permissao de acesso via SSH/VPC"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "db_backup_retention_period" {
  description = "Dias para reter os backups automaticos do RDS"
  type        = number
  default     = 0
}

variable "db_skip_final_snapshot" {
  description = "Pular snapshot final antes de deletar o banco"
  type        = bool
  default     = true
}