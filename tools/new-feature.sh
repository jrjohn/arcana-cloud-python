#!/usr/bin/env bash
# Generate ONE vertical feature slice the way the template's layers are built (AGENTS.md §2):
#
#   model (app/models) → DAO interface + SQLAlchemy impl (app/dao, app/dao/impl)
#   → repository interface + impl (app/repository, app/repository/impl)
#   → service interface + impl (app/services, app/services/impl)
#   → schemas/DTOs (app/schemas) → REST controller (app/controllers) + gRPC servicer
#   (app/grpc_protos/protos + servers) → DI registration (app/di_container.py)
#   → blueprint + gRPC registration → unit tests for every layer (tests/unit/…).
#
#   tools/new-feature.sh Invoice            # PascalCase, singular
#   tools/new-feature.sh PurchaseOrder
#
# Fields: the slice starts with `name` + `description`. Add fields afterwards in the order
# model → schemas → proto (re-run grpc_tools.protoc, see the generated servicer) → tests.
# Needs grpcio-tools (in requirements.txt) for the proto compile; set PYTHON=… to pick the
# interpreter (default: python3). Fails loudly if an anchor it edits has moved.
set -euo pipefail

[ $# -eq 1 ] || { echo "usage: $0 <FeatureName>   (PascalCase, singular, e.g. Invoice)" >&2; exit 1; }
P="$1"
[[ "$P" =~ ^[A-Z][a-zA-Z0-9]*$ ]] || { echo "FeatureName must be PascalCase (e.g. Invoice, PurchaseOrder)" >&2; exit 1; }
s="$(printf '%s' "$P" | perl -pe 's/(?<=[a-z0-9])([A-Z])/_$1/g; $_=lc')"   # PurchaseOrder → purchase_order
TABLE="${s}s"
URL="$(printf '%s' "$TABLE" | tr '_' '-')"
case "$s" in user|auth|oauth_token|health|repository|common) echo "'$P' collides with a template feature" >&2; exit 1 ;; esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
"$PY" -c 'import grpc_tools.protoc' 2>/dev/null \
    || { echo "new-feature: $PY cannot import grpc_tools — pip install -r requirements.txt (or set PYTHON=<venv>/bin/python)" >&2; exit 1; }

for f in app/di_container.py app/__init__.py app/controllers/__init__.py \
         app/grpc_protos/servers/user_service_server.py app/grpc_protos/protos/user_service.proto; do
    [ -f "$f" ] || { echo "new-feature: anchor file $f missing — template layout changed, nothing generated" >&2; exit 1; }
done
[ ! -e "app/services/${s}_service.py" ] || { echo "feature '$P' already exists (app/services/${s}_service.py)" >&2; exit 1; }
# The proto package is the template's wire identity; reuse whatever user_service.proto declares.
PKG="$(sed -n 's/^package \([A-Za-z0-9_.]*\);.*/\1/p' app/grpc_protos/protos/user_service.proto | head -1)"
[ -n "$PKG" ] || { echo "new-feature: no 'package x;' in app/grpc_protos/protos/user_service.proto" >&2; exit 1; }

render() {
    mkdir -p "$(dirname "$1")"
    sed -e "s/__P__/$P/g" -e "s/__s__/$s/g" -e "s/__TABLE__/$TABLE/g" -e "s/__URL__/$URL/g" \
        -e "s/__PKG__/$PKG/g" > "$1"
    echo "  + $1"
}
# insert_after <file> <perl-regex anchor> <text>: exits non-zero when the anchor is missing,
# so a template change breaks this script instead of silently skipping a registration.
insert_after() {
    local f="$1" anchor="$2" text="$3"
    ANCHOR="$anchor" TEXT="$text" perl -0777 -i -pe '
        BEGIN { $n = 0 }
        $n += s/($ENV{ANCHOR})/$1$ENV{TEXT}/s;
        END { exit($n ? 0 : 3) }' "$f" \
        || { echo "new-feature: anchor not found in $f: $anchor — registration NOT done" >&2; exit 1; }
    echo "  ~ $f"
}
insert_before() {
    local f="$1" anchor="$2" text="$3"
    ANCHOR="$anchor" TEXT="$text" perl -0777 -i -pe '
        BEGIN { $n = 0 }
        $n += s/($ENV{ANCHOR})/$ENV{TEXT}$1/s;
        END { exit($n ? 0 : 3) }' "$f" \
        || { echo "new-feature: anchor not found in $f: $anchor — registration NOT done" >&2; exit 1; }
    echo "  ~ $f"
}

