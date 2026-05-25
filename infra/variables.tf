variable "aws_region" {
  description = "Regiao da AWS"
  type        = string
  default     = "us-east-2"
}

variable "environment" {
  description = "Ambiente da infraestrutura"
  type        = string
  default     = "staging"
}

variable "instance_type" {
  description = "Tipo de instancia da EC2"
  type        = string
  default     = "t3.micro"
}

variable "gitlab_runner_token" {
  description = "Token do GitLab Runner (Formato GLRT-)"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "Tamanho do Banco de Dados"
  type        = string
  default     = "db.t3.micro"
}

variable "db_password" {
  description = "Senha do administrador do banco de dados RDS"
  type        = string
  sensitive   = true
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

variable "allowed_ssh_cidrs" {
  description = "Lista de blocos CIDR autorizados para acesso SSH"
  type        = list(string)
}
