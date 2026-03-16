# Portal da Transparência — RPA API

Robô de automação web para coleta de dados de pessoas físicas no Portal da Transparência do Governo Federal, exposto como API REST assíncrona com fila de execução e autenticação JWT.

---

## Tecnologias

- **Python** + **FastAPI** — API REST
- **Playwright** — automação web (modo headless)
- **Redis** + **RQ (Redis Queue)** — fila de jobs assíncronos
- **Pydantic** — validação de dados
- **JWT** — autenticação via Bearer token

---

## Arquitetura

```
POST /token  →  Autentica e retorna JWT

POST /search  →  Enfileira o job no RQ  →  Worker executa a automação  →  Resultado salvo no Redis
GET /result/{job_id}  →  Consulta o resultado pelo ID do job
```

A API não bloqueia na execução do robô. O cliente recebe um `job_id` imediatamente e consulta o resultado quando quiser. Isso permite execuções simultâneas sem bloqueio.

---

## Estrutura do Projeto

```
app/
├── schemas/
│   └── main.py      # Models Pydantic
├── automation.py    # Robô Playwright
├── main.py          # Rotas FastAPI
└── rq.py            # Configuração Redis + fila
.env
pyproject.toml
```

---

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
USERNAME=seu_usuario
SENHA=sua_senha
JWT_KEY=sua_chave_secreta
```

---

## Como Rodar

### Pré-requisitos

- Python 3.12+
- Redis instalado e rodando
- Poetry

### Instalação

```bash
poetry install
poetry run playwright install
poetry run playwright install-deps
```

### Subir os serviços

```bash
# Terminal 1 — Redis
redis-server

# Terminal 2 — Worker RQ
poetry run rq worker

# Terminal 3 — API
poetry run uvicorn app.main:app --reload
```

---

## Autenticação

Todas as rotas (exceto `/token`) exigem um Bearer token JWT.

### Obter token

```
POST /token
```

Envie `username` e `password` via form data. O token expira em 1 hora.

---

## Endpoints

### `POST /search`

Inicia uma busca no Portal da Transparência.

**Parâmetros:**
- `search` (obrigatório) — nome, CPF ou NIS. Mínimo 3 caracteres.
- `filtro_busca` (opcional) — ex: `"BENEFICIÁRIO DE PROGRAMA SOCIAL"`

Retorna um `job_id` para consulta posterior.

---

### `GET /result/{job_id}`

Consulta o resultado de um job. Possíveis status: `pending`, `Success` ou `failed`.

O resultado inclui nome, CPF, localidade, benefícios encontrados e evidência da tela em Base64.

---

## Documentação interativa

Com a API rodando, acesse:

```
http://localhost:8000/docs
```

---

## Decisões Técnicas

**Playwright** foi escolhido por sua API moderna, suporte nativo a sync/async, e robustez no tratamento de páginas com JavaScript pesado como o Portal da Transparência.

**RQ + Redis** foi escolhido para desacoplar o recebimento da requisição da execução do robô, permitindo que múltiplas buscas sejam enfileiradas e executadas simultaneamente por workers independentes, sem bloquear a API.

**JWT** foi adicionado para proteger os endpoints, com credenciais configuráveis via variáveis de ambiente.

O robô retorna a **evidência da tela em Base64** junto aos dados coletados, eliminando a necessidade de armazenar arquivos em disco.