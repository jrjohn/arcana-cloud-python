# AGENTS.md — arcana-cloud-python

Instructions for any AI coding agent (Claude Code, Codex, Cursor, Copilot, Gemini…) working
in this repository **or in any product created from it**. `CLAUDE.md`, `GEMINI.md` and
`.github/copilot-instructions.md` all point here; this file is the single source.

> **You MUST NOT report a task as done until `tools/arch-check.sh` exits 0 and the CI unit
> test lane (§5) exits 0.** Breaking the layering costs a red build: the pre-commit hook
> (`tools/githooks/pre-commit`) rejects new flat files and `*Impl` references outside the DI
> container, and Jenkins stage "Architecture Qube" fails the merge below score 90.

## 0. First command in a fresh clone

Run `tools/install-hooks.sh` once. Git does not install hooks on clone; until you run it the
pre-commit check does not exist and only CI catches a flat layout — after the work is
written. `tools/new-app.sh` runs it for you.

## 1. Starting something new

| Situation | Do this | Never do this |
|---|---|---|
| New service product | `tools/new-app.sh <name> <dest-dir>` — copies the whole repo, renames the Jenkins `APP_NAME`/image, Sonar key, CI container/network/kind names, compose/k8s names and database names, resets version and changelog, installs the hook | `flask` from scratch and copy a few packages or files into it |
| New business feature (entity + CRUD API) | `tools/new-feature.sh <Name>` — one vertical slice: model, DAO interface + SQLAlchemy impl, repository interface + impl, service interface + impl, marshmallow schemas, REST blueprint, `.proto` + compiled stubs + gRPC servicer, DI + blueprint + gRPC registration, unit tests for every layer | Put SQL or `db.session` in a controller or service, or a new module next to `app/__init__.py` |

Copying parts instead of `new-app.sh` loses this file, the hook and the CI gate, so nothing
tells the next agent the rules exist. `new-feature.sh` needs `grpcio-tools`
(`pip install -r requirements.txt`; `PYTHON=<venv>/bin/python` picks the interpreter).

## 2. Layers — where a file goes

| Layer | Path | Contains | May depend on |
|---|---|---|---|
| Entry + DI | `app/__init__.py` (`create_app`, blueprint registration), `app/di_container.py`, `wsgi.py`, `app/{controller,service,repository}_server.py` | app factory, `DIContainer` registrations + `get_<x>_service()` getters | everything; the only place that names `*Impl` classes |
| REST boundary | `app/controllers/<x>_controller.py` | Flask blueprints: extract → call a service from a DI getter → dump through a schema | service interfaces (via `app.di_container`), `app/communication/`, schemas, decorators, utils, model enums |
| gRPC boundary | `app/grpc_protos/protos/<x>.proto` → generated `app/grpc_protos/<x>_pb2*.py`; servicers in `app/grpc_protos/servers/` | Controller→Service and Service→Repository gRPC servers, started per `DEPLOYMENT_LAYER` by `grpc_server_runner.py` | service interfaces (via `app.di_container`), models, utils |
| Inter-layer transport | `app/communication/` (Direct/HTTP/gRPC factory), `app/services/{routes,clients,adapters}/`, `app/repositories/{routes,clients}/` | what lets the layered and microservices deployments split controller / service / repository into separate processes | service and repository interfaces |
| Service | interface `app/services/<x>_service.py` (ABC); impl `app/services/impl/<x>_service_impl.py` | business rules and validation, raises `app/utils` exceptions | repository interfaces in `app/repository/`, models, utils |
| Repository | interface `app/repository/<x>_repository.py` (extends `BaseRepository`); impl `app/repository/impl/<x>_repository_impl.py` | domain-level data access, delegates to one DAO | DAO interfaces, models |
| DAO | new features: `app/dao/<x>_dao.py` + `app/dao/impl/<x>_dao_impl.py`. User/OAuthToken: `app/repositories/<x>_repository.py` + `app/repositories/impl/` (historic name; registered as `user_dao` / `oauth_token_dao`) | the only code that uses the SQLAlchemy session | models, utils |
| Model | `app/models/<x>.py` | SQLAlchemy entities and enums | `app.extensions` |
| Schemas (DTOs) | `app/schemas/<x>_schema.py` | marshmallow request/response schemas | nothing in `app/` |
| Cross-cutting | `app/decorators/` (auth, validation), `app/utils/` (exceptions, responses), `app/tasks/` (Celery), `app/Config.py`, `app/Extensions.py` | shared infrastructure | models, utils |