echo "new-feature: $P (module ${s}, table ${TABLE}, REST /api/v1/${URL}, gRPC ${PKG}.${P}Service)"

# ------------------------------------------------------------------ model (entity)
render "app/models/${s}.py" <<'EOF'
"""
__P__ Model
SQLAlchemy entity for the __TABLE__ table.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class __P__(db.Model):
    """__P__ entity"""
    __tablename__ = '__TABLE__'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    def __init__(self, name: str, description: Optional[str] = None):
        self.name = name
        self.description = description

    def __repr__(self) -> str:
        return f'<__P__ {self.id} {self.name}>'
EOF

# ------------------------------------------------------------------ schemas (DTOs)
render "app/schemas/${s}_schema.py" <<'EOF'
"""
__P__ Schemas
Request/response DTOs for the __P__ API. Controllers and gRPC servicers never expose the
SQLAlchemy entity directly; they dump it through __P__Schema.
"""
from marshmallow import Schema, fields, validate


class __P__Schema(Schema):
    """__P__ output schema"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class __P__CreateSchema(Schema):
    """__P__ create schema"""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    description = fields.Str(allow_none=True, load_default=None)


class __P__UpdateSchema(Schema):
    """__P__ update schema (partial)"""
    name = fields.Str(validate=validate.Length(min=1, max=120))
    description = fields.Str(allow_none=True)
EOF

# ------------------------------------------------------------------ DAO
render "app/dao/${s}_dao.py" <<'EOF'
"""
__P__ DAO Interface
Data-access contract for __P__; the only layer that talks to the database.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from app.models.__s__ import __P__


class __P__Dao(ABC):
    """__P__ DAO interface"""

    @abstractmethod
    def find_by_id(self, entity_id: int) -> Optional[__P__]:
        """Return the row with this id, or None."""

    @abstractmethod
    def find_page(self, page: int, per_page: int) -> Tuple[List[__P__], int]:
        """Return (rows of one page, total row count)."""

    @abstractmethod
    def insert(self, entity: __P__) -> __P__:
        """Insert and return the entity with its id."""

    @abstractmethod
    def update(self, entity: __P__) -> __P__:
        """Persist changes to an existing entity."""

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Delete by id; False when no row matched."""
EOF
[ -f app/dao/impl/__init__.py ] || render app/dao/impl/__init__.py <<'EOF'
"""DAO implementations (SQLAlchemy)."""
EOF
render "app/dao/impl/${s}_dao_impl.py" <<'EOF'
"""
__P__ DAO Implementation (SQLAlchemy)
"""
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.dao.__s___dao import __P__Dao
from app.models.__s__ import __P__
from app.utils.exceptions import DatabaseError


class __P__DaoImpl(__P__Dao):
    """SQLAlchemy-backed __P__ DAO"""

    def __init__(self, session: Session):
        self.session = session

    def find_by_id(self, entity_id: int) -> Optional[__P__]:
        return self.session.get(__P__, entity_id)

    def find_page(self, page: int, per_page: int) -> Tuple[List[__P__], int]:
        query = self.session.query(__P__)
        total = query.count()
        items = query.order_by(__P__.id).offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    def insert(self, entity: __P__) -> __P__:
        return self._commit(entity, 'create')

    def update(self, entity: __P__) -> __P__:
        return self._commit(entity, 'update')

    def delete(self, entity_id: int) -> bool:
        entity = self.find_by_id(entity_id)
        if entity is None:
            return False
        try:
            self.session.delete(entity)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to delete __s__: {e}")

    def _commit(self, entity: __P__, action: str) -> __P__:
        try:
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return entity
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to {action} __s__: {e}")
EOF

