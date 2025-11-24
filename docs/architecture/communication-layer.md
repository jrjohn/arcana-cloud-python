# Communication Layer Abstraction

## 概述

抽象化的通信層設計，支援 **Monolithic**、**Layered** 和 **Microservices** 三種部署模式，並可在打包時自動切換。Layered 和 Microservices 模式支援 **HTTP/REST** 和 **gRPC** 兩種通信協議。

## 設計模式

### 1. **Strategy Pattern (策略模式)**
不同的通信實現（Direct, HTTP, gRPC）作為不同的策略。

### 2. **Factory Pattern (工廠模式)**
`CommunicationFactory` 根據環境變數自動創建適當的通信實現。

### 3. **Adapter Pattern (適配器模式)**
統一的接口 `CommunicationInterface` 適配不同的底層實現。

---

## 架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Code                         │
│                  (Controller, Service)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Uses
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              CommunicationFactory (Factory)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Automatically selects implementation based on:       │  │
│  │  - DEPLOYMENT_MODE (monolithic/layered/microservices)│  │
│  │  - COMMUNICATION_PROTOCOL (http/grpc)                │  │
│  │  - DEPLOYMENT_LAYER (controller/service/repository)  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Creates
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          CommunicationInterface (Abstract Interface)         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Common Methods:                                      │  │
│  │  - call(method, **kwargs)                            │  │
│  │  - get_mode()                                         │  │
│  │  - get_protocol()                                     │  │
│  │  - health_check()                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└────┬──────────────────┬──────────────────┬─────────────────┘
     │                  │                  │
     │ Direct           │ HTTP             │ gRPC
     ▼                  ▼                  ▼
┌─────────┐      ┌──────────┐      ┌──────────┐
│ Direct  │      │   HTTP   │      │   gRPC   │
│ Impl    │      │   Impl   │      │   Impl   │
│         │      │          │      │          │
│ (In     │      │ (requests│      │ (grpcio) │
│ process)│      │  library)│      │          │
└─────────┘      └──────────┘      └──────────┘
```

---

## 通信模式決策矩陣

| Deployment Mode | Protocol | Current Layer | Controller→Service | Service→Repository |
|----------------|----------|---------------|-------------------|-------------------|
| **Monolithic** | direct   | any           | Direct            | Direct            |
| **Layered**    | http     | controller    | **HTTP**          | Direct            |
|                |          | service       | Direct            | Direct            |
| **Layered**    | **grpc** | controller    | **gRPC**          | Direct            |
|                |          | service       | Direct            | Direct            |
| **Microservices** | http  | any           | **HTTP**          | **HTTP**          |
| **Microservices** | **grpc** | any        | **gRPC**          | **gRPC**          |

---

## 文件結構

```
app/communication/
├── __init__.py                          # Package exports
├── interfaces.py                        # Abstract interfaces
├── factory.py                           # Factory for creating implementations
└── implementations/
    ├── __init__.py
    ├── direct.py                        # Direct in-process communication
    ├── http_rest.py                     # HTTP/REST implementation
    └── grpc_impl.py                     # gRPC implementation
```

---

## 使用方式

### 1. Monolithic Mode (單體模式)

```bash
# Environment Variables
export DEPLOYMENT_MODE=monolithic
export DEPLOYMENT_LAYER=monolithic
```

```python
# Controller Code
from app.communication import CommunicationFactory

# Factory automatically creates DirectServiceCommunication
service_comm = CommunicationFactory.create_service_communication()

# Direct in-process call
result = service_comm.get_user_by_id(user_id=1)
# → Calls UserServiceImpl.getUserById(1) directly
```

**Flow**:
```
Controller → DirectServiceCommunication → UserServiceImpl → Repository → DB
(All in same process, direct method calls)
```

---

### 2. Layered Mode with HTTP

```bash
# Controller Container
export DEPLOYMENT_MODE=layered
export DEPLOYMENT_LAYER=controller
export COMMUNICATION_PROTOCOL=http
export USER_SERVICE_URLS=http://service-layer:5001
```

```python
# Controller Code
from app.communication import CommunicationFactory

# Factory automatically creates HTTPServiceCommunication
service_comm = CommunicationFactory.create_service_communication()

# HTTP POST to service layer
result = service_comm.get_user_by_id(user_id=1)
# → HTTP GET http://service-layer:5001/internal/users/1
```

**Flow**:
```
Controller Container:
  UserController → HTTPServiceCommunication
      ↓ HTTP GET http://service-layer:5001/internal/users/1
──────────────────────────────────────────────────────────
Service Container:
  UserServiceRoutes → UserServiceImpl → Repository → DB
```

---

### 3. Layered Mode with gRPC

```bash
# Controller Container
export DEPLOYMENT_MODE=layered
export DEPLOYMENT_LAYER=controller
export COMMUNICATION_PROTOCOL=grpc
export USER_SERVICE_URLS=service-layer:50051
```

```python
# Controller Code
from app.communication import CommunicationFactory

# Factory automatically creates GRPCServiceCommunication
service_comm = CommunicationFactory.create_service_communication()

