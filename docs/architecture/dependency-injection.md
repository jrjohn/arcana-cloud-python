# 依賴注入 (Dependency Injection) 實現說明

## 概述

本專案已完全實現**依賴注入 (Dependency Injection, DI)** 模式，解決了之前硬編碼依賴和每次創建新實例的問題。

---

## 依賴注入的優勢

### ✅ 解決的問題

1. **解耦合 (Loose Coupling)**
   - Controller 不再直接依賴具體的 Service 或 Repository 實現
   - 可以輕鬆替換不同的實現（如測試時使用 Mock）

2. **統一管理依賴**
   - 所有依賴在 DI Container 中集中管理
   - 實例的生命週期由容器控制（Singleton vs Transient）

3. **避免重複創建實例**
   - Singleton 模式確保同一個實例被重用
   - 減少記憶體消耗和初始化開銷

4. **易於測試 (Testability)**
   - 可以輕鬆注入 Mock/Stub 進行單元測試
   - 不需要修改業務代碼即可替換依賴

5. **符合 SOLID 原則**
   - **依賴倒置原則 (Dependency Inversion Principle)**：高層模組不依賴低層模組，都依賴抽象
   - **單一職責原則 (Single Responsibility Principle)**：依賴創建與業務邏輯分離

---

## 架構設計

### 依賴注入容器 (DI Container)

位置：`app/di_container.py`

```python
class DIContainer:
    """
    簡單的依賴注入容器

    支援：
    - Singleton instances (創建一次，重複使用)
    - Factory functions (每次創建新實例)
    - Lazy initialization (延遲初始化)
    """

    def register_singleton(self, name: str, factory: Callable):
        """註冊單例依賴"""

    def register_transient(self, name: str, factory: Callable):
        """註冊暫態依賴（每次創建新實例）"""

    def register_instance(self, name: str, instance: Any):
        """註冊已存在的實例"""

    def get(self, name: str) -> Any:
        """獲取依賴實例"""
```

---

## 依賴層次結構

```
┌─────────────────────────────────────────────────────────┐
│                   DI Container                          │
│  (app/di_container.py)                                  │
│                                                          │
│  管理所有依賴的生命週期：                                │
│  - db_session (Database Session)                        │
│  - user_repository (UserRepositoryImpl)                 │
│  - oauth_token_repository (OAuthTokenRepositoryImpl)    │
│  - user_service (UserServiceImpl)                       │
│  - auth_service (AuthServiceImpl)                       │
│  - service_communication (ServiceCommunicationInterface)│
│  - repository_communication (RepositoryCommunication)   │
└─────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  Controller  │   │   Service    │   │  Repository  │
    │              │   │              │   │              │
    │ 注入:        │   │ 注入:        │   │ 注入:        │
    │ service_comm │   │ repository   │   │ db_session   │
    └──────────────┘   └──────────────┘   └──────────────┘
```

---

## 已實現的依賴注入

### 1. Controller Layer

**之前的問題：**
```python
# ❌ 每次都創建新實例，浪費資源
def get_service_communication():
    return CommunicationFactory.create_service_communication()

@user_bp.route('', methods=['GET'])
def get_users():
    service_comm = get_service_communication()  # 每次都是新實例
```

**現在的解決方案：**
```python
# ✅ 從 DI Container 獲取 Singleton 實例
from app.di_container import get_service_communication

@user_bp.route('', methods=['GET'])
def get_users():
    service_comm = get_service_communication()  # 重用同一個實例
```

**已更新的 Controllers：**
- ✅ `app/controllers/UserController.py`
- ✅ `app/controllers/PublicUserController.py`
- ✅ `app/controllers/AuthController.py`

---

### 2. Communication Factory

**之前的問題：**
```python
# ❌ Factory 內部直接創建依賴，違反 DI 原則
@classmethod
def create_service_communication(cls):
    # 硬編碼創建依賴
    from app.services.implementations.UserServiceImpl import UserServiceImpl
    from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
    from app.Extensions import db

    user_repo = UserRepositoryImpl(db.session)
    user_service = UserServiceImpl(user_repo)
    return DirectServiceCommunication(user_service)
```