# ------------------------------------------------------------------ repository
render "app/repository/${s}_repository.py" <<'EOF'
"""
__P__ Repository Interface
Domain-level access to __P__; implementations delegate to __P__Dao.
"""
from abc import abstractmethod
from typing import List, Tuple

from app.repository.base_repository import BaseRepository
from app.models.__s__ import __P__


class __P__Repository(BaseRepository[__P__, int]):
    """__P__ Repository interface"""

    @abstractmethod
    def find_all_paginated(self, page: int = 1, per_page: int = 20) -> Tuple[List[__P__], int]:
        """Return (one page of entities, total count)."""
EOF
render "app/repository/impl/${s}_repository_impl.py" <<'EOF'
"""
__P__ Repository Implementation
Delegates persistence to the injected __P__Dao.
"""
from typing import List, Optional, Tuple

from app.dao.__s___dao import __P__Dao
from app.models.__s__ import __P__
from app.repository.__s___repository import __P__Repository


class __P__RepositoryImpl(__P__Repository):
    """Concrete __P__ Repository"""

    def __init__(self, dao: __P__Dao):
        self._dao = dao

    def save(self, entity: __P__) -> __P__:
        if entity.id is None:
            return self._dao.insert(entity)
        return self._dao.update(entity)

    def find_by_id(self, id: int) -> Optional[__P__]:  # NOSONAR python:S6796
        return self._dao.find_by_id(id)

    def find_all(self) -> List[__P__]:
        items, _ = self._dao.find_page(page=1, per_page=100_000)
        return items

    def count(self) -> int:
        _, total = self._dao.find_page(page=1, per_page=1)
        return total

    def delete_by_id(self, id: int) -> bool:  # NOSONAR python:S6796
        return self._dao.delete(id)

    def exists_by_id(self, id: int) -> bool:  # NOSONAR python:S6796
        return self._dao.find_by_id(id) is not None

    def find_all_paginated(self, page: int = 1, per_page: int = 20) -> Tuple[List[__P__], int]:
        return self._dao.find_page(page=page, per_page=per_page)
EOF