# gRPC call to service layer
result = service_comm.get_user_by_id(user_id=1)
# → gRPC call to service-layer:50051
```

**Flow**:
```
Controller Container:
  UserController → GRPCServiceCommunication
      ↓ gRPC call to service-layer:50051 (GetUser RPC)
──────────────────────────────────────────────────────────
Service Container:
  gRPC Server → UserServiceImpl → Repository → DB
```

**Note**: gRPC 需要先定義 `.proto` 文件並生成 Python stubs。

---

### 4. Microservices Mode with gRPC

```bash
# User Service Container
export DEPLOYMENT_MODE=microservices
export DEPLOYMENT_LAYER=service
export COMMUNICATION_PROTOCOL=grpc
export USER_REPO_URLS=user-repository:50052
```

```python
# Service Code
from app.communication import CommunicationFactory

# Factory creates GRPCRepositoryCommunication
repo_comm = CommunicationFactory.create_repository_communication()

# gRPC call to repository service
result = repo_comm.get_by_id(entity='user', entity_id=1)
# → gRPC call to user-repository:50052
```

**Flow**:
```
User Service Container:
  UserServiceImpl → GRPCRepositoryCommunication
      ↓ gRPC call to user-repository:50052
──────────────────────────────────────────────────────────
User Repository Service Container:
  gRPC Server → UserRepositoryImpl → DB
```

---

## 配置環境變數

### 必需的環境變數

| Variable | Values | Description |
|----------|--------|-------------|
| `DEPLOYMENT_MODE` | `monolithic`, `layered`, `microservices` | 部署模式 |
| `DEPLOYMENT_LAYER` | `monolithic`, `controller`, `service`, `repository` | 當前層 |

### 可選的環境變數

| Variable | Values | Description |
|----------|--------|-------------|
| `COMMUNICATION_PROTOCOL` | `http`, `grpc` | 通信協議（默認：layered=http, microservices=http） |
| `USER_SERVICE_URLS` | `http://host:port` or `host:port` | Service 層 URL（HTTP 或 gRPC） |
| `USER_REPO_URLS` | `http://host:port` or `host:port` | Repository 層 URL（HTTP 或 gRPC） |

---

## 範例配置

### Monolithic Mode

```yaml
# docker-compose.yml
services:
  app:
    environment:
      - DEPLOYMENT_MODE=monolithic
      - DEPLOYMENT_LAYER=monolithic
```

### Layered Mode with HTTP

```yaml
# docker-compose.yml
services:
  controller-layer:
    environment:
      - DEPLOYMENT_MODE=layered
      - DEPLOYMENT_LAYER=controller
      - COMMUNICATION_PROTOCOL=http
      - USER_SERVICE_URLS=http://service-layer:5001

  service-layer:
    environment:
      - DEPLOYMENT_MODE=layered
      - DEPLOYMENT_LAYER=service
      - USER_REPO_URLS=http://repository-layer:5002
```

### Layered Mode with gRPC

```yaml
# docker-compose.yml
services:
  controller-layer:
    environment:
      - DEPLOYMENT_MODE=layered
      - DEPLOYMENT_LAYER=controller
      - COMMUNICATION_PROTOCOL=grpc
      - USER_SERVICE_URLS=service-layer:50051  # gRPC port

  service-layer:
    environment:
      - DEPLOYMENT_MODE=layered
      - DEPLOYMENT_LAYER=service
      - COMMUNICATION_PROTOCOL=grpc
      # Service still uses direct repository access in layered mode
```

### Microservices Mode with gRPC

```yaml
# docker-compose.yml
services:
  user-service:
    environment:
      - DEPLOYMENT_MODE=microservices
      - DEPLOYMENT_LAYER=service
      - COMMUNICATION_PROTOCOL=grpc
      - USER_REPO_URLS=user-repository:50052

  user-repository:
    environment:
      - DEPLOYMENT_MODE=microservices
      - DEPLOYMENT_LAYER=repository
```

---

## 實現細節

### DirectServiceCommunication (Direct)

```python
class DirectServiceCommunication(ServiceCommunicationInterface):
    def __init__(self, service_instance):
        self.service = service_instance  # UserServiceImpl

    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        # Direct method call (no network)
        user = self.service.getUserById(user_id)
        return user.toDict()
```

### HTTPServiceCommunication (HTTP/REST)

```python
class HTTPServiceCommunication(ServiceCommunicationInterface):
    def __init__(self, service_urls: list, deployment_mode: DeploymentMode):
        self.service_urls = service_urls
        self.session = requests.Session()  # Connection pooling

    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        # HTTP GET request
        url = f"{self.service_urls[0]}/internal/users/{user_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()['data']
```

### GRPCServiceCommunication (gRPC)

