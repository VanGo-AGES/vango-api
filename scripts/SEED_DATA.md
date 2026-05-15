# Dados do Seed — VanGo API

Referência rápida para testes manuais no app. Todos os usuários usam a mesma senha.

**Senha padrão:** `senha123`

---

## Como executar

```bash
# Dentro do container ou com o venv ativo, a partir da raiz do projeto

# Popula (só roda se o banco ainda estiver vazio)
python -m scripts.seed

# Limpa tudo e re-popula do zero
python -m scripts.seed --reset
```

---

## Usuários

### Motoristas

| Nome | E-mail | Senha | CPF |
|---|---|---|---|
| Carlos Eduardo Oliveira | `carlos.oliveira@example.com` | `senha123` | 123.456.789-01 |
| Roberto Alves Ferreira | `roberto.ferreira@example.com` | `senha123` | 987.654.321-00 |

### Guardiões (com dependentes)

| Nome | E-mail | Senha | Dependente |
|---|---|---|---|
| Ana Paula Rodrigues | `ana.rodrigues@example.com` | `senha123` | Mateus Rodrigues |
| Fernanda Lima | `fernanda.lima@example.com` | `senha123` | Isabela Lima |

### Passageiros

| Nome | E-mail | Senha | Status na rota |
|---|---|---|---|
| João Vitor Santos | `joao.santos@example.com` | `senha123` | Aceito (Rota Escolar) |
| Mariana Costa | `mariana.costa@example.com` | `senha123` | Aceita (Rota Empresarial) |
| Thiago Becker | `thiago.becker@example.com` | `senha123` | Aceito (Rota Empresarial) |
| Juliana Fonseca | `juliana.fonseca@example.com` | `senha123` | **Pendente** (Rota Empresarial) |

---

## Cenário 1 — Rota Escolar Zona Norte (Carlos Oliveira)

**Veículo:** Sprinter branca — placa `IJK-1A23`, 8 lugares

### Rota

| Campo | Valor |
|---|---|
| Nome | Rota Escolar Zona Norte — Manhã |
| Tipo | `outbound` (ida) |
| Recorrência | seg, ter, qua, qui, sex |
| Horário | 07:00 |
| Status | ativa |
| Origem | Av. Assis Brasil, 3970 — Passo d'Areia |
| Destino | Rua Mostardeiro, 50 — Moinhos de Vento |

### Passageiros da rota

| Passageiro | Dependente | Endereço de embarque | Dias | Status |
|---|---|---|---|---|
| Ana Paula Rodrigues | Mateus Rodrigues | Rua Ângelo Giusti, 120 — Passo d'Areia | seg–sex | aceito |
| Fernanda Lima | Isabela Lima | Av. Assis Brasil, 1256 — Floresta | seg–sex | aceito |
| João Vitor Santos | — | Rua Felipe Camarão, 800 — Higienópolis | seg, qua, sex | aceito |

### Stops (paradas)

| Ordem | Endereço | Tipo | Passageiro |
|---|---|---|---|
| 1 | Rua Ângelo Giusti, 120 — Passo d'Areia | embarque | Mateus Rodrigues (Ana Paula) |
| 2 | Av. Assis Brasil, 1256 — Floresta | embarque | Isabela Lima (Fernanda) |
| 3 | Rua Felipe Camarão, 800 — Higienópolis | embarque | João Vitor Santos |

### Viagens

| # | Data | Status | Observação |
|---|---|---|---|
| Trip 1 | Ontem — 07:00 | `finalizada` | Todos presentes. 12,4 km. Duração: ~46 min. |
| Trip 2 | Hoje — 07:00 | `iniciada` | Ana Paula e João embarcaram. Isabela **ausente** (avisou: "Isabela está doente hoje."). |

---

## Cenário 2 — Rota Empresarial Centro (Roberto Ferreira)

**Veículo:** Master prata — placa `RST-5B67`, 12 lugares

### Rota

| Campo | Valor |
|---|---|
| Nome | Rota Empresarial Centro — Tarde |
| Tipo | `inbound` (volta) |
| Recorrência | seg, qua, sex |
| Horário | 17:45 |
| Status | ativa |
| Origem | Rua da República, 230 — Cidade Baixa |
| Destino | Av. Nilo Peçanha, 2900 — Bela Vista |

### Passageiros da rota

| Passageiro | Endereço de embarque | Dias | Status |
|---|---|---|---|
| Mariana Costa | Av. Borges de Medeiros, 1501 — Centro Histórico | seg, qua, sex | aceita |
| Thiago Becker | Rua dos Andradas, 1234 — Centro Histórico | seg, qua, sex | aceito |
| Juliana Fonseca | Rua General Lima e Silva, 712 — Cidade Baixa | — | **pendente** (sem stop, sem schedule) |

### Stops (paradas)

| Ordem | Endereço | Tipo | Passageiro |
|---|---|---|---|
| 1 | Av. Borges de Medeiros, 1501 — Centro Histórico | embarque | Mariana Costa |
| 2 | Rua dos Andradas, 1234 — Centro Histórico | embarque | Thiago Becker |

### Viagens

| # | Data | Status | Observação |
|---|---|---|---|
| Trip 1 | Hoje — 17:45 | `iniciada` | Mariana embarcou. Thiago ainda pendente. |

---

## Regras de negócio refletidas no seed

- **Stop** só existe para passageiros com status `accepted` — Juliana (pendente) não tem stop nem schedule.
- **TripPassanger** só é criado para passageiros aceitos na rota no momento da viagem.
- **AbsenceModel** registrado para Isabela Lima na Trip 2: aviso prévio de falta vinculado à viagem em andamento.
- **Veículo** pertence ao motorista da rota em que é usado.