# ------------------------------------------------------------------ service
render "app/services/${s}_service.py" <<'EOF'
"""
__P__ Service Interface
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from app.models.__s__ import __P__


class __P__Service(ABC):
    """__P__ Service interface"""

    @abstractmethod
    def create__P__(self, name: str, description: Optional[str] = None) -> __P__:
        """Create; raises ValidationError on bad input."""

    @abstractmethod
    def get__P__ById(self, entity_id: int) -> __P__:
        """Return the entity; raises NotFoundError."""

    @abstractmethod
    def list__P__s(self, page: int = 1, per_page: int = 20) -> Tuple[List[__P__], int]:
        """Return (one page, total count)."""

    @abstractmethod
    def update__P__(self, entity_id: int, changes: Dict[str, Any]) -> __P__:
        """Apply name/description changes; raises NotFoundError / ValidationError."""

    @abstractmethod
    def delete__P__(self, entity_id: int) -> None:
        """Delete; raises NotFoundError."""
EOF
render "app/services/impl/${s}_service_impl.py" <<'EOF'
"""
__P__ Service Implementation
Business rules for __P__; persistence goes through __P__Repository only.
"""
from typing import Any, Dict, List, Optional, Tuple

from app.models.__s__ import __P__
from app.repository.__s___repository import __P__Repository
from app.services.__s___service import __P__Service
from app.utils.exceptions import NotFoundError, ValidationError

_UPDATABLE = ('name', 'description')


class __P__ServiceImpl(__P__Service):
    """__P__ Service implementation"""

    def __init__(self, repository: __P__Repository):
        self._repository = repository

    @staticmethod
    def _validate_name(name: Optional[str]) -> str:
        cleaned = (name or '').strip()
        if not cleaned:
            raise ValidationError("name must not be empty")
        if len(cleaned) > 120:
            raise ValidationError("name must be at most 120 characters")
        return cleaned

    def create__P__(self, name: str, description: Optional[str] = None) -> __P__:
        entity = __P__(name=self._validate_name(name), description=description)
        return self._repository.save(entity)

    def get__P__ById(self, entity_id: int) -> __P__:
        entity = self._repository.find_by_id(entity_id)
        if entity is None:
            raise NotFoundError(f"__P__ {entity_id} not found")
        return entity

    def list__P__s(self, page: int = 1, per_page: int = 20) -> Tuple[List[__P__], int]:
        if page < 1 or per_page < 1:
            raise ValidationError("page and per_page must be positive")
        return self._repository.find_all_paginated(page=page, per_page=per_page)

    def update__P__(self, entity_id: int, changes: Dict[str, Any]) -> __P__:
        entity = self.get__P__ById(entity_id)
        if 'name' in changes:
            changes = {**changes, 'name': self._validate_name(changes['name'])}
        for key in _UPDATABLE:
            if key in changes:
                setattr(entity, key, changes[key])
        return self._repository.save(entity)

    def delete__P__(self, entity_id: int) -> None:
        if not self._repository.delete_by_id(entity_id):
            raise NotFoundError(f"__P__ {entity_id} not found")
EOF

# ------------------------------------------------------------------ REST controller
render "app/controllers/${s}_controller.py" <<'EOF'
"""
__P__ Controller
REST boundary: extract → call __P__Service (from the DI container) → dump through the schema.
APIException subclasses raised by the service are rendered by the global error handler.
"""
from flask import Blueprint, request

from app.decorators.auth_decorators import token_required
from app.decorators.validation_decorators import validate_schema, validate_pagination
from app.di_container import get___s___service
from app.schemas.__s___schema import __P__Schema, __P__CreateSchema, __P__UpdateSchema
from app.utils.response import success_response, paginated_response

__s___bp = Blueprint('__s__', __name__)
_one = __P__Schema()
_many = __P__Schema(many=True)


@__s___bp.route('', methods=['GET'])
@token_required
@validate_pagination()
def list___s__s():
    """GET /api/v1/__URL__?page=1&per_page=20"""
    page, per_page = request.pagination['page'], request.pagination['per_page']
    items, total = get___s___service().list__P__s(page=page, per_page=per_page)
    return paginated_response(items=_many.dump(items), page=page, per_page=per_page, total=total)


@__s___bp.route('/<int:entity_id>', methods=['GET'])
@token_required
def get___s__(entity_id: int):
    """GET /api/v1/__URL__/<id>"""
    return success_response(data=_one.dump(get___s___service().get__P__ById(entity_id)))


@__s___bp.route('', methods=['POST'])
@token_required
@validate_schema(__P__CreateSchema)
def create___s__():
    """POST /api/v1/__URL__"""
    data = request.validated_data
    entity = get___s___service().create__P__(data['name'], data.get('description'))
    return success_response(data=_one.dump(entity), message='Created', status_code=201)


@__s___bp.route('/<int:entity_id>', methods=['PUT'])
@token_required
@validate_schema(__P__UpdateSchema)
def update___s__(entity_id: int):
    """PUT /api/v1/__URL__/<id>"""
    entity = get___s___service().update__P__(entity_id, request.validated_data)
    return success_response(data=_one.dump(entity), message='Updated')


@__s___bp.route('/<int:entity_id>', methods=['DELETE'])
@token_required
def delete___s__(entity_id: int):
    """DELETE /api/v1/__URL__/<id>"""
    get___s___service().delete__P__(entity_id)
    return success_response(message='Deleted')
EOF

# ------------------------------------------------------------------ gRPC: proto + servicer
render "app/grpc_protos/protos/${s}_service.proto" <<'EOF'
syntax = "proto3";

package __PKG__;

// __P__Service - Controller → Service communication for __P__ (generated by tools/new-feature.sh)

service __P__Service {
    rpc Get__P__(Get__P__Request) returns (__P__Message);
    rpc List__P__s(List__P__sRequest) returns (List__P__sResponse);
    rpc Create__P__(Create__P__Request) returns (__P__Message);
    rpc Delete__P__(Delete__P__Request) returns (Delete__P__Response);
}

message __P__Message {
    int64 id = 1;
    string name = 2;
    string description = 3;
    string created_at = 4;
    string updated_at = 5;
}

message Get__P__Request { int64 id = 1; }
message List__P__sRequest { int32 page = 1; int32 per_page = 2; }
message List__P__sResponse { repeated __P__Message items = 1; int64 total = 2; }
message Create__P__Request { string name = 1; string description = 2; }
message Delete__P__Request { int64 id = 1; }
message Delete__P__Response { bool deleted = 1; }
EOF
"$PY" -m grpc_tools.protoc -I app/grpc_protos/protos --python_out=app/grpc_protos \
    --grpc_python_out=app/grpc_protos "app/grpc_protos/protos/${s}_service.proto"
# protoc emits a top-level import; the template imports generated modules as app.grpc_protos.*
perl -pi -e "s/^import ${s}_service_pb2 as /from app.grpc_protos import ${s}_service_pb2 as /" \
    "app/grpc_protos/${s}_service_pb2_grpc.py"
grep -q "^from app.grpc_protos import ${s}_service_pb2 as " "app/grpc_protos/${s}_service_pb2_grpc.py" \
    || { echo "new-feature: could not rewrite the import in app/grpc_protos/${s}_service_pb2_grpc.py" >&2; exit 1; }
echo "  + app/grpc_protos/${s}_service_pb2.py, ${s}_service_pb2_grpc.py (grpc_tools.protoc)"

render "app/grpc_protos/servers/${s}_service_server.py" <<'EOF'
"""
__P__ Service gRPC Servicer
gRPC boundary for __P__Service; registered on the service-layer server in user_service_server.serve().
"""
import grpc

from app.grpc_protos import __s___service_pb2, __s___service_pb2_grpc
from app.di_container import get___s___service
from app.utils.exceptions import NotFoundError, ValidationError


def _to_proto(entity) -> __s___service_pb2.__P__Message:
    return __s___service_pb2.__P__Message(
        id=entity.id or 0,
        name=entity.name or "",
        description=entity.description or "",
        created_at=entity.created_at.isoformat() if entity.created_at else "",
        updated_at=entity.updated_at.isoformat() if entity.updated_at else "",
    )


class __P__ServiceServicer(__s___service_pb2_grpc.__P__ServiceServicer):
    """gRPC servicer for __P__Service"""

    def __init__(self, app=None):
        self.app = app

    def _call(self, context, fn, *args):
        try:
            return fn(*args)
        except NotFoundError as e:
            context.abort(grpc.StatusCode.NOT_FOUND, e.message)
        except ValidationError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, e.message)

    def Get__P__(self, request, context):
        return _to_proto(self._call(context, get___s___service().get__P__ById, request.id))

    def List__P__s(self, request, context):
        items, total = self._call(
            context, get___s___service().list__P__s, request.page or 1, request.per_page or 20
        )
        return __s___service_pb2.List__P__sResponse(items=[_to_proto(i) for i in items], total=total)

    def Create__P__(self, request, context):
        entity = self._call(
            context, get___s___service().create__P__, request.name, request.description or None
        )
        return _to_proto(entity)

    def Delete__P__(self, request, context):
        self._call(context, get___s___service().delete__P__, request.id)
        return __s___service_pb2.Delete__P__Response(deleted=True)


def register(server, app=None) -> None:
    """Add this servicer to a grpc.Server."""
    __s___service_pb2_grpc.add___P__ServiceServicer_to_server(__P__ServiceServicer(app), server)
EOF

# ------------------------------------------------------------------ wiring
insert_after app/di_container.py "    container\\.register_singleton\\('auth_service', create_auth_service\\)\\n" "
    # __P__ slice (tools/new-feature.sh): DAO → Repository → Service
    def create_${s}_dao():
        from app.dao.impl.${s}_dao_impl import ${P}DaoImpl
        return ${P}DaoImpl(container.get('db_session'))

    def create_${s}_repository():
        from app.repository.impl.${s}_repository_impl import ${P}RepositoryImpl
        return ${P}RepositoryImpl(container.get('${s}_dao'))

    def create_${s}_service():
        from app.services.impl.${s}_service_impl import ${P}ServiceImpl
        return ${P}ServiceImpl(container.get('${s}_repository'))

    container.register_singleton('${s}_dao', create_${s}_dao)
    container.register_singleton('${s}_repository', create_${s}_repository)
    container.register_singleton('${s}_service', create_${s}_service)
"
cat >> app/di_container.py <<EOF


def get_${s}_service():
    """
    Get ${P} service from DI container

    Returns:
        ${P}Service implementation
    """
    return get_container().get('${s}_service')
EOF
echo "  ~ app/di_container.py (getter)"

insert_after app/controllers/__init__.py "from app\\.controllers\\.public_user_controller import public_user_bp\\n" \
    "from app.controllers.${s}_controller import ${s}_bp
"
perl -0777 -i -pe "s/__all__ = \\[([^\\]]*)\\]/__all__ = [\$1, '${s}_bp']/s or exit 3" app/controllers/__init__.py \
    || { echo "new-feature: __all__ not found in app/controllers/__init__.py" >&2; exit 1; }
insert_after app/__init__.py "        app\\.register_blueprint\\(public_user_bp\\)[^\\n]*\\n" \
    "        from app.controllers import ${s}_bp
        app.register_blueprint(${s}_bp, url_prefix='/api/v1/${URL}')
"
insert_before app/grpc_protos/servers/user_service_server.py "    server\\.add_insecure_port\\(" \
    "    from app.grpc_protos.servers import ${s}_service_server
    ${s}_service_server.register(server, app)
"

# ------------------------------------------------------------------ tests (mirror tests/unit layout)
render "tests/unit/test_models/test_${s}_model.py" <<'EOF'
"""__P__ model unit tests"""
from app.models.__s__ import __P__


def test_constructor_sets_fields():
    e = __P__(name='n', description='d')
    assert (e.name, e.description) == ('n', 'd')
    assert e.id is None
    assert '__P__' in repr(e)
EOF
mkdir -p tests/unit/test_dao
[ -f tests/unit/test_dao/__init__.py ] || : > tests/unit/test_dao/__init__.py
render "tests/unit/test_dao/test_${s}_dao_impl.py" <<'EOF'
"""__P__DaoImpl unit tests against an in-memory SQLite database (no MySQL needed)."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.dao.impl.__s___dao_impl import __P__DaoImpl
from app.models.__s__ import __P__


