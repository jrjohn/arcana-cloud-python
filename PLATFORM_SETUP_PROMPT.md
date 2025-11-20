# Flask RESTful API 雲平台建置 Prompt

## 版本要求
- **Python**: 3.14.0 (最新穩定版)
- **Flask**: 3.1.0+ (最新版)
- **SQLAlchemy**: 2.0.35+ (最新 2.0 系列)
- **Celery**: 5.4.0+ (最新版)
- **pytest**: 8.3.4+ (最新版)

> 注意：確保所有依賴套件與 Python 3.14.0 完全相容，利用最新版本的新特性與性能改進。

## 專案概述
請協助建立一個基於 Flask 的企業級 RESTful API 雲平台，具備以下核心功能與架構設計：

## 核心需求

### 1. 技術棧
- **Python 版本**: Python 3.14.0 (最新版)
- **框架**: Flask 3.1.0+ (最新版) + Flask-RESTful
- **認證**: OAuth2 + JWT Token (Annotation 驗證)
- **資料庫**: 支援 MySQL、PostgreSQL 等關聯式資料庫
- **ORM**: SQLAlchemy 2.0+ (最新版)
- **遷移工具**: Alembic (自動生成 SQL schema)
- **容器化**: Docker + Docker Compose
- **編排**: Kubernetes ready (支援水平擴展)
- **任務佇列**: Celery 5.4+ (最新版) + Redis/RabbitMQ
- **API 文檔**: Swagger/OpenAPI (Flask-RESTX 或 flasgger)
- **測試**: pytest 8.0+ + pytest-cov (單元測試 + 整合測試)

### 2. 架構設計原則

#### 2.1 Interface-Implementation 模式
所有服務層和資料存取層都必須使用接口-實現模式：

```python
# 定義接口 (Abstract Base Class)
from abc import ABC, abstractmethod

class IUserService(ABC):
    @abstractmethod
    def create_user(self, user_data: dict) -> User:
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        pass

# 實現類
class UserService(IUserService):
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    def create_user(self, user_data: dict) -> User:
        # 實現邏輯
        pass
```

**優點**:
- 依賴注入 (Dependency Injection)
- 易於測試 (可使用 Mock)
- 解耦合
- 符合 SOLID 原則

#### 2.2 分散式分層架構 (Distributed Layered Architecture)

**重要**: 每一層都設計為可獨立部署的微服務，支援水平擴展和負載平衡。

```
┌─────────────────────────────────────────────────────────────┐
│ Controller Layer (API Gateway / 控制層)                      │
│ - 可部署多個實例 (Docker/K8s)                                 │
│ - 通過 HTTP/REST 或 gRPC 調用 Service 層                     │
│ - 負載平衡器分散請求                                          │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP/REST/gRPC
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ Service Layer (業務邏輯層) - 可獨立部署                       │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│ │UserService   │  │UserService   │  │AuthService   │       │
│ │Instance 1    │  │Instance 2    │  │Instance 1    │       │
│ │(Docker/K8s)  │  │(Docker/K8s)  │  │(Docker/K8s)  │       │
│ └──────────────┘  └──────────────┘  └──────────────┘       │
│ - Interface + Implementation 模式                            │
│ - 無狀態設計，可水平擴展                                      │
│ - 通過 HTTP/REST 或 gRPC 調用 Repository 層                 │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP/REST/gRPC
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ Repository/DAO Layer (資料存取層) - 可獨立部署                │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│ │UserRepo      │  │UserRepo      │  │TransRepo     │       │
│ │Instance 1    │  │Instance 2    │  │Instance 1    │       │
│ │(K8s Pod 1)   │  │(K8s Pod 2)   │  │(K8s Pod 3)   │       │
│ └──────────────┘  └──────────────┘  └──────────────┘       │
│ - 封裝資料庫存取邏輯                                          │
│ - 連接池管理                                                 │
│ - 快取策略                                                   │
└─────────────────┬───────────────────────────────────────────┘
                  │ Database Protocol
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ Database Layer (資料庫層)                                    │
│ - MySQL/PostgreSQL Cluster                                  │
│ - 主從架構 / 讀寫分離                                         │
│ - 連接池                                                     │
└─────────────────────────────────────────────────────────────┘
```

**分散式部署優點**:
- ✅ **獨立擴展**: 每層可根據負載獨立擴展
- ✅ **故障隔離**: 單一實例失敗不影響整體服務
- ✅ **負載平衡**: 請求自動分散到多個實例
- ✅ **彈性部署**: Controller 可調用不同 Docker/K8s 的 Service 實例
- ✅ **微服務架構**: 符合雲原生設計

#### 2.3 分散式通訊設計

**支援兩種部署模式**:

##### 模式 1: 單體應用 (Monolithic)
所有層在同一個應用內，通過直接函數調用

##### 模式 2: 微服務架構 (Microservices) ⭐ **推薦**
各層獨立部署，通過 HTTP/REST 或 gRPC 通訊

```python
# 服務發現與負載平衡
class ServiceClient:
    """服務客戶端 - 支援多實例調用"""

    def __init__(self, service_name: str):
        self.service_urls = self._discover_services(service_name)
        self.load_balancer = RoundRobinLoadBalancer(self.service_urls)

    def call(self, endpoint: str, method: str = 'GET', **kwargs):
        """調用服務 - 自動負載平衡"""
        service_url = self.load_balancer.get_next()
        return requests.request(method, f"{service_url}{endpoint}", **kwargs)

# Controller 調用 Service 層 (跨 Docker/K8s)
class UserController:
    def __init__(self):
        # 自動發現並連接到 UserService 實例
        # 環境變數: USER_SERVICE_URLS=http://user-svc-1:5001,http://user-svc-2:5001
        self.user_service_client = ServiceClient('user-service')

    @token_required
    def get_user(self, user_id: int):
        # 自動負載平衡到不同的 Service 實例
        response = self.user_service_client.call(
            f'/internal/users/{user_id}',
            method='GET'
        )
        return response.json()

# Service 層調用 Repository 層 (跨 K8s Pod)
class UserServiceImpl(IUserService):
    def __init__(self):
        # 自動發現並連接到 Repository 實例
        # 環境變數: USER_REPO_URLS=http://user-repo-1:5002,http://user-repo-2:5002
        self.user_repo_client = ServiceClient('user-repository')

    def get_user_by_id(self, user_id: int) -> User:
        response = self.user_repo_client.call(
            f'/internal/repository/users/{user_id}',
            method='GET'
        )
        return User(**response.json())
```

**服務發現機制**:
- **Kubernetes**: 使用 K8s Service 自動發現
- **Docker Compose**: 使用 Docker DNS
- **Consul/Eureka**: 服務註冊與發現
- **環境變數**: 配置多個服務端點

##### 模式 3: 細粒度微服務拆分 ⭐⭐ **進階**
每個業務服務可進一步拆分為獨立的微服務，部署在不同 Docker/K8s：

