# VanGO - Infraestrutura como Código (IaC) com Terraform

Este diretório contém a especificação da infraestrutura do VanGO na AWS para o ambiente de **Staging (Homologação)**. Toda a stack é provisionada de forma automatizada e idempotente.

## 🚀 Arquitetura Resumida
* **Rede:** Utiliza a VPC Default da conta na região de Ohio (`us-east-2`).
* **Segurança (Security Groups):** * `sg-ec2`: Permite SSH (porta 22) e tráfego HTTP para a API (porta 80).
  * `sg-rds`: Segurança **SG-to-SG**. Isola totalmente o banco de dados, permitindo conexões na porta 5432 vinda *única e exclusivamente* da instância EC2.
* **Computação (EC2):** Instância baseada em Amazon Linux 2023. O script de `user_data` instala automaticamente o Docker, o Docker Compose e registra um GitLab Runner dinâmico vinculado ao projeto. Possui uma IAM Role dedicada para acesso restrito ao S3.
* **Banco de Dados (RDS):** Instância gerenciada PostgreSQL 16 com proteção contra exclusão controlável.
* **Armazenamento (S3):** Bucket privado com versionamento ativo, criptografia AES256 padrão e bloqueio total de acesso público (4 flags ativas).

## 🛠️ Como Utilizar Localmente

### 1. Pré-requisitos
* Terraform CLI instalado (versão >= 1.5.0)
* AWS CLI instalado e configurado com as credenciais da conta de Staging

### 2. Configuração Inicial
Na raiz da pasta `infra/`, copie o arquivo de exemplo de variáveis:
```bash
cp terraform.tfvars.example terraform.tfvars