@pytest.fixture
def dao():
    engine = create_engine('sqlite://')
    __P__.__table__.create(engine)
    with Session(engine) as session:
        yield __P__DaoImpl(session)


def test_insert_find_update_delete(dao):
    created = dao.insert(__P__(name='a', description='x'))
    assert created.id is not None
    assert dao.find_by_id(created.id).name == 'a'
    created.name = 'b'
    assert dao.update(created).name == 'b'
    assert dao.delete(created.id) is True
    assert dao.find_by_id(created.id) is None
    assert dao.delete(created.id) is False


def test_find_page_returns_page_and_total(dao):
    for i in range(5):
        dao.insert(__P__(name=f'n{i}'))
    items, total = dao.find_page(page=2, per_page=2)
    assert total == 5
    assert [i.name for i in items] == ['n2', 'n3']
EOF
render "tests/unit/test_repository/test_${s}_repository_impl.py" <<'EOF'
"""__P__RepositoryImpl unit tests (DAO mocked)"""
from unittest.mock import Mock

import pytest

from app.models.__s__ import __P__
from app.repository.impl.__s___repository_impl import __P__RepositoryImpl


@pytest.fixture
def dao():
    return Mock()


@pytest.fixture
def repo(dao):
    return __P__RepositoryImpl(dao)