```
Service 層細粒度拆分範例：
┌──────────────────────────────────────────────────┐
│ UserService (原本單一服務)                        │
│ ↓ 拆分為多個獨立微服務                            │
│ ┌────────────────┐  ┌────────────────┐          │
│ │UserAuthService │  │UserProfileSvc  │          │
│ │(Docker 1)      │  │(Docker 2)      │          │
│ │- 登入/登出      │  │- 個人資料 CRUD │          │
│ │- Token 驗證     │  │- 頭像上傳      │          │
│ └────────────────┘  └────────────────┘          │
│                                                  │
│ ┌────────────────┐  ┌────────────────┐          │
│ │UserPermission  │  │UserNotification│          │
│ │Service(K8s P1) │  │Service(K8s P2) │          │
│ │- 權限管理       │  │- 通知發送      │          │
│ │- 角色分配       │  │- 訂閱管理      │          │
│ └────────────────┘  └────────────────┘          │
└──────────────────────────────────────────────────┘
```

**細粒度拆分實現**:
```python
# 原本的 UserService 拆分為多個獨立服務

# 1. 用戶認證微服務 (獨立 Docker)
class UserAuthMicroservice:
    """
    部署在獨立 Docker: user-auth-service:5101
    """
    @app.route('/auth/login', methods=['POST'])
    @validate_schema(LoginSchema)
    def login(self):
        # 登入邏輯
        pass

    @app.route('/auth/logout', methods=['POST'])
    @token_required
    def logout(self):
        # 登出邏輯
        pass

# 2. 用戶資料微服務 (獨立 Docker)
class UserProfileMicroservice:
    """
    部署在獨立 Docker: user-profile-service:5102
    """
    @app.route('/profile/<int:user_id>', methods=['GET'])
    @token_required
    def get_profile(self, user_id):
        # 獲取資料邏輯
        pass

    @app.route('/profile/<int:user_id>', methods=['PUT'])
    @token_required
    def update_profile(self, user_id):
        # 更新資料邏輯
        pass

# 3. 用戶權限微服務 (獨立 K8s Pod)
class UserPermissionMicroservice:
    """
    部署在獨立 K8s Pod: user-permission-service:5103
    """
    @app.route('/permissions/<int:user_id>', methods=['GET'])
    @token_required
    def get_permissions(self, user_id):
        # 獲取權限邏輯
        pass

    @app.route('/permissions/assign', methods=['POST'])
    @token_required
    @role_required('admin')
    def assign_permission(self):
        # 分配權限邏輯
        pass

# Controller 層調用細粒度微服務
class UserController:
    def __init__(self):
        # 連接到不同的用戶微服務
        self.auth_client = ServiceClient('user-auth-service')
        self.profile_client = ServiceClient('user-profile-service')
        self.permission_client = ServiceClient('user-permission-service')
        self.notification_client = ServiceClient('user-notification-service')

    @token_required
    def get_user_complete_info(self, user_id: int):
        """
        聚合多個微服務的數據
        """
        # 並行調用多個微服務
        with ThreadPoolExecutor(max_workers=3) as executor:
            profile_future = executor.submit(
                self.profile_client.call, f'/profile/{user_id}'
            )
            permission_future = executor.submit(
                self.permission_client.call, f'/permissions/{user_id}'
            )
            notification_future = executor.submit(
                self.notification_client.call, f'/notifications/{user_id}/count'
            )

            profile = profile_future.result().json()
            permissions = permission_future.result().json()
            notification_count = notification_future.result().json()

        return {
            'profile': profile,
            'permissions': permissions,
            'notification_count': notification_count
        }
```

**細粒度拆分的 Docker Compose 配置**:
```yaml
services:
  # === User 微服務群組 ===
  user-auth-service-1:
    build:
      context: .
      dockerfile: docker/Dockerfile.user-auth
    ports:
      - "5101:5101"
    environment:
      - SERVICE_NAME=user-auth
      - SERVICE_PORT=5101

  user-auth-service-2:
    build:
      context: .
      dockerfile: docker/Dockerfile.user-auth
    ports:
      - "5111:5101"
    environment:
      - SERVICE_NAME=user-auth
      - SERVICE_PORT=5101

  user-profile-service-1:
    build:
      context: .
      dockerfile: docker/Dockerfile.user-profile
    ports:
      - "5102:5102"
    environment:
      - SERVICE_NAME=user-profile
      - SERVICE_PORT=5102

  user-profile-service-2:
    build:
      context: .
      dockerfile: docker/Dockerfile.user-profile
    ports:
      - "5112:5102"
    environment:
      - SERVICE_NAME=user-profile
      - SERVICE_PORT=5102

  user-permission-service:
    build:
      context: .
      dockerfile: docker/Dockerfile.user-permission
    ports:
      - "5103:5103"
    environment:
      - SERVICE_NAME=user-permission
      - SERVICE_PORT=5103

  user-notification-service:
    build:
      context: .
      dockerfile: docker/Dockerfile.user-notification
    ports:
      - "5104:5104"
    environment:
      - SERVICE_NAME=user-notification
      - SERVICE_PORT=5104
```

**細粒度拆分優點**:
- ✅ **極致解耦**: 每個功能獨立部署和維護
- ✅ **靈活擴展**: 高負載功能可單獨擴展
- ✅ **團隊協作**: 不同團隊負責不同微服務
- ✅ **技術異構**: 不同服務可使用不同技術棧
- ✅ **故障隔離**: 單一功能失敗不影響其他功能

