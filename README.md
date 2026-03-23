# 🚐 VanGO API

Repositório da API do projeto VanGO (Gestão de Vans Escolares). 
Este projeto utiliza **Dev Containers** para padronizar o ambiente de desenvolvimento.

---

## 🚀 Como Começar (Quick Start)

### Pré-requisitos:
1. **Docker** instalado e rodando.
2. **VS Code** com a extensão **Dev Containers**.

### Instalação:
1. Clone o repositório.
2. Abra a pasta no VS Code.
3. Quando o prompt aparecer, clique em **"Reopen in Container"** (ou use `F1` > `Dev Containers: Reopen in Container`).
4. O VS Code fará o build da imagem e instalará as dependências automaticamente.

---

## 🛠 Comandos Essenciais (Terminal do Container)

### 🔌 Servidor de Desenvolvimento
#### Opção 1: Debugger do VS Code (Altamente Recomendado 🚀)
Esta é a melhor forma de desenvolver. Permite pausar a execução (breakpoints) e inspecionar variáveis.
1. Pressione `F5` no teclado.
2. O servidor subirá automaticamente com o debugger ativado.

#### Opção 2: Terminal (Hot-reload manual)
Caso prefira rodar direto no terminal:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger UI: http://localhost:8000/docs

🗄 Banco de Dados (PostgreSQL + Alembic)

As tabelas são gerenciadas via migrações:
```bash

# Aplicar migrações ao banco
alembic upgrade head

# Criar nova revisão após alterar um modelo
alembic revision --autogenerate -m "nome_da_mudanca"
```

🧹 Qualidade de Código (Ruff)

O linter e o formatador já estão configurados:
```bash
ruff check . --fix  # Corrige erros de lint e tipos automaticamente
ruff format .       # Formata o código conforme o padrão do projeto
```
⚠️ Troubleshooting

Erro de porta já em uso: Certifique-se de que não há outro Postgres rodando localmente na porta 5432.

Conflito de Containers: Rode docker rm -f vango_api vango_db no seu terminal local se o build falhar por nomes duplicados.

Para dúvidas mais específicas, chame um dos AGES III do Backend, Dalton ou Stéfano no Discord.