**現在的解決方案：**
```python
# ✅ 支援依賴注入，但保留向後兼容性
@classmethod
def create_service_communication(cls, service_instance=None):
    if not use_remote:
        if service_instance is None:
            # Legacy behavior: 向後兼容
            from app.services.implementations.UserServiceImpl import UserServiceImpl
            from app.repositories.implementations.UserRepositoryImpl import UserRepositoryImpl
            from app.Extensions import db

            user_repo = UserRepositoryImpl(db.session)
            service_instance = UserServiceImpl(user_repo)

        # ✅ 使用注入的實例
        return DirectServiceCommunication(service_instance)
```

**已更新的文件：**
- ✅ `app/communication/factory.py`

---

### 3. Application Initialization

**Application Factory 初始化 DI Container：**

位置：`app/__init__.py`

```python
def create_app(config_name: str = 'development') -> Flask:
    app = Flask(__name__)

    # ... 其他初始化 ...

    # ✅ 初始化新的 DI Container
    with app.app_context():
        from app.di_container import initialize_dependencies
        initialize_dependencies(app)

    # 註冊 blueprints
    register_blueprints(app)

    return app
```

**DI Container 初始化邏輯：**

位置：`app/di_container.py`

```python
def initialize_dependencies(app: Flask):
    """
    初始化應用依賴

    註冊所有依賴到 DI Container
    應在應用啟動時調用一次
    """
    container = get_container()

    # 註冊 database session
    container.register_instance('db_session', db.session)

    # 註冊 repositories (Singleton)
    container.register_singleton('user_repository', create_user_repository)
    container.register_singleton('oauth_token_repository', create_oauth_token_repository)

    # 註冊 services (Singleton)
    container.register_singleton('user_service', create_user_service)
    container.register_singleton('auth_service', create_auth_service)

    # 註冊 communication layer (Singleton)
    container.register_singleton('service_communication', create_service_communication)
    container.register_singleton('repository_communication', create_repository_communication)
```

---

## 使用方式

### 在 Controller 中使用

```python
# UserController.py
from app.di_container import get_service_communication

@user_bp.route('', methods=['GET'])
@token_required
def get_users():
    # ✅ 從 DI Container 獲取單例實例
    service_comm = get_service_communication()

    # 使用 communication layer
    result = service_comm.get_users(page=1, per_page=20)
    return success_response(data=result)
```

### 在 Service 中使用（如果需要）

```python
from app.di_container import get_user_repository

class UserServiceImpl:
    def __init__(self):
        # ✅ 從 DI Container 獲取 repository
        self.user_repo = get_user_repository()
```

### 在測試中使用

```python
from app.di_container import get_container

def test_user_creation():
    container = get_container()

    # ✅ 注入 Mock Repository
    mock_repo = MagicMock()
    container.register_instance('user_repository', mock_repo)

    # 測試代碼會使用 mock_repo
    service = container.get('user_service')
    service.createUser(...)

    # 驗證
    mock_repo.create.assert_called_once()
```

---

## 依賴生命週期

### Singleton (單例模式)

**特性：**
- 創建一次，全應用重用
- 適合無狀態的服務、Repository

**已註冊的 Singletons：**
- `user_repository`
- `oauth_token_repository`
- `user_service`
- `auth_service`
- `service_communication`
- `repository_communication`

### Transient (暫態模式)

**特性：**
- 每次請求都創建新實例
- 適合有狀態的物件

**註冊方式：**
```python
container.register_transient('some_service', factory_function)
```

---

## 依賴關係圖

```
db_session (Database Session)
    │
    ├──> user_repository (UserRepositoryImpl)
    │        │
    │        ├──> user_service (UserServiceImpl)
    │        │        │
    │        │        └──> service_communication (DirectServiceCommunication)
    │        │                  │
    │        │                  └──> UserController
    │        │
    │        └──> repository_communication (DirectRepositoryCommunication)
    │
    └──> oauth_token_repository (OAuthTokenRepositoryImpl)
             │
             └──> auth_service (AuthServiceImpl)
                      │
                      └──> AuthController
```

---

## SOLID 原則符合性

### 1. ✅ 單一職責原則 (Single Responsibility Principle)

- **Controller**：只負責處理 HTTP 請求/響應
- **Service**：只負責業務邏輯
- **Repository**：只負責資料庫操作
- **DI Container**：只負責管理依賴

### 2. ✅ 開閉原則 (Open/Closed Principle)

- 可以新增新的 Service 實現，無需修改 Controller
- 可以替換 Communication Layer 實現（Direct → HTTP → gRPC）