#### 2.4 專案結構
```
project/
├── app/
│   ├── __init__.py                 # Flask app factory
│   ├── config.py                   # 配置管理 (環境變數)
│   ├── extensions.py               # 擴展初始化
│   ├── container.py                # DI Container (依賴注入容器)
│   │
│   ├── controllers/                # API 控制層 (可獨立部署)
│   │   ├── __init__.py
│   │   ├── auth_controller.py      # OAuth2 認證端點
│   │   ├── user_controller.py
│   │   └── resource_controller.py
│   │
│   ├── services/                   # 服務層 (可獨立部署)
│   │   ├── __init__.py
│   │   ├── interfaces/             # 服務接口
│   │   │   ├── __init__.py
│   │   │   ├── i_auth_service.py
│   │   │   ├── i_user_service.py
│   │   │   └── i_transaction_service.py
│   │   ├── implementations/        # 服務實現
│   │   │   ├── __init__.py
│   │   │   ├── auth_service_impl.py
│   │   │   ├── user_service_impl.py
│   │   │   └── transaction_service_impl.py
│   │   └── clients/                # 服務客戶端 (用於跨實例調用)
│   │       ├── __init__.py
│   │       ├── service_client.py
│   │       └── load_balancer.py
│   │
│   ├── repositories/               # 資料存取層 (可獨立部署)
│   │   ├── __init__.py
│   │   ├── interfaces/             # Repository 接口
│   │   │   ├── __init__.py
│   │   │   ├── i_base_repository.py
│   │   │   ├── i_user_repository.py
│   │   │   └── i_transaction_repository.py
│   │   ├── implementations/        # Repository 實現
│   │   │   ├── __init__.py
│   │   │   ├── base_repository_impl.py
│   │   │   ├── user_repository_impl.py
│   │   │   └── transaction_repository_impl.py
│   │   └── clients/                # Repository 客戶端
│   │       ├── __init__.py
│   │       └── repository_client.py
│   │
│   ├── models/                     # 資料模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── oauth_client.py
│   │   ├── oauth_token.py
│   │   └── transaction.py
│   │
│   ├── schemas/                    # Marshmallow Schemas
│   │   ├── __init__.py
│   │   ├── user_schema.py
│   │   ├── auth_schema.py
│   │   └── transaction_schema.py
│   │
│   ├── decorators/                 # Annotation 裝飾器
│   │   ├── __init__.py
│   │   ├── auth_decorators.py      # @token_required, @permission_required
│   │   ├── transaction_decorators.py  # @transactional
│   │   ├── cache_decorators.py     # @cached
│   │   └── validation_decorators.py   # @validate_schema
│   │
│   ├── middleware/                 # 中間件
│   │   ├── __init__.py
│   │   ├── auth_middleware.py
│   │   ├── logging_middleware.py
│   │   └── request_id_middleware.py
│   │
│   ├── tasks/                      # Celery 任務
│   │   ├── __init__.py
│   │   ├── scheduled_tasks.py      # 定時任務
│   │   └── background_tasks.py     # 長時間運行任務
│   │
│   └── utils/                      # 工具類
│       ├── __init__.py
│       ├── jwt_utils.py            # JWT Token 工具
│       ├── exceptions.py           # 自定義異常
│       ├── response.py             # 響應格式化
│       └── validators.py           # 驗證器
│
├── migrations/                     # Alembic 遷移文件
│
├── tests/                          # 測試文件
│   ├── __init__.py
│   ├── conftest.py                 # pytest 配置與 fixtures
│   ├── unit/                       # 單元測試
│   │   ├── __init__.py
│   │   ├── test_services/
│   │   │   ├── test_user_service.py
│   │   │   ├── test_auth_service.py
│   │   │   └── test_transaction_service.py
│   │   ├── test_repositories/
│   │   │   ├── test_user_repository.py
│   │   │   └── test_transaction_repository.py
│   │   └── test_utils/
│   │       ├── test_jwt_utils.py
│   │       └── test_validators.py
│   │
│   ├── integration/                # 整合測試
│   │   ├── __init__.py
│   │   ├── test_api/
│   │   │   ├── test_auth_api.py
│   │   │   ├── test_user_api.py
│   │   │   └── test_transaction_api.py
│   │   ├── test_database/
│   │   │   └── test_models.py
│   │   └── test_tasks/
│   │       └── test_celery_tasks.py
│   │
│   ├── fixtures/                   # 測試數據
│   │   ├── __init__.py
│   │   ├── user_fixtures.py
│   │   └── transaction_fixtures.py
│   │
│   └── mocks/                      # Mock 對象
│       ├── __init__.py
│       ├── mock_repositories.py
│       └── mock_services.py
│
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.test             # 測試環境 Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.test.yml     # 測試環境 compose
│   └── docker-compose.prod.yml
│
├── k8s/                            # Kubernetes 配置
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── hpa.yaml                    # Horizontal Pod Autoscaler
│   └── ingress.yaml
│
├── .env.example                    # 環境變數範例
├── .env.test                       # 測試環境變數
├── requirements.txt
├── requirements-dev.txt            # 開發依賴
├── pytest.ini                      # pytest 配置
├── .coveragerc                     # 覆蓋率配置
├── celery_worker.py               # Celery worker 入口
└── wsgi.py                        # WSGI 入口
```

### 3. 功能需求詳細說明

#### 3.1 OAuth2 + JWT Token 認證系統

##### 3.1.1 Token 驗證 Annotation (裝飾器)
```python
from functools import wraps
from flask import request, g
import jwt

def token_required(f):
    """
    Token 驗證裝飾器
    使用方式: @token_required
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return {'message': 'Token is missing'}, 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            g.current_user = User.query.get(data['user_id'])
        except:
            return {'message': 'Token is invalid'}, 401

        return f(*args, **kwargs)

    return decorated


def permission_required(*permissions):
    """
    權限驗證裝飾器
    使用方式: @permission_required('user:read', 'user:write')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.has_permissions(permissions):
                return {'message': 'Insufficient permissions'}, 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(*roles):
    """
    角色驗證裝飾器
    使用方式: @role_required('admin', 'manager')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.has_role(roles):
                return {'message': 'Insufficient role'}, 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

##### 3.1.2 Controller 使用範例
```python
from flask_restful import Resource
from app.decorators.auth_decorators import token_required, permission_required, role_required
from app.decorators.validation_decorators import validate_schema
from app.schemas.user_schema import UserCreateSchema, UserUpdateSchema

class UserResource(Resource):
    def __init__(self, user_service: IUserService):
        self.user_service = user_service

    @token_required
    @permission_required('user:read')
    def get(self, user_id):
        """獲取用戶資訊"""
        user = self.user_service.get_user_by_id(user_id)
        return {'data': user}, 200

    @token_required
    @role_required('admin')
    @validate_schema(UserCreateSchema)
    def post(self):
        """創建用戶 (僅管理員)"""
        user = self.user_service.create_user(g.validated_data)
        return {'data': user}, 201

    @token_required
    @permission_required('user:write')
    @validate_schema(UserUpdateSchema)
    def put(self, user_id):
        """更新用戶"""
        user = self.user_service.update_user(user_id, g.validated_data)
        return {'data': user}, 200
```

##### 3.1.3 OAuth2 流程實現
- Authorization Code Grant
- Client Credentials Grant
- Password Grant
- Refresh Token
- Token 儲存: Redis (支援分散式)
- 支援 JWT Token
- Token 撤銷機制

#### 3.2 資料庫自動遷移
- 使用 Alembic 自動生成遷移腳本
- 提供 CLI 命令:
  - `flask db init` - 初始化遷移環境
  - `flask db migrate -m "message"` - 自動生成遷移腳本
  - `flask db upgrade` - 執行遷移
  - `flask db downgrade` - 回滾遷移
- 容器啟動時自動執行遷移
- 支援多資料庫連線

#### 3.3 分散式架構支援 (無狀態設計)
- **Session 管理**: 使用 Redis 儲存 session
- **Token 儲存**: Redis (支援多實例共享)
- **檔案儲存**: 使用物件儲存 (S3/MinIO)
- **快取**: Redis 分散式快取
- **配置**: 環境變數注入 (支援 K8s ConfigMap/Secrets)
- **健康檢查**: `/health` 和 `/ready` 端點
- **優雅關閉**: 處理 SIGTERM 信號
- **日誌**: 結構化日誌輸出到 stdout (JSON 格式)

#### 3.4 分散式任務系統 (Celery + 分散式鎖)

##### 3.4.1 架構設計原則
**重要**: Job 可分散在不同 Docker 或 K8s 中運行，但同一任務只能由一個實例執行（使用分散式鎖）。

```
┌─────────────────────────────────────────────────────────┐
│              Celery Beat (排程器)                        │
│    - 只部署 1 個實例，負責定時任務調度                    │
│    - 使用 Redis 鎖確保單實例運行                         │
└────────────────────┬────────────────────────────────────┘
                     │ 發送任務到 Redis Queue
                     ↓