```python
class GRPCServiceCommunication(ServiceCommunicationInterface):
    def __init__(self, service_urls: list, deployment_mode: DeploymentMode):
        self.channels = {}
        for url in service_urls:
            channel = grpc.insecure_channel(url)
            self.channels[url] = channel
            # self.stubs[url] = user_service_pb2_grpc.UserServiceStub(channel)

    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        # gRPC call
        # request = user_service_pb2.GetUserRequest(user_id=user_id)
        # response = stub.GetUser(request)
        # return MessageToDict(response)
        raise NotImplementedError("gRPC requires protobuf definitions")
```

---

## 查看當前配置

```python
from app.communication import CommunicationFactory

# Get current communication configuration
info = CommunicationFactory.get_communication_info()
print(info)

# Output:
# {
#     'deployment_mode': 'layered',
#     'deployment_layer': 'controller',
#     'communication_protocol': 'grpc',
#     'service_communication': {
#         'remote': True,
#         'protocol': 'grpc',
#         'urls': 'service-layer:50051'
#     },
#     'repository_communication': {
#         'remote': False,
#         'protocol': 'direct',
#         'urls': 'N/A'
#     }
# }
```

---

## gRPC 實現步驟

gRPC 實現需要額外步驟：

### 1. 定義 Protocol Buffers

```protobuf
// protos/user_service.proto
syntax = "proto3";

package user_service;

service UserService {
  rpc GetUser (GetUserRequest) returns (GetUserResponse);
  rpc CreateUser (CreateUserRequest) returns (CreateUserResponse);
  rpc UpdateUser (UpdateUserRequest) returns (UpdateUserResponse);
  rpc DeleteUser (DeleteUserRequest) returns (DeleteUserResponse);
}

message GetUserRequest {
  int32 user_id = 1;
}

message GetUserResponse {
  int32 id = 1;
  string username = 2;
  string email = 3;
  string first_name = 4;
  string last_name = 5;
}

// ... other messages
```

### 2. 生成 Python Stubs

```bash
# Install grpcio-tools
pip install grpcio-tools

# Generate Python code
python -m grpc_tools.protoc \
  -I./protos \
  --python_out=./app/grpc \
  --grpc_python_out=./app/grpc \
  protos/user_service.proto
```

### 3. 實現 gRPC Server

```python
# app/grpc/user_service_server.py
import grpc
from concurrent import futures
from app.grpc import user_service_pb2_grpc

class UserServiceServicer(user_service_pb2_grpc.UserServiceServicer):
    def GetUser(self, request, context):
        # Call actual service
        user = user_service.getUserById(request.user_id)
        return user_service_pb2.GetUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name
        )

# Start gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
user_service_pb2_grpc.add_UserServiceServicer_to_server(
    UserServiceServicer(), server
)
server.add_insecure_port('[::]:50051')
server.start()
```

### 4. 更新 GRPCServiceCommunication

```python
# app/communication/implementations/grpc_impl.py
from app.grpc import user_service_pb2, user_service_pb2_grpc
from google.protobuf.json_format import MessageToDict

class GRPCServiceCommunication(ServiceCommunicationInterface):
    def _initialize_connections(self):
        for url in self.service_urls:
            channel = grpc.insecure_channel(url)
            self.channels[url] = channel
            self.stubs[url] = user_service_pb2_grpc.UserServiceStub(channel)

    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        stub = self.stubs[self.service_urls[0]]
        request = user_service_pb2.GetUserRequest(user_id=user_id)
        response = stub.GetUser(request, timeout=30)
        return MessageToDict(response)
```

---

## 優勢

### 1. **自動切換**
- 打包時只需修改環境變數，無需改動代碼
- Factory 自動選擇正確的實現

### 2. **統一接口**
- 應用代碼不需要知道底層使用哪種協議
- 切換協議對業務邏輯透明

### 3. **靈活配置**
- 支援 Monolithic/Layered/Microservices 三種模式
- 支援 HTTP 和 gRPC 兩種協議
- 可獨立縮放每一層

### 4. **易於測試**
- 可以輕鬆 mock 不同的通信實現
- 單元測試使用 Direct 模式
- 集成測試使用 HTTP/gRPC 模式

---

## 性能比較

| Mode | Latency | Throughput | Complexity | Use Case |
|------|---------|------------|------------|----------|
| **Direct** | Lowest (ns) | Highest | Low | Development, Small apps |
| **HTTP/REST** | Medium (ms) | Medium | Medium | Standard microservices |
| **gRPC** | Low (µs) | High | High | High-performance microservices |

---

## 下一步

1. ✅ 完成 Direct 和 HTTP 實現
2. ⏳ 定義 `.proto` 文件
3. ⏳ 生成 gRPC Python stubs
4. ⏳ 實現 gRPC Server
5. ⏳ 完成 gRPC Client 實現
6. ⏳ 編寫單元測試
7. ⏳ 編寫集成測試
8. ⏳ 性能基準測試

---

## 參考資料

- [gRPC Python Documentation](https://grpc.io/docs/languages/python/)
- [Protocol Buffers](https://developers.google.com/protocol-buffers)
- [Factory Pattern](https://refactoring.guru/design-patterns/factory-method)
- [Strategy Pattern](https://refactoring.guru/design-patterns/strategy)
