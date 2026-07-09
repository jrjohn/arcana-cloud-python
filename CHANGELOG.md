# Changelog

## [1.1.7](https://github.com/jrjohn/arcana-cloud-python/compare/v1.1.6...v1.1.7) (2026-07-08)


### Documentation

* sync README versions + CI badges ([3fb3500](https://github.com/jrjohn/arcana-cloud-python/commit/3fb3500d8ebb1848646a69b84187652d64519bae))

## [1.1.6](https://github.com/jrjohn/arcana-cloud-python/compare/v1.1.5...v1.1.6) (2026-06-19)


### Documentation

* sync README versions + CI badges ([45d480f](https://github.com/jrjohn/arcana-cloud-python/commit/45d480f5dd0a81816b029e4aa93053f6481c7d35))

## [1.1.5](https://github.com/jrjohn/arcana-cloud-python/compare/v1.1.4...v1.1.5) (2026-06-15)


### Documentation

* sync README versions + CI badges ([337c9d8](https://github.com/jrjohn/arcana-cloud-python/commit/337c9d8b43f6cbf33a7cf3d2bc3ebaa9b5f00056))

## [1.1.4](https://github.com/jrjohn/arcana-cloud-python/compare/v1.1.3...v1.1.4) (2026-06-14)


### Documentation

* sync README versions + CI badges ([ec5e158](https://github.com/jrjohn/arcana-cloud-python/commit/ec5e158f354961cea2a7a2a697ffc497369c8a46))

## [1.1.3](https://github.com/jrjohn/arcana-cloud-python/compare/v1.1.2...v1.1.3) (2026-06-14)


### Documentation

* sync README versions + CI badges ([dc34c19](https://github.com/jrjohn/arcana-cloud-python/commit/dc34c19f5d309656464851baa0ec1dafab6b0f4c))

## [1.1.2](https://github.com/jrjohn/arcana-cloud-python/compare/v1.1.1...v1.1.2) (2026-06-14)


### Documentation

* sync README versions with manifests ([3e13ca5](https://github.com/jrjohn/arcana-cloud-python/commit/3e13ca5c852f650fa18f3d5bd1ac6f68f5d45ce4))

## [1.1.1](https://github.com/jrjohn/arcana-cloud-python/compare/v1.1.0...v1.1.1) (2026-06-12)


### Documentation

* sync README versions with manifests ([111aec1](https://github.com/jrjohn/arcana-cloud-python/commit/111aec108c06801c2264415628547d8dceef5f7f))

## [1.1.0](https://github.com/jrjohn/arcana-cloud-python/compare/v1.0.0...v1.1.0) (2026-06-11)


### Features

* add comprehensive unit tests for repository, di_container, communication, schemas, tasks, decorators layers ([cc39f97](https://github.com/jrjohn/arcana-cloud-python/commit/cc39f97d604d574b173798aa8acaaf7677e973f0))
* add DAO layer following arcana-cloud-springboot pattern ([7112eea](https://github.com/jrjohn/arcana-cloud-python/commit/7112eead978fddfefe3d7111c9a3ba57fc208986))
* add layered gRPC CI + K8s gRPC CI integration tests ([ce16f64](https://github.com/jrjohn/arcana-cloud-python/commit/ce16f64f3fdec68441c1c60bec187b2bd1014020))


### Bug Fixes

* add --cov-config=.coveragerc to pytest addopts ([5602e0a](https://github.com/jrjohn/arcana-cloud-python/commit/5602e0a6f154d1af9f8f139feee15df35b006c28))
* add case-sensitivity file rename to Dockerfile.ci (mirrors Dockerfile.test) ([01e155a](https://github.com/jrjohn/arcana-cloud-python/commit/01e155a6c91679f36067a9002ef105594b7e702c))
* add netcat+curl to Dockerfile.ci, fix kubectl apply in kind-smoke-test ([b6471e4](https://github.com/jrjohn/arcana-cloud-python/commit/b6471e4ba282b5e0340716659701b6cced5e8169))
* **arch-qube:** add DAO layer (controller-service-repo-dao rule) ([2ea8938](https://github.com/jrjohn/arcana-cloud-python/commit/2ea893818a20904e97d87f4308b8a6af78c84b99))
* **arch-qube:** merge impl-naming fix with remote file renames ([6c7148c](https://github.com/jrjohn/arcana-cloud-python/commit/6c7148c127d2744da24ddda7cb571ea9f39ef726))
* **arch-qube:** rename communication impl classes to follow impl-naming convention ([963f40a](https://github.com/jrjohn/arcana-cloud-python/commit/963f40a7d87618080608685c4e565910a25fc361))
* **arch-qube:** rename direct.py→direct_impl.py, http_rest.py→http_rest_impl.py (impl-naming rule) ([8525603](https://github.com/jrjohn/arcana-cloud-python/commit/8525603829001963d223cd82c589bc701b6d0647))
* **ci:** extract pytest coverage via docker cp so SonarQube gate passes ([83e9473](https://github.com/jrjohn/arcana-cloud-python/commit/83e9473161b587577588948ffdde6c2398ceab46))
* **ci:** harden python gates + fix Layered-gRPC missing-env-file bug ([32dc03c](https://github.com/jrjohn/arcana-cloud-python/commit/32dc03c10354b1511c12c0c33f9801ffbeb040d5))
* **ci:** make OAuth token expiry tz-safe in layered mode + align decorator tests ([6b61025](https://github.com/jrjohn/arcana-cloud-python/commit/6b61025781d0e354c85cf5bbcd5d072a21ba3f8a))
* **ci:** wire auth decorators through DI so token validation works in layered gRPC ([a9014d7](https://github.com/jrjohn/arcana-cloud-python/commit/a9014d73c13a316b23a055581319cfa2e5d50872))
* connect Jenkins to Docker network + delete stale kind cluster ([0630086](https://github.com/jrjohn/arcana-cloud-python/commit/0630086fc50c50321d8c13fffecc7a24dd463e3f))
* correct auth URL to /api/v1/auth and use MagicMock for User in tests ([04ab835](https://github.com/jrjohn/arcana-cloud-python/commit/04ab8358159fa1f6659b108718f38377597b56dd))
* correct test failures from build [#51](https://github.com/jrjohn/arcana-cloud-python/issues/51) ([1132c8d](https://github.com/jrjohn/arcana-cloud-python/commit/1132c8d9bacc18abe2245dbc9a3bfba4ad116096))
* **coverage:** exclude wsgi.py and Config.py from coverage (entry-point/config code) ([0d6e51a](https://github.com/jrjohn/arcana-cloud-python/commit/0d6e51a21cc6e85cc0fa056c81dabbb6372b075b))
* exclude grpc_protos from coverage + sonar analysis ([4ed1d96](https://github.com/jrjohn/arcana-cloud-python/commit/4ed1d9644a11f2009efc3fc3f292331f08f35e3d))
* improve path resolution in fix_coverage.py ([bbd7a11](https://github.com/jrjohn/arcana-cloud-python/commit/bbd7a115efa3106a23282ee84eefce70c79a394b))
* K8s S6865/S6873/S6892/S6864/S6897 + S6697 DATABASE_URL to Secret; compose S6697 to env_file ([645d839](https://github.com/jrjohn/arcana-cloud-python/commit/645d839c9eaf2794d7bebf6993072d8cfe043d1d))
* multiple test assertion and mock corrections ([8f4bc95](https://github.com/jrjohn/arcana-cloud-python/commit/8f4bc959a760307333d79eb7a1b8e1e6e121c4af))
* patch the source modules instead: ([52d14b6](https://github.com/jrjohn/arcana-cloud-python/commit/52d14b668b4f44276e0450e29f3c414dcf1658e5))
* patch urllib3 Retry.method_whitelist → allowed_methods in controller test conftest ([d77b7ed](https://github.com/jrjohn/arcana-cloud-python/commit/d77b7ed9790ea807f7e02333b34939d22b95bda1))
* remaining 16 test failures - mock methods, timezone, response format ([b1bff60](https://github.com/jrjohn/arcana-cloud-python/commit/b1bff60dd9bc653cb88ad9fbe533a84b2bbf8be3))
* remove line number=0 entries from coverage.xml before SonarQube import ([01abd78](https://github.com/jrjohn/arcana-cloud-python/commit/01abd78efdb069d5434bc0493312d65d89898ce2))
* resolve residual issues - S6796 NOSONAR on TypeVar function sigs, k8s redis-dev S6865/S6870, S6697 WONTFIX ([493b3d3](https://github.com/jrjohn/arcana-cloud-python/commit/493b3d3c7cab642356c3b829a56b658fc79dd12e))
* resolve SonarQube issues - S1481, S1172, S5886, S2737, S6353, S6476, S3516, S3776 ([250db7c](https://github.com/jrjohn/arcana-cloud-python/commit/250db7c2917632f2ad8abda2ad94e23744de7ef2))
* resolve SonarQube issues - S6903 datetime.utcnow, S6596/S7020 docker/k8s, S6865/S6870/S6897 k8s, S6792/S6796/S5890/S7519/S3457 python, S6697 secrets NOSONAR ([834a1ac](https://github.com/jrjohn/arcana-cloud-python/commit/834a1aca8db13f978d388759e767361a51544804))
* resolve SonarQube S5754/S1192/S3776 critical issues ([12ecfd8](https://github.com/jrjohn/arcana-cloud-python/commit/12ecfd88ecefdbe338ac27c3cf97bd682f9da052))
* restore test constants broken by S1192 fix ([ea5262b](https://github.com/jrjohn/arcana-cloud-python/commit/ea5262bf66da2b841ab866d31a2739f2a8ac926f))
* S6697 residual - K8s DATABASE_URL to base64/data; rm .env.ci; nginx NOSONAR ([23886fc](https://github.com/jrjohn/arcana-cloud-python/commit/23886fc80fa7cef454e683530f62fd38db594ac7))
* **sonar:** comprehensive coverage exclusions for infra/routing code ([3ecef62](https://github.com/jrjohn/arcana-cloud-python/commit/3ecef629923c3673b278ebdc88e086072533465c))
* **sonar:** resolve all SonarQube violations across the codebase ([adb8112](https://github.com/jrjohn/arcana-cloud-python/commit/adb811215678ca8d86763b33e91838a54600206d))
* test patch target (direct→direct_impl) + coverage config ([813c9a4](https://github.com/jrjohn/arcana-cloud-python/commit/813c9a4ad70446262c1582e9c7044dd48b8b37a8))
* update broken test imports after direct.py→direct_impl.py rename + add sonar coverage config ([3a152a4](https://github.com/jrjohn/arcana-cloud-python/commit/3a152a4a09a6fb10023bdedc8b7ed6a229689b85))
* update communication factory test for monolithic mode ([36d44e1](https://github.com/jrjohn/arcana-cloud-python/commit/36d44e101c1ca937299433299df8030a95972559))
* use correct patch targets for lazy-imported auth dependencies ([52d14b6](https://github.com/jrjohn/arcana-cloud-python/commit/52d14b668b4f44276e0450e29f3c414dcf1658e5))
* use FLASK_ENV=development so DATABASE_URL is read correctly ([1810fb5](https://github.com/jrjohn/arcana-cloud-python/commit/1810fb5bea7643f81f3be2d75305d4e9ed8d2f0d))
* validate and strip out-of-range line numbers from coverage.xml ([8b5a9f5](https://github.com/jrjohn/arcana-cloud-python/commit/8b5a9f5ee508150625a9f67182af6394f057b83f))


### Documentation

* **readme:** fix Build badge -&gt; static shields.io [skip ci] ([6e71eeb](https://github.com/jrjohn/arcana-cloud-python/commit/6e71eeb42b4fecbec6c8c24c38f93dc47d717d1d))
* **readme:** fix Quality Gate badge -&gt; static shields.io [skip ci] ([c8fa179](https://github.com/jrjohn/arcana-cloud-python/commit/c8fa1799c807c6c542425f1bef1091df480097f3))
* **readme:** point Build badge at -mb job + live status [skip ci] ([2997b80](https://github.com/jrjohn/arcana-cloud-python/commit/2997b803fe7909b914bfe7cec9eabe4810a6fce3))
* **readme:** refresh agent-managed badges ([ddf89fe](https://github.com/jrjohn/arcana-cloud-python/commit/ddf89feb499a22c1a5c717bd27ea7fb451f9f3b3))
* **readme:** refresh agent-managed badges + sync gRPC version badge ([24ee305](https://github.com/jrjohn/arcana-cloud-python/commit/24ee305461e48f527f944b642d75b4cc8cfca695))
* **readme:** refresh agent-managed Build badge to passing [skip ci] ([6be9082](https://github.com/jrjohn/arcana-cloud-python/commit/6be9082eaca38f121a9cd4b6de47f8a35a77ee3b))
* **readme:** refresh Build badge to current status (building) [skip ci] ([739f6c4](https://github.com/jrjohn/arcana-cloud-python/commit/739f6c47bfee9858b130a1ea63b9e2e33b334d1d))
* **readme:** unify badges — center+segment Quality Gate block below architecture badges [skip ci] ([6754853](https://github.com/jrjohn/arcana-cloud-python/commit/6754853af4f24f416a5526140aec1f0eb3c7db83))
