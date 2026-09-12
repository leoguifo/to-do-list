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

### Documentação de diagramas (Diagrams as Code)

- [`docs/roteiro-diagrama-componentes.md`](docs/roteiro-diagrama-componentes.md): roteiro que fundamenta o diagrama de componentes (Escopo, Nível, Limites, Integrações, Restrições, Lacunas).
- [`docs/diagram-as-code.md`](docs/diagram-as-code.md): diagrama de componentes (C4 nível 3) em Mermaid C4.
- [`docs/relatorio-diagram-as-code.md`](docs/relatorio-diagram-as-code.md): relatório de discovery de documentação, com decisões e ajustes sobre o que o modelo gerou.

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

## Análise de riscos e comunicação

Foi realizada uma análise estruturada de riscos do MVP com registro em duas frentes complementares:

- Pasta `riscos/`:
	- `identificação.md`: levantamento dos principais riscos técnicos do projeto.
	- `analise.md`: classificação qualitativa de probabilidade e impacto, com matriz de riscos.
	- `respostas.md`: estratégias de tratamento por risco (evitar, mitigar, transferir ou aceitar), incluindo trade-offs e critérios de decisão.
- Pasta `comunicacao/`:
	- `status-stakeholders.md`: consolidação executiva para diretoria e áreas de negócio, destacando status, causas de atraso, impactos no negócio e próximos passos.

### Síntese dos principais riscos mapeados

- Configuração de banco de dados dependente de caminho fixo no código.
- Ausência de migração versionada de schema.
- Campo `status` sem restrição no nível do banco.
- Listagem sem paginação (risco de degradação com crescimento de volume).
- Dependências sem lock transitive completo.
- Evolução de escopo com potencial de refatoração estrutural.
- Falta de padronização automatizada de lint/formatação para equipe distribuída.
- `PATCH` com payload vazio aceito silenciosamente.

### Resultado da análise

A análise indicou que, embora o MVP esteja funcional, havia risco de retrabalho em evolução e operação. Por isso, foi recomendado um ajuste de curto prazo no planejamento para priorizar estabilização técnica (configuração por ambiente, estratégia de migrações, paginação básica e padronização de qualidade), reduzindo exposição a regressões e melhorando previsibilidade das próximas entregas.
