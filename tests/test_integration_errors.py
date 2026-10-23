"""Integration tests for error handling and edge cases of the To-Do List API.

Focus (complementing ``test_integration_crud.py``): negative and boundary
scenarios across the full stack (Routes -> Service -> Repository -> ORM), with
an explicit separation between *validation failures* and *internal server
errors*:

* Validation failures are produced before the business/persistence layers by
  FastAPI/Pydantic (body) and FastAPI query/path coercion. They return
  HTTP 422 and must never persist anything.
* "Not found" is a business outcome: the service raises ``TaskNotFoundError``
  and the route maps it to HTTP 404.
* Internal errors are unexpected failures in the layers below the route (e.g.
  a persistence/commit failure in the repository). The routes only catch
  ``TaskNotFoundError``; anything else propagates as HTTP 500. These are
  simulated with mocks so the repository raises as a real backend would.

Each test documents: the data used, the execution steps, the expected HTTP
status code, and the expected application behavior.

Test IDs: CT-E01..CT-E26.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api.task_routes import get_task_service
from app.db.database import Base
from app.main import app
from app.models.task_model import Task
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService


@pytest.fixture
def session() -> Iterator[Session]:
    """Provide a fresh in-memory SQLite session with the real schema."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    db: Session = session_local()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    """TestClient wired to the real service stack over the test session.

    ``raise_server_exceptions=False`` lets us observe real HTTP 500 responses
    (instead of re-raising) when a lower layer fails unexpectedly.
    """

    def _override_task_service() -> TaskService:
        return TaskService(TaskRepository(session))

    app.dependency_overrides[get_task_service] = _override_task_service
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _count(session: Session) -> int:
    """Number of persisted task rows, read straight from the DB."""
    session.expire_all()
    return session.query(Task).count()


# =========================================================================== #
# Grupo 1 - Campos obrigatorios ausentes (validacao -> 422)
# =========================================================================== #
def test_cte01_create_without_body_returns_422(
    client: TestClient, session: Session
) -> None:
    """CT-E01: POST /tasks sem corpo.

    Dados: nenhum corpo enviado.
    Passos: POST /tasks sem JSON.
    HTTP esperado: 422.
    Comportamento: falha de validacao (title obrigatorio); nada persiste.
    """
    response = client.post("/tasks")

    assert response.status_code == 422
    assert _count(session) == 0


def test_cte02_create_missing_title_reports_field_and_type(
    client: TestClient, session: Session
) -> None:
    """CT-E02: POST /tasks sem o campo obrigatorio ``title``.

    Dados: {"description": "sem titulo"}.
    Passos: POST /tasks com corpo sem title.
    HTTP esperado: 422.
    Comportamento: erro aponta o campo ``title`` como ``missing``; nada persiste.
    """
    response = client.post("/tasks", json={"description": "sem titulo"})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(
        err["type"] == "missing" and err["loc"][-1] == "title" for err in detail
    )
    assert _count(session) == 0


def test_cte03_create_null_title_returns_422(
    client: TestClient, session: Session
) -> None:
    """CT-E03: POST /tasks com ``title`` nulo.

    Dados: {"title": null}.
    Passos: POST /tasks com title=None.
    HTTP esperado: 422.
    Comportamento: title nao aceita None; nada persiste.
    """
    response = client.post("/tasks", json={"title": None})

    assert response.status_code == 422
    assert _count(session) == 0


# =========================================================================== #
# Grupo 2 - Tipos de dados invalidos (validacao -> 422)
# =========================================================================== #
def test_cte04_create_title_as_list_returns_422(
    client: TestClient, session: Session
) -> None:
    """CT-E04: tipo invalido para ``title`` (lista em vez de string).

    Dados: {"title": ["a", "b"]}.
    Passos: POST /tasks.
    HTTP esperado: 422.
    Comportamento: falha de validacao de tipo; nada persiste.
    """
    response = client.post("/tasks", json={"title": ["a", "b"]})

    assert response.status_code == 422
    assert _count(session) == 0


def test_cte05_create_description_as_number_returns_422(
    client: TestClient, session: Session
) -> None:
    """CT-E05: tipo invalido para ``description`` (objeto em vez de string).

    Dados: {"title": "ok", "description": {"x": 1}}.
    Passos: POST /tasks.
    HTTP esperado: 422.
    Comportamento: description so aceita string ou null; nada persiste.
    """
    response = client.post(
        "/tasks", json={"title": "ok", "description": {"x": 1}}
    )

    assert response.status_code == 422
    assert _count(session) == 0


def test_cte06_create_status_as_bool_returns_422(
    client: TestClient, session: Session
) -> None:
    """CT-E06: tipo invalido para ``status`` (boolean em vez de enum).

    Dados: {"title": "ok", "status": true}.
    Passos: POST /tasks.
    HTTP esperado: 422.
    Comportamento: status nao e um valor de TaskStatus; nada persiste.
    """
    response = client.post("/tasks", json={"title": "ok", "status": True})

    assert response.status_code == 422
    assert _count(session) == 0


def test_cte07_create_with_malformed_json_returns_422(client: TestClient) -> None:
    """CT-E07: corpo nao e JSON valido.

    Dados: corpo textual malformado ``{"title":``.
    Passos: POST /tasks com content-type JSON e corpo quebrado.
    HTTP esperado: 422.
    Comportamento: falha ao desserializar o corpo antes de qualquer regra.
    """
    response = client.post(
        "/tasks",
        content='{"title":',
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422


def test_cte08_path_id_non_numeric_returns_422(client: TestClient) -> None:
    """CT-E08: identificador de rota com tipo invalido (nao inteiro).

    Dados: GET /tasks/abc.
    Passos: GET com path param nao numerico.
    HTTP esperado: 422.
    Comportamento: coercao de path int falha antes da camada de negocio.
    """
    response = client.get("/tasks/abc")

    assert response.status_code == 422


# =========================================================================== #
# Grupo 3 - Identificadores inexistentes / tarefa nao encontrada (negocio -> 404)
# =========================================================================== #
def test_cte09_get_unknown_id_returns_404(client: TestClient) -> None:
    """CT-E09: GET de id inexistente.

    Dados: id 999 (DB vazia).
    Passos: GET /tasks/999.
    HTTP esperado: 404.
    Comportamento: service lanca TaskNotFoundError, rota mapeia para 404.
    """
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id=999 not found"


def test_cte10_update_unknown_id_returns_404(
    client: TestClient, session: Session
) -> None:
    """CT-E10: PUT de id inexistente.

    Dados: id 999, body {"title": "x"}.
    Passos: PUT /tasks/999.
    HTTP esperado: 404.
    Comportamento: nada e atualizado/criado; mensagem de nao encontrado.
    """
    response = client.put("/tasks/999", json={"title": "x"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id=999 not found"
    assert _count(session) == 0


def test_cte11_delete_unknown_id_returns_404(client: TestClient) -> None:
    """CT-E11: DELETE de id inexistente.

    Dados: id 999.
    Passos: DELETE /tasks/999.
    HTTP esperado: 404.
    Comportamento: service lanca TaskNotFoundError, rota mapeia para 404.
    """
    response = client.delete("/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id=999 not found"


def test_cte12_operations_on_deleted_task_return_404(client: TestClient) -> None:
    """CT-E12: tarefa existente e removida; operacoes seguintes -> 404.

    Dados: cria uma tarefa, deleta, depois tenta GET/PUT/DELETE no mesmo id.
    Passos: POST -> DELETE -> GET/PUT/DELETE.
    HTTP esperado: 204 no delete; 404 nas operacoes posteriores.
    Comportamento: estado consistente apos remocao.
    """
    task_id = client.post("/tasks", json={"title": "Temporaria"}).json()["id"]
    assert client.delete(f"/tasks/{task_id}").status_code == 204

    assert client.get(f"/tasks/{task_id}").status_code == 404
    assert client.put(f"/tasks/{task_id}", json={"title": "x"}).status_code == 404
    assert client.delete(f"/tasks/{task_id}").status_code == 404


def test_cte13_large_id_returns_404_not_crash(client: TestClient) -> None:
    """CT-E13: id numerico muito grande em DB vazia.

    Dados: id 9_999_999_999.
    Passos: GET /tasks/9999999999.
    HTTP esperado: 404.
    Comportamento: tratado como ausente, sem erro interno.
    """
    response = client.get("/tasks/9999999999")

    assert response.status_code == 404


# =========================================================================== #
# Grupo 4 - Limites de validacao (boundary -> 422 / 201)
# =========================================================================== #
def test_cte14_description_at_max_length_is_accepted(client: TestClient) -> None:
    """CT-E14: description com exatamente 500 caracteres (limite superior).

    Dados: title valido + description de 500 chars.
    Passos: POST /tasks.
    HTTP esperado: 201.
    Comportamento: valor no limite e aceito e persistido.
    """
    response = client.post(
        "/tasks", json={"title": "ok", "description": "d" * 500}
    )

    assert response.status_code == 201
    assert len(response.json()["description"]) == 500


def test_cte15_description_over_max_length_returns_422(
    client: TestClient, session: Session
) -> None:
    """CT-E15: description com 501 caracteres (acima do limite).

    Dados: title valido + description de 501 chars.
    Passos: POST /tasks.
    HTTP esperado: 422.
    Comportamento: falha de validacao de tamanho; nada persiste.
    """
    response = client.post(
        "/tasks", json={"title": "ok", "description": "d" * 501}
    )

    assert response.status_code == 422
    assert _count(session) == 0


def test_cte16_update_title_whitespace_only_returns_422(
    client: TestClient, session: Session
) -> None:
    """CT-E16: PUT com title so de espacos (min_length apos strip).

    Dados: cria tarefa; PUT {"title": "   "}.
    Passos: POST -> PUT.
    HTTP esperado: 422.
    Comportamento: apos strip, title fica vazio e viola min_length=1; a linha
    permanece inalterada.
    """
    created = client.post("/tasks", json={"title": "Original"}).json()

    response = client.put(f"/tasks/{created['id']}", json={"title": "   "})

    assert response.status_code == 422
    row = session.get(Task, created["id"])
    assert row is not None
    assert row.title == "Original"


def test_cte17_filter_id_zero_returns_422(client: TestClient) -> None:
    """CT-E17: /tasks/filter com id=0 (abaixo do minimo ge=1).

    Dados: query id=0.
    Passos: GET /tasks/filter?id=0.
    HTTP esperado: 422.
    Comportamento: restricao ge=1 rejeita o valor.
    """
    response = client.get("/tasks/filter?id=0")

    assert response.status_code == 422


def test_cte18_filter_id_negative_returns_422(client: TestClient) -> None:
    """CT-E18: /tasks/filter com id negativo.

    Dados: query id=-5.
    Passos: GET /tasks/filter?id=-5.
    HTTP esperado: 422.
    Comportamento: restricao ge=1 rejeita o valor.
    """
    response = client.get("/tasks/filter?id=-5")

    assert response.status_code == 422


def test_cte19_filter_invalid_status_returns_422(client: TestClient) -> None:
    """CT-E19: /tasks/filter com status fora do enum.

    Dados: query status=archived.
    Passos: GET /tasks/filter?status=archived.
    HTTP esperado: 422.
    Comportamento: valor de status invalido e rejeitado na validacao da query.
    """
    response = client.get("/tasks/filter?status=archived")

    assert response.status_code == 422


def test_cte20_list_invalid_status_filter_returns_422(client: TestClient) -> None:
    """CT-E20: GET /tasks?status=invalid.

    Dados: query status=invalid.
    Passos: GET /tasks?status=invalid.
    HTTP esperado: 422.
    Comportamento: filtro de status invalido e barrado antes do negocio.
    """
    response = client.get("/tasks?status=invalid")

    assert response.status_code == 422


# =========================================================================== #
# Grupo 5 - Dados inconsistentes (persistencia divergente do contrato -> 500)
# =========================================================================== #
def test_cte21_response_fails_when_persisted_status_is_inconsistent(
    client: TestClient, session: Session
) -> None:
    """CT-E21: linha com status fora do enum (dado inconsistente no banco).

    Dados: insere diretamente no banco uma tarefa com status 'archived', que
    nao pertence a TaskStatus (simula dado legado/corrompido).
    Passos: INSERT direto no banco -> GET /tasks/{id}.
    HTTP esperado: 500.
    Comportamento: a serializacao de resposta (response_model=TaskOut) falha ao
    validar o enum; o erro NAO e de validacao de entrada (422), e sim um erro
    interno de contrato entre a persistencia e a camada de apresentacao.
    """
    entity = Task(title="Legada", description=None, status="archived")
    session.add(entity)
    session.commit()
    session.refresh(entity)

    response = client.get(f"/tasks/{entity.id}")

    assert response.status_code == 500


def test_cte22_null_title_is_blocked_by_db_constraint(
    session: Session,
) -> None:
    """CT-E22: a propria persistencia impede dado inconsistente (title nulo).

    Dados: tentativa de INSERT direto com title=None.
    Passos: adiciona uma linha com title=None e tenta commit.
    HTTP esperado: nao se aplica (erro ocorre antes de qualquer resposta HTTP).
    Comportamento: a coluna ``tasks.title`` e NOT NULL, entao o banco rejeita a
    gravacao com IntegrityError. Este e um guard de consistencia na camada de
    persistencia, distinto da validacao de entrada (422) e do enum invalido do
    CT-E21 (que o banco aceita, mas a resposta recusa).
    """
    session.add(Task(title=None, description=None, status="pending"))

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


# =========================================================================== #
# Grupo 6 - Falhas de persistencia / erro interno (infra -> 500)
# =========================================================================== #
def test_cte23_create_persistence_failure_returns_500(
    client: TestClient, session: Session
) -> None:
    """CT-E23: falha de persistencia no POST.

    Dados: payload valido {"title": "Vai falhar"}.
    Passos: mocka TaskRepository.create para lancar OperationalError (ex.: banco
    indisponivel) -> POST /tasks.
    HTTP esperado: 500.
    Comportamento: a rota so trata TaskNotFoundError; qualquer outra excecao
    propaga como erro interno. Entrada valida nao vira 422.
    """
    with patch.object(
        TaskRepository,
        "create",
        side_effect=OperationalError("INSERT", {}, Exception("db down")),
    ):
        response = client.post("/tasks", json={"title": "Vai falhar"})

    assert response.status_code == 500


def test_cte24_list_persistence_failure_returns_500(client: TestClient) -> None:
    """CT-E24: falha de persistencia no GET /tasks.

    Dados: nenhum (listagem).
    Passos: mocka TaskRepository.list para lancar SQLAlchemyError -> GET /tasks.
    HTTP esperado: 500.
    Comportamento: erro de leitura propaga como erro interno, nao como 422/404.
    """
    with patch.object(
        TaskRepository, "list", side_effect=SQLAlchemyError("connection lost")
    ):
        response = client.get("/tasks")

    assert response.status_code == 500


def test_cte25_update_commit_failure_returns_500(
    client: TestClient, session: Session
) -> None:
    """CT-E25: falha ao confirmar (commit) um UPDATE valido de tarefa existente.

    Dados: cria tarefa; PUT {"status": "completed"} valido.
    Passos: cria -> mocka TaskRepository.update para lancar OperationalError ->
    PUT /tasks/{id}.
    HTTP esperado: 500.
    Comportamento: a tarefa existe (nao e 404) e a entrada e valida (nao e 422);
    a falha e estritamente de persistencia -> erro interno.
    """
    created = client.post("/tasks", json={"title": "Original"}).json()

    with patch.object(
        TaskRepository,
        "update",
        side_effect=OperationalError("UPDATE", {}, Exception("disk full")),
    ):
        response = client.put(
            f"/tasks/{created['id']}", json={"status": "completed"}
        )

    assert response.status_code == 500


def test_cte26_delete_persistence_failure_returns_500(client: TestClient) -> None:
    """CT-E26: falha de persistencia no DELETE de tarefa existente.

    Dados: cria tarefa; DELETE no id existente.
    Passos: cria -> mocka TaskRepository.delete para lancar SQLAlchemyError ->
    DELETE /tasks/{id}.
    HTTP esperado: 500.
    Comportamento: id existe (nao e 404); a falha de remocao e erro interno,
    diferenciada de uma tarefa inexistente.
    """
    created = client.post("/tasks", json={"title": "Remover"}).json()

    with patch.object(
        TaskRepository, "delete", side_effect=SQLAlchemyError("io error")
    ):
        response = client.delete(f"/tasks/{created['id']}")

    assert response.status_code == 500
