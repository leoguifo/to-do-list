# Escopo do Projeto — To-Do List API

## Objetivo

Desenvolver um MVP de uma API REST para gerenciamento de tarefas, focada em simplicidade, testabilidade e evolução incremental. A API deve expor operações CRUD completas sobre tarefas, suportar controle de status e persistir dados localmente via SQLite.

---

## Requisitos Funcionais

| ID | Descrição |
|----|-----------|
| RF01 | Criar uma tarefa com título e descrição opcional |
| RF02 | Listar todas as tarefas cadastradas |
| RF03 | Buscar uma tarefa pelo seu identificador único |
| RF04 | Atualizar título e/ou descrição de uma tarefa existente |
| RF05 | Excluir uma tarefa pelo seu identificador único |
| RF06 | Marcar uma tarefa como concluída |
| RF07 | Filtrar tarefas por status (`pending` / `completed`) |

---

## Requisitos Não Funcionais

| ID | Descrição |
|----|-----------|
| RNF01 | A API deve seguir os princípios REST (verbos HTTP, status codes semânticos) |
| RNF02 | Os dados devem ser persistidos em banco SQLite local via SQLAlchemy ORM |
| RNF03 | A aplicação deve expor documentação interativa via Swagger UI (`/docs`) |
| RNF04 | O código deve possuir cobertura de testes automatizados com Pytest |
| RNF05 | A estrutura do projeto deve separar responsabilidades em camadas: router, service e repository |
| RNF06 | Payloads de entrada e saída devem ser validados com Pydantic |
| RNF07 | A aplicação deve ser executável localmente sem dependências externas além do Python |

---

## Fora de Escopo

- Autenticação e autorização (JWT, OAuth2, API keys)
- Multi-tenancy ou isolamento de dados por usuário
- Interface gráfica (frontend web ou mobile)
- Deploy em ambiente de produção (cloud, containers, CI/CD)
- Banco de dados relacional externo (PostgreSQL, MySQL etc.)
- Paginação e ordenação avançada de resultados
- Soft delete ou histórico de alterações
- Notificações ou integrações com serviços externos