### 3. ✅ 里氏替換原則 (Liskov Substitution Principle)

- 所有 Service 實現都遵循 `ServiceCommunicationInterface`
- 可以無縫替換不同的實現

### 4. ✅ 介面隔離原則 (Interface Segregation Principle)

- `ServiceCommunicationInterface` 只定義必要的方法
- `RepositoryCommunicationInterface` 專注於 Repository 通信

### 5. ✅ 依賴倒置原則 (Dependency Inversion Principle)

- **高層模組 (Controller)** 不依賴低層模組 (Service 實現)
- **都依賴抽象** (`ServiceCommunicationInterface`)
- **抽象不依賴細節**，細節依賴抽象

---

## 對比：依賴注入前後

### 之前（❌ 硬編碼依賴）

```python
# UserController.py
def get_user_service():
    # ❌ 硬編碼創建依賴
    user_repo = UserRepositoryImpl(db.session)
    return UserServiceImpl(user_repo)

@user_bp.route('', methods=['GET'])
def get_users():
    service = get_user_service()  # 每次都創建新實例
```

**問題：**
1. Controller 直接依賴具體實現（UserServiceImpl, UserRepositoryImpl）
2. 每次請求都創建新實例，浪費資源
3. 難以測試（無法注入 Mock）
4. 違反依賴倒置原則

---

### 現在（✅ 依賴注入）

```python
# UserController.py
from app.di_container import get_service_communication

@user_bp.route('', methods=['GET'])
def get_users():
    # ✅ 從 DI Container 獲取單例
    service_comm = get_service_communication()
```

**優勢：**
1. Controller 只依賴抽象接口（ServiceCommunicationInterface）
2. 實例由 DI Container 管理，重用 Singleton
3. 易於測試（可以注入 Mock）
4. 符合 SOLID 原則

---

## 測試範例

### 單元測試：注入 Mock

```python
import unittest
from unittest.mock import MagicMock
from app.di_container import get_container

class TestUserController(unittest.TestCase):
    def setUp(self):
        # 清除容器
        container = get_container()
        container.clear()

        # 注入 Mock
        self.mock_service = MagicMock()
        container.register_instance('service_communication', self.mock_service)

    def test_get_users(self):
        # Mock 返回值
        self.mock_service.get_users.return_value = {
            'items': [{'id': 1, 'name': 'Test'}],
            'total': 1
        }

        # 測試 Controller
        from app.controllers.UserController import get_users
        result = get_users()

        # 驗證
        self.mock_service.get_users.assert_called_once()
```

---

## 環境變數配置

DI Container 會根據環境變數自動選擇適當的實現：

```bash
# Monolithic Mode
DEPLOYMENT_MODE=monolithic
DEPLOYMENT_LAYER=monolithic
# → DirectServiceCommunication (Singleton)

# Layered Mode with HTTP
DEPLOYMENT_MODE=layered
DEPLOYMENT_LAYER=controller
COMMUNICATION_PROTOCOL=http
USER_SERVICE_URLS=http://service-layer:5001
# → HTTPServiceCommunication

# Layered Mode with gRPC
DEPLOYMENT_MODE=layered
DEPLOYMENT_LAYER=controller
COMMUNICATION_PROTOCOL=grpc
USER_SERVICE_URLS=service-layer:50051
# → GRPCServiceCommunication
```

---

## 總結

### ✅ 已實現

1. **DI Container** ([di_container.py](../app/di_container.py))
   - Singleton 管理
   - Lazy Initialization
   - 統一的依賴獲取接口

2. **Controller 依賴注入**
   - UserController
   - PublicUserController
   - AuthController

3. **Factory 支援 DI**
   - CommunicationFactory 支援依賴注入
   - 保留向後兼容性

4. **Application 初始化**
   - 在 `create_app()` 中初始化 DI Container

### 🎯 優勢

1. **完全解耦** - Controller 不依賴具體實現
2. **易於測試** - 可以輕鬆注入 Mock
3. **資源優化** - Singleton 避免重複創建
4. **符合 SOLID** - 遵循所有 SOLID 原則
5. **靈活擴展** - 易於添加新的服務或實現

### 📚 參考資料

- [Dependency Injection in Python](https://python-dependency-injector.ets-labs.org/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Design Patterns: Dependency Injection](https://refactoring.guru/design-patterns/dependency-injection)
