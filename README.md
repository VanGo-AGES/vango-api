# 🚐 VanGO API

Repositório da API do projeto VanGO (Gestão de Vans Escolares).
Este projeto utiliza **Dev Containers** para padronizar o ambiente de desenvolvimento.

## 📚 Guias de Engenharia

- [Como adicionar um domínio do zero](readmes/adding-new-domain.md)

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

## 🗄 Banco de Dados (PostgreSQL + Alembic)

As tabelas são gerenciadas via migrações:
```bash
# Aplicar migrações ao banco
alembic upgrade head

# Criar nova revisão após alterar um modelo
alembic revision --autogenerate -m "nome_da_mudanca"
```

### Recriar o banco do zero

Se você quer subir um banco limpo, recrie o schema antes de rodar o Alembic:

IMPORTANTE: ANTES DE RODAR OS COMANDOS SAIA DO DEV CONTAINER (CLIQUE F1, ABRIR PALHETA DE COMANDOS E SELECIONE O COMANDO 'OPEN FOLDER LOCALLY (DEV CONTAINERS)')
```bash
# Derruba o banco e remove o volume do Postgres
docker compose down -v

# Sobe apenas o banco novamente
docker compose up -d db

```

```bash
# Aplica tudo no banco limpo
alembic upgrade head
```


## 🧹 Qualidade de Código (Ruff)

O linter e o formatador já estão configurados:
```bash
ruff check . --fix  # Corrige erros de lint e tipos automaticamente
ruff format .       # Formata o código conforme o padrão do projeto
```

## ⚠️ Troubleshooting

- **Erro de porta já em uso:** Certifique-se de que não há outro Postgres rodando localmente na porta 5432.
- **Conflito de Containers:** Rode `docker rm -f vango_api vango_db` no seu terminal local se o build falhar por nomes duplicados.

Para dúvidas mais específicas, chame um dos AGES III do Backend, Dalton ou Stéfano no Discord.

---

## 🌿 Padrão de Branches

Use o padrão abaixo para manter organização no fluxo de trabalho:

- `feat/<descricao-curta>`: novas funcionalidades.
- `fix/<descricao-curta>`: correções de bugs.
- `hotfix/<descricao-curta>`: correções urgentes em produção.
- `chore/<descricao-curta>`: ajustes de configuração, dependências e tarefas internas.
- `docs/<descricao-curta>`: atualizações de documentação.
- `test/<descricao-curta>`: criação ou ajuste de testes.

Além disso, commits diretos nas branches `main` e `dev` são bloqueados pelo pre-commit.

### Exemplos

- `feat/cadastro-responsavel`
- `fix/validacao-cpf`
- `chore/atualiza-pre-commit`
- `test/cobertura-endpoints-users`

## 📝 Padrão de Commits

Adote o padrão **Conventional Commits**:

```text
<tipo>(escopo opcional): <mensagem curta no imperativo>
```

### Tipos recomendados

- `feat`: adiciona nova funcionalidade.
- `fix`: corrige bug.
- `docs`: altera documentação.
- `style`: ajustes de formatação (sem alteração lógica).
- `refactor`: refatoração sem mudança de comportamento.
- `test`: adiciona/ajusta testes.
- `chore`: tarefas de manutenção (build, dependências, tooling).

### Exemplos

- `feat(users): adicionar endpoint de cadastro de responsável`
- `fix(auth): corrigir validação de token expirado`
- `docs(readme): atualizar seção de setup com dev container`
- `chore(ci): ajustar workflow de lint`

### Boas práticas

- Escreva mensagens claras e objetivas.
- Prefira commits pequenos e com objetivo único.
- Evite commits genéricos como `ajustes` ou `update`.