def test_save_new_inserts(repo, dao):
    e = __P__(name='a')
    dao.insert.return_value = e
    assert repo.save(e) is e
    dao.insert.assert_called_once_with(e)


def test_save_existing_updates(repo, dao):
    e = __P__(name='a')
    e.id = 7
    dao.update.return_value = e
    assert repo.save(e) is e
    dao.update.assert_called_once_with(e)


def test_reads_delegate(repo, dao):
    dao.find_by_id.return_value = None
    dao.find_page.return_value = ([], 3)
    dao.delete.return_value = True
    assert repo.find_by_id(1) is None
    assert repo.exists_by_id(1) is False
    assert repo.find_all() == []
    assert repo.count() == 3
    assert repo.find_all_paginated(2, 5) == ([], 3)
    assert repo.delete_by_id(1) is True
EOF
render "tests/unit/test_services/test_${s}_service.py" <<'EOF'
"""__P__ServiceImpl unit tests (repository mocked)"""
from unittest.mock import Mock

import pytest

from app.models.__s__ import __P__
from app.services.impl.__s___service_impl import __P__ServiceImpl
from app.utils.exceptions import NotFoundError, ValidationError


@pytest.fixture
def repo():
    r = Mock()
    r.save.side_effect = lambda e: e
    return r


@pytest.fixture
def service(repo):
    return __P__ServiceImpl(repo)