┌─────────────────────────────────────────────────────────┐
│                 Redis (訊息佇列 + 分散式鎖)               │
└────────────────────┬────────────────────────────────────┘
                     │ 多個 Worker 競爭任務
      ┌──────────────┼──────────────┬──────────────┐
      │              │              │              │
┌─────▼─────┐  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
│ Worker 1  │  │ Worker 2 │  │ Worker 3 │  │ Worker N │
│(Docker 1) │  │(Docker 2)│  │(K8s Pod1)│  │(K8s PodN)│
│           │  │          │  │          │  │          │
│Task: A,B  │  │Task: C   │  │Task: D,E │  │Task: F   │
└───────────┘  └──────────┘  └──────────┘  └──────────┘
```

##### 3.4.2 分散式鎖實現
確保同一任務只能由一個 Worker 執行：

```python
# app/tasks/decorators.py
from functools import wraps
from redis import Redis
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

def single_instance_task(timeout=3600):
    """
    確保任務只在一個實例中執行的裝飾器
    使用 Redis 分散式鎖
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            redis_client = Redis.from_url(os.getenv('REDIS_URL'))
            lock_key = f"celery:lock:{func.__name__}"

            # 嘗試獲取鎖，超時時間為 timeout 秒
            lock = redis_client.lock(lock_key, timeout=timeout, blocking=False)

            if lock.acquire(blocking=False):
                try:
                    logger.info(f"Task {func.__name__} acquired lock, executing...")
                    result = func(*args, **kwargs)
                    return result
                finally:
                    lock.release()
                    logger.info(f"Task {func.__name__} released lock")
            else:
                logger.warning(f"Task {func.__name__} is already running, skipped")
                return None

        return wrapper
    return decorator
```

##### 3.4.3 定時任務實現
```python
# app/tasks/scheduled_tasks.py
from celery import Celery
from app.tasks.decorators import single_instance_task

celery = Celery('tasks')

@celery.task
@single_instance_task(timeout=1800)  # 30分鐘超時
def cleanup_expired_tokens():
    """
    清理過期 Token
    - 即使部署多個 Celery Beat，也只有一個實例執行
    - 多個 Worker 競爭，但只有一個能獲得鎖
    """
    logger.info("Starting token cleanup task...")
    # 清理邏輯
    expired_count = Token.query.filter(Token.expires_at < datetime.now()).delete()
    db.session.commit()
    logger.info(f"Cleaned up {expired_count} expired tokens")
    return expired_count

@celery.task
@single_instance_task(timeout=3600)  # 1小時超時
def generate_daily_report():
    """
    生成每日報表
    - 確保只有一個 Worker 執行此任務
    """
    logger.info("Generating daily report...")
    # 報表生成邏輯
    report = generate_report(date=datetime.now().date())
    return report.id

@celery.task
@single_instance_task(timeout=7200)  # 2小時超時
def process_batch_data():
    """
    批次處理數據
    - 長時間運行的任務
    - 分散式鎖確保不會重複執行
    """
    logger.info("Processing batch data...")
    # 批次處理邏輯
    processed_count = 0
    for batch in get_data_batches():
        process_batch(batch)
        processed_count += len(batch)
    return processed_count
```

##### 3.4.4 Celery Beat 配置 (單實例部署)
```python
# celery_config.py
from celery.schedules import crontab

beat_schedule = {
    'cleanup-expired-tokens': {
        'task': 'app.tasks.scheduled_tasks.cleanup_expired_tokens',
        'schedule': crontab(minute='*/30'),  # 每30分鐘執行
    },
    'generate-daily-report': {
        'task': 'app.tasks.scheduled_tasks.generate_daily_report',
        'schedule': crontab(hour=0, minute=0),  # 每天午夜執行
    },
    'process-batch-data': {
        'task': 'app.tasks.scheduled_tasks.process_batch_data',
        'schedule': crontab(hour='*/6'),  # 每6小時執行
    },
}

# Celery Beat 鎖定機制（確保只有一個 Beat 實例）
beat_scheduler = 'redbeat.RedBeatScheduler'  # 使用 RedBeat 支援分散式
redbeat_redis_url = os.getenv('REDIS_URL')
```

##### 3.4.5 背景任務（無鎖，可並行執行）
```python
# app/tasks/background_tasks.py
@celery.task
def send_email(to: str, subject: str, body: str):
    """
    發送郵件 - 可並行執行
    - 不需要鎖，多個 Worker 可同時處理不同郵件
    """
    logger.info(f"Sending email to {to}")
    # 郵件發送邏輯
    send_smtp_email(to, subject, body)
    return True

@celery.task
def process_user_upload(user_id: int, file_path: str):
    """
    處理用戶上傳 - 可並行執行
    - 不同用戶的上傳可由不同 Worker 處理
    """
    logger.info(f"Processing upload for user {user_id}")
    # 處理上傳邏輯
    result = process_file(file_path)
    return result

@celery.task(bind=True, max_retries=3)
def calculate_metrics(self, metric_type: str):
    """
    計算指標 - 可並行執行，支援重試
    """
    try:
        logger.info(f"Calculating {metric_type} metrics")
        result = perform_calculation(metric_type)
        return result
    except Exception as exc:
        logger.error(f"Calculation failed: {exc}")
        raise self.retry(exc=exc, countdown=60)  # 60秒後重試
```

##### 3.4.6 Docker/K8s 部署配置

**Celery Beat (單實例，使用 Deployment replicas=1)**:
```yaml
# docker-compose.yml
celery-beat:
  build: .
  command: celery -A celery_worker.celery beat --loglevel=info --scheduler redbeat.RedBeatScheduler
  environment:
    - REDIS_URL=redis://redis:6379/0
  deploy:
    replicas: 1  # 只部署一個實例
  depends_on:
    - redis
```

**Celery Workers (多實例，可水平擴展)**:
```yaml
# docker-compose.yml
celery-worker:
  build: .
  command: celery -A celery_worker.celery worker --loglevel=info --concurrency=4
  environment:
    - REDIS_URL=redis://redis:6379/0
    - WORKER_ID=${HOSTNAME}  # 每個 Worker 有唯一 ID
  deploy:
    replicas: 5  # 部署5個 Worker 實例
  depends_on:
    - redis
    - mysql

# Kubernetes 配置
# k8s/celery-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
spec:
  replicas: 5  # 5個 Worker Pod
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: worker
        image: your-registry/flask-celery-worker:latest
        env:
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        - name: WORKER_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name  # Pod 名稱作為 Worker ID
```

##### 3.4.7 任務監控與管理
- **Flower**: Web 監控界面，查看所有 Worker 狀態
- **Redis Insight**: 查看任務佇列和鎖狀態
- **日誌聚合**: 所有 Worker 日誌統一收集
- **任務重試**: 自動重試失敗任務
- **任務優先級**: 高優先級任務優先執行

**部署優點**:
- ✅ **任務唯一性**: 分散式鎖確保定時任務不重複執行
- ✅ **高可用性**: 多個 Worker 提供容錯能力
- ✅ **水平擴展**: Worker 可根據負載動態擴展
- ✅ **靈活部署**: Worker 可分散在不同 Docker/K8s
- ✅ **故障恢復**: 某個 Worker 失敗，其他 Worker 接管任務

#### 3.5 交易管理 (Transaction)

##### 3.5.1 @transactional 裝飾器
```python
from functools import wraps
from flask import current_app
from app.extensions import db

def transactional(f):
    """
    交易管理裝飾器
    自動處理 commit 和 rollback
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Transaction failed: {str(e)}")
            raise
    return decorated_function
