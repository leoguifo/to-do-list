# Identificação de Riscos — To-Do List API

**Data da análise:** 2026-07-16
**Escopo:** MVP de API REST para gerenciamento de tarefas (FastAPI + SQLite)

---

## 1. Lista de Riscos Identificados

---

### Risco 1: Caminho do banco de dados hardcoded

- **Risco:** O `DATABASE_URL` está fixo como `"sqlite:///./app/db/todolist.db"` no código-fonte.
- **Descrição:** O caminho relativo depende do diretório de trabalho no momento da execução. Se a aplicação for iniciada de um diretório diferente da raiz do projeto, o banco de dados será criado em local inesperado ou a conexão falhará silenciosamente criando um novo arquivo vazio.
- **Contexto de ocorrência:** Ao executar testes, scripts ou a aplicação a partir de um diretório diferente da raiz do projeto; ao introduzir containerização ou CI/CD futuramente (itens atualmente fora de escopo, mas com probabilidade de adoção).

---

### Risco 2: Ausência de ferramenta de migração de schema (ex.: Alembic)

- **Risco:** O schema do banco é criado via `Base.metadata.create_all()`, sem controle de versão de migrações.
- **Descrição:** Qualquer alteração no modelo ORM (ex.: novo campo em `Task`) exigirá intervenção manual no banco existente, pois o `create_all` não modifica tabelas já existentes. Isso pode causar inconsistências entre o modelo em código e o schema real do banco em ambientes que já possuem dados.
- **Contexto de ocorrência:** Quando os requisitos evoluírem e for necessário adicionar atributos à entidade `Task` (ex.: prioridade, prazo, categoria) — situação explicitamente antecipada pelo escopo como possível.

---

### Risco 3: Campo `status` persistido como String sem restrição no banco

- **Risco:** O campo `status` é declarado como `String(20)` no modelo ORM, sem constraint de `CHECK` ou tipo `Enum` no nível do banco.
- **Descrição:** A validação dos valores (`"pending"` / `"completed"`) ocorre apenas na camada Pydantic. Operações diretas no banco (scripts, ferramentas de BI, migrações manuais) podem inserir valores inválidos que passarão despercebidos até serem retornados pela API.
- **Contexto de ocorrência:** Manipulação direta do arquivo `.db` por membros da equipe distribuída durante depuração ou populações manuais de dados; ao executar scripts de seed ou fixtures de teste que não passem pelo schema Pydantic.

---

### Risco 4: Ausência de paginação expõe risco de degradação de desempenho

- **Risco:** O endpoint de listagem (`GET /tasks`) retorna todas as tarefas sem limite.
- **Descrição:** O método `repository.list()` executa `SELECT * FROM tasks` sem `LIMIT`. Com o crescimento do volume de dados, a resposta pode aumentar indefinidamente, impactando performance e consumo de memória. Paginação está explicitamente fora do escopo atual, mas o crescimento de dados não foi limitado por nenhum mecanismo técnico.
- **Contexto de ocorrência:** Se o projeto evoluir para uso com volume maior de tarefas antes que a paginação seja incorporada ao escopo; em testes de carga ou demonstrações com datasets representativos.

---

### Risco 5: Ausência de arquivo de lock de dependências

- **Risco:** O projeto utiliza `requirements.txt` com versões fixas, mas sem arquivo de lock (ex.: `poetry.lock`, `pip-compile`).
- **Descrição:** Embora as versões diretas estejam pinadas, as dependências transitivas (sub-dependências do FastAPI, SQLAlchemy, etc.) não estão bloqueadas. Em ambientes diferentes de membros da equipe distribuída, a instalação via `pip install -r requirements.txt` pode resolver versões transitivas distintas, gerando comportamento inconsistente.
- **Contexto de ocorrência:** Ao configurar o ambiente de desenvolvimento em máquinas diferentes de membros da equipe; ao executar pipelines de CI/CD futuros.

---

### Risco 6: Evolução de requisitos pode exigir refatoração estrutural significativa

- **Risco:** A arquitetura atual é projetada para MVP sem autenticação, sem multi-tenancy e sem deploy em produção — todos itens explicitamente fora de escopo.
- **Descrição:** Caso os requisitos evoluam para incluir qualquer um desses itens (especialmente autenticação ou banco de dados externo), a base de código atual não possui os pontos de extensão necessários (ex.: middleware de auth, abstração de banco independente de SQLite). A refatoração retroativa em contexto de equipe distribuída aumenta o risco de regressões.
- **Contexto de ocorrência:** Em decisões de negócio que ampliem o escopo além do MVP atual; ao incorporar novos membros à equipe que não conhecem as restrições originais do escopo.

---

### Risco 7: Coordenação de padrões de código em equipe distribuída sem configuração de linting/formatação

- **Risco:** Não foram identificados arquivos de configuração de linting (ex.: `ruff`, `flake8`, `pylint`) ou formatação (ex.: `black`, `isort`) no projeto.
- **Descrição:** Em equipes distribuídas, a ausência de ferramentas automatizadas de estilo e qualidade aumenta o risco de divergência de padrões entre contribuições, gerando overhead em revisões de código e potencial introdução de bugs silenciosos. *Necessita validação — pode existir configuração em arquivos não examinados como `pyproject.toml` ou `.pre-commit-config.yaml`.*
- **Contexto de ocorrência:** Ao receber contribuições de pull requests de membros remotos da equipe; ao incorporar novos desenvolvedores sem onboarding estruturado.

---

### Risco 8: Requisição `PATCH` sem campos preenchidos é aceita silenciosamente

- **Risco:** O schema `TaskUpdate` tem todos os campos opcionais (`title`, `description`, `status` todos com `default=None`). Um `PATCH` com body `{}` é válido e não retorna erro.
- **Descrição:** Uma requisição de atualização vazia resulta em uma operação de banco sem efeito, mas retorna `200 OK` com os dados inalterados. Isso pode mascarar erros de integração em clientes que enviem payloads malformados, dificultando a depuração.
- **Contexto de ocorrência:** Durante integração de clientes da API por membros da equipe distribuída que estejam desenvolvendo frontends ou scripts de consumo.