def test_create_trims_and_saves(service, repo):
    e = service.create__P__('  a  ', 'd')
    assert (e.name, e.description) == ('a', 'd')
    repo.save.assert_called_once()


@pytest.mark.parametrize('bad', ['', '   ', None, 'x' * 121])
def test_create_rejects_bad_name(service, bad):
    with pytest.raises(ValidationError):
        service.create__P__(bad)


def test_get_missing_raises(service, repo):
    repo.find_by_id.return_value = None
    with pytest.raises(NotFoundError):
        service.get__P__ById(1)


def test_list_validates_paging(service, repo):
    repo.find_all_paginated.return_value = ([], 0)
    assert service.list__P__s(1, 20) == ([], 0)
    with pytest.raises(ValidationError):
        service.list__P__s(0, 20)


def test_update_applies_known_fields_only(service, repo):
    repo.find_by_id.return_value = __P__(name='old')
    e = service.update__P__(1, {'name': 'new', 'description': 'd', 'id': 99})
    assert (e.name, e.description, e.id) == ('new', 'd', None)


def test_delete_missing_raises(service, repo):
    repo.delete_by_id.return_value = False
    with pytest.raises(NotFoundError):
        service.delete__P__(1)
EOF
render "tests/unit/test_controllers/test_${s}_controller.py" <<'EOF'
"""__P__ controller unit tests: blueprint on a bare Flask app, service and auth mocked."""
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from app.controllers.__s___controller import __s___bp
from app.models.__s__ import __P__
from app.utils.exceptions import APIException, NotFoundError
from app.utils.response import error_response

URL = '/api/v1/__URL__'
HDR = {'Authorization': 'Bearer t', 'Content-Type': 'application/json'}


@pytest.fixture
def service():
    return MagicMock()


