# Diagrama de Componentes (Diagram as Code) — To-Do List API

Diagrama estrutural no nível de **componentes** (C4 nível 3), gerado a partir do
roteiro aprovado em [`roteiro-diagrama-componentes.md`](./roteiro-diagrama-componentes.md).

> Renderização: o bloco abaixo usa **Mermaid C4**, que o GitHub e a maioria dos
> previews Markdown renderizam nativamente.

## Diagrama

```mermaid
C4Component
    title Diagrama de Componentes - To-Do List API

    Person(client, "Client", "Consumidor da API: browser, app, curl etc.")

    Container_Boundary(api, "To-Do List API (processo FastAPI local)") {
        Component(router, "Router / Controller", "FastAPI APIRouter", "Recebe requisicoes HTTP e delega ao Service.")
        Component(service, "Task Service", "Python", "Regras de negocio e orquestracao dos casos de uso.")
        Component(repository, "Task Repository", "SQLAlchemy ORM", "Acesso a dados: operacoes CRUD sobre a entidade Task.")
        Component(planned, "Evolucoes planejadas «planejado»", "Roadmap", "Migracoes (Alembic), config por ambiente, paginacao/ordenacao, CI. NAO concluido.")
    }

    System_Ext(db, "SQLite Database «external»", "Persistencia local via SQLAlchemy ORM (arquivo .db).")

    Rel(client, router, "HTTP Request", "JSON / REST")
    Rel(router, service, "Chama regras de negocio")
    Rel(service, repository, "Delega operacoes de dados")
    Rel(repository, db, "Executa queries", "SQLAlchemy ORM")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

## Legenda das decisões

- **Escopo:** apenas Router, Service, Repository e persistência (DB).
- **Camadas:** `Client -> Router -> Service -> Repository -> SQLite`.
- **Aresta `Router -> Repository`:** idealizada (ausente); o Router conhece apenas o Service.
- **Persistência:** sistema separado, fora da fronteira da API, marcado como «external».
- **Entidade Task:** única e implícita no Repository (sem separar ORM e Pydantic).
- **Evoluções planejadas:** sinalizadas como «planejado» / não concluídas.
- **Ocultos:** schemas Pydantic, camada `db` (engine/session), router de `health`, detalhes internos.
