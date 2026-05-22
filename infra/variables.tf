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