# To-Do List API

Micro-API REST para gerenciamento de tarefas, desenvolvida como MVP com FastAPI, SQLAlchemy e SQLite.

## Objetivo

Disponibilizar uma base enxuta e evolutiva para gerenciamento de tarefas com operações de CRUD, filtragem e validação de dados, priorizando separação de responsabilidades e testabilidade.

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy ORM
- SQLite
- Pydantic v2
- Pytest
- Uvicorn

## Funcionalidades do MVP

- Criar tarefa
- Listar tarefas
- Buscar tarefa por ID
- Atualizar tarefa
- Excluir tarefa
- Filtrar tarefas por ID e status
- Endpoint de health check

## Arquitetura

Arquitetura em camadas para separar responsabilidades:

- `api`:
	Camada HTTP (roteamento, status codes, tratamento de exceções de aplicação).
- `services`:
	Regras de negócio e orquestração dos casos de uso.
- `repositories`:
	Acesso a dados via SQLAlchemy.
- `models`:
	Entidades ORM persistidas no banco.
- `schemas`:
	Contratos de entrada e saída com validação via Pydantic.
- `db`:
	Configuração de engine, sessão e inicialização de tabelas.

Fluxo principal:

`Request HTTP -> Router -> Service -> Repository -> SQLite`

## Instalação

### Pré-requisitos

- Python 3.12+
- `pip`

### Passos

```bash
git clone https://github.com/leoguifo/to-do-list.git
cd to-do-list

python -m venv .venv
```

Ativação do ambiente virtual:

```bash
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

Instalação de dependências:

```bash
pip install -r requirements.txt
```

## Execução da aplicação

```bash
uvicorn app.main:app --reload
```

Endpoints úteis:

- API: http://localhost:8000
- Docs Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Testes

Executar toda a suíte:

```bash
pytest
```

Executar apenas testes de serviço:

```bash
pytest tests/test_task_service.py -q
```

Executar apenas testes de rota:

```bash
pytest tests/test_task_routes.py tests/test_health_routes.py -q
```

## Limitações atuais (MVP)

- Sem autenticação/autorização
- Sem paginação e ordenação avançada
- Sem observabilidade estruturada (logs, tracing e métricas)
- Sem migrações de banco versionadas
- Sem suporte a multiusuário/multi-tenant

## Próximos passos

- Adicionar camada de configuração por ambiente
- Incluir migrações com Alembic
- Implementar paginação e ordenação em listagens
- Adicionar cobertura de testes para cenários negativos adicionais
- Incluir pipeline CI para lint, testes e validação de build

## Licença

Uso educacional e de prototipação.