```

##### 3.5.2 Service 層使用範例
```python
class TransactionServiceImpl(ITransactionService):
    def __init__(self, transaction_repository: ITransactionRepository):
        self.transaction_repository = transaction_repository

    @transactional
    def create_transaction(self, transaction_data: dict) -> Transaction:
        """創建交易 (自動處理事務)"""
        transaction = self.transaction_repository.create(transaction_data)
        # 其他業務邏輯
        return transaction

    @transactional
    def process_payment(self, transaction_id: int) -> Transaction:
        """處理支付 (包含多個操作)"""
        transaction = self.transaction_repository.get_by_id(transaction_id)
        transaction.status = 'processing'
        # 更新餘額
        # 記錄日誌
        # 發送通知
        return transaction
```

### 4. 依賴注入 (Dependency Injection)

#### 4.1 DI Container
```python
# app/container.py
from dependency_injector import containers, providers
from app.repositories.implementations.user_repository_impl import UserRepositoryImpl
from app.services.implementations.user_service_impl import UserServiceImpl

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Database
    db = providers.Singleton(Database, db_url=config.db.url)

    # Repositories
    user_repository = providers.Factory(
        UserRepositoryImpl,
        session_factory=db.provided.session
    )

    transaction_repository = providers.Factory(
        TransactionRepositoryImpl,
        session_factory=db.provided.session
    )

    # Services
    user_service = providers.Factory(
        UserServiceImpl,
        user_repository=user_repository
    )

    auth_service = providers.Factory(
        AuthServiceImpl,
        user_repository=user_repository
    )

    transaction_service = providers.Factory(
        TransactionServiceImpl,
        transaction_repository=transaction_repository
    )
```

### 5. 測試架構

#### 5.1 單元測試 (Unit Tests)

##### 5.1.1 測試配置 (conftest.py)
```python
import pytest
from app import create_app
from app.extensions import db
from app.container import Container

@pytest.fixture(scope='session')
def app():
    """創建測試 Flask app"""
    app = create_app('testing')
    return app

@pytest.fixture(scope='session')
def _db(app):
    """創建測試數據庫"""
    db.app = app
    db.create_all()
    yield db
    db.drop_all()

@pytest.fixture(scope='function')
def session(_db):
    """創建數據庫 session"""
    connection = _db.engine.connect()
    transaction = connection.begin()
    session = _db.create_scoped_session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def mock_user_repository():
    """Mock User Repository"""
    from unittest.mock import Mock
    from app.repositories.interfaces.i_user_repository import IUserRepository

    mock_repo = Mock(spec=IUserRepository)
    return mock_repo

@pytest.fixture
def user_service(mock_user_repository):
    """創建 UserService (使用 Mock Repository)"""
    from app.services.implementations.user_service_impl import UserServiceImpl
    return UserServiceImpl(mock_user_repository)
```

##### 5.1.2 Service 單元測試範例
```python
# tests/unit/test_services/test_user_service.py
import pytest
from app.models.user import User

class TestUserService:
    def test_create_user_success(self, user_service, mock_user_repository):
        """測試創建用戶成功"""
        # Arrange
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        }
        expected_user = User(**user_data)
        mock_user_repository.create.return_value = expected_user

        # Act
        result = user_service.create_user(user_data)

        # Assert
        assert result.username == 'testuser'
        assert result.email == 'test@example.com'
        mock_user_repository.create.assert_called_once()

    def test_get_user_by_id_not_found(self, user_service, mock_user_repository):
        """測試獲取不存在的用戶"""
        # Arrange
        mock_user_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(UserNotFoundException):
            user_service.get_user_by_id(999)
```

##### 5.1.3 Repository 單元測試範例
```python
# tests/unit/test_repositories/test_user_repository.py
import pytest
from app.models.user import User

class TestUserRepository:
    def test_create_user(self, user_repository, session):
        """測試創建用戶"""
        # Arrange
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com'
        }

        # Act
        user = user_repository.create(user_data)
        session.flush()

        # Assert
        assert user.id is not None
        assert user.username == 'testuser'

    def test_find_by_email(self, user_repository, session):
        """測試通過郵箱查找用戶"""
        # Arrange
        user = User(username='test', email='test@example.com')
        session.add(user)
        session.flush()

        # Act
        found_user = user_repository.find_by_email('test@example.com')

        # Assert
        assert found_user is not None
        assert found_user.email == 'test@example.com'
```

#### 5.2 整合測試 (Integration Tests)

##### 5.2.1 API 整合測試範例
```python
# tests/integration/test_api/test_user_api.py
import pytest
import json