Direction is one way: controller → service → repository → DAO → model. A lower layer never
imports a higher one. `app/dao/user_dao.py` and `app/dao/oauth_token_dao.py` are not used by
anything; the live User DAO is `app/repositories/impl/user_repository_impl.py`. Worked example
of every layer: `auth_controller.py` → `AuthService`/`AuthServiceImpl` →
`UserRepository`/`UserRepositoryImpl` (`app/repository`) → User DAO (`app/repositories`),
wired in `app/di_container.py` `initialize_dependencies`.

## 3. Rules

| # | Rule | Enforced by |
|---|---|---|
| R1 | Every service, repository and DAO is an ABC interface implemented by `XServiceImpl` / `XRepositoryImpl` / `XDaoImpl` in an `impl/` directory beside it, file `<x>_service_impl.py` / `<x>_repository_impl.py` / `<x>_dao_impl.py`, dependencies passed to `__init__`. | arch-qube "Interface/Impl Colocation", "Implementation Naming Convention" |
| R2 | Only `app/di_container.py` names a concrete `*Impl` class. Everyone else calls a `get_<x>_service()` getter and types against the interface. Re-exports in `__init__.py`, the impl files themselves and tests are the only other allowed mentions. | arch-qube "Only DI Container Imports Impl"; pre-commit hook |
| R3 | Controllers and servicers call services only; services call repositories only; only DAOs touch `db.session`. | arch-qube "Backend Layer Chain", "Controller Cannot Use DAO", "Service Cannot Access DB Directly", "Repository Cannot Call Service", "Layer Direction Enforcement" |
| R4 | A route handler only extracts, delegates and dumps: ≤ 20 lines. Raise `app/utils` exceptions in the service and let the global `APIException` handler render them. The legacy User/Auth controllers break this (21 findings in the report); new handlers must not. | arch-qube "No Business Logic in Boundary" |
| R5 | APIs return schema dumps (`app/schemas/`), never a raw entity. | arch-qube "DTO/Entity Separation"; "Controller Uses DTO" is NOT evaluated without AI, so this half is on you |
| R6 | A new `.py` under `app/` goes in a layer directory of §2; no new module at the `app/` root. Module file names are lowercase snake_case (CI runs on case-sensitive Linux). | pre-commit hook; Jenkins stage "Unit Tests" (imports fail) |
| R7 | Every new service, repository, DAO, controller and servicer has a unit test under `tests/unit/test_<layer>/` that runs without MySQL (mocks or in-memory SQLite, as `new-feature.sh` generates). Total coverage stays ≥ 80 %. | Jenkins stage "Unit Tests" (`pytest.ini` `--cov-fail-under=80`); arch-qube "Test Coverage Threshold"; SonarQube quality gate |
| R8 | Never hand-edit `app/grpc_protos/*_pb2*.py`. Edit the `.proto`, regenerate with `python -m grpc_tools.protoc -I app/grpc_protos/protos --python_out=app/grpc_protos --grpc_python_out=app/grpc_protos <file>.proto`, then change the generated `import <x>_pb2` to `from app.grpc_protos import <x>_pb2`. | on you (Sonar excludes `app/grpc_protos/**`) |

## 4. Architecture check (arch-qube)