@pytest.fixture
def client(service):
    app = Flask(__name__)
    app.register_blueprint(__s___bp, url_prefix=URL)
    app.register_error_handler(
        APIException, lambda e: error_response(e.message, e.status_code, e.error_code)
    )
    auth = MagicMock()
    auth.validateToken.return_value = MagicMock()
    with patch('app.di_container.get_auth_service', return_value=auth), \
         patch('app.controllers.__s___controller.get___s___service', return_value=service):
        yield app.test_client()


def _entity(i=1):
    e = __P__(name=f'n{i}', description=None)
    e.id = i
    return e


def test_requires_token(client):
    assert client.get(URL).status_code == 401


def test_list(client, service):
    service.list__P__s.return_value = ([_entity(1), _entity(2)], 2)
    r = client.get(URL, headers=HDR)
    assert r.status_code == 200
    assert r.get_json()['data']['pagination']['total'] == 2


def test_get_and_not_found(client, service):
    service.get__P__ById.return_value = _entity(3)
    assert client.get(f'{URL}/3', headers=HDR).get_json()['data']['name'] == 'n3'
    service.get__P__ById.side_effect = NotFoundError('nope')
    assert client.get(f'{URL}/4', headers=HDR).status_code == 404


def test_create_validates_body(client, service):
    service.create__P__.return_value = _entity(5)
    assert client.post(URL, headers=HDR, json={'name': 'n5'}).status_code == 201
    assert client.post(URL, headers=HDR, json={}).status_code == 400


def test_update_and_delete(client, service):
    service.update__P__.return_value = _entity(6)
    assert client.put(f'{URL}/6', headers=HDR, json={'name': 'x'}).status_code == 200
    assert client.delete(f'{URL}/6', headers=HDR).status_code == 200
    service.delete__P__.assert_called_once_with(6)
EOF
mkdir -p tests/unit/test_grpc
[ -f tests/unit/test_grpc/__init__.py ] || : > tests/unit/test_grpc/__init__.py
render "tests/unit/test_grpc/test_${s}_service_server.py" <<'EOF'
"""__P__ gRPC servicer unit tests (service mocked, no network)."""
from unittest.mock import MagicMock, patch

import grpc
import pytest

from app.grpc_protos import __s___service_pb2 as pb
from app.grpc_protos.servers.__s___service_server import __P__ServiceServicer, register
from app.models.__s__ import __P__
from app.utils.exceptions import NotFoundError


@pytest.fixture
def service():
    with patch('app.grpc_protos.servers.__s___service_server.get___s___service') as get:
        yield get.return_value


def _entity():
    e = __P__(name='n', description='d')
    e.id = 1
    return e


def test_get_and_create(service):
    service.get__P__ById.return_value = _entity()
    service.create__P__.return_value = _entity()
    s = __P__ServiceServicer()
    assert s.Get__P__(pb.Get__P__Request(id=1), MagicMock()).name == 'n'
    assert s.Create__P__(pb.Create__P__Request(name='n'), MagicMock()).id == 1


def test_list_and_delete(service):
    service.list__P__s.return_value = ([_entity()], 1)
    s = __P__ServiceServicer()
    assert s.List__P__s(pb.List__P__sRequest(), MagicMock()).total == 1
    assert s.Delete__P__(pb.Delete__P__Request(id=1), MagicMock()).deleted is True


def test_not_found_aborts(service):
    service.get__P__ById.side_effect = NotFoundError('x')
    ctx = MagicMock()
    ctx.abort.side_effect = RuntimeError('aborted')   # a real context.abort raises
    with pytest.raises(RuntimeError):
        __P__ServiceServicer().Get__P__(pb.Get__P__Request(id=9), ctx)
    ctx.abort.assert_called_once_with(grpc.StatusCode.NOT_FOUND, 'x')


def test_register_adds_handler():
    server = MagicMock()
    register(server)
    server.add_generic_rpc_handlers.assert_called_once()
EOF

echo "done. Next: run the tests (AGENTS.md §5), add your fields, then tools/arch-check.sh."