class TestUserAPI:
    def test_create_user_api(self, client, auth_headers):
        """測試用戶創建 API"""
        # Arrange
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'Password123!'
        }

        # Act
        response = client.post(
            '/api/v1/users',
            data=json.dumps(user_data),
            headers=auth_headers,
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['username'] == 'newuser'

    def test_get_user_unauthorized(self, client):
        """測試未授權訪問"""
        # Act
        response = client.get('/api/v1/users/1')

        # Assert
        assert response.status_code == 401

    def test_get_user_with_token(self, client, auth_token):
        """測試使用 Token 獲取用戶"""
        # Act
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = client.get('/api/v1/users/1', headers=headers)

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
```

##### 5.2.2 數據庫整合測試
```python
# tests/integration/test_database/test_models.py
import pytest
from app.models.user import User
from app.models.transaction import Transaction

class TestModels:
    def test_user_transaction_relationship(self, session):
        """測試用戶與交易的關聯關係"""
        # Arrange
        user = User(username='test', email='test@example.com')
        session.add(user)
        session.flush()

        transaction = Transaction(
            user_id=user.id,
            amount=100.0,
            type='payment'
        )
        session.add(transaction)
        session.flush()

        # Act
        retrieved_user = session.query(User).get(user.id)

        # Assert
        assert len(retrieved_user.transactions) == 1
        assert retrieved_user.transactions[0].amount == 100.0
```

##### 5.2.3 Celery 任務測試
```python
# tests/integration/test_tasks/test_celery_tasks.py
import pytest
from app.tasks.scheduled_tasks import cleanup_expired_tokens

class TestCeleryTasks:
    def test_cleanup_expired_tokens(self, session):
        """測試清理過期 Token 任務"""
        # Arrange
        # 創建過期 token

        # Act
        result = cleanup_expired_tokens.apply()

        # Assert
        assert result.successful()
```

#### 5.3 測試工具與 Fixtures

##### 5.3.1 常用 Fixtures
```python
# tests/conftest.py
@pytest.fixture
def client(app):
    """測試客戶端"""
    return app.test_client()

@pytest.fixture
def auth_token(client):
    """生成測試用 Token"""
    response = client.post('/api/v1/oauth/token', json={
        'username': 'admin',
        'password': 'admin123',
        'grant_type': 'password'
    })
    data = json.loads(response.data)
    return data['access_token']

@pytest.fixture
def auth_headers(auth_token):
    """認證 Headers"""
    return {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }
```

##### 5.3.2 測試數據工廠
```python
# tests/fixtures/user_fixtures.py
import factory
from app.models.user import User

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = 'commit'

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')
```

#### 5.4 測試命令與配置

##### 5.4.1 pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

##### 5.4.2 .coveragerc
```ini
[run]
source = app
omit =
    */tests/*
    */migrations/*
    */venv/*
    */__pycache__/*

[report]
precision = 2
show_missing = True
skip_covered = False
```

##### 5.4.3 測試命令
```bash
# 執行所有測試
pytest

# 只執行單元測試
pytest tests/unit -m unit

# 只執行整合測試
pytest tests/integration -m integration

# 生成覆蓋率報告
pytest --cov=app --cov-report=html

# 平行執行測試 (需要 pytest-xdist)
pytest -n auto

# 只執行失敗的測試
pytest --lf

# 詳細輸出
pytest -v -s
```

### 6. Docker 化要求

#### 6.1 多階段構建 Dockerfile
```dockerfile
# 建置階段
FROM python:3.14-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 運行階段
FROM python:3.14-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV FLASK_APP=wsgi.py

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "wsgi:app"]
```

#### 6.2 測試環境 Dockerfile
```dockerfile
FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY . .

CMD ["pytest", "-v", "--cov=app"]
```

#### 6.3 分散式 Docker Compose 配置

##### 6.3.1 微服務架構 Docker Compose (推薦)
```yaml
version: '3.8'

services:
  # ==================== Controller 層 ====================
  api-gateway-1:
    build:
      context: .
      dockerfile: docker/Dockerfile.controller
    ports:
      - "5000:5000"
    environment:
      - DEPLOYMENT_LAYER=controller
      - USER_SERVICE_URLS=http://user-service-1:5001,http://user-service-2:5001
      - AUTH_SERVICE_URLS=http://auth-service-1:5003,http://auth-service-2:5003
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    deploy:
      replicas: 2  # Controller 層多實例

  api-gateway-2:
    build:
      context: .
      dockerfile: docker/Dockerfile.controller
    ports:
      - "5010:5000"
    environment:
      - DEPLOYMENT_LAYER=controller
      - USER_SERVICE_URLS=http://user-service-1:5001,http://user-service-2:5001
      - AUTH_SERVICE_URLS=http://auth-service-1:5003,http://auth-service-2:5003
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  # ==================== Service 層 (User Service) ====================
  user-service-1:
    build:
      context: .
      dockerfile: docker/Dockerfile.service
    ports:
      - "5001:5001"
    environment:
      - DEPLOYMENT_LAYER=service
      - SERVICE_NAME=user-service
      - SERVICE_PORT=5001
      - USER_REPO_URLS=http://user-repo-1:5002,http://user-repo-2:5002
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - user-repo-1
      - user-repo-2

  user-service-2:
    build:
      context: .
      dockerfile: docker/Dockerfile.service
    ports:
      - "5011:5001"
    environment:
      - DEPLOYMENT_LAYER=service
      - SERVICE_NAME=user-service
      - SERVICE_PORT=5001
      - USER_REPO_URLS=http://user-repo-1:5002,http://user-repo-2:5002
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - user-repo-1
      - user-repo-2

  # ==================== Service 層 (Auth Service) ====================
  auth-service-1:
    build:
      context: .
      dockerfile: docker/Dockerfile.service
    ports:
      - "5003:5003"
    environment:
      - DEPLOYMENT_LAYER=service
      - SERVICE_NAME=auth-service
      - SERVICE_PORT=5003
      - USER_REPO_URLS=http://user-repo-1:5002,http://user-repo-2:5002
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  auth-service-2:
    build:
      context: .
      dockerfile: docker/Dockerfile.service
    ports:
      - "5013:5003"
    environment:
      - DEPLOYMENT_LAYER=service
      - SERVICE_NAME=auth-service
      - SERVICE_PORT=5003
      - USER_REPO_URLS=http://user-repo-1:5002,http://user-repo-2:5002
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  # ==================== Repository 層 ====================
  user-repo-1:
    build:
      context: .
      dockerfile: docker/Dockerfile.repository
    ports:
      - "5002:5002"
    environment:
      - DEPLOYMENT_LAYER=repository
      - REPOSITORY_NAME=user-repository
      - REPOSITORY_PORT=5002
      - DATABASE_URL=mysql+pymysql://user:pass@mysql:3306/db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - mysql
      - redis

  user-repo-2:
    build:
      context: .
      dockerfile: docker/Dockerfile.repository
    ports:
      - "5012:5002"
    environment:
      - DEPLOYMENT_LAYER=repository
      - REPOSITORY_NAME=user-repository
      - REPOSITORY_PORT=5002
      - DATABASE_URL=mysql+pymysql://user:pass@mysql:3306/db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - mysql
      - redis

  transaction-repo-1:
    build:
      context: .
      dockerfile: docker/Dockerfile.repository
    ports:
      - "5004:5004"
    environment:
      - DEPLOYMENT_LAYER=repository
      - REPOSITORY_NAME=transaction-repository
      - REPOSITORY_PORT=5004
      - DATABASE_URL=mysql+pymysql://user:pass@mysql:3306/db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - mysql
      - redis

  # ==================== Celery Workers ====================
  celery-worker:
    build: .
    command: celery -A celery_worker.celery worker --loglevel=info
    environment:
      - DATABASE_URL=mysql+pymysql://user:pass@mysql:3306/db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - mysql
    deploy:
      replicas: 3

  celery-beat:
    build: .
    command: celery -A celery_worker.celery beat --loglevel=info
    environment:
      - DATABASE_URL=mysql+pymysql://user:pass@mysql:3306/db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  # ==================== 共享服務 ====================
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  mysql:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: db
      MYSQL_USER: user
      MYSQL_PASSWORD: pass
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql

  # ==================== 負載平衡器 ====================
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api-gateway-1
      - api-gateway-2

volumes:
  mysql-data:
```

##### 6.3.2 Nginx 負載平衡配置
```nginx
# nginx/nginx.conf
upstream api_gateway {
    least_conn;  # 最少連接負載平衡
    server api-gateway-1:5000 max_fails=3 fail_timeout=30s;
    server api-gateway-2:5000 max_fails=3 fail_timeout=30s;
}

upstream user_service {
    least_conn;
    server user-service-1:5001 max_fails=3 fail_timeout=30s;
    server user-service-2:5001 max_fails=3 fail_timeout=30s;
}

upstream auth_service {
    least_conn;
    server auth-service-1:5003 max_fails=3 fail_timeout=30s;
    server auth-service-2:5003 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;

    # API Gateway (對外)
    location /api/ {
        proxy_pass http://api_gateway;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 健康檢查
        proxy_next_upstream error timeout http_502 http_503 http_504;
    }

    # 健康檢查端點
    location /health {
        proxy_pass http://api_gateway/health;
    }
}
```

#### 6.4 測試環境 Docker Compose
```yaml
# docker-compose.test.yml
version: '3.8'

services:
  test:
    build:
      context: .
      dockerfile: docker/Dockerfile.test
    environment:
      - DATABASE_URL=mysql+pymysql://root:testpass@mysql-test:3306/test_db
      - REDIS_URL=redis://redis-test:6379/0
    depends_on:
      - mysql-test
      - redis-test

  mysql-test:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: testpass
      MYSQL_DATABASE: test_db

  redis-test:
    image: redis:7-alpine
```

### 7. Kubernetes 分散式部署配置

#### 7.1 Controller 層 Deployment
```yaml
# k8s/controller-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  labels:
    app: api-gateway
    tier: controller
spec:
  replicas: 3  # Controller 層 3 個實例
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
        tier: controller
    spec:
      containers:
      - name: api-gateway
        image: your-registry/flask-api-gateway:latest
        ports:
        - containerPort: 5000
        env:
        - name: DEPLOYMENT_LAYER
          value: "controller"
        - name: USER_SERVICE_URLS
          value: "http://user-service:5001"
        - name: AUTH_SERVICE_URLS
          value: "http://auth-service:5003"
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis_url
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 5000
  selector:
    app: api-gateway
```

#### 7.2 Service 層 Deployment (User Service)
```yaml
# k8s/user-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  labels:
    app: user-service
    tier: service
spec:
  replicas: 4  # Service 層 4 個實例
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
        tier: service
    spec:
      containers:
      - name: user-service
        image: your-registry/flask-user-service:latest
        ports:
        - containerPort: 5001
        env:
        - name: DEPLOYMENT_LAYER
          value: "service"
        - name: SERVICE_NAME
          value: "user-service"
        - name: SERVICE_PORT
          value: "5001"
        - name: USER_REPO_URLS
          value: "http://user-repository:5002"
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis_url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  type: ClusterIP  # 內部服務
  ports:
  - port: 5001
    targetPort: 5001
  selector:
    app: user-service
```

#### 7.3 Repository 層 Deployment
```yaml
# k8s/user-repository-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-repository
  labels:
    app: user-repository
    tier: repository
spec:
  replicas: 3  # Repository 層 3 個實例
  selector:
    matchLabels:
      app: user-repository
  template:
    metadata:
      labels:
        app: user-repository
        tier: repository
    spec:
      containers:
      - name: user-repository
        image: your-registry/flask-user-repository:latest
        ports:
        - containerPort: 5002
        env:
        - name: DEPLOYMENT_LAYER
          value: "repository"
        - name: REPOSITORY_NAME
          value: "user-repository"
        - name: REPOSITORY_PORT
          value: "5002"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis_url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: user-repository
spec:
  type: ClusterIP  # 內部服務
  ports:
  - port: 5002
    targetPort: 5002
  selector:
    app: user-repository
```

#### 7.4 HPA (自動擴展) - 各層獨立配置
```yaml
# k8s/controller-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
---
# k8s/service-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: user-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: user-service
  minReplicas: 4
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
---
# k8s/repository-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: user-repository-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: user-repository
  minReplicas: 3
  maxReplicas: 15
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### 7.5 部署架構圖
```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
│                   (K8s Ingress/LB)                      │
└────────────────────┬────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
│Controller │  │Controller│  │Controller│  ← 3-10 Pods (HPA)
│  Pod 1    │  │  Pod 2   │  │  Pod 3   │
└─────┬─────┘  └────┬─────┘  └────┬─────┘
      │              │              │
      └──────────────┼──────────────┘
                     │ K8s Service (ClusterIP)
      ┌──────────────┼───────────────────┐
      │              │                   │
┌─────▼─────┐  ┌────▼─────┐  ...  ┌────▼─────┐
│ Service   │  │ Service  │       │ Service  │  ← 4-20 Pods (HPA)
│  Pod 1    │  │  Pod 2   │       │  Pod N   │
└─────┬─────┘  └────┬─────┘       └────┬─────┘
      │              │                   │
      └──────────────┼───────────────────┘
                     │ K8s Service (ClusterIP)
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
│Repository │  │Repository│  │Repository│  ← 3-15 Pods (HPA)
│  Pod 1    │  │  Pod 2   │  │  Pod 3   │
└─────┬─────┘  └────┬─────┘  └────┬─────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
              ┌──────▼──────┐
              │  Database   │
              │  (MySQL)    │
              └─────────────┘
```

### 8. API 設計規範

#### 8.1 RESTful 端點
```
# 認證
POST   /api/v1/oauth/token          # 取得 Token
POST   /api/v1/oauth/revoke         # 撤銷 Token
POST   /api/v1/oauth/refresh        # 刷新 Token

# 用戶管理
GET    /api/v1/users                # 取得使用者列表
POST   /api/v1/users                # 建立使用者
GET    /api/v1/users/{id}           # 取得單一使用者
PUT    /api/v1/users/{id}           # 更新使用者
DELETE /api/v1/users/{id}           # 刪除使用者

# 交易
POST   /api/v1/transactions         # 建立交易
GET    /api/v1/transactions/{id}    # 查詢交易
GET    /api/v1/transactions         # 查詢交易列表

# 健康檢查
GET    /health                      # 存活檢查
GET    /ready                       # 就緒檢查
```

#### 8.2 標準響應格式
```json
{
  "success": true,
  "data": {},
  "message": "Operation successful",
  "timestamp": "2025-11-19T10:30:00Z",
  "request_id": "uuid"
}
```

### 9. 依賴套件清單

#### 9.1 requirements.txt
```
# Python 3.14.0 compatible packages (最新版)

# Flask 框架與擴展
Flask==3.1.0
Flask-RESTful==0.3.10
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.7
Flask-RESTX==1.3.0
flask-marshmallow==1.2.1
flask-cors==5.0.0
flask-limiter==3.8.0

# 資料庫與 ORM
SQLAlchemy==2.0.35
alembic==1.13.3
PyMySQL==1.1.1

# 數據驗證與序列化
marshmallow==3.23.1

# 認證與安全
authlib==1.3.2
PyJWT==2.10.1
cryptography==44.0.0

# Redis 與快取
redis==5.2.0
redis-py-cluster==2.1.3

# Celery 任務佇列（含分散式支援）
celery==5.4.0
celery-redbeat==2.2.0  # Redis-backed Celery Beat Scheduler (分散式定時任務)
flower==2.0.1

# 依賴注入
dependency-injector==4.42.0

# WSGI 服務器
gunicorn==23.0.0

# 工具與輔助
python-dotenv==1.0.1
requests==2.32.3
python-json-logger==3.2.1  # 結構化日誌

# 服務間通訊（可選）
grpcio==1.68.1  # gRPC 支援
grpcio-tools==1.68.1
```

#### 9.2 requirements-dev.txt
```
# Testing & Development tools (最新版)
pytest==8.3.4
pytest-cov==6.0.0
pytest-mock==3.14.0
pytest-xdist==3.6.1
pytest-flask==1.3.0
pytest-asyncio==0.24.0
factory-boy==3.3.1
faker==33.1.0
black==24.10.0
flake8==7.1.1
mypy==1.13.0
coverage==7.6.9
ruff==0.8.4
bandit==1.8.0
safety==3.2.11
```

### 10. 執行命令

```bash
# 開發環境
docker-compose up -d

# 執行測試
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
# 或本地執行
pytest

# 單元測試
pytest tests/unit -m unit

# 整合測試
pytest tests/integration -m integration

# 覆蓋率報告
pytest --cov=app --cov-report=html

# 生產環境
docker-compose -f docker-compose.prod.yml up -d

# Kubernetes 部署
kubectl apply -f k8s/

# 資料庫遷移
flask db upgrade

# Celery Worker
celery -A celery_worker.celery worker --loglevel=info

# Celery Beat
celery -A celery_worker.celery beat --loglevel=info

# Flower (Celery 監控)
celery -A celery_worker.celery flower
```

## 11. Python 3.14 新特性應用

請在專案中充分利用 Python 3.14 的新特性：

### 11.1 性能改進
- 利用 JIT 編譯器加速執行（如果可用）
- 優化的字典和列表操作
- 改進的垃圾回收機制

### 11.2 語法增強
- 使用最新的 Type Hints 語法
- Pattern Matching 優化（match-case）
- 新的標準庫功能

### 11.3 異步支援
```python
# 使用最新的 async/await 特性
from typing import AsyncIterator

async def stream_data() -> AsyncIterator[dict]:
    """使用 async generator 處理大量數據"""
    async for item in fetch_data():
        yield process(item)
```

### 11.4 Type Hints 強化
```python
from typing import Self, TypedDict, Required, NotRequired

class UserDict(TypedDict):
    id: Required[int]
    username: Required[str]
    email: NotRequired[str]

class BaseModel:
    def update(self, **kwargs) -> Self:
        """返回 Self 類型"""
        return self
```

## 實作要求總結

請按照以上規範實作完整的專案，確保：

### 核心架構要求
1. **使用 Python 3.14.0 及所有依賴套件的最新穩定版本**
2. **所有服務層和資料存取層使用 Interface-Implementation 模式**
3. **所有 API 端點使用 Annotation 方式進行認證和權限驗證**
4. **完整的單元測試和整合測試，覆蓋率 > 80%**

### 分散式架構要求 ⭐
5. **各層可獨立部署為微服務**:
   - Controller 層可部署多個實例，調用不同的 Service 實例
   - Service 層可部署在不同的 Docker Container 或 K8s Pod
   - **Service 層支援細粒度拆分**：單一服務（如 UserService）可拆分為多個獨立微服務（UserAuthService、UserProfileService、UserPermissionService 等），各自部署在不同 Docker/K8s
   - Repository/DAO 層可分散至不同的 K8s Pod 或 Docker 中
   - 每層支援獨立水平擴展

6. **服務間通訊**:
   - 實現 ServiceClient 和 RepositoryClient 用於跨實例調用
   - 支援服務發現機制（K8s Service、環境變數配置）
   - 實現負載平衡（Round-Robin、Least Connection）
   - 支援 HTTP/REST 或 gRPC 通訊協議
   - Controller 可並行調用多個細粒度微服務並聚合結果

7. **容器化與編排**:
   - 提供各層獨立的 Dockerfile（controller、service、repository）
   - 提供細粒度微服務的獨立 Dockerfile（user-auth、user-profile、user-permission 等）
   - Docker Compose 配置支援微服務架構部署
   - Kubernetes 配置包含各層的 Deployment、Service、HPA
   - 支援 Nginx 負載平衡器配置

### 分散式任務系統要求 ⭐⭐
8. **Celery 分散式 Job 管理**:
   - Celery Beat 單實例部署（replicas=1），使用 RedBeat 支援分散式排程
   - Celery Worker 多實例部署，可分散在不同 Docker/K8s
   - **實現分散式鎖機制**：使用 Redis 鎖確保同一定時任務只能由一個 Worker 執行
   - 定時任務使用 `@single_instance_task` 裝飾器防止重複執行
   - 背景任務可並行執行，無需鎖機制
   - 支援任務重試、優先級、超時控制
   - 使用 Flower 監控所有 Worker 狀態

### 其他核心功能
9. **資料庫自動遷移** (Alembic)
10. **分散式無狀態設計** (Redis Session、Token 共享)
11. **完整的交易管理** (@transactional 裝飾器)
12. **依賴注入容器管理**
13. **完整的錯誤處理和日誌記錄**
14. **利用 Python 3.14 的新特性提升性能和代碼品質**

### 代碼品質要求
所有代碼必須：
- 遵循 PEP 8 規範
- 使用 Python 3.14 的 Type Hints 新語法
- 包含完整的 docstrings
- 相容 Python 3.14.0 運行環境
- 支援單體和微服務兩種部署模式
