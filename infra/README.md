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
```

Edite `terraform.tfvars` com os valores reais (senha do RDS, token do GitLab Runner, CIDRs autorizados de SSH, nome do bucket). **Nunca commite esse arquivo** — ele já está coberto pelo `.gitignore` (`*.tfvars`).

### 3. Inicialização
Baixa providers e configura o backend S3 que armazena o `tfstate`:
```bash
terraform init
```

Esse passo precisa ser feito uma vez por máquina (e novamente se a versão do provider mudar). O `.terraform.lock.hcl` é versionado no Git pra garantir que todo dev/CI use exatamente a mesma versão do provider AWS.

### 4. Plano e Apply
Sempre rode `plan` antes de `apply` pra revisar o que vai ser criado/alterado:
```bash
terraform fmt -check
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
```

No primeiro apply numa conta limpa, o Terraform vai criar: VPC default já existente (não cria nova), 2 Security Groups, IAM Role + Instance Profile + Policy, instância EC2 com Elastic IP, DB Subnet Group, instância RDS PostgreSQL 16, bucket S3. Tempo médio: **~6 a 10 minutos** (o RDS é o gargalo).

Ao final, os outputs trazem os endereços úteis:
```
ec2_public_ip   = "18.x.x.x"
rds_endpoint    = "vango-db-staging.xxxxx.us-east-2.rds.amazonaws.com:5432"
s3_bucket_name  = "vango-app-files-staging-..."
```

### 5. Destroy
Pra desfazer a stack inteira (cuidado em produção — só rode em staging!):
```bash
terraform destroy
```

`s3_force_destroy = true` por default permite que o bucket seja apagado mesmo com objetos dentro. Se quiser preservar o bucket por engano, defina `s3_force_destroy = false` no `tfvars` antes do destroy. O RDS pula o final snapshot (`skip_final_snapshot = true`) — adequado pra staging, **não usar essa config em produção**.

## Troubleshooting

**"Error: error configuring S3 Backend: NoCredentialProviders"**
AWS CLI sem credenciais configuradas. Rode `aws configure` ou exporte `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` no shell.

**"Error: BucketAlreadyExists"**
Nome de bucket S3 é global. Troque `bucket_name` no `terraform.tfvars` por algo único (ex.: sufixo com seu nome ou um hash).

**"Error: InvalidParameterValue: The parameter MasterUserPassword is not a valid password"**
RDS exige senha com no mínimo 8 caracteres, sem `/`, `"`, `@`, espaços. Ajuste `db_password` no `tfvars`.

**EC2 sobe mas a aplicação não conecta no RDS**
Confira que o `sg-rds` recebe ingress só do `sg-ec2` (já é o caso por design). Verifique também se a instância EC2 está usando a `DATABASE_URL` apontando pro `rds_endpoint` do output — esse valor não é injetado automaticamente, ele vai via GitLab CI/CD variables.

**"Error: timeout while waiting for state to become 'available' (RDS)"**
Pode ser limite de capacidade na região ou subnet group inválido. Rode `terraform apply` de novo — operações do RDS são idempotentes e o Terraform retoma de onde parou.

**`terraform destroy` trava no bucket**
Aconteceu de o `s3_force_destroy` estar `false` e o bucket ter objetos. Edite `terraform.tfvars` pra `s3_force_destroy = true`, rode `terraform apply` pra atualizar o atributo, depois `terraform destroy` novamente.

## Segredos
Esta stack **não gerencia segredos da aplicação**. `DATABASE_URL`, `FIREBASE_CREDENTIALS_PATH` e `MAPBOX_API_KEY` continuam armazenados como **GitLab CI/CD Variables** (Settings → CI/CD → Variables, marcadas como masked + protected).

O Terraform só conhece a senha do RDS, e ela vive como variável `sensitive` em `terraform.tfvars` (não vai pro Git). O `tfstate` (no bucket S3 configurado em `main.tf`) contém essa senha em texto claro — proteja o acesso ao bucket de state com bucket policy restritiva.
