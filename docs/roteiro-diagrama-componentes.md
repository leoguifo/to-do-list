# Roteiro — Diagrama de Componentes (To-Do List API)

> Documento de planejamento do diagrama estrutural (C4 nível de componentes).
> Etapa de roteiro aprovada. O diagrama PlantUML será produzido em etapa posterior,
> seguindo exatamente este roteiro.

## Roteiro (Tabela 2)

| Elemento | Definição |
|----------|-----------|
| **Escopo** | Refinamento do diagrama de **componentes** (`docs/architecture.md`), representando a organização interna em camadas da To-Do List API (FastAPI + SQLAlchemy). Entram 4 elementos: Router/Controller, Task Service, Task Repository e persistência. Fora: schemas Pydantic, camada `db` (engine/session), router de `health`, timestamps, exceções e status codes. |
| **Nível** | Componentes (C4 nível 3). |
| **Limites** | Fronteira única "To-Do List API (processo FastAPI local)"; ator externo "Client" (HTTP/JSON). Persistência **fora** da fronteira da API, como sistema separado. Sem fronteiras de deploy/cloud/containers. |
| **Integrações** | Única integração externa = banco SQLite via SQLAlchemy ORM, modelado como sistema/serviço separado. Sem auth, sem terceiros, sem multi-tenant. |
| **Restrições** | Fluxo estritamente em camadas `Router -> Service -> Repository -> SQLite` (cada camada só conhece a imediatamente inferior). Aresta `Router->Repository` representada de forma **idealizada (b)**: Router conhece apenas o Service. Entidade "Task" representada de forma **única** (sem separar ORM de Pydantic). Notação-alvo: C4 em PlantUML. |
| **Lacunas resolvidas** | Aresta `Router->Repository` = idealizada (b); itens planejados (Alembic/migrações, config por ambiente, paginação/ordenação, CI) aparecerão marcados como **não concluídos / futuros** (estereótipo «planejado» ou nota), sem sugerir que já existem. |

## Resumo das decisões

- **Nível:** componentes (refino do C4 atual).
- **Escopo:** Router, Service, Repository, DB.
- **Ocultos:** schemas, camada `db`, health router, detalhes internos.
- **Camadas:** `Router -> Service -> Repository -> SQLite`, com `Router->Repository` idealizado (b).
- **Task:** entidade única.
- **Persistência:** sistema/serviço separado, fora da fronteira da API.
- **Planejado:** incluído e sinalizado como não concluído.
- **Notação:** C4 em PlantUML.

## Próxima etapa

Gerar o PlantUML (C4 de componentes) seguindo este roteiro. Não incluído nesta etapa.