arch-qube (https://github.com/jrjohn/arcana-arch-qube) is the static architecture gate Jenkins
runs in stage "Architecture Qube": `--framework python --no-ai --ci --threshold 90` over the
whole checkout. Usage guide: https://github.com/jrjohn/arcana-skills/tree/main/arch-qube-skill.
The version is pinned in `tools/arch-qube.version`; the Jenkinsfile and
`tools/arch-check.sh` both read it.

`tools/arch-qube.version` is bumped automatically by Renovate when arch-qube releases; do not edit the version anywhere else.

- Run it: `tools/arch-check.sh` — same image as CI, `ghcr.io/jrjohn/arch-qube:<version>`
  (public, multi-arch) then `arcana.boo/arcana/arch-qube:<version>`, no `:latest` fallback;
  same framework, threshold and exclusions as CI. Exit 0 prints `arch-check: PASS`; exit 2
  means Docker or the image was unavailable — that is NOT a pass.
- Without Docker: `pipx run --spec "git+https://github.com/jrjohn/arcana-arch-qube.git@v$(cat tools/arch-qube.version)" arch-qube scan . --framework python --no-ai --ci --format json,markdown -o arch-qube-reports --threshold 90`
  (or `pip install` the same spec into a venv). Use the tag matching `tools/arch-qube.version`.
- PASS = score ≥ threshold **and** zero violations in every CRITICAL rule — a 99 can still FAIL.
- `--ci` prints nothing on failure. Rerun without `--ci` (or open `arch-qube.md`) to see why.
- Report: `arch-qube-reports/arch-qube.md` and `arch-qube.json`. The score alone is not
  enough: read every FAIL row and the violation list for files you touched. A rule under
  "Not evaluated" (NOT EVALUATED) is not a pass. In the JSON check `files_checked` per
  rule — a rule that checked 0 files said nothing. A project with no recognised layer directories scores 0 on
  "Layer Direction Enforcement".
- False positive: open an issue on https://github.com/jrjohn/arcana-arch-qube/issues with the
  report attached. NEVER lower `--threshold`, add exclusions or move code to dodge a rule.

### What enforces the check locally (there is no CI server)

| Trigger | Mechanism | Blocks when |
|---|---|---|
| Claude Code finishes a turn | `.claude/settings.json` Stop hook → `tools/claude-stop-arch-check.sh` | source under `app/`, `tests/` changed and `tools/arch-check.sh` fails (gives up after 3 blocks, saying the work is NOT done) |
| `git push` | `tools/githooks/pre-push` | pushed commits touch `app/`, `tests/` and the check fails or cannot run |
| `git commit` | `tools/githooks/pre-commit` | fast layering checks (no Docker) |

Claude Code asks once whether to trust this project's settings: answer yes, or the Stop hook never runs.
Git hooks run only after `tools/install-hooks.sh`.

## 5. Before you say "done"

Run these, in this order, and paste the last line of each into your summary:

```bash
tools/arch-check.sh                                                # must print "arch-check: PASS"
docker compose -f docker-compose.test.yml run --rm --build test    # the Jenkins "Unit Tests" lane; must exit 0
```

The second command runs exactly what Jenkins runs:
`pytest tests/unit -q --tb=short --cov=app --cov-report=xml:/app/cov/coverage.xml --no-header`
in `Dockerfile.test` (Python 3.15, Linux). Use Docker for it: a bare `pytest` on macOS fails at
`from app.config import …` because the files are `Config.py` / `Extensions.py` / `Container.py`,
which only `Dockerfile.test` lowercases. Jenkins runs no linter or type checker; the later
stages (layered gRPC compose, kind) need the Jenkins host and are not part of local done.

## 6. Reference

- Optional detail: `arcana-python-developer-skill`
  (https://github.com/jrjohn/arcana-skills/tree/main/arcana-python-developer-skill).
  This file is the source of truth: if the skill and this file disagree, this file wins.
