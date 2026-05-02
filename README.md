# To-Do List API

API REST para gerenciamento de tarefas, desenvolvida como MVP com FastAPI e persistência em SQLite.

## Objetivo

Fornecer um CRUD completo de tarefas com suporte a marcação de conclusão e filtragem por status, servindo como base para aplicações de produtividade ou estudo de APIs REST com Python.

## Stack

- **Python 3.11+**
- **FastAPI** — framework web assíncrono
- **SQLite** — banco de dados embutido
- **SQLAlchemy** — ORM para acesso ao banco
- **Pydantic** — validação de dados
- **Pytest** — testes automatizados
- **Uvicorn** — servidor ASGI

## Funcionalidades

- Criar, listar, atualizar e excluir tarefas
- Marcar tarefas como concluídas
- Filtrar tarefas por status (`pending` / `completed`)

## Como rodar localmente

### Pré-requisitos

- Python 3.11 ou superior
- `pip`

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/to-do-list.git
cd to-do-list

# Crie e ative o ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/macOS

# Instale as dependências
pip install -r requirements.txt
```

### Executando a API

```bash
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000`.  
Documentação interativa: `http://localhost:8000/docs`.

### Executando os testes

```bash
pytest
```
