# MergenVision Implementation Details

## Belgenin kullanım amacı

- Bu belge **kodun yerine geçmez**. Gerçek kaynak ve testler her zaman en güncel source-of-truth’tur.
- Her sprint sonunda bu belgeye `append/update` edilecektir; böylece projenin teknik detaylarına hakim olmayan proje sahibi de "şu anda gerçekten ne çalışıyor?" sorusuna somut yanıt bulabilir.
- Her sprintte neyin tamamlandığı, neyin henüz başlamadığı, kanıt dosyaları ve bilinen kısıtlar burada izlenecektir.

## Current Product Status

| Katman | Durum | Kısa açıklama | Kanıt dosyası / komut |
|---|---|---|---|
| Foundation | VERIFIED | Build/test çalışan repo iskeleti, katman import kuralları, C++ native library proto-contract’ı oluşturuldu. | `make verify-foundation` |
| PostgreSQL | VERIFIED | Frozen 8-tablo SQLAlchemy model, Alembic migration, national-ID security ve 8 repository port/adapter implement edildi. | `make verify-db` |
| MinIO | NOT_STARTED | Object storage adapter/bucket yönetimi yok. | — |
| Qdrant | NOT_STARTED | Vector index adapter/collection yok. | — |
| API | NOT_STARTED | FastAPI app, router, endpoint yok. | — |
| Native ML | NOT_STARTED | Sadece tek görüntülü proto-contract var; gerçek GPU runtime yok. | `contracts/face_inference/v1/face_inference.proto` |
| Bulk enrollment | NOT_STARTED | Sadece benchmark spec var; worker/import kodu yok. | `docs/benchmarks/BULK_ENROLLMENT_BENCHMARK_SPEC.md` |
| UI | NOT_STARTED | Sadece frontend boundary README var; React/Vite scaffold yok. | `frontend/README.md` |
| Docker | NOT_STARTED | Dockerfile / docker-compose yok. | — |
| Phase 2 | NOT_STARTED | Video/live-stream/object-detection kodu ve tabloları yok. | — |

## Sprint 001 — Foundation Sprint 0–1

### Amaç

Patron dilinde:

> “Ürün özelliği yazılmadı. Gelecek kodların doğru katmanlarda tutulacağı, Python ve C++ taraflarının build/test edilebildiği, dondurulmuş mimari dokümanların bozulmadığı güvenli bir repo temeli oluşturuldu.”

### Commit / çalışma durumu

- `git rev-parse HEAD`: `209ecd939e1fe94fa4b3b0f621e744174d29d07c`
- Çalışma ağacı: temiz değil; bu sprintte düzeltme ve yeni belgeler eklendi, commit yapılmadı.
- Tarih: 2026-07-12

### Gerçekten oluşturulan işlevler

| Dosya yolu | Sorumluluğu | Önemli symbol/target/test | Şu anda gerçekten yaptığı şey | Henüz yapmadığı şey |
|---|---|---|---|---|
| `backend/pyproject.toml` | Python paket metadata ve dev bağımlılıkları | `mergenvision-backend` package | `setuptools` ile `src` düzeninde paket iskeletini tanımlar; `pytest`, `ruff`, `mypy` konfigürasyonunu tutar. | Runtime bağımlılık (FastAPI, SQLAlchemy, MinIO, Qdrant, torch, TensorRT vb.) eklemedi. |
| `backend/src/mergenvision/__init__.py` | Paket kökü | `__version__ = "0.1.0"` | Paket versiyonunu export eder, import edilebilirliği sağlar. | İş mantığı içermez. |
| `backend/src/mergenvision/api/__init__.py` | API router katmanı placeholder’ı | `api` package | Boş katman iskeleti; doğru import yönüne uymak için var. | FastAPI route, endpoint, schema yok. |
| `backend/src/mergenvision/application/__init__.py` | Application service katmanı placeholder’ı | `application` package | Boş katman iskeleti. | Servis, workflow, iş mantığı yok. |
| `backend/src/mergenvision/domain/__init__.py` | Domain model katmanı placeholder’ı | `domain` package | Boş katman iskeleti. | Entity, value object yok. |
| `backend/src/mergenvision/ports/__init__.py` | Port/arayüz katmanı placeholder’ı | `ports` package | Boş katman iskeleti. | Repository/storage port tanımı yok. |
| `backend/src/mergenvision/infrastructure/__init__.py` | Infrastructure adapter katmanı placeholder’ı | `infrastructure` package | Boş katman iskeleti. | PostgreSQL, MinIO, Qdrant adapter’ı yok. |
| `backend/src/mergenvision/config/__init__.py` | Shared configuration katmanı placeholder’ı | `config` package | Boş katman iskeleti; paylaşılmış config sınırı olarak bırakıldı. | Gerçek ayar sınıfı yok. |
| `backend/tests/test_package_smoke.py` | Paket smoke testi | `test_version`, `test_imports` | `mergenvision` paketinin import edilebildiğini ve alt paketlerinin var olduğunu doğrular. | ML doğruluğu, DB, API test etmez. |
| `backend/tests/test_dependency_boundaries.py` | Import yönü kural testi | `test_dependency_direction_rules` | Production source’un domain/ports/application/infrastructure/api arasındaki import kurallarına uyduğunu AST taramasıyla doğrular; negatif testlerle sahte ihlalleri de yakaladığını ispatlar. | Runtime davranışı test etmez. |
| `backend/tests/test_forbidden_runtime_dependencies.py` | Yasaklı bağımlılık taraması | `test_forbidden_runtime_dependencies_absent` | `deepface`, `FaceAnalysis`, `paddle`, `nvidia.dali`, `DALI`, `cv2.VideoCapture`, `CPUExecutionProvider` ve `/home/user/` mutlak yollarının production source’da olmadığını doğrular. | Kodun gerçekten çalıştığını test etmez. |
| `native/CMakeLists.txt` | C++ native build konfigürasyonu | `mergenvision_face_core` target | C++20 standardında static kütüphane ve `version_smoke` test executable’ını tanımlar. | Model inference kodu yok. |
| `native/include/mergenvision/face_core/version.hpp` | Public native API | `version.hpp` | Kütüphane versiyon/ABI sabitlerini export eder. | Yüz tanıma fonksiyonu yok. |
| `native/src/version.cpp` | Native versiyon implementasyonu | `version.cpp` | Versiyon string’ini implemente eder. | Yüz tanıma implementasyonu yok. |
| `native/tests/version_smoke.cpp` | Native smoke testi | `version_smoke` testi | Kütüphaneye linklendiğini ve versiyon sabitlerini doğrular. | GPU/CUDA testi değil. |
| `contracts/face_inference/v1/face_inference.proto` | Internal RPC contract | `FaceInference` service | Python kontrol plane ile native GPU worker arasındaki tek görüntülü inferans sözleşmesini yazılı hale getirir; PII içermez. | Server/client implementasyonu, bulk/dynamic batching contract’ı yok. |
| `scripts/verify_repository_boundaries.sh` | Repo seviyesi boundary doğrulama | `verify_repository_boundaries.sh` | Dondurulmuş dosyaların bütünlüğünü (SHA-256), yasaklı bağımlılıkların varlığını, Phase 2 sızmasını, model binary’lerinin tracked olup olmadığını kontrol eder. | Kodun çalışma zamanını doğrulamaz. |
| `Makefile` | Foundation automation | `make verify-foundation` | Python testleri, C++ build/test, repo boundary ve SHA-256 kontrollerini sırayla çalıştırır. | Paket indirmez; önce `bootstrap-foundation` gerekir. |
| `frontend/README.md` | UI boundary belgesi | — | Hedef stack ve iletişim sınırını açıklar; gerçek UI kodu yok. | React/Vite scaffold ve ekranlar yok. |
| `architecture/FROZEN_SHA256SUMS` | Dondurulmuş belge hash’leri | — | Onaylanmış mimari/requirement dosyalarının SHA-256 özetlerini tutar. | İçeriği değiştirmez (değişiklik ancak kullanıcı onayıyla). |

### Çalışma akışı

Foundation için gerçek akış:

```bash
make bootstrap-foundation
# → python3 -m venv .venv
# → .venv/bin/python -m pip install --upgrade pip
# → .venv/bin/python -m pip install -e 'backend[dev]'

make verify-foundation
# → Python compileall
# → pytest backend/tests
# → ruff check backend/src backend/tests
# → protoc syntax validation (varsa)
# → CMake configure
# → native build
# → CTest
# → repository boundary verification
# → frozen SHA-256 verification
```

`verify-foundation` paket indirmez; yalnızca önceden bootstrap edilmiş environment’ı doğrular. Bootstrap yapılmamışsa açık hata verir: `Run make bootstrap-foundation first.`

### Şu anda ürün olarak çalışmayanlar

Açıkça:

- FastAPI app yok.
- HTTP endpoint yok.
- SQLAlchemy model yok.
- Alembic migration yok.
- PostgreSQL repository yok.
- MinIO adapter / bucket yönetimi yok.
- Qdrant adapter / collection yok.
- RetinaFace / ArcFace implementasyonu yok.
- TensorRT engine / CUDA kernel yok.
- Bulk enrollment worker yok.
- React / Vite uygulaması yok.
- Docker / Docker Compose yok.
- Phase 2 video/live-stream/object-detection kodu yok.

### Testlerin ispatladıkları

| Test | Ne ispatlıyor | Ne ispatlamıyor |
|---|---|---|
| `test_package_smoke.py` | `mergenvision` Python paketinin ve alt modüllerinin `PYTHONPATH=backend/src` ile import edilebildiğini. | Kodun doğruluğunu, ML kalitesini, DB/API davranışını. |
| `test_dependency_boundaries.py` | Production source’un domain→application/ports/infrastructure/api, ports→application/infrastructure/api, application→infrastructure/api, infrastructure→application/api ve api→domain/infrastructure import etmediğini; AST tabanlı tespitin sahte ihlalleri de yakaladığını. | Runtime davranışı, performans, business kararları. |
| `test_forbidden_runtime_dependencies.py` | Phase 1 foundation aşamasında yasaklanmış kütüphane/token’lerin ve eski repo mutlak yollarının production source’da bulunmadığını. | Yasaklı bir şeyin aslında gerekli olup olmadığını, ileride eklenmeyeceğini. |
| `native/tests/version_smoke.cpp` | C++ kütüphanesinin CMake ile derlendiğini ve versiyon sabitlerinin bağlandığını. | GPU inference, model doğruluğu. |
| `scripts/verify_repository_boundaries.sh` | Dondurulmuş dosyaların Git diff ve SHA-256 ile değişmediğini, yasaklı token’lerin, Phase 2 sızmasının, model binary’lerinin repo’ya girmemiş olduğunu. | Çalışma zamanı doğruluğu. |

### Known limitations

- `face_inference.proto` şu anda **yalnızca single-image RPC** (`InferImage`) içeriyor.
- Bulk enrollment için `InferBatch`, streaming veya dynamic micro-batching kararı **henüz verilmedi**; bu karar native ML runtime design sprintinde reference/benchmark kanıtıyla verilecek.
- Gerçek Python/native RPC implementation yok.
- Gerçek CUDA veya TensorRT kanıtı yok.
- Foundation testleri boş katmanlar üzerinde çalıştığı için, katmanlar arasına gerçek koddan sonra doğrulamayı güçlendirmek gerekecek.

### Sonraki sprint

**PostgreSQL + Alembic implementation sprint**

- Hedef: Dondurulmuş 8-tablo ERD’nin SQLAlchemy modelini, Alembic migration’ını, repository’lerini ve national ID encryption/HMAC/masking sınırını oluşturmak.
- Bu sprintte henüz FastAPI endpoint, MinIO/Qdrant adapter veya ML runtime implementasyonu yapılmayacak.

## Sprint 002 — PostgreSQL + Alembic + national-ID security + repository layer

### Amaç

Dondurulmuş 8-tablo Phase 1 ERD’yi gerçek çalışan SQLAlchemy 2 modelleri, Alembic migration, national-ID security boundary, repository port/adapter katmanı ve gerçek PostgreSQL integration testleriyle implement etmek.

### Commit / çalışma durumu

- `git rev-parse HEAD`: `209ecd939e1fe94fa4b3b0f621e744174d29d07c` (değişmedi, commit yapılmadı)
- Çalışma ağacı: Sprint 002 kaynak/test/migration/config/script dosyaları eklendi; commit yapılmadı.
- Tarih: 2026-07-12

### Gerçekten oluşturulan işlevler

| Dosya yolu | Sorumluluğu | Önemli symbol/target/test | Şu anda gerçekten yaptığı şey | Henüz yapmadığı şey |
|---|---|---|---|---|
| `backend/src/mergenvision/domain/ids.py` | UUIDv7 üretici | `new_uuid7()` | Python built-in veya RFC 9562 manuel bit-layout ile UUIDv7 döner; `uuid.version == 7` test edilir. | Distributed UUID üretimi veya DB seviyesi UUID fonksiyonu değil. |
| `backend/src/mergenvision/domain/enums.py` | Status constant class’ları | `PersonStatus`, `ProcessStatus`, `RecognitionStatus`, ... | String typo-safe constant’lar; DB’de varchar kullanılır, native PostgreSQL ENUM değil. | — |
| `backend/src/mergenvision/domain/errors.py` | Domain exception hiyerarşisi | `ConflictError`, `RepositoryError`, `SecurityError`, ... | Repository’ler SQLAlchemy `IntegrityError`’ı `ConflictError`’a evirerek sanitized hata döner. | — |
| `backend/src/mergenvision/domain/entities.py` | Tipili domain entity’ler | `Person`, `FaceIdentity`, `ProcessRecord`, ... | Sekiz tablonun alanlarını taşıyan dataclass’lar; ORM importu içermez. | Business workflow değil. |
| `backend/src/mergenvision/ports/national_id.py` | National-ID port | `NationalIdProtector`, `NationalIdProtectedValue` | Port + değer nesnesi; raw ID değeri repr’da bulunmaz. | Concrete algoritma yok. |
| `backend/src/mergenvision/ports/repositories.py` | Repository port’ları | `PersonRepository`, `FaceIdentityRepository`, ... (sekiz adet) | Async abstract repository API; domain entity ile çalışır, SQLAlchemy importu yok. | Concrete implementasyon burada değil. |
| `backend/src/mergenvision/infrastructure/security/national_id.py` | AES-GCM + HMAC adapter | `AesGcmNationalIdProtector` | NFKC+trim normalize, random nonce AES-256-GCM authenticated encryption, HMAC-SHA256 lookup hash, masking, fail-closed key validation, versioned ciphertext. | — |
| `backend/src/mergenvision/infrastructure/database/base.py` | SQLAlchemy declarative base | `Base` | Naming convention ile `DeclarativeBase`; import-time engine yok. | Model tanımı yok. |
| `backend/src/mergenvision/infrastructure/database/models.py` | ORM modelleri | `Person`, `FaceIdentity`, `ProcessRecord`, `InferenceProfile`, `PersonPhoto`, `FaceSample`, `RecognitionResult`, `ProcessEvent` | Frozen 8 tablo, UUIDv7 PK default’ları, unique/index/check constraint’ler, foreign key’lerde broad cascade yok. | Runtime ML veya storage logic yok. |
| `backend/src/mergenvision/infrastructure/database/session.py` | Engine/session factory | `make_engine`, `make_session_factory` | Import-time engine oluşturmadan `create_async_engine` + `async_sessionmaker` üretir. | Bağlantı havuzu benchmark’ı yok. |
| `backend/src/mergenvision/infrastructure/database/mappers.py` | ORM ↔ domain mapping | `map_person`, `map_face_identity`, ... | Dataclass field reflection ile eşleme. | Complex mapping yok. |
| `backend/src/mergenvision/infrastructure/database/repositories.py` | PostgreSQL repository adapter’ları | `PostgresPersonRepository`, ..., `PostgresProcessEventRepository` | Sekiz repository implementasyonu; `flush` eder, `commit` yapmaz; `ConflictError`/`RepositoryError` map eder. | MinIO/Qdrant çağrısı yok. |
| `backend/src/mergenvision/config/settings.py` | Environment-based settings | `Settings` | `MERGENVISION_DATABASE_URL`, `MERGENVISION_TEST_DATABASE_URL`, national-ID key env var’larını okur; `SecretStr` kullanır. | — |
| `backend/alembic.ini` | Alembic konfigürasyonu | `script_location = %(here)s/alembic` | Repo root’tan `alembic -c backend/alembic.ini` çalışır. | — |
| `backend/alembic/env.py` | Async migration environment | `run_async_migrations()` | `async_engine_from_config`, `target_metadata = Base.metadata`, `sqlalchemy.url` env ile set edilir. | — |
| `backend/alembic/versions/0001_phase1_schema.py` | Initial migration | `upgrade/downgrade` | `Base.metadata.create_all` / `drop_all` ile ORM metadata’yı doğrudan yansıtır; 8 tabloyu gerçek PostgreSQL’de oluşturur. | Data migration yok. |
| `backend/tests/unit/test_uuid7.py` | UUIDv7 testleri | `test_new_uuid7_returns_uuid7`, ... | Version, uniqueness, RFC 4122 variant ve timestamp-sortable (aynı milisaniye içinde strict total order garantisi yok) doğrular. | — |
| `backend/tests/unit/test_national_id_protection.py` | National-ID güvenlik testleri | `test_encrypt_then_decrypt_round_trip`, ... | AES-GCM round trip, farklı ciphertext, deterministic HMAC, masking, fail-closed key, tamper detection, repr kaybı doğrular. | — |
| `backend/tests/unit/test_domain_entities.py` | Entity ve enum testleri | `test_status_constants_are_strings`, ... | Typo-safe status, entity construction, recognition known/unknown shape doğrular. | — |
| `backend/tests/unit/test_database_metadata_contract.py` | Metadata contract | `test_all_business_tables_defined`, ... | 8 tablo, kolonlar, unique/index/constraint isimleri doğrular. | — |
| `backend/tests/integration/conftest.py` | Integration fixtures | `db_engine`, `session` | Gerçek `MERGENVISION_DATABASE_URL` ile async engine/session oluşturur; URL yoksa tüm integration skip eder. | — |
| `backend/tests/integration/test_alembic_postgres.py` | Alembic PostgreSQL kanıtı | `test_alembic_upgrade_downgrade_reupgrade`, `test_required_constraints_and_indexes_exist` | Upgrade/downgrade/re-upgrade ve constraint/index introspection doğrular. | — |
| `backend/tests/integration/test_postgres_constraints.py` | PostgreSQL constraint kanıtı | Duplicate, unique, partial unique, check constraint, broad cascade yok testleri | Gerçek PostgreSQL transaction’ında constraint hatalarını doğrular. | — |
| `backend/tests/integration/test_postgres_repositories.py` | Repository kanıtı | CRUD, national-ID lookup, no auto-commit, raw national ID DB’de yok | Sekiz repository’nin gerçek PostgreSQL’de çalıştığını ve transaction ownership’i koruduğunu doğrular. | — |
| `scripts/run_postgres_integration_tests.sh` | Ephemeral PostgreSQL test harness | `make test-db-integration` | `MERGENVISION_TEST_DATABASE_URL` yoksa `postgres:16-alpine` container başlatır, Alembic upgrade ve integration testleri çalıştırır, yalnızca kendi container’ını durdurur. | — |
| `Makefile` | Sprint 002 target’ları | `test-db-unit`, `test-db-integration`, `verify-db`, `verify-sprint-002` | DB security/domain unit testlerini, gerçek PostgreSQL integration’ını, mypy ve foundation ile birlikte koşar. | — |
| `backend/pyproject.toml` | Bağımlılık güncellemesi | `sqlalchemy`, `alembic`, `asyncpg`, `cryptography`, `pydantic-settings`, `pytest-asyncio` | Bounded runtime + test bağımlılıklarını ekler. | Kilit dosyası üretmez. |
| `scripts/bootstrap_foundation.sh` | `.venv` onarımı | `python3 -m venv --clear --copies .venv` | `.venv` var ama `.venv/bin/python` executable değilse environment’ı onarır. | — |
| `docs/implementation/CURRENT_SPRINT.md` | Sprint 002 planı | objective, deliverables, acceptance, non-goals, DoD | Plan dokümanı; implementation öncesi güncellendi. | — |
| `docs/implementation/REFERENCE_DECISION_LOG.md` | Karar kaydı | SQLAlchemy async, Alembic async, partial unique index, UUIDv7, AES-GCM, HMAC, repo transaction ownership | Referans/Source ve ret alternatif kaydedildi. | — |

### Çalışma akışı

Sprint 002 için gerçek akış:

```bash
make test-db-unit
# → PYTHONPATH=backend/src pytest backend/tests/unit -v  (30 passed)

make test-db-integration
# → scripts/run_postgres_integration_tests.sh
# → ephemeral postgres:16-alpine başlat
# → alembic upgrade head
# → pytest backend/tests/integration -v  (34 passed)
# → container durdur

make verify-db
# → ruff check backend/src backend/tests
# → make test-db-unit
# → make test-db-integration
# → mypy backend/src

make verify-foundation
# → Foundation Sprint 0–1 regresyonu geçti

make verify-sprint-002
# → verify-foundation + verify-db
```

### Şu anda ürün olarak çalışmayanlar

Açıkça:

- FastAPI app / endpoint / response schema yok.
- MinIO adapter / bucket yönetimi yok.
- Qdrant adapter / collection yok.
- RetinaFace / ArcFace / TensorRT / CUDA kernel yok.
- Bulk enrollment worker yok.
- React / Vite uygulaması yok.
- Docker / Docker Compose yok.
- Phase 2 video/live-stream/object-detection kodu yok.

### Testlerin ispatladıkları

| Test | Ne ispatlıyor | Ne ispatlamıyor |
|---|---|---|
| `backend/tests/unit` (30 passed) | UUIDv7 gerçek; national-ID AES-GCM/HMAC/masking doğru; status constant’lar var; ORM metadata 8 tabloyu, kolonları, constraint/index isimlerini doğru içeriyor. | Gerçek PostgreSQL, concurrency, repository runtime’ı değil. |
| `backend/tests/integration/test_alembic_postgres.py` | Alembic upgrade/downgrade/re-upgrade gerçek PostgreSQL’de çalışır; constraint/index’ler `inspect` ile var. | Performans, veri. |
| `backend/tests/integration/test_postgres_constraints.py` | Unique, partial unique, check constraint’ler gerçek PostgreSQL transaction’ında çalışır; FK’lerde broad cascade yok. | ORM dışı raw SQL. |
| `backend/tests/integration/test_postgres_repositories.py` | 8 repository gerçek PostgreSQL’de CRUD yapar; national-ID lookup; repository commit yapmaz; raw national ID DB’de yok; process event sequence sıralı artar. | MinIO/Qdrant entegrasyonu, ML doğruluğu. |
| `verify-foundation` | Eski foundation test/compile/Ruff/native build/boundary/frozen hash’ler hâlâ geçiyor. | Sprint 002 olmadan da geçmeliydi. |

### Known limitations

- Integration test’ler `pytest-asyncio` Python 3.15+ olay döngüsü deprecation uyarıları veriyor; bugün testleri geçiyor, gelecekte `loop_scope` ile güncellenecek.
- Repository testleri tekli transaction İçinde çalışıyor; aynı anda çoklu session concurrency testi eklenmedi.
- Process event concurrency testi (iki concurrent append) bu sprintte yapılmadı; `SELECT ... FOR UPDATE` + unique constraint mevcut.
- Database connection pool ayarları henüz benchmark edilmemiş; `pool_pre_ping=True` varsayılan.
- `inference_profile.is_active` için “tek active profile” business kuralı uygulanmadı; frozen ERD buna ileride izin veriyor.
- `PersonRepository.list_active` gibi listeler yalnızca limit/offset; cursor pagination yok.

### Sonraki sprint

**MinIO + Qdrant adapters + cross-store lifecycle/reconciliation**

- Hedef: MinIO object storage adapter, Qdrant vector index adapter, fotoğraf/örnek/sample ve process lifecycle’da cross-store consistency kurallarını implement etmek.
- Bu sprintte FastAPI endpoint, ML runtime ve UI yok.


### Sprint 002 kaynak kodu

Bu bölüm, prompt sırasında oluşturulan/değiştirilen kaynak, test, migration, config ve script dosyalarının final içeriklerini içerir.

#### `Makefile`

```makefile
.PHONY: bootstrap-foundation check-venv test-python ruff proto-syntax configure-native build-native test-native verify-boundaries frozen-hashes verify-foundation test-db-unit test-db-integration verify-db verify-sprint-002

PYTHON := .venv/bin/python
PYTEST := $(PYTHON) -m pytest

REPO_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# ---------------------------------------------------------------------------
# Environment bootstrap (idempotent, no global system packages)
# ---------------------------------------------------------------------------

bootstrap-foundation:
	@bash scripts/bootstrap_foundation.sh

check-venv:
	@test -x $(PYTHON) || { echo "Run make bootstrap-foundation first." >&2; exit 1; }

# ---------------------------------------------------------------------------
# Python layer
# ---------------------------------------------------------------------------

test-python: check-venv
	@echo "==> Compiling Python source"
	$(PYTHON) -m compileall backend/src
	@echo "==> Running Python tests"
	PYTHONPATH=backend/src $(PYTEST) backend/tests -v

ruff: check-venv
	@echo "==> Running Ruff"
	$(PYTHON) -m ruff check backend/src backend/tests

proto-syntax:
	@echo "==> Validating proto syntax"
	@if command -v protoc >/dev/null 2>&1; then \
		mkdir -p /tmp/proto_check; \
		protoc --proto_path=contracts/face_inference/v1 face_inference.proto --python_out=/tmp/proto_check; \
		echo "Proto syntax OK"; \
	else \
		echo "SKIPPED_TOOL_UNAVAILABLE: protoc not installed"; \
	fi

# ---------------------------------------------------------------------------
# Native layer
# ---------------------------------------------------------------------------

configure-native:
	@cmake -S native -B build/native

build-native: configure-native
	@cmake --build build/native --parallel

test-native: build-native
	@ctest --test-dir build/native --output-on-failure

# ---------------------------------------------------------------------------
# Repository-level boundary checks
# ---------------------------------------------------------------------------

verify-boundaries:
	@bash scripts/verify_repository_boundaries.sh

frozen-hashes:
	@echo "==> Verifying frozen file hashes"
	@sha256sum --check architecture/FROZEN_SHA256SUMS

# ---------------------------------------------------------------------------
# Database sprint targets (Sprint 002 - real PostgreSQL)
# ---------------------------------------------------------------------------

test-db-unit: check-venv
	@echo "==> Running DB/security/domain unit tests"
	PYTHONPATH=backend/src $(PYTEST) backend/tests/unit -v

test-db-integration:
	@echo "==> Running real PostgreSQL integration tests"
	@bash scripts/run_postgres_integration_tests.sh

verify-db: ruff test-db-unit test-db-integration
	@echo "==> Running mypy"
	$(PYTHON) -m mypy backend/src
	@echo "==> Database verification complete"

verify-sprint-002: verify-foundation verify-db
	@echo "==> Sprint 002 verification complete"

# ---------------------------------------------------------------------------
# Foundation gate: all of the above, in order, non-destructive
# ---------------------------------------------------------------------------

verify-foundation: test-python ruff proto-syntax configure-native build-native test-native verify-boundaries frozen-hashes
	@echo "==> Foundation verification complete"

```

#### `backend/pyproject.toml`

```toml
[project]
name = "mergenvision-backend"
version = "0.1.0"
description = "MergenVision Phase 1 photo-based person recognition backend"
requires-python = ">=3.12"
dependencies = [
    "sqlalchemy[asyncio]>=2.0.0,<3.0.0",
    "alembic>=1.13.0,<2.0.0",
    "asyncpg>=0.29.0,<0.32.0",
    "cryptography>=42.0.0,<45.0.0",
    "pydantic-settings>=2.0.0,<3.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8,<9",
    "pytest-asyncio>=0.23.0,<0.26.0",
    "ruff>=0.5,<0.8",
    "mypy>=1.11,<1.12",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src/"]
include = ["mergenvision*"]

[tool.ruff]
target-version = "py312"
line-length = 100
exclude = [".venv", "build", "dist"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = ["E501", "B008"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-v"
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"

```

#### `scripts/bootstrap_foundation.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root relative to this script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "==> Bootstrapping foundation environment"

if [[ ! -d ".venv" ]] || [[ ! -x ".venv/bin/python" ]]; then
    echo "==> Creating/repairing local virtual environment"
    python3 -m venv --clear --copies .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e './backend[dev]'

echo "==> Bootstrap complete: .venv is ready"

```

#### `scripts/run_postgres_integration_tests.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

CONTAINER_ID=""
EXIT_CODE=0
IMAGE="postgres:16-alpine"
DEFAULT_USER="test"
DEFAULT_PASSWORD="test"
DEFAULT_DB="mergenvision"

choose_port() {
    python3 - <<'PY'
import socket
with socket.socket() as s:
    s.bind(("", 0))
    print(s.getsockname()[1])
PY
}

cleanup() {
    if [[ -n "${CONTAINER_ID}" ]]; then
        echo "==> Stopping ephemeral PostgreSQL container ${CONTAINER_ID}"
        docker stop "${CONTAINER_ID}" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

run_migrations_and_tests() {
    local database_url="$1"
    echo "==> Running Alembic migrations"
    (
        cd backend
        MERGENVISION_DATABASE_URL="${database_url}" \
            "${REPO_ROOT}/.venv/bin/alembic" -c alembic.ini upgrade head
    )

    echo "==> Running integration tests"
    MERGENVISION_DATABASE_URL="${database_url}" \
        MERGENVISION_TEST_DATABASE_URL="${database_url}" \
        "${REPO_ROOT}/.venv/bin/python" -m pytest backend/tests/integration -v
}

if [[ -n "${MERGENVISION_TEST_DATABASE_URL:-}" ]]; then
    echo "==> Using provided MERGENVISION_TEST_DATABASE_URL"
    run_migrations_and_tests "${MERGENVISION_TEST_DATABASE_URL}"
    exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker is required to start ephemeral PostgreSQL" >&2
    exit 1
fi

TEST_PORT="$(choose_port)"
CONTAINER_NAME="mergenvision-test-postgres-$$-${RANDOM}"

echo "==> Starting ephemeral PostgreSQL on port ${TEST_PORT}"
CONTAINER_ID="$(docker run --rm -d \
    --name "${CONTAINER_NAME}" \
    -e POSTGRES_USER="${DEFAULT_USER}" \
    -e POSTGRES_PASSWORD="${DEFAULT_PASSWORD}" \
    -e POSTGRES_DB="${DEFAULT_DB}" \
    -p "${TEST_PORT}:5432" \
    "${IMAGE}")"

echo "==> Waiting for PostgreSQL to be ready"
for _ in {1..60}; do
    if docker exec "${CONTAINER_ID}" pg_isready -U "${DEFAULT_USER}" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

for _ in {1..60}; do
    if docker exec "${CONTAINER_ID}" psql -U "${DEFAULT_USER}" -d "${DEFAULT_DB}" -c "SELECT 1" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

if ! docker exec "${CONTAINER_ID}" psql -U "${DEFAULT_USER}" -d "${DEFAULT_DB}" -c "SELECT 1" >/dev/null 2>&1; then
    echo "ERROR: PostgreSQL did not become ready" >&2
    exit 1
fi

DATABASE_URL="postgresql+asyncpg://${DEFAULT_USER}:${DEFAULT_PASSWORD}@localhost:${TEST_PORT}/${DEFAULT_DB}"
run_migrations_and_tests "${DATABASE_URL}"

```

#### `backend/alembic.ini`

```ini
[alembic]
script_location = %(here)s/alembic
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S

```

#### `backend/alembic/env.py`

```python
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mergenvision.config.settings import Settings
from mergenvision.infrastructure.database.base import Base

settings = Settings()
config = context.config
if settings.database_url:
    config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

```

#### `backend/alembic/script.py.mako`

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}

```

#### `backend/alembic/versions/0001_phase1_schema.py`

```python
"""Phase 1 initial schema: eight frozen business tables."""

from typing import Sequence, Union

from alembic import op

from mergenvision.infrastructure.database.base import Base
from mergenvision.infrastructure.database import models as _models  # noqa: F401

revision: str = "0001_phase1_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())

```

#### `backend/src/mergenvision/config/settings.py`

```python
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from mergenvision.infrastructure.security.national_id import AesGcmNationalIdProtector
from mergenvision.ports.national_id import NationalIdProtector


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MERGENVISION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    test_database_url: str | None = None
    national_id_encryption_key_b64: SecretStr | None = None
    national_id_hmac_key_b64: SecretStr | None = None

    def create_national_id_protector(self) -> NationalIdProtector:
        if self.national_id_encryption_key_b64 is None or self.national_id_hmac_key_b64 is None:
            raise RuntimeError("National ID encryption/HMAC keys are not configured")
        return AesGcmNationalIdProtector(
            encryption_key_b64=self.national_id_encryption_key_b64.get_secret_value(),
            hmac_key_b64=self.national_id_hmac_key_b64.get_secret_value(),
        )

```

#### `backend/src/mergenvision/domain/ids.py`

```python
import time
import uuid


def _uuid7_from_builtin() -> uuid.UUID | None:
    fn = getattr(uuid, "uuid7", None)
    if fn is None:
        return None
    return fn()


def _uuid7_rfc9562() -> uuid.UUID:
    timestamp_ms = int(time.time_ns() // 1_000_000)
    rand = uuid.uuid4().int & ((1 << 76) - 1)
    rand = (rand & ~0xC000000000000000) | 0x8000000000000000
    uuid_int = (timestamp_ms << 80) | (7 << 76) | rand
    return uuid.UUID(int=uuid_int, version=7)


def new_uuid7() -> uuid.UUID:
    value = _uuid7_from_builtin()
    return value if value is not None else _uuid7_rfc9562()

```

#### `backend/src/mergenvision/domain/enums.py`

```python
class PersonStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"


class FaceIdentityStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"


class PersonPhotoStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"


class SampleStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"


class ProcessStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RecognitionStatus:
    KNOWN = "known"
    UNKNOWN = "unknown"

```

#### `backend/src/mergenvision/domain/errors.py`

```python
class DomainError(Exception):
    pass


class SecurityError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class RepositoryError(DomainError):
    pass

```

#### `backend/src/mergenvision/domain/entities.py`

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(kw_only=True)
class Person:
    person_id: UUID
    first_name: str
    last_name: str
    national_id_ciphertext: bytes
    national_id_lookup_hash: str
    national_id_masked: str
    additional_details: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass(kw_only=True)
class FaceIdentity:
    face_identity_id: UUID
    person_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass(kw_only=True)
class ProcessRecord:
    process_id: UUID
    process_type: str
    status: str
    inference_profile_id: UUID | None = None
    input_object_key: str | None = None
    input_sha256: str | None = None
    input_mime_type: str | None = None
    input_size_bytes: int | None = None
    input_width: int | None = None
    input_height: int | None = None
    retention_until: datetime | None = None
    detected_face_count: int | None = None
    error_code: str | None = None
    error_message_sanitized: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass(kw_only=True)
class InferenceProfile:
    inference_profile_id: UUID
    profile_name: str
    detector_name: str
    detector_version: str
    detector_artifact_sha256: str
    alignment_version: str
    embedder_name: str
    embedder_version: str
    embedder_artifact_sha256: str
    preprocessing_version: str
    embedding_dimension: int
    distance_metric: str
    match_threshold: float
    is_active: bool
    created_at: datetime
    retired_at: datetime | None = None


@dataclass(kw_only=True)
class PersonPhoto:
    photo_id: UUID
    person_id: UUID
    enrollment_process_id: UUID | None = None
    object_key: str
    content_sha256: str
    mime_type: str
    file_size_bytes: int
    width: int
    height: int
    is_primary: bool
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass(kw_only=True)
class FaceSample:
    sample_id: UUID
    face_identity_id: UUID
    photo_id: UUID
    inference_profile_id: UUID
    bbox_x: int
    bbox_y: int
    bbox_width: int
    bbox_height: int
    landmarks: dict[str, Any]
    detection_confidence: float
    quality_score: float | None = None
    status: str
    created_at: datetime
    deleted_at: datetime | None = None


@dataclass(kw_only=True)
class RecognitionResult:
    result_id: UUID
    process_id: UUID
    face_index: int
    recognition_status: str
    bbox_x: int
    bbox_y: int
    bbox_width: int
    bbox_height: int
    detection_confidence: float
    threshold_used: float
    matched_face_identity_id: UUID | None = None
    matched_sample_id: UUID | None = None
    similarity_score: float | None = None
    created_at: datetime


@dataclass(kw_only=True)
class ProcessEvent:
    event_id: UUID
    process_id: UUID
    sequence_no: int
    event_type: str
    details: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime

```

#### `backend/src/mergenvision/ports/national_id.py`

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class NationalIdProtectedValue:
    ciphertext: bytes
    lookup_hash: str
    masked: str

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"ciphertext=<{len(self.ciphertext)} bytes>, "
            f"lookup_hash=<{len(self.lookup_hash)} chars>, "
            f"masked={self.masked!r})"
        )


class NationalIdProtector(ABC):
    @abstractmethod
    def protect(self, raw_national_id: str) -> NationalIdProtectedValue:
        raise NotImplementedError

    @abstractmethod
    def reveal(self, protected: NationalIdProtectedValue) -> str:
        raise NotImplementedError

```

#### `backend/src/mergenvision/ports/repositories.py`

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from mergenvision.domain.entities import (
    FaceIdentity,
    FaceSample,
    InferenceProfile,
    Person,
    PersonPhoto,
    ProcessEvent,
    ProcessRecord,
    RecognitionResult,
)


class PersonRepository(ABC):
    @abstractmethod
    async def add(self, person: Person) -> Person:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, person_id: UUID) -> Person | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_national_id_lookup_hash(self, lookup_hash: str) -> Person | None:
        raise NotImplementedError

    @abstractmethod
    async def list_active(self, *, limit: int, offset: int) -> list[Person]:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        person_id: UUID,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        additional_details: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> Person | None:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(self, person_id: UUID) -> Person | None:
        raise NotImplementedError


class FaceIdentityRepository(ABC):
    @abstractmethod
    async def add(self, face_identity: FaceIdentity) -> FaceIdentity:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, face_identity_id: UUID) -> FaceIdentity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_person_id(self, person_id: UUID) -> FaceIdentity | None:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(self, face_identity_id: UUID) -> FaceIdentity | None:
        raise NotImplementedError


class InferenceProfileRepository(ABC):
    @abstractmethod
    async def add(self, profile: InferenceProfile) -> InferenceProfile:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, profile_id: UUID) -> InferenceProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_name(self, profile_name: str) -> InferenceProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def get_active(self) -> InferenceProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def retire(self, profile_id: UUID) -> InferenceProfile | None:
        raise NotImplementedError


class ProcessRecordRepository(ABC):
    @abstractmethod
    async def add(self, record: ProcessRecord) -> ProcessRecord:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, process_id: UUID) -> ProcessRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_started(self, process_id: UUID) -> ProcessRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_completed(
        self,
        process_id: UUID,
        *,
        detected_face_count: int | None = None,
    ) -> ProcessRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_failed(
        self,
        process_id: UUID,
        *,
        error_code: str,
        error_message_sanitized: str,
    ) -> ProcessRecord | None:
        raise NotImplementedError


class PersonPhotoRepository(ABC):
    @abstractmethod
    async def add(self, photo: PersonPhoto) -> PersonPhoto:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, photo_id: UUID) -> PersonPhoto | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_person(self, person_id: UUID, *, limit: int, offset: int) -> list[PersonPhoto]:
        raise NotImplementedError

    @abstractmethod
    async def set_primary(self, photo_id: UUID) -> PersonPhoto | None:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(self, photo_id: UUID) -> PersonPhoto | None:
        raise NotImplementedError


class FaceSampleRepository(ABC):
    @abstractmethod
    async def add(self, sample: FaceSample) -> FaceSample:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, sample_id: UUID) -> FaceSample | None:
        raise NotImplementedError

    @abstractmethod
    async def list_active_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[FaceSample]:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(self, photo_id: UUID) -> FaceSample | None:
        raise NotImplementedError


class RecognitionResultRepository(ABC):
    @abstractmethod
    async def add(self, result: RecognitionResult) -> RecognitionResult:
        raise NotImplementedError

    @abstractmethod
    async def list_by_process(self, process_id: UUID) -> list[RecognitionResult]:
        raise NotImplementedError

    @abstractmethod
    async def list_history_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[RecognitionResult]:
        raise NotImplementedError


class ProcessEventRepository(ABC):
    @abstractmethod
    async def append(
        self,
        process_id: UUID,
        *,
        event_type: str,
        details: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> ProcessEvent:
        raise NotImplementedError

    @abstractmethod
    async def list_by_process(self, process_id: UUID, *, limit: int, offset: int) -> list[ProcessEvent]:
        raise NotImplementedError

```

#### `backend/src/mergenvision/infrastructure/security/national_id.py`

```python
from __future__ import annotations

import base64
import hmac
import os
import struct
import unicodedata
from hashlib import sha256

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from mergenvision.domain.errors import SecurityError
from mergenvision.ports.national_id import NationalIdProtectedValue, NationalIdProtector

_FORMAT_VERSION = 1
_NONCE_LEN = 12
_AEAD_ASSOCIATED_DATA = b"mergenvision:national-id:v1"
_KEY_LEN = 32


class AesGcmNationalIdProtector(NationalIdProtector):
    def __init__(self, encryption_key_b64: str, hmac_key_b64: str) -> None:
        self._encryption_key = self._decode_key(encryption_key_b64, "encryption_key")
        self._hmac_key = self._decode_key(hmac_key_b64, "hmac_key")
        self._aesgcm = AESGCM(self._encryption_key)

    def protect(self, raw_national_id: str) -> NationalIdProtectedValue:
        normalized = self._normalize(raw_national_id)
        if not normalized:
            raise SecurityError("National ID is empty after normalization")
        nonce = os.urandom(_NONCE_LEN)
        plaintext = normalized.encode("utf-8")
        ciphertext_with_tag = self._aesgcm.encrypt(nonce, plaintext, _AEAD_ASSOCIATED_DATA)
        payload = struct.pack("!B", _FORMAT_VERSION) + nonce + ciphertext_with_tag
        return NationalIdProtectedValue(
            ciphertext=payload,
            lookup_hash=self._lookup_hash(normalized),
            masked=self._mask(normalized),
        )

    def reveal(self, protected: NationalIdProtectedValue) -> str:
        payload = protected.ciphertext
        if len(payload) < 1 + _NONCE_LEN + 16:
            raise SecurityError("Ciphertext is too short")
        version = payload[0]
        if version != _FORMAT_VERSION:
            raise SecurityError(f"Unsupported ciphertext format version: {version}")
        nonce = payload[1 : 1 + _NONCE_LEN]
        ciphertext_with_tag = payload[1 + _NONCE_LEN :]
        try:
            plaintext = self._aesgcm.decrypt(nonce, ciphertext_with_tag, _AEAD_ASSOCIATED_DATA)
        except InvalidTag as exc:
            raise SecurityError("National ID decryption failed: authentication tag mismatch") from exc
        return plaintext.decode("utf-8")

    def encryption_key_b64(self) -> str:
        return base64.b64encode(self._encryption_key).decode("ascii")

    def hmac_key_b64(self) -> str:
        return base64.b64encode(self._hmac_key).decode("ascii")

    @staticmethod
    def _normalize(raw: str) -> str:
        return unicodedata.normalize("NFKC", raw).strip()

    @staticmethod
    def _mask(normalized: str) -> str:
        if len(normalized) > 4:
            return "*" * (len(normalized) - 4) + normalized[-4:]
        return "*" * len(normalized)

    def _lookup_hash(self, normalized: str) -> str:
        return hmac.new(
            self._hmac_key,
            normalized.encode("utf-8"),
            sha256,
        ).hexdigest()

    @staticmethod
    def _decode_key(key_b64: str, name: str) -> bytes:
        try:
            raw = base64.b64decode(key_b64, validate=True)
        except Exception as exc:
            raise SecurityError(f"Invalid Base64 for {name}") from exc
        if len(raw) != _KEY_LEN:
            raise SecurityError(
                f"{name} must decode to exactly {_KEY_LEN} bytes, got {len(raw)}"
            )
        return raw

```

#### `backend/src/mergenvision/infrastructure/database/base.py`

```python
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_N_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }

    )

```

#### `backend/src/mergenvision/infrastructure/database/session.py`

```python
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def make_engine(database_url: str, *, pool_pre_ping: bool = True) -> AsyncEngine:
    return create_async_engine(
        database_url,
        pool_pre_ping=pool_pre_ping,
        future=True,
    )


def make_session_factory(
    engine: AsyncEngine,
    *,
    expire_on_commit: bool = False,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=expire_on_commit,
    )

```

#### `backend/src/mergenvision/infrastructure/database/mappers.py`

```python
import dataclasses
from typing import TypeVar

from mergenvision.domain import entities as domain
from mergenvision.infrastructure.database import models as orm

_T = TypeVar("_T")


def _map_to_domain(model: object, domain_cls: type[_T]) -> _T:
    kwargs: dict[str, object] = {}
    for field in dataclasses.fields(domain_cls):  # type: ignore[arg-type]
        value = getattr(model, field.name)
        kwargs[field.name] = value
    return domain_cls(**kwargs)


def map_person(model: orm.Person) -> domain.Person:
    return _map_to_domain(model, domain.Person)


def map_face_identity(model: orm.FaceIdentity) -> domain.FaceIdentity:
    return _map_to_domain(model, domain.FaceIdentity)


def map_process_record(model: orm.ProcessRecord) -> domain.ProcessRecord:
    return _map_to_domain(model, domain.ProcessRecord)


def map_inference_profile(model: orm.InferenceProfile) -> domain.InferenceProfile:
    return _map_to_domain(model, domain.InferenceProfile)


def map_person_photo(model: orm.PersonPhoto) -> domain.PersonPhoto:
    return _map_to_domain(model, domain.PersonPhoto)


def map_face_sample(model: orm.FaceSample) -> domain.FaceSample:
    return _map_to_domain(model, domain.FaceSample)


def map_recognition_result(model: orm.RecognitionResult) -> domain.RecognitionResult:
    return _map_to_domain(model, domain.RecognitionResult)


def map_process_event(model: orm.ProcessEvent) -> domain.ProcessEvent:
    return _map_to_domain(model, domain.ProcessEvent)

```

#### `backend/src/mergenvision/infrastructure/database/models.py`

```python
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from mergenvision.domain.ids import new_uuid7
from mergenvision.infrastructure.database.base import Base


class Person(Base):
    __tablename__ = "person"

    person_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    first_name: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(255), nullable=False)
    last_name: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(255), nullable=False)
    national_id_ciphertext: sa.orm.Mapped[bytes] = sa.orm.mapped_column(
        sa.LargeBinary, nullable=False
    )
    national_id_lookup_hash: sa.orm.Mapped[str] = sa.orm.mapped_column(
        sa.String(64), nullable=False, unique=True
    )
    national_id_masked: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(255), nullable=False)
    additional_details: sa.orm.Mapped[dict[str, Any]] = sa.orm.mapped_column(
        JSONB, nullable=False, default=dict
    )
    status: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(32), nullable=False)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    deleted_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.Index("ix_person_status", "status"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
    )


class FaceIdentity(Base):
    __tablename__ = "face_identity"

    face_identity_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    person_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True),
        sa.ForeignKey("person.person_id"),
        nullable=False,
        unique=True,
    )
    status: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(32), nullable=False)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    deleted_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.Index("ix_face_identity_status", "status"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
    )


class InferenceProfile(Base):
    __tablename__ = "inference_profile"

    inference_profile_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    profile_name: sa.orm.Mapped[str] = sa.orm.mapped_column(
        sa.String(255), nullable=False, unique=True
    )
    detector_name: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(255), nullable=False)
    detector_version: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    detector_artifact_sha256: sa.orm.Mapped[str] = sa.orm.mapped_column(
        sa.String(64), nullable=False
    )
    alignment_version: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    embedder_name: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(255), nullable=False)
    embedder_version: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    embedder_artifact_sha256: sa.orm.Mapped[str] = sa.orm.mapped_column(
        sa.String(64), nullable=False
    )
    preprocessing_version: sa.orm.Mapped[str] = sa.orm.mapped_column(
        sa.String(64), nullable=False
    )
    embedding_dimension: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    distance_metric: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(32), nullable=False)
    match_threshold: sa.orm.Mapped[float] = sa.orm.mapped_column(sa.REAL, nullable=False)
    is_active: sa.orm.Mapped[bool] = sa.orm.mapped_column(sa.Boolean, nullable=False)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    retired_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.CheckConstraint("embedding_dimension > 0", name="embedding_dimension_positive"),
    )


class ProcessRecord(Base):
    __tablename__ = "process_record"

    process_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    process_type: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    status: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(32), nullable=False)
    inference_profile_id: sa.orm.Mapped[UUID | None] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("inference_profile.inference_profile_id"), nullable=True
    )
    input_object_key: sa.orm.Mapped[str | None] = sa.orm.mapped_column(sa.Text, nullable=True)
    input_sha256: sa.orm.Mapped[str | None] = sa.orm.mapped_column(sa.String(64), nullable=True)
    input_mime_type: sa.orm.Mapped[str | None] = sa.orm.mapped_column(sa.String(64), nullable=True)
    input_size_bytes: sa.orm.Mapped[int | None] = sa.orm.mapped_column(sa.BigInteger, nullable=True)
    input_width: sa.orm.Mapped[int | None] = sa.orm.mapped_column(sa.Integer, nullable=True)
    input_height: sa.orm.Mapped[int | None] = sa.orm.mapped_column(sa.Integer, nullable=True)
    retention_until: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    detected_face_count: sa.orm.Mapped[int | None] = sa.orm.mapped_column(sa.Integer, nullable=True)
    error_code: sa.orm.Mapped[str | None] = sa.orm.mapped_column(sa.String(64), nullable=True)
    error_message_sanitized: sa.orm.Mapped[str | None] = sa.orm.mapped_column(sa.Text, nullable=True)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    started_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    completed_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.Index("ix_process_record_process_type_status_created_at", "process_type", "status", "created_at"),
        sa.Index("ix_process_record_created_at", "created_at"),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="status",
        ),
        sa.CheckConstraint(
            "input_size_bytes IS NULL OR input_size_bytes > 0",
            name="input_size_positive",
        ),
        sa.CheckConstraint(
            "input_width IS NULL OR input_width > 0",
            name="input_width_positive",
        ),
        sa.CheckConstraint(
            "input_height IS NULL OR input_height > 0",
            name="input_height_positive",
        ),
        sa.CheckConstraint(
            "detected_face_count IS NULL OR detected_face_count >= 0",
            name="detected_face_count_nonnegative",
        ),
    )


class PersonPhoto(Base):
    __tablename__ = "person_photo"

    photo_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    person_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("person.person_id"), nullable=False
    )
    enrollment_process_id: sa.orm.Mapped[UUID | None] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("process_record.process_id"), nullable=True
    )
    object_key: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.Text, nullable=False, unique=True)
    content_sha256: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    mime_type: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    file_size_bytes: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.BigInteger, nullable=False)
    width: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    height: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    is_primary: sa.orm.Mapped[bool] = sa.orm.mapped_column(sa.Boolean, nullable=False)
    status: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(32), nullable=False)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    deleted_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.UniqueConstraint("person_id", "content_sha256", name="uq_person_photo_person_id_content_sha256"),
        sa.Index("ix_person_photo_person_id_status", "person_id", "status"),
        sa.Index(
            "ix_uq_person_photo_active_primary",
            "person_id",
            unique=True,
            postgresql_where=sa.and_(
                sa.text("is_primary = true"),
                sa.text("status = 'active'"),
                sa.text("deleted_at IS NULL"),
            ),
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
        sa.CheckConstraint("file_size_bytes > 0", name="file_size_positive"),
        sa.CheckConstraint("width > 0", name="width_positive"),
        sa.CheckConstraint("height > 0", name="height_positive"),
    )


class FaceSample(Base):
    __tablename__ = "face_sample"

    sample_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    face_identity_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("face_identity.face_identity_id"), nullable=False
    )
    photo_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("person_photo.photo_id"), nullable=False
    )
    inference_profile_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("inference_profile.inference_profile_id"), nullable=False
    )
    bbox_x: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    bbox_y: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    bbox_width: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    bbox_height: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    landmarks: sa.orm.Mapped[dict[str, Any]] = sa.orm.mapped_column(JSONB, nullable=False, default=dict)
    detection_confidence: sa.orm.Mapped[float] = sa.orm.mapped_column(sa.REAL, nullable=False)
    quality_score: sa.orm.Mapped[float | None] = sa.orm.mapped_column(sa.REAL, nullable=True)
    status: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(32), nullable=False)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    deleted_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "photo_id", "inference_profile_id", name="uq_face_sample_photo_id_inference_profile_id"
        ),
        sa.Index("ix_face_sample_face_identity_id_status", "face_identity_id", "status"),
        sa.Index("ix_face_sample_inference_profile_id_status", "inference_profile_id", "status"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
        sa.CheckConstraint("bbox_width > 0", name="bbox_width_positive"),
        sa.CheckConstraint("bbox_height > 0", name="bbox_height_positive"),
        sa.CheckConstraint(
            "detection_confidence >= 0 AND detection_confidence <= 1",
            name="detection_confidence_range",
        ),
        sa.CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)",
            name="quality_score_range",
        ),
    )


class RecognitionResult(Base):
    __tablename__ = "recognition_result"

    result_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    process_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("process_record.process_id"), nullable=False
    )
    face_index: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    matched_face_identity_id: sa.orm.Mapped[UUID | None] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("face_identity.face_identity_id"), nullable=True
    )
    matched_sample_id: sa.orm.Mapped[UUID | None] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("face_sample.sample_id"), nullable=True
    )
    recognition_status: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(16), nullable=False)
    bbox_x: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    bbox_y: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    bbox_width: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    bbox_height: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    detection_confidence: sa.orm.Mapped[float] = sa.orm.mapped_column(sa.REAL, nullable=False)
    similarity_score: sa.orm.Mapped[float | None] = sa.orm.mapped_column(sa.REAL, nullable=True)
    threshold_used: sa.orm.Mapped[float] = sa.orm.mapped_column(sa.REAL, nullable=False)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        sa.UniqueConstraint("process_id", "face_index", name="uq_recognition_result_process_id_face_index"),
        sa.Index("ix_recognition_result_matched_face_identity_id_created_at", "matched_face_identity_id", "created_at"),
        sa.Index("ix_recognition_result_matched_sample_id", "matched_sample_id"),
        sa.Index("ix_recognition_result_recognition_status_created_at", "recognition_status", "created_at"),
        sa.CheckConstraint(
            "recognition_status IN ('known', 'unknown')",
            name="status_values",
        ),
        sa.CheckConstraint("bbox_width > 0", name="bbox_width_positive"),
        sa.CheckConstraint("bbox_height > 0", name="bbox_height_positive"),
        sa.CheckConstraint(
            "detection_confidence >= 0 AND detection_confidence <= 1",
            name="detection_confidence_range",
        ),
        sa.CheckConstraint(
            """
            (
                recognition_status = 'known'
                AND matched_face_identity_id IS NOT NULL
                AND matched_sample_id IS NOT NULL
                AND similarity_score IS NOT NULL
            )
            OR
            (
                recognition_status = 'unknown'
                AND matched_face_identity_id IS NULL
                AND matched_sample_id IS NULL
                AND similarity_score IS NULL
            )
            """,
            name="status_consistency",
        ),
        sa.CheckConstraint("face_index >= 0", name="face_index_nonnegative"),
    )


class ProcessEvent(Base):
    __tablename__ = "process_event"

    event_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    process_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("process_record.process_id"), nullable=False
    )
    sequence_no: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    event_type: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    details: sa.orm.Mapped[dict[str, Any]] = sa.orm.mapped_column(
        JSONB, nullable=False, default=dict
    )
    occurred_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        sa.UniqueConstraint("process_id", "sequence_no", name="uq_process_event_process_id_sequence_no"),
        sa.Index("ix_process_event_occurred_at", "occurred_at"),
    )

```

#### `backend/src/mergenvision/infrastructure/database/repositories.py`

```python
from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from mergenvision.domain import entities as domain
from mergenvision.domain.entities import (
    FaceIdentity,
    FaceSample,
    InferenceProfile,
    Person,
    PersonPhoto,
    ProcessEvent,
    ProcessRecord,
    RecognitionResult,
)
from mergenvision.domain.enums import (
    FaceIdentityStatus,
    PersonPhotoStatus,
    PersonStatus,
    ProcessStatus,
    SampleStatus,
)
from mergenvision.domain.errors import ConflictError, NotFoundError, RepositoryError
from mergenvision.domain.ids import new_uuid7
from mergenvision.infrastructure.database import mappers
from mergenvision.infrastructure.database import models as orm
from mergenvision.ports.repositories import (
    FaceIdentityRepository,
    FaceSampleRepository,
    InferenceProfileRepository,
    PersonPhotoRepository,
    PersonRepository,
    ProcessEventRepository,
    ProcessRecordRepository,
    RecognitionResultRepository,
)


def _handle_db_error(exc: Exception) -> None:
    if isinstance(exc, IntegrityError):
        raise ConflictError("Resource conflict or constraint violation") from exc
    if isinstance(exc, SQLAlchemyError):
        raise RepositoryError("Database operation failed") from exc
    raise exc


class PostgresPersonRepository(PersonRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, person: Person) -> Person:
        orm_obj = orm.Person(**dataclasses.asdict(person))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person(orm_obj)

    async def get_by_id(self, person_id: UUID) -> Person | None:
        stmt = (
            select(orm.Person)
            .where(orm.Person.person_id == person_id)
            .where(orm.Person.status == PersonStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_person(row) if row else None

    async def get_by_national_id_lookup_hash(self, lookup_hash: str) -> Person | None:
        stmt = select(orm.Person).where(orm.Person.national_id_lookup_hash == lookup_hash)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_person(row) if row else None

    async def list_active(self, *, limit: int, offset: int) -> list[Person]:
        stmt = (
            select(orm.Person)
            .where(orm.Person.status == PersonStatus.ACTIVE)
            .order_by(orm.Person.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_person(row) for row in result.scalars().all()]

    async def update(
        self,
        person_id: UUID,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        additional_details: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> Person | None:
        row = await self._get_active_orm(person_id)
        if row is None:
            return None
        if first_name is not None:
            row.first_name = first_name
        if last_name is not None:
            row.last_name = last_name
        if additional_details is not None:
            row.additional_details = additional_details
        if status is not None:
            row.status = status
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person(row)

    async def deactivate(self, person_id: UUID) -> Person | None:
        row = await self._get_active_orm(person_id)
        if row is None:
            return None
        row.status = PersonStatus.INACTIVE
        row.deleted_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person(row)

    async def _get_active_orm(self, person_id: UUID) -> orm.Person | None:
        stmt = (
            select(orm.Person)
            .where(orm.Person.person_id == person_id)
            .where(orm.Person.status == PersonStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class PostgresFaceIdentityRepository(FaceIdentityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, face_identity: FaceIdentity) -> FaceIdentity:
        orm_obj = orm.FaceIdentity(**dataclasses.asdict(face_identity))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_identity(orm_obj)

    async def get_by_id(self, face_identity_id: UUID) -> FaceIdentity | None:
        stmt = (
            select(orm.FaceIdentity)
            .where(orm.FaceIdentity.face_identity_id == face_identity_id)
            .where(orm.FaceIdentity.status == FaceIdentityStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_face_identity(row) if row else None

    async def get_by_person_id(self, person_id: UUID) -> FaceIdentity | None:
        stmt = (
            select(orm.FaceIdentity)
            .where(orm.FaceIdentity.person_id == person_id)
            .where(orm.FaceIdentity.status == FaceIdentityStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_face_identity(row) if row else None

    async def deactivate(self, face_identity_id: UUID) -> FaceIdentity | None:
        stmt = (
            select(orm.FaceIdentity)
            .where(orm.FaceIdentity.face_identity_id == face_identity_id)
            .where(orm.FaceIdentity.status == FaceIdentityStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = FaceIdentityStatus.INACTIVE
        row.deleted_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_identity(row)


class PostgresInferenceProfileRepository(InferenceProfileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, profile: InferenceProfile) -> InferenceProfile:
        orm_obj = orm.InferenceProfile(**dataclasses.asdict(profile))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_inference_profile(orm_obj)

    async def get_by_id(self, profile_id: UUID) -> InferenceProfile | None:
        stmt = select(orm.InferenceProfile).where(
            orm.InferenceProfile.inference_profile_id == profile_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_inference_profile(row) if row else None

    async def get_by_name(self, profile_name: str) -> InferenceProfile | None:
        stmt = select(orm.InferenceProfile).where(
            orm.InferenceProfile.profile_name == profile_name
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_inference_profile(row) if row else None

    async def get_active(self) -> InferenceProfile | None:
        stmt = select(orm.InferenceProfile).where(
            orm.InferenceProfile.is_active.is_(True)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_inference_profile(row) if row else None

    async def retire(self, profile_id: UUID) -> InferenceProfile | None:
        stmt = select(orm.InferenceProfile).where(
            orm.InferenceProfile.inference_profile_id == profile_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.is_active = False
        row.retired_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_inference_profile(row)


class PostgresProcessRecordRepository(ProcessRecordRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, record: ProcessRecord) -> ProcessRecord:
        orm_obj = orm.ProcessRecord(**dataclasses.asdict(record))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_record(orm_obj)

    async def get_by_id(self, process_id: UUID) -> ProcessRecord | None:
        stmt = select(orm.ProcessRecord).where(orm.ProcessRecord.process_id == process_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_process_record(row) if row else None

    async def mark_started(self, process_id: UUID) -> ProcessRecord | None:
        row = await self._get_orm(process_id)
        if row is None:
            return None
        row.status = ProcessStatus.PROCESSING
        row.started_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_record(row)

    async def mark_completed(
        self,
        process_id: UUID,
        *,
        detected_face_count: int | None = None,
    ) -> ProcessRecord | None:
        row = await self._get_orm(process_id)
        if row is None:
            return None
        row.status = ProcessStatus.COMPLETED
        row.completed_at = datetime.now(UTC)
        if detected_face_count is not None:
            row.detected_face_count = detected_face_count
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_record(row)

    async def mark_failed(
        self,
        process_id: UUID,
        *,
        error_code: str,
        error_message_sanitized: str,
    ) -> ProcessRecord | None:
        row = await self._get_orm(process_id)
        if row is None:
            return None
        row.status = ProcessStatus.FAILED
        row.completed_at = datetime.now(UTC)
        row.error_code = error_code
        row.error_message_sanitized = error_message_sanitized
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_record(row)

    async def _get_orm(self, process_id: UUID) -> orm.ProcessRecord | None:
        stmt = select(orm.ProcessRecord).where(orm.ProcessRecord.process_id == process_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class PostgresPersonPhotoRepository(PersonPhotoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, photo: PersonPhoto) -> PersonPhoto:
        orm_obj = orm.PersonPhoto(**dataclasses.asdict(photo))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person_photo(orm_obj)

    async def get_by_id(self, photo_id: UUID) -> PersonPhoto | None:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.photo_id == photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_person_photo(row) if row else None

    async def list_by_person(self, person_id: UUID, *, limit: int, offset: int) -> list[PersonPhoto]:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.person_id == person_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
            .order_by(orm.PersonPhoto.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_person_photo(row) for row in result.scalars().all()]

    async def set_primary(self, photo_id: UUID) -> PersonPhoto | None:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.photo_id == photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        await self._session.execute(
            update(orm.PersonPhoto)
            .where(orm.PersonPhoto.person_id == row.person_id)
            .where(orm.PersonPhoto.photo_id != row.photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
            .values(is_primary=False)
        )
        row.is_primary = True
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person_photo(row)

    async def deactivate(self, photo_id: UUID) -> PersonPhoto | None:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.photo_id == photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = PersonPhotoStatus.INACTIVE
        row.deleted_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        if row.is_primary:
            row.is_primary = False
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person_photo(row)


class PostgresFaceSampleRepository(FaceSampleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, sample: FaceSample) -> FaceSample:
        orm_obj = orm.FaceSample(**dataclasses.asdict(sample))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_sample(orm_obj)

    async def get_by_id(self, sample_id: UUID) -> FaceSample | None:
        stmt = (
            select(orm.FaceSample)
            .where(orm.FaceSample.sample_id == sample_id)
            .where(orm.FaceSample.status == SampleStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_face_sample(row) if row else None

    async def list_active_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[FaceSample]:
        stmt = (
            select(orm.FaceSample)
            .where(orm.FaceSample.face_identity_id == face_identity_id)
            .where(orm.FaceSample.status == SampleStatus.ACTIVE)
            .order_by(orm.FaceSample.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_face_sample(row) for row in result.scalars().all()]

    async def deactivate(self, sample_id: UUID) -> FaceSample | None:
        stmt = (
            select(orm.FaceSample)
            .where(orm.FaceSample.sample_id == sample_id)
            .where(orm.FaceSample.status == SampleStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = SampleStatus.INACTIVE
        row.deleted_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_sample(row)


class PostgresRecognitionResultRepository(RecognitionResultRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, result: RecognitionResult) -> RecognitionResult:
        orm_obj = orm.RecognitionResult(**dataclasses.asdict(result))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_recognition_result(orm_obj)

    async def list_by_process(self, process_id: UUID) -> list[RecognitionResult]:
        stmt = (
            select(orm.RecognitionResult)
            .where(orm.RecognitionResult.process_id == process_id)
            .order_by(orm.RecognitionResult.face_index.asc())
        )
        result = await self._session.execute(stmt)
        return [mappers.map_recognition_result(row) for row in result.scalars().all()]

    async def list_history_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[RecognitionResult]:
        stmt = (
            select(orm.RecognitionResult)
            .where(orm.RecognitionResult.matched_face_identity_id == face_identity_id)
            .order_by(orm.RecognitionResult.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_recognition_result(row) for row in result.scalars().all()]


class PostgresProcessEventRepository(ProcessEventRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        process_id: UUID,
        *,
        event_type: str,
        details: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> ProcessEvent:
        lock_stmt = (
            select(orm.ProcessRecord)
            .where(orm.ProcessRecord.process_id == process_id)
            .with_for_update()
        )
        lock_result = await self._session.execute(lock_stmt)
        process = lock_result.scalar_one_or_none()
        if process is None:
            raise NotFoundError(f"Process {process_id} not found")
        next_sequence = await self._next_sequence_no(process_id)
        event = domain.ProcessEvent(
            event_id=new_uuid7(),
            process_id=process_id,
            sequence_no=next_sequence,
            event_type=event_type,
            details=details if details is not None else {},
            occurred_at=occurred_at if occurred_at is not None else datetime.now(UTC),
        )
        orm_obj = orm.ProcessEvent(**dataclasses.asdict(event))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_event(orm_obj)

    async def list_by_process(
        self,
        process_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[ProcessEvent]:
        stmt = (
            select(orm.ProcessEvent)
            .where(orm.ProcessEvent.process_id == process_id)
            .order_by(orm.ProcessEvent.sequence_no.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_process_event(row) for row in result.scalars().all()]

    async def _next_sequence_no(self, process_id: UUID) -> int:
        stmt = select(
            func.coalesce(func.max(orm.ProcessEvent.sequence_no), 0) + 1
        ).where(orm.ProcessEvent.process_id == process_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

```

#### `backend/tests/unit/test_uuid7.py`

```python
from uuid import UUID

from mergenvision.domain.ids import new_uuid7


def test_new_uuid7_returns_uuid7():
    value = new_uuid7()
    assert isinstance(value, UUID)
    assert value.version == 7


def test_new_uuid7_generates_unique_values():
    values = {new_uuid7() for _ in range(1000)}
    assert len(values) == 1000


def test_new_uuid7_is_time_ordered_under_reasonable_generation():
    ids = [new_uuid7() for _ in range(20)]
    for previous, current in zip(ids, ids[1:], strict=False):
        assert current.int > previous.int

```

#### `backend/tests/unit/test_national_id_protection.py`

```python
import base64
import os

import pytest

from mergenvision.domain.errors import SecurityError
from mergenvision.infrastructure.security.national_id import AesGcmNationalIdProtector
from mergenvision.ports.national_id import NationalIdProtectedValue


def _key_b64() -> str:
    return base64.b64encode(os.urandom(32)).decode("ascii")


def _other_key_b64() -> str:
    return base64.b64encode(os.urandom(32)).decode("ascii")


@pytest.fixture
def protector() -> AesGcmNationalIdProtector:
    return AesGcmNationalIdProtector(
        encryption_key_b64=_key_b64(),
        hmac_key_b64=_key_b64(),
    )


def test_encrypt_then_decrypt_round_trip(protector: AesGcmNationalIdProtector) -> None:
    raw = "12345678901"
    protected = protector.protect(raw)
    assert protector.reveal(protected) == raw


def test_repeated_encryption_produces_different_ciphertexts(
    protector: AesGcmNationalIdProtector,
) -> None:
    raw = "12345678901"
    first = protector.protect(raw)
    second = protector.protect(raw)
    assert first.ciphertext != second.ciphertext
    assert first.lookup_hash == second.lookup_hash


def test_hmac_is_deterministic_for_same_key(protector: AesGcmNationalIdProtector) -> None:
    raw = "12345678901"
    a = protector.protect(raw)
    b = protector.protect(raw)
    assert a.lookup_hash == b.lookup_hash


def test_different_hmac_key_produces_different_hash() -> None:
    raw = "12345678901"
    p1 = AesGcmNationalIdProtector(
        encryption_key_b64=_key_b64(),
        hmac_key_b64=_key_b64(),
    )
    p2 = AesGcmNationalIdProtector(
        encryption_key_b64=p1.encryption_key_b64(),
        hmac_key_b64=_other_key_b64(),
    )
    assert p1.protect(raw).lookup_hash != p2.protect(raw).lookup_hash


def test_masking_reveals_last_four_digits(protector: AesGcmNationalIdProtector) -> None:
    protected = protector.protect("12345678901")
    assert protected.masked == "*******8901"


def test_masking_short_value_is_fully_masked(protector: AesGcmNationalIdProtector) -> None:
    protected = protector.protect("1234")
    assert protected.masked == "****"


def test_normalization_trims_and_nfkc(protector: AesGcmNationalIdProtector) -> None:
    raw = "\u00A0  123456789  \u00A0"
    protected = protector.protect(raw)
    assert protector.reveal(protected) == "123456789"


def test_protected_repr_does_not_contain_raw_id(protector: AesGcmNationalIdProtector) -> None:
    raw = "12345678901"
    protected = protector.protect(raw)
    representation = repr(protected)
    assert raw not in representation
    assert "lookup_hash" in representation or "protected" in representation


def test_invalid_encryption_key_size_fails_closed() -> None:
    with pytest.raises(SecurityError):
        AesGcmNationalIdProtector(
            encryption_key_b64=base64.b64encode(os.urandom(16)).decode("ascii"),
            hmac_key_b64=_key_b64(),
        )


def test_invalid_hmac_key_size_fails_closed() -> None:
    with pytest.raises(SecurityError):
        AesGcmNationalIdProtector(
            encryption_key_b64=_key_b64(),
            hmac_key_b64=base64.b64encode(os.urandom(16)).decode("ascii"),
        )


def test_tampered_ciphertext_raises_security_error(
    protector: AesGcmNationalIdProtector,
) -> None:
    protected = protector.protect("12345678901")
    tampered = NationalIdProtectedValue(
        ciphertext=protected.ciphertext[:-1] + bytes([protected.ciphertext[-1] ^ 1]),
        lookup_hash=protected.lookup_hash,
        masked=protected.masked,
    )
    with pytest.raises(SecurityError):
        protector.reveal(tampered)


def test_wrong_encryption_key_raises_security_error() -> None:
    raw = "12345678901"
    p1 = AesGcmNationalIdProtector(
        encryption_key_b64=_key_b64(),
        hmac_key_b64=_key_b64(),
    )
    p2 = AesGcmNationalIdProtector(
        encryption_key_b64=_other_key_b64(),
        hmac_key_b64=p1.hmac_key_b64(),
    )
    protected = p1.protect(raw)
    with pytest.raises(SecurityError):
        p2.reveal(protected)

```

#### `backend/tests/unit/test_domain_entities.py`

```python
from dataclasses import fields
from datetime import UTC, datetime
from uuid import UUID, uuid7

from mergenvision.domain.entities import (
    FaceSample,
    InferenceProfile,
    Person,
    PersonPhoto,
    ProcessEvent,
    RecognitionResult,
)
from mergenvision.domain.enums import (
    FaceIdentityStatus,
    PersonPhotoStatus,
    PersonStatus,
    ProcessStatus,
    RecognitionStatus,
    SampleStatus,
)


def test_status_constants_are_strings() -> None:
    assert PersonStatus.ACTIVE == "active"
    assert PersonStatus.INACTIVE == "inactive"
    assert FaceIdentityStatus.ACTIVE == "active"
    assert ProcessStatus.PENDING == "pending"
    assert ProcessStatus.PROCESSING == "processing"
    assert ProcessStatus.COMPLETED == "completed"
    assert ProcessStatus.FAILED == "failed"
    assert RecognitionStatus.KNOWN == "known"
    assert RecognitionStatus.UNKNOWN == "unknown"


def test_person_entity_fields() -> None:
    now = datetime.now(UTC)
    entity = Person(
        person_id=uuid7(),
        first_name="Ada",
        last_name="Lovelace",
        national_id_ciphertext=b"ct",
        national_id_lookup_hash="hash",
        national_id_masked="*******1234",
        additional_details={"department": "Research"},
        status=PersonStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    assert isinstance(entity.person_id, UUID)
    assert entity.status == PersonStatus.ACTIVE
    assert len(fields(Person)) == 11


def test_recognition_result_known_requires_references() -> None:
    result = RecognitionResult(
        result_id=uuid7(),
        process_id=uuid7(),
        face_index=0,
        matched_face_identity_id=uuid7(),
        matched_sample_id=uuid7(),
        recognition_status=RecognitionStatus.KNOWN,
        bbox_x=10,
        bbox_y=20,
        bbox_width=100,
        bbox_height=100,
        detection_confidence=0.99,
        similarity_score=0.85,
        threshold_used=0.70,
        created_at=datetime.now(UTC),
    )
    assert result.recognition_status == RecognitionStatus.KNOWN
    assert result.similarity_score is not None


def test_recognition_result_unknown_has_no_references() -> None:
    result = RecognitionResult(
        result_id=uuid7(),
        process_id=uuid7(),
        face_index=0,
        recognition_status=RecognitionStatus.UNKNOWN,
        bbox_x=10,
        bbox_y=20,
        bbox_width=100,
        bbox_height=100,
        detection_confidence=0.99,
        threshold_used=0.70,
        created_at=datetime.now(UTC),
    )
    assert result.recognition_status == RecognitionStatus.UNKNOWN
    assert result.matched_face_identity_id is None
    assert result.matched_sample_id is None
    assert result.similarity_score is None


def test_process_event_default_details() -> None:
    event = ProcessEvent(
        event_id=uuid7(),
        process_id=uuid7(),
        sequence_no=1,
        event_type="started",
        occurred_at=datetime.now(UTC),
    )
    assert event.details == {}


def test_inference_profile_entity() -> None:
    profile = InferenceProfile(
        inference_profile_id=uuid7(),
        profile_name="retinaface-arcface-v1",
        detector_name="retinaface",
        detector_version="1.0",
        detector_artifact_sha256="sha",
        alignment_version="v1",
        embedder_name="arcface",
        embedder_version="1.0",
        embedder_artifact_sha256="sha",
        preprocessing_version="v1",
        embedding_dimension=512,
        distance_metric="cosine",
        match_threshold=0.65,
        is_active=True,
        created_at=datetime.now(UTC),
    )
    assert profile.embedding_dimension == 512
    assert profile.is_active is True


def test_face_sample_entity_landmarks() -> None:
    sample = FaceSample(
        sample_id=uuid7(),
        face_identity_id=uuid7(),
        photo_id=uuid7(),
        inference_profile_id=uuid7(),
        bbox_x=0,
        bbox_y=0,
        bbox_width=100,
        bbox_height=100,
        landmarks={"left_eye": [10, 10]},
        detection_confidence=0.98,
        quality_score=0.91,
        status=SampleStatus.ACTIVE,
        created_at=datetime.now(UTC),
    )
    assert sample.landmarks == {"left_eye": [10, 10]}


def test_person_photo_entity() -> None:
    photo = PersonPhoto(
        photo_id=uuid7(),
        person_id=uuid7(),
        object_key="people/test/source.jpg",
        content_sha256="sha",
        mime_type="image/jpeg",
        file_size_bytes=1234,
        width=1920,
        height=1080,
        is_primary=True,
        status=PersonPhotoStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert photo.is_primary is True

```

#### `backend/tests/unit/test_database_metadata_contract.py`

```python

from mergenvision.infrastructure.database.base import Base
from mergenvision.infrastructure.database.models import (
    Person,
    PersonPhoto,
    RecognitionResult,
)

EXPECTED_TABLES = {
    "person",
    "face_identity",
    "process_record",
    "inference_profile",
    "person_photo",
    "face_sample",
    "recognition_result",
    "process_event",
}


def test_all_business_tables_defined() -> None:
    tables = set(Base.metadata.tables.keys())
    assert tables >= EXPECTED_TABLES


def test_person_columns_match_frozen_contract() -> None:
    columns = {col.name for col in Person.__table__.columns}
    expected = {
        "person_id",
        "first_name",
        "last_name",
        "national_id_ciphertext",
        "national_id_lookup_hash",
        "national_id_masked",
        "additional_details",
        "status",
        "created_at",
        "updated_at",
        "deleted_at",
    }
    assert columns == expected


def test_person_primary_key_is_uuid() -> None:
    pk = Person.__table__.primary_key
    assert len(pk.columns) == 1
    assert pk.columns[0].name == "person_id"


def test_recognition_result_check_constraint_exists() -> None:
    checks = {c.name for c in RecognitionResult.__table__.constraints if hasattr(c, "name")}
    assert "ck_recognition_result_status_consistency" in checks


def test_person_photo_unique_constraints() -> None:
    unique_names = {c.name for c in PersonPhoto.__table__.constraints if hasattr(c, "name")}
    assert "uq_person_photo_object_key" in unique_names
    assert "uq_person_photo_person_id_content_sha256" in unique_names


def test_indexes_are_defined() -> None:
    index_names = {idx.name for idx in Base.metadata.tables["person"].indexes}
    assert "ix_person_status" in index_names
    face_indexes = {idx.name for idx in Base.metadata.tables["face_sample"].indexes}
    assert "ix_face_sample_face_identity_id_status" in face_indexes
    assert "ix_face_sample_inference_profile_id_status" in face_indexes


def test_foreign_keys_exist_for_person_photo() -> None:
    fks = {fk.name for fk in PersonPhoto.__table__.foreign_keys if hasattr(fk, "name")}
    assert "fk_person_photo_person_id" in fks or len(PersonPhoto.__table__.foreign_keys) >= 1

```

#### `backend/tests/integration/conftest.py`

```python
import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mergenvision.config.settings import Settings

if not os.environ.get("MERGENVISION_DATABASE_URL"):
    pytest.skip("MERGENVISION_DATABASE_URL not set; skipping integration tests", allow_module_level=True)


@pytest_asyncio.fixture
async def db_engine():
    settings = Settings()
    engine = create_async_engine(
        settings.database_url,
        future=True,
        pool_pre_ping=True,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(db_engine) -> AsyncSession:
    factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as s:
        yield s
        await s.rollback()

```

#### `backend/tests/integration/test_alembic_postgres.py`

```python
import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import inspect

from mergenvision.config.settings import Settings

EXPECTED_TABLES = {
    "person",
    "face_identity",
    "process_record",
    "inference_profile",
    "person_photo",
    "face_sample",
    "recognition_result",
    "process_event",
}

REPO_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC = REPO_ROOT / ".venv" / "bin" / "alembic"


def _run_alembic(*command: str) -> None:
    settings = Settings()
    env = os.environ.copy()
    env["MERGENVISION_DATABASE_URL"] = settings.database_url
    subprocess.run(
        [str(ALEMBIC), "-c", "backend/alembic.ini", *command],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )


def _table_names(sync_conn):
    return set(inspect(sync_conn).get_table_names())


@pytest.mark.asyncio
async def test_alembic_upgrade_downgrade_reupgrade(db_engine):
    async with db_engine.begin() as conn:
        _run_alembic("downgrade", "base")
        tables_after_downgrade = await conn.run_sync(_table_names)
        assert EXPECTED_TABLES.isdisjoint(tables_after_downgrade)

        _run_alembic("upgrade", "head")
        tables_after_upgrade = await conn.run_sync(_table_names)
        assert tables_after_upgrade >= EXPECTED_TABLES

        _run_alembic("downgrade", "base")
        _run_alembic("upgrade", "head")
        tables_after_reupgrade = await conn.run_sync(_table_names)
        assert tables_after_reupgrade >= EXPECTED_TABLES


def _gather_constraints_and_indexes(sync_conn):
    inspector = inspect(sync_conn)
    data = {}
    for table in [
        "person",
        "face_identity",
        "person_photo",
        "face_sample",
        "recognition_result",
        "process_event",
    ]:
        data[table] = {
            "unique": {c["name"] for c in inspector.get_unique_constraints(table)},
            "indexes": {idx["name"] for idx in inspector.get_indexes(table)},
            "checks": {c["name"] for c in inspector.get_check_constraints(table)},
        }
    return data


@pytest.mark.asyncio
async def test_required_constraints_and_indexes_exist(db_engine):
    _run_alembic("upgrade", "head")

    async with db_engine.begin() as conn:
        data = await conn.run_sync(_gather_constraints_and_indexes)

    assert "uq_person_national_id_lookup_hash" in data["person"]["unique"]
    assert "ix_person_status" in data["person"]["indexes"]

    assert "uq_face_identity_person_id" in data["face_identity"]["unique"]

    assert "uq_person_photo_object_key" in data["person_photo"]["unique"]
    assert "uq_person_photo_person_id_content_sha256" in data["person_photo"]["unique"]
    assert "ix_person_photo_person_id_status" in data["person_photo"]["indexes"]
    assert "ix_uq_person_photo_active_primary" in data["person_photo"]["indexes"]

    assert "uq_face_sample_photo_id_inference_profile_id" in data["face_sample"]["unique"]
    assert "ix_face_sample_face_identity_id_status" in data["face_sample"]["indexes"]
    assert "ix_face_sample_inference_profile_id_status" in data["face_sample"]["indexes"]

    assert "uq_recognition_result_process_id_face_index" in data["recognition_result"]["unique"]
    assert "ix_recognition_result_matched_face_identity_id_created_at" in data["recognition_result"]["indexes"]
    assert "ix_recognition_result_matched_sample_id" in data["recognition_result"]["indexes"]
    assert "ix_recognition_result_recognition_status_created_at" in data["recognition_result"]["indexes"]

    assert "uq_process_event_process_id_sequence_no" in data["process_event"]["unique"]
    assert "ix_process_event_occurred_at" in data["process_event"]["indexes"]

    assert "ck_recognition_result_status_consistency" in data["recognition_result"]["checks"]
    assert "ck_recognition_result_status_values" in data["recognition_result"]["checks"]

```

#### `backend/tests/integration/test_postgres_constraints.py`

```python
import base64
import os
import random
from uuid import uuid7

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from mergenvision.domain.enums import (
    FaceIdentityStatus,
    PersonPhotoStatus,
    PersonStatus,
    ProcessStatus,
    RecognitionStatus,
    SampleStatus,
)
from mergenvision.infrastructure.database import models as orm
from mergenvision.infrastructure.security.national_id import AesGcmNationalIdProtector

PROTECTOR = AesGcmNationalIdProtector(
    encryption_key_b64=base64.b64encode(os.urandom(32)).decode("ascii"),
    hmac_key_b64=base64.b64encode(os.urandom(32)).decode("ascii"),
)


def _unique_national_id() -> str:
    return f"nat-{random.randint(100000000, 999999999)}"


def _make_person(national_id: str | None = None) -> orm.Person:
    raw = national_id or _unique_national_id()
    protected = PROTECTOR.protect(raw)
    return orm.Person(
        person_id=uuid7(),
        first_name="Ada",
        last_name="Lovelace",
        national_id_ciphertext=protected.ciphertext,
        national_id_lookup_hash=protected.lookup_hash,
        national_id_masked=protected.masked,
        additional_details={},
        status=PersonStatus.ACTIVE,
    )


def _make_face_identity(person_id) -> orm.FaceIdentity:
    return orm.FaceIdentity(
        face_identity_id=uuid7(),
        person_id=person_id,
        status=FaceIdentityStatus.ACTIVE,
    )


def _make_profile(name: str = "default") -> orm.InferenceProfile:
    return orm.InferenceProfile(
        inference_profile_id=uuid7(),
        profile_name=name,
        detector_name="retinaface",
        detector_version="1",
        detector_artifact_sha256="sha",
        alignment_version="v1",
        embedder_name="arcface",
        embedder_version="1",
        embedder_artifact_sha256="sha",
        preprocessing_version="v1",
        embedding_dimension=512,
        distance_metric="cosine",
        match_threshold=0.65,
        is_active=True,
    )


def _make_photo(
    person_id,
    object_key: str,
    *,
    is_primary: bool = False,
    content_sha256: str | None = None,
) -> orm.PersonPhoto:
    return orm.PersonPhoto(
        photo_id=uuid7(),
        person_id=person_id,
        object_key=object_key,
        content_sha256=content_sha256 or ("sha" + object_key),
        mime_type="image/jpeg",
        file_size_bytes=1234,
        width=100,
        height=100,
        is_primary=is_primary,
        status=PersonPhotoStatus.ACTIVE,
    )


def _make_sample(face_identity_id, photo_id, profile_id) -> orm.FaceSample:
    return orm.FaceSample(
        sample_id=uuid7(),
        face_identity_id=face_identity_id,
        photo_id=photo_id,
        inference_profile_id=profile_id,
        bbox_x=0,
        bbox_y=0,
        bbox_width=50,
        bbox_height=50,
        landmarks={},
        detection_confidence=0.99,
        quality_score=0.9,
        status=SampleStatus.ACTIVE,
    )


def _make_process() -> orm.ProcessRecord:
    return orm.ProcessRecord(
        process_id=uuid7(),
        process_type="identification",
        status=ProcessStatus.PENDING,
    )


@pytest.mark.asyncio
async def test_duplicate_national_id_lookup_hash_rejected(session):
    person1 = _make_person("same-id")
    person2 = _make_person("same-id")
    session.add(person1)
    await session.flush()
    session.add(person2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_second_face_identity_for_person_rejected(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    identity1 = _make_face_identity(person.person_id)
    identity2 = _make_face_identity(person.person_id)
    session.add(identity1)
    await session.flush()
    session.add(identity2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_duplicate_object_key_rejected(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo1 = _make_photo(person.person_id, "same-key")
    photo2 = _make_photo(person.person_id, "same-key")
    session.add(photo1)
    await session.flush()
    session.add(photo2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_duplicate_photo_content_rejected(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo1 = _make_photo(person.person_id, "key-1", content_sha256="dup-sha")
    photo2 = _make_photo(person.person_id, "key-2", content_sha256="dup-sha")
    session.add(photo1)
    await session.flush()
    session.add(photo2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_two_active_primary_photos_rejected(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo1 = _make_photo(person.person_id, "primary-1", is_primary=True)
    photo2 = _make_photo(person.person_id, "primary-2", is_primary=True)
    session.add(photo1)
    await session.flush()
    session.add(photo2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_two_active_primary_photos_different_persons_allowed(session):
    person1 = _make_person()
    person2 = _make_person()
    session.add_all([person1, person2])
    await session.flush()
    photo1 = _make_photo(person1.person_id, "primary-a", is_primary=True)
    photo2 = _make_photo(person2.person_id, "primary-b", is_primary=True)
    session.add_all([photo1, photo2])
    await session.flush()

    result = await session.execute(
        select(orm.PersonPhoto).where(orm.PersonPhoto.is_primary.is_(True))
    )
    assert len(result.scalars().all()) == 2


@pytest.mark.asyncio
async def test_duplicate_face_sample_photo_profile_rejected(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "sample-photo")
    session.add(photo)
    await session.flush()
    sample1 = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    sample2 = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    session.add(sample1)
    await session.flush()
    session.add(sample2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_duplicate_recognition_result_process_face_index_rejected(session):
    process = _make_process()
    session.add(process)
    await session.flush()
    result1 = orm.RecognitionResult(
        result_id=uuid7(),
        process_id=process.process_id,
        face_index=0,
        recognition_status=RecognitionStatus.UNKNOWN,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
    )
    result2 = orm.RecognitionResult(
        result_id=uuid7(),
        process_id=process.process_id,
        face_index=0,
        recognition_status=RecognitionStatus.UNKNOWN,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
    )
    session.add(result1)
    await session.flush()
    session.add(result2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_duplicate_process_event_sequence_rejected(session):
    process = _make_process()
    session.add(process)
    await session.flush()
    event1 = orm.ProcessEvent(
        event_id=uuid7(),
        process_id=process.process_id,
        sequence_no=1,
        event_type="started",
    )
    event2 = orm.ProcessEvent(
        event_id=uuid7(),
        process_id=process.process_id,
        sequence_no=1,
        event_type="completed",
    )
    session.add(event1)
    await session.flush()
    session.add(event2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_photo_file_size_must_be_positive(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo = _make_photo(person.person_id, "bad-size")
    photo.file_size_bytes = 0
    session.add(photo)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_photo_dimensions_must_be_positive(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo = _make_photo(person.person_id, "bad-width")
    photo.width = 0
    session.add(photo)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_face_sample_bbox_must_be_positive(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "sample-bad")
    session.add(photo)
    await session.flush()
    sample = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    sample.bbox_width = 0
    session.add(sample)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_detection_confidence_must_be_zero_to_one(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "sample-conf")
    session.add(photo)
    await session.flush()
    sample = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    sample.detection_confidence = 1.5
    session.add(sample)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_quality_score_must_be_zero_to_one_or_null(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "sample-quality")
    session.add(photo)
    await session.flush()
    sample = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    sample.quality_score = 1.5
    session.add(sample)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_inference_profile_dimension_must_be_positive(session):
    profile = _make_profile()
    profile.embedding_dimension = 0
    session.add(profile)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_process_input_size_positive(session):
    process = _make_process()
    process.input_size_bytes = 0
    session.add(process)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_process_input_width_positive(session):
    process = _make_process()
    process.input_width = 0
    session.add(process)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_process_detected_face_count_nonnegative(session):
    process = _make_process()
    process.detected_face_count = -1
    session.add(process)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_recognition_result_known_requires_references(session):
    process = _make_process()
    session.add(process)
    await session.flush()
    result = orm.RecognitionResult(
        result_id=uuid7(),
        process_id=process.process_id,
        face_index=0,
        recognition_status=RecognitionStatus.KNOWN,
        matched_face_identity_id=None,
        matched_sample_id=None,
        similarity_score=None,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
    )
    session.add(result)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_recognition_result_unknown_must_not_have_references(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "unknown-refs")
    session.add(photo)
    await session.flush()
    sample = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    session.add(sample)
    await session.flush()
    process = _make_process()
    session.add(process)
    await session.flush()
    result = orm.RecognitionResult(
        result_id=uuid7(),
        process_id=process.process_id,
        face_index=0,
        recognition_status=RecognitionStatus.UNKNOWN,
        matched_face_identity_id=identity.face_identity_id,
        matched_sample_id=sample.sample_id,
        similarity_score=0.5,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
    )
    session.add(result)
    with pytest.raises(IntegrityError):
        await session.flush()


def _get_foreign_keys(sync_conn):
    inspector = inspect(sync_conn)
    return {
        table: inspector.get_foreign_keys(table)
        for table in [
            "face_identity",
            "process_record",
            "person_photo",
            "face_sample",
            "recognition_result",
            "process_event",
        ]
    }


@pytest.mark.asyncio
async def test_no_broad_cascade_on_foreign_keys(db_engine):
    async with db_engine.begin() as conn:
        fks_by_table = await conn.run_sync(_get_foreign_keys)
    for _table, fks in fks_by_table.items():
        for fk in fks:
            assert fk.get("ondelete") is None
            assert fk.get("onupdate") is None

```

#### `backend/tests/integration/test_postgres_repositories.py`

```python
import base64
import os
import random
from datetime import UTC, datetime
from uuid import uuid7

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from mergenvision.domain.entities import (
    FaceIdentity,
    FaceSample,
    InferenceProfile,
    Person,
    PersonPhoto,
    ProcessRecord,
    RecognitionResult,
)
from mergenvision.domain.enums import (
    FaceIdentityStatus,
    PersonPhotoStatus,
    PersonStatus,
    ProcessStatus,
    RecognitionStatus,
    SampleStatus,
)
from mergenvision.domain.errors import ConflictError
from mergenvision.infrastructure.database import models as orm
from mergenvision.infrastructure.database.repositories import (
    PostgresFaceIdentityRepository,
    PostgresFaceSampleRepository,
    PostgresInferenceProfileRepository,
    PostgresPersonPhotoRepository,
    PostgresPersonRepository,
    PostgresProcessEventRepository,
    PostgresProcessRecordRepository,
    PostgresRecognitionResultRepository,
)
from mergenvision.infrastructure.security.national_id import AesGcmNationalIdProtector


def _key() -> str:
    return base64.b64encode(os.urandom(32)).decode("ascii")


@pytest.fixture
def protector() -> AesGcmNationalIdProtector:
    return AesGcmNationalIdProtector(
        encryption_key_b64=_key(),
        hmac_key_b64=_key(),
    )


def _unique_id() -> str:
    return f"id-{random.randint(100000000, 999999999)}"


def _make_person(protector: AesGcmNationalIdProtector, raw: str | None = None) -> Person:
    raw_id = raw or _unique_id()
    protected = protector.protect(raw_id)
    return Person(
        person_id=uuid7(),
        first_name="Ada",
        last_name="Lovelace",
        national_id_ciphertext=protected.ciphertext,
        national_id_lookup_hash=protected.lookup_hash,
        national_id_masked=protected.masked,
        additional_details={"department": "Research"},
        status=PersonStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_face_identity(person_id) -> FaceIdentity:
    return FaceIdentity(
        face_identity_id=uuid7(),
        person_id=person_id,
        status=FaceIdentityStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_profile(name: str = "profile") -> InferenceProfile:
    return InferenceProfile(
        inference_profile_id=uuid7(),
        profile_name=name,
        detector_name="retinaface",
        detector_version="1",
        detector_artifact_sha256="sha",
        alignment_version="v1",
        embedder_name="arcface",
        embedder_version="1",
        embedder_artifact_sha256="sha",
        preprocessing_version="v1",
        embedding_dimension=512,
        distance_metric="cosine",
        match_threshold=0.65,
        is_active=True,
        created_at=datetime.now(UTC),
    )


def _make_photo(person_id, object_key: str, *, is_primary: bool = False) -> PersonPhoto:
    return PersonPhoto(
        photo_id=uuid7(),
        person_id=person_id,
        object_key=object_key,
        content_sha256="sha" + object_key,
        mime_type="image/jpeg",
        file_size_bytes=1234,
        width=100,
        height=100,
        is_primary=is_primary,
        status=PersonPhotoStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_process(process_type: str = "identification") -> ProcessRecord:
    return ProcessRecord(
        process_id=uuid7(),
        process_type=process_type,
        status=ProcessStatus.PENDING,
        created_at=datetime.now(UTC),
    )


def _make_sample(identity_id, photo_id, profile_id) -> FaceSample:
    return FaceSample(
        sample_id=uuid7(),
        face_identity_id=identity_id,
        photo_id=photo_id,
        inference_profile_id=profile_id,
        bbox_x=0,
        bbox_y=0,
        bbox_width=50,
        bbox_height=50,
        landmarks={"left_eye": [10, 10]},
        detection_confidence=0.99,
        quality_score=0.9,
        status=SampleStatus.ACTIVE,
        created_at=datetime.now(UTC),
    )


def _make_result(
    process_id,
    face_index: int,
    status: str,
    *,
    identity_id=None,
    sample_id=None,
    similarity=None,
) -> RecognitionResult:
    return RecognitionResult(
        result_id=uuid7(),
        process_id=process_id,
        face_index=face_index,
        recognition_status=status,
        matched_face_identity_id=identity_id,
        matched_sample_id=sample_id,
        similarity_score=similarity,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_person_repository_crud(session: AsyncSession, protector: AesGcmNationalIdProtector):
    repo = PostgresPersonRepository(session)
    person = _make_person(protector)
    created = await repo.add(person)
    assert created.person_id == person.person_id

    fetched = await repo.get_by_id(created.person_id)
    assert fetched is not None
    assert fetched.national_id_lookup_hash == person.national_id_lookup_hash

    by_hash = await repo.get_by_national_id_lookup_hash(person.national_id_lookup_hash)
    assert by_hash is not None
    assert by_hash.person_id == person.person_id

    listed = await repo.list_active(limit=10, offset=0)
    assert any(p.person_id == person.person_id for p in listed)

    updated = await repo.update(
        person.person_id,
        first_name="Updated",
        additional_details={"department": "AI"},
    )
    assert updated is not None
    assert updated.first_name == "Updated"
    assert updated.additional_details == {"department": "AI"}

    deactivated = await repo.deactivate(person.person_id)
    assert deactivated is not None
    assert deactivated.status == PersonStatus.INACTIVE

    not_found = await repo.get_by_id(person.person_id)
    assert not_found is None


@pytest.mark.asyncio
async def test_person_repository_duplicate_national_id_raises_conflict(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    repo = PostgresPersonRepository(session)
    person1 = _make_person(protector, raw="duplicate")
    person2 = _make_person(protector, raw="duplicate")
    await repo.add(person1)
    with pytest.raises(ConflictError):
        await repo.add(person2)


@pytest.mark.asyncio
async def test_face_identity_repository(session: AsyncSession, protector: AesGcmNationalIdProtector):
    repo = PostgresFaceIdentityRepository(session)
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    identity = _make_face_identity(person.person_id)
    created = await repo.add(identity)
    assert created.face_identity_id == identity.face_identity_id

    fetched = await repo.get_by_id(created.face_identity_id)
    assert fetched is not None

    by_person = await repo.get_by_person_id(person.person_id)
    assert by_person is not None
    assert by_person.face_identity_id == created.face_identity_id

    deactivated = await repo.deactivate(created.face_identity_id)
    assert deactivated is not None
    assert deactivated.status == FaceIdentityStatus.INACTIVE


@pytest.mark.asyncio
async def test_inference_profile_repository(session: AsyncSession):
    repo = PostgresInferenceProfileRepository(session)
    profile = _make_profile("test-profile")
    created = await repo.add(profile)
    assert created.profile_name == "test-profile"

    fetched = await repo.get_by_id(created.inference_profile_id)
    assert fetched is not None

    by_name = await repo.get_by_name("test-profile")
    assert by_name is not None

    active = await repo.get_active()
    assert active is not None

    retired = await repo.retire(created.inference_profile_id)
    assert retired is not None
    assert retired.is_active is False


@pytest.mark.asyncio
async def test_process_record_repository(session: AsyncSession):
    repo = PostgresProcessRecordRepository(session)
    record = _make_process()
    created = await repo.add(record)
    assert created.status == ProcessStatus.PENDING

    started = await repo.mark_started(created.process_id)
    assert started is not None
    assert started.status == ProcessStatus.PROCESSING
    assert started.started_at is not None

    completed = await repo.mark_completed(
        created.process_id,
        detected_face_count=0,
    )
    assert completed is not None
    assert completed.status == ProcessStatus.COMPLETED
    assert completed.completed_at is not None
    assert completed.detected_face_count == 0

    failed_record = await repo.add(_make_process("identification"))
    failed = await repo.mark_failed(
        failed_record.process_id,
        error_code="ERR",
        error_message_sanitized="safe message",
    )
    assert failed is not None
    assert failed.status == ProcessStatus.FAILED


@pytest.mark.asyncio
async def test_person_photo_repository(session: AsyncSession, protector: AesGcmNationalIdProtector):
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    photo_repo = PostgresPersonPhotoRepository(session)
    photo1 = await photo_repo.add(_make_photo(person.person_id, "photo-1"))
    photo2 = await photo_repo.add(_make_photo(person.person_id, "photo-2"))

    listed = await photo_repo.list_by_person(person.person_id, limit=10, offset=0)
    assert len(listed) == 2

    primary = await photo_repo.set_primary(photo1.photo_id)
    assert primary is not None
    assert primary.is_primary is True

    switch = await photo_repo.set_primary(photo2.photo_id)
    assert switch is not None
    assert switch.is_primary is True

    refreshed = await photo_repo.get_by_id(photo1.photo_id)
    assert refreshed is not None
    assert refreshed.is_primary is False

    deactivated = await photo_repo.deactivate(photo2.photo_id)
    assert deactivated is not None
    assert deactivated.status == PersonPhotoStatus.INACTIVE


@pytest.mark.asyncio
async def test_face_sample_repository(session: AsyncSession, protector: AesGcmNationalIdProtector):
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    identity_repo = PostgresFaceIdentityRepository(session)
    identity = await identity_repo.add(_make_face_identity(person.person_id))

    profile_repo = PostgresInferenceProfileRepository(session)
    profile = await profile_repo.add(_make_profile("sample-profile"))

    photo_repo = PostgresPersonPhotoRepository(session)
    photo = await photo_repo.add(_make_photo(person.person_id, "sample-photo"))

    sample_repo = PostgresFaceSampleRepository(session)
    sample = await sample_repo.add(
        _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    )
    assert sample.sample_id is not None

    listed = await sample_repo.list_active_by_identity(
        identity.face_identity_id, limit=10, offset=0
    )
    assert len(listed) == 1

    deactivated = await sample_repo.deactivate(sample.sample_id)
    assert deactivated is not None
    assert deactivated.status == SampleStatus.INACTIVE


@pytest.mark.asyncio
async def test_recognition_result_repository(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    identity_repo = PostgresFaceIdentityRepository(session)
    identity = await identity_repo.add(_make_face_identity(person.person_id))

    profile_repo = PostgresInferenceProfileRepository(session)
    profile = await profile_repo.add(_make_profile("result-profile"))

    photo_repo = PostgresPersonPhotoRepository(session)
    photo = await photo_repo.add(_make_photo(person.person_id, "result-photo"))

    sample_repo = PostgresFaceSampleRepository(session)
    sample = await sample_repo.add(
        _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    )

    process_repo = PostgresProcessRecordRepository(session)
    process = await process_repo.add(_make_process())

    result_repo = PostgresRecognitionResultRepository(session)
    known = await result_repo.add(
        _make_result(
            process.process_id,
            0,
            RecognitionStatus.KNOWN,
            identity_id=identity.face_identity_id,
            sample_id=sample.sample_id,
            similarity=0.85,
        )
    )
    assert known.recognition_status == RecognitionStatus.KNOWN

    unknown = await result_repo.add(
        _make_result(process.process_id, 1, RecognitionStatus.UNKNOWN)
    )
    assert unknown.recognition_status == RecognitionStatus.UNKNOWN

    by_process = await result_repo.list_by_process(process.process_id)
    assert len(by_process) == 2

    history = await result_repo.list_history_by_identity(
        identity.face_identity_id, limit=10, offset=0
    )
    assert len(history) == 1
    assert history[0].result_id == known.result_id


@pytest.mark.asyncio
async def test_process_event_repository(session: AsyncSession):
    process_repo = PostgresProcessRecordRepository(session)
    process = await process_repo.add(_make_process())

    event_repo = PostgresProcessEventRepository(session)
    event1 = await event_repo.append(process.process_id, event_type="started")
    event2 = await event_repo.append(process.process_id, event_type="completed")

    assert event1.sequence_no == 1
    assert event2.sequence_no == 2

    listed = await event_repo.list_by_process(process.process_id, limit=10, offset=0)
    assert len(listed) == 2
    assert listed[0].sequence_no == 1
    assert listed[1].sequence_no == 2


@pytest.mark.asyncio
async def test_repository_does_not_auto_commit(
    session: AsyncSession,
    db_engine,
    protector: AesGcmNationalIdProtector,
):
    repo = PostgresPersonRepository(session)
    person = await repo.add(_make_person(protector))

    factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as new_session:
        result = await new_session.execute(
            select(orm.Person).where(orm.Person.person_id == person.person_id)
        )
        assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_raw_national_id_not_persisted(session: AsyncSession, protector: AesGcmNationalIdProtector):
    raw_id = "12345678901"
    repo = PostgresPersonRepository(session)
    person = await repo.add(_make_person(protector, raw=raw_id))

    result = await session.execute(
        select(
            orm.Person.national_id_ciphertext,
            orm.Person.national_id_lookup_hash,
            orm.Person.national_id_masked,
        ).where(orm.Person.person_id == person.person_id)
    )
    row = result.one()
    assert raw_id not in row.national_id_lookup_hash
    assert row.national_id_masked != raw_id
    assert row.national_id_masked == "*******8901"
    assert protector.reveal(
        protector.protect(raw_id)
    ) == raw_id

```

## Prompt: Sprint 002 — Surgical Code-Review Correction

Outcome: **PASS** (with documented limitation: local runtime is Python 3.14.6; Python 3.12 runtime not available for direct execution).

Amaç: Sprint 002'nin mevcut implementasyonunu koruyarak, code-review'de doğrulanan bulguları test-first şekilde düzeltmek. Bulgular: Alembic migration bağımsızlığı, Python 3.12 uyumlu UUIDv7 fallback, national-ID secret exposure kaldırılması, stored national-ID testi, test DB safety guard, repository contract düzeltmeleri, cross-store lifecycle aktivasyonu ve pytest-asyncio warning kök nedeni çözümü.

### Changed files

- `backend/alembic/versions/0001_phase1_schema.py`: fully explicit Alembic initial revision (no ORM metadata dependency).
- `backend/alembic/env.py`: imports `mergenvision.infrastructure.database.models` before `target_metadata = Base.metadata`.
- `backend/src/mergenvision/domain/ids.py`: Python 3.12-safe UUIDv7 fallback via integer bit layout.
- `backend/src/mergenvision/infrastructure/security/national_id.py`: removes key-export methods, rejects identical encryption/HMAC keys.
- `backend/src/mergenvision/ports/repositories.py`: adds `PersonRepository.update_national_id`, lifecycle `activate` methods on `PersonPhotoRepository`/`FaceSampleRepository`, fixes `deactivate(sample_id)` signature.
- `backend/src/mergenvision/infrastructure/database/repositories.py`: implements corrected contracts, sanitizes `InferenceProfileRepository.get_active`, adds PostgreSQL advisory xact lock in `ProcessEventRepository.append`.
- `backend/pyproject.toml`: pytest-asyncio upper bound raised to `<1.5.0`.
- `scripts/check_test_database_safety.py`: new script validating external test DB URL.
- `scripts/run_postgres_integration_tests.sh`: calls safety script before destructive migrations on provided test DB.
- `backend/tests/unit/test_uuid7.py`: uses `new_uuid7()` and monkeypatch-tests fallback.
- `backend/tests/unit/test_national_id_protection.py`: removes adapter key-export usage, adds same-key rejection, no-export, no-leak tests.
- `backend/tests/unit/test_alembic_source_immutability.py`: new unit test.
- `backend/tests/unit/test_test_database_safety.py`: new unit tests for the safety guard.
- `backend/tests/integration/test_alembic_postgres.py`: exact table-set test and `alembic check` clean test.
- `backend/tests/integration/test_postgres_constraints.py`: replaces `uuid7()` with `new_uuid7()`.
- `backend/tests/integration/test_postgres_repositories.py`: replaces `uuid7()` with `new_uuid7()`, adds stored national-ID, atomic update, multiple active profile, lifecycle activate, and concurrent process-event tests.
- `docs/implementation/REFERENCE_DECISION_LOG.md`: corrected Alembic and UUIDv7 rows; updated national-ID row with distinct-key/no-export decisions.

### Key behavior and data flow

- `new_uuid7()` uses `uuid.uuid7()` if it exists; otherwise constructs a 128-bit integer with timestamp (48 bits), version `0111` (4 bits), two random chunks, and RFC 4122 variant `10` before calling `uuid.UUID(int=...)`. No `version=7` constructor argument.
- `AesGcmNationalIdProtector` no longer exposes `encryption_key_b64()` or `hmac_key_b64()`. Constructor raises `SecurityError` if decoded keys are byte-equal.
- Explicit Alembic migration creates all 8 business tables, primary/foreign keys, unique/check constraints, and the partial unique index for active primary photos via `op.create_table`/`op.create_index`. Downgrade drops tables in reverse dependency order.
- `PersonRepository.update_national_id(protected)` atomically updates `national_id_ciphertext`, `national_id_lookup_hash`, and `national_id_masked` inside the caller's transaction.
- `InferenceProfileRepository.get_active` catches SQLAlchemy `MultipleResultsFound` and raises sanitized `RepositoryError`.
- `ProcessEventRepository.append` acquires a per-process `pg_advisory_xact_lock` so concurrent sessions serialize sequence-number generation; concurrent test with two separate `AsyncSession`s verifies `[1, 2]` ordering and uniqueness.
- `PersonPhotoRepository.activate()` and `FaceSampleRepository.activate()` transition inactive rows back to active (no new columns).
- Test DB safety guard requires `postgresql+asyncpg://` URL and a database name starting with `test_` or ending with `_test`, unless `MERGENVISION_ALLOW_DESTRUCTIVE_TEST_DATABASE=YES` is set.
- pytest-asyncio upgraded to `1.4.0` to eliminate the `asyncio.get_event_loop_policy` DeprecationWarning emitted by `0.25.x`/`0.26.0` on Python 3.14.

### Verified commands and results

- `make bootstrap-foundation` — PASS (editable install succeeded).
- `make verify-foundation` — PASS: Python tests 56 passed, 1 skipped; ruff clean; native CMake build/test passed; boundary verification passed; frozen SHA-256 sums OK.
- `make test-db-unit` — PASS: 41 unit tests passed.
- `make test-db-integration` — PASS: ephemeral PostgreSQL container started; Alembic upgrade head, downgrade base, upgrade head succeeded; 41 integration tests passed on real PostgreSQL.
- `make verify-db` — PASS: ruff + unit tests + real PostgreSQL integration + mypy.
- `make verify-sprint-002` — PASS.
- `.venv/bin/python -m ruff check backend/src backend/tests` — All checks passed.
- `.venv/bin/python -m mypy backend/src` — Success: no issues found in 22 source files.
- `git diff --check` — no output.
- `bash scripts/verify_repository_boundaries.sh` — PASS: repository boundaries verified.
- `sha256sum --check architecture/FROZEN_SHA256SUMS` — all frozen files OK.
- External test DB guard rejection test: `MERGENVISION_TEST_DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/mergenvision" make test-db-integration` → rejected with explicit error.
- External test DB guard override test: same URL with `MERGENVISION_ALLOW_DESTRUCTIVE_TEST_DATABASE=YES` → guard allowed; subsequent failure is expected because the DB does not exist.

### Known limitations

- Local execution uses Python 3.14.6. The implementation is written for Python 3.12+, but a native Python 3.12 runtime is not available in this environment to execute. The UUIDv7 fallback is exercised by monkeypatching `uuid.uuid7` out of existence.
- 21st MCP is forbidden by user and was not used.
- Context7, DeepWiki, Exa, Postman and Playwright MCP tools were not required for this correction and were skipped with documented justification.

### Source file final contents

#### `backend/alembic/versions/0001_phase1_schema.py`

```python
"""Phase 1 initial schema: eight frozen business tables.

This revision is fully explicit. It does not depend on runtime ORM metadata,
so future model changes cannot silently alter the initial schema.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001_phase1_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "person",
        sa.Column("person_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("last_name", sa.String(255), nullable=False),
        sa.Column("national_id_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("national_id_lookup_hash", sa.String(64), nullable=False),
        sa.Column("national_id_masked", sa.String(255), nullable=False),
        sa.Column("additional_details", JSONB(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("person_id", name="pk_person"),
        sa.UniqueConstraint("national_id_lookup_hash", name="uq_person_national_id_lookup_hash"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
    )
    op.create_index("ix_person_status", "person", ["status"])

    op.create_table(
        "face_identity",
        sa.Column("face_identity_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("face_identity_id", name="pk_face_identity"),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["person.person_id"],
            name="fk_face_identity_person_id_person",
        ),
        sa.UniqueConstraint("person_id", name="uq_face_identity_person_id"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
    )
    op.create_index("ix_face_identity_status", "face_identity", ["status"])

    op.create_table(
        "inference_profile",
        sa.Column("inference_profile_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_name", sa.String(255), nullable=False),
        sa.Column("detector_name", sa.String(255), nullable=False),
        sa.Column("detector_version", sa.String(64), nullable=False),
        sa.Column("detector_artifact_sha256", sa.String(64), nullable=False),
        sa.Column("alignment_version", sa.String(64), nullable=False),
        sa.Column("embedder_name", sa.String(255), nullable=False),
        sa.Column("embedder_version", sa.String(64), nullable=False),
        sa.Column("embedder_artifact_sha256", sa.String(64), nullable=False),
        sa.Column("preprocessing_version", sa.String(64), nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False),
        sa.Column("distance_metric", sa.String(32), nullable=False),
        sa.Column("match_threshold", sa.REAL(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("inference_profile_id", name="pk_inference_profile"),
        sa.UniqueConstraint("profile_name", name="uq_inference_profile_profile_name"),
        sa.CheckConstraint("embedding_dimension > 0", name="embedding_dimension_positive"),
    )

    op.create_table(
        "process_record",
        sa.Column("process_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("process_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("inference_profile_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("input_object_key", sa.Text(), nullable=True),
        sa.Column("input_sha256", sa.String(64), nullable=True),
        sa.Column("input_mime_type", sa.String(64), nullable=True),
        sa.Column("input_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("input_width", sa.Integer(), nullable=True),
        sa.Column("input_height", sa.Integer(), nullable=True),
        sa.Column("retention_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("detected_face_count", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message_sanitized", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("process_id", name="pk_process_record"),
        sa.ForeignKeyConstraint(
            ["inference_profile_id"],
            ["inference_profile.inference_profile_id"],
            name="fk_process_record_inference_profile_id_inference_profile",
        ),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name="status"),
        sa.CheckConstraint(
            "input_size_bytes IS NULL OR input_size_bytes > 0",
            name="input_size_positive",
        ),
        sa.CheckConstraint("input_width IS NULL OR input_width > 0", name="input_width_positive"),
        sa.CheckConstraint("input_height IS NULL OR input_height > 0", name="input_height_positive"),
        sa.CheckConstraint(
            "detected_face_count IS NULL OR detected_face_count >= 0",
            name="detected_face_count_nonnegative",
        ),
    )
    op.create_index(
        "ix_process_record_process_type_status_created_at",
        "process_record",
        ["process_type", "status", "created_at"],
    )
    op.create_index("ix_process_record_created_at", "process_record", ["created_at"])

    op.create_table(
        "person_photo",
        sa.Column("photo_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("enrollment_process_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("mime_type", sa.String(64), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("photo_id", name="pk_person_photo"),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["person.person_id"],
            name="fk_person_photo_person_id_person",
        ),
        sa.ForeignKeyConstraint(
            ["enrollment_process_id"],
            ["process_record.process_id"],
            name="fk_person_photo_enrollment_process_id_process_record",
        ),
        sa.UniqueConstraint("object_key", name="uq_person_photo_object_key"),
        sa.UniqueConstraint(
            "person_id",
            "content_sha256",
            name="uq_person_photo_person_id_content_sha256",
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
        sa.CheckConstraint("file_size_bytes > 0", name="file_size_positive"),
        sa.CheckConstraint("width > 0", name="width_positive"),
        sa.CheckConstraint("height > 0", name="height_positive"),
    )
    op.create_index(
        "ix_person_photo_person_id_status",
        "person_photo",
        ["person_id", "status"],
    )
    op.create_index(
        "ix_uq_person_photo_active_primary",
        "person_photo",
        ["person_id"],
        unique=True,
        postgresql_where=sa.text(
            "is_primary = true AND status = 'active' AND deleted_at IS NULL"
        ),
    )

    op.create_table(
        "face_sample",
        sa.Column("sample_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("face_identity_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("photo_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("inference_profile_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("bbox_x", sa.Integer(), nullable=False),
        sa.Column("bbox_y", sa.Integer(), nullable=False),
        sa.Column("bbox_width", sa.Integer(), nullable=False),
        sa.Column("bbox_height", sa.Integer(), nullable=False),
        sa.Column("landmarks", JSONB(), nullable=False),
        sa.Column("detection_confidence", sa.REAL(), nullable=False),
        sa.Column("quality_score", sa.REAL(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("sample_id", name="pk_face_sample"),
        sa.ForeignKeyConstraint(
            ["face_identity_id"],
            ["face_identity.face_identity_id"],
            name="fk_face_sample_face_identity_id_face_identity",
        ),
        sa.ForeignKeyConstraint(
            ["photo_id"],
            ["person_photo.photo_id"],
            name="fk_face_sample_photo_id_person_photo",
        ),
        sa.ForeignKeyConstraint(
            ["inference_profile_id"],
            ["inference_profile.inference_profile_id"],
            name="fk_face_sample_inference_profile_id_inference_profile",
        ),
        sa.UniqueConstraint(
            "photo_id",
            "inference_profile_id",
            name="uq_face_sample_photo_id_inference_profile_id",
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
        sa.CheckConstraint("bbox_width > 0", name="bbox_width_positive"),
        sa.CheckConstraint("bbox_height > 0", name="bbox_height_positive"),
        sa.CheckConstraint(
            "detection_confidence >= 0 AND detection_confidence <= 1",
            name="detection_confidence_range",
        ),
        sa.CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)",
            name="quality_score_range",
        ),
    )
    op.create_index(
        "ix_face_sample_face_identity_id_status",
        "face_sample",
        ["face_identity_id", "status"],
    )
    op.create_index(
        "ix_face_sample_inference_profile_id_status",
        "face_sample",
        ["inference_profile_id", "status"],
    )

    op.create_table(
        "recognition_result",
        sa.Column("result_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("process_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("face_index", sa.Integer(), nullable=False),
        sa.Column("matched_face_identity_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("matched_sample_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("recognition_status", sa.String(16), nullable=False),
        sa.Column("bbox_x", sa.Integer(), nullable=False),
        sa.Column("bbox_y", sa.Integer(), nullable=False),
        sa.Column("bbox_width", sa.Integer(), nullable=False),
        sa.Column("bbox_height", sa.Integer(), nullable=False),
        sa.Column("detection_confidence", sa.REAL(), nullable=False),
        sa.Column("similarity_score", sa.REAL(), nullable=True),
        sa.Column("threshold_used", sa.REAL(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("result_id", name="pk_recognition_result"),
        sa.ForeignKeyConstraint(
            ["process_id"],
            ["process_record.process_id"],
            name="fk_recognition_result_process_id_process_record",
        ),
        sa.ForeignKeyConstraint(
            ["matched_face_identity_id"],
            ["face_identity.face_identity_id"],
            name="fk_recognition_result_matched_face_identity_id_face_identity",
        ),
        sa.ForeignKeyConstraint(
            ["matched_sample_id"],
            ["face_sample.sample_id"],
            name="fk_recognition_result_matched_sample_id_face_sample",
        ),
        sa.UniqueConstraint(
            "process_id",
            "face_index",
            name="uq_recognition_result_process_id_face_index",
        ),
        sa.CheckConstraint(
            "recognition_status IN ('known', 'unknown')",
            name="status_values",
        ),
        sa.CheckConstraint("bbox_width > 0", name="bbox_width_positive"),
        sa.CheckConstraint("bbox_height > 0", name="bbox_height_positive"),
        sa.CheckConstraint(
            "detection_confidence >= 0 AND detection_confidence <= 1",
            name="detection_confidence_range",
        ),
        sa.CheckConstraint(
            """
            (
                recognition_status = 'known'
                AND matched_face_identity_id IS NOT NULL
                AND matched_sample_id IS NOT NULL
                AND similarity_score IS NOT NULL
            )
            OR
            (
                recognition_status = 'unknown'
                AND matched_face_identity_id IS NULL
                AND matched_sample_id IS NULL
                AND similarity_score IS NULL
            )
            """,
            name="status_consistency",
        ),
        sa.CheckConstraint("face_index >= 0", name="face_index_nonnegative"),
    )
    op.create_index(
        "ix_recognition_result_matched_face_identity_id_created_at",
        "recognition_result",
        ["matched_face_identity_id", "created_at"],
    )
    op.create_index(
        "ix_recognition_result_matched_sample_id",
        "recognition_result",
        ["matched_sample_id"],
    )
    op.create_index(
        "ix_recognition_result_recognition_status_created_at",
        "recognition_result",
        ["recognition_status", "created_at"],
    )

    op.create_table(
        "process_event",
        sa.Column("event_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("process_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("details", JSONB(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id", name="pk_process_event"),
        sa.ForeignKeyConstraint(
            ["process_id"],
            ["process_record.process_id"],
            name="fk_process_event_process_id_process_record",
        ),
        sa.UniqueConstraint(
            "process_id",
            "sequence_no",
            name="uq_process_event_process_id_sequence_no",
        ),
    )
    op.create_index(
        "ix_process_event_occurred_at",
        "process_event",
        ["occurred_at"],
    )


def downgrade() -> None:
    op.drop_table("process_event")
    op.drop_table("recognition_result")
    op.drop_table("face_sample")
    op.drop_table("person_photo")
    op.drop_table("process_record")
    op.drop_table("inference_profile")
    op.drop_table("face_identity")
    op.drop_table("person")
```

#### `backend/alembic/env.py`

```python
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mergenvision.config.settings import Settings
from mergenvision.infrastructure.database.base import Base
from mergenvision.infrastructure.database import models  # noqa: F401

settings = Settings()
config = context.config
if settings.database_url:
    config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

#### `backend/src/mergenvision/domain/ids.py`

```python
import secrets
import time
import uuid


def _uuid7_from_builtin() -> uuid.UUID | None:
    fn = getattr(uuid, "uuid7", None)
    if fn is None:
        return None
    return fn()


def _uuid7_rfc9562() -> uuid.UUID:
    timestamp_ms = int(time.time_ns() // 1_000_000)
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)
    uuid_int = (
        (timestamp_ms << 80)
        | (0x7 << 76)
        | (rand_a << 64)
        | (0x2 << 62)
        | rand_b
    )
    value = uuid.UUID(int=uuid_int)
    if value.version != 7 or value.variant != uuid.RFC_4122:
        raise RuntimeError("UUIDv7 fallback produced an invalid UUID")
    return value


def new_uuid7() -> uuid.UUID:
    value = _uuid7_from_builtin()
    return value if value is not None else _uuid7_rfc9562()
```

#### `backend/src/mergenvision/infrastructure/security/national_id.py`

```python
from __future__ import annotations

import base64
import hmac
import os
import struct
import unicodedata
from hashlib import sha256

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from mergenvision.domain.errors import SecurityError
from mergenvision.ports.national_id import NationalIdProtectedValue, NationalIdProtector

_FORMAT_VERSION = 1
_NONCE_LEN = 12
_AEAD_ASSOCIATED_DATA = b"mergenvision:national-id:v1"
_KEY_LEN = 32


class AesGcmNationalIdProtector(NationalIdProtector):
    def __init__(self, encryption_key_b64: str, hmac_key_b64: str) -> None:
        self._encryption_key = self._decode_key(encryption_key_b64, "encryption_key")
        self._hmac_key = self._decode_key(hmac_key_b64, "hmac_key")
        if self._encryption_key == self._hmac_key:
            raise SecurityError("Encryption key and HMAC key must be distinct")
        self._aesgcm = AESGCM(self._encryption_key)

    def protect(self, raw_national_id: str) -> NationalIdProtectedValue:
        normalized = self._normalize(raw_national_id)
        if not normalized:
            raise SecurityError("National ID is empty after normalization")
        nonce = os.urandom(_NONCE_LEN)
        plaintext = normalized.encode("utf-8")
        ciphertext_with_tag = self._aesgcm.encrypt(nonce, plaintext, _AEAD_ASSOCIATED_DATA)
        payload = struct.pack("!B", _FORMAT_VERSION) + nonce + ciphertext_with_tag
        return NationalIdProtectedValue(
            ciphertext=payload,
            lookup_hash=self._lookup_hash(normalized),
            masked=self._mask(normalized),
        )

    def reveal(self, protected: NationalIdProtectedValue) -> str:
        payload = protected.ciphertext
        if len(payload) < 1 + _NONCE_LEN + 16:
            raise SecurityError("Ciphertext is too short")
        version = payload[0]
        if version != _FORMAT_VERSION:
            raise SecurityError(f"Unsupported ciphertext format version: {version}")
        nonce = payload[1 : 1 + _NONCE_LEN]
        ciphertext_with_tag = payload[1 + _NONCE_LEN :]
        try:
            plaintext = self._aesgcm.decrypt(nonce, ciphertext_with_tag, _AEAD_ASSOCIATED_DATA)
        except InvalidTag as exc:
            raise SecurityError("National ID decryption failed: authentication tag mismatch") from exc
        return plaintext.decode("utf-8")

    @staticmethod
    def _normalize(raw: str) -> str:
        return unicodedata.normalize("NFKC", raw).strip()

    @staticmethod
    def _mask(normalized: str) -> str:
        if len(normalized) > 4:
            return "*" * (len(normalized) - 4) + normalized[-4:]
        return "*" * len(normalized)

    def _lookup_hash(self, normalized: str) -> str:
        return hmac.new(
            self._hmac_key,
            normalized.encode("utf-8"),
            sha256,
        ).hexdigest()

    @staticmethod
    def _decode_key(key_b64: str, name: str) -> bytes:
        try:
            raw = base64.b64decode(key_b64, validate=True)
        except Exception as exc:
            raise SecurityError(f"Invalid Base64 for {name}") from exc
        if len(raw) != _KEY_LEN:
            raise SecurityError(
                f"{name} must decode to exactly {_KEY_LEN} bytes, got {len(raw)}"
            )
        return raw
```

#### `backend/src/mergenvision/ports/repositories.py`

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from mergenvision.domain.entities import (
    FaceIdentity,
    FaceSample,
    InferenceProfile,
    Person,
    PersonPhoto,
    ProcessEvent,
    ProcessRecord,
    RecognitionResult,
)
from mergenvision.ports.national_id import NationalIdProtectedValue


class PersonRepository(ABC):
    @abstractmethod
    async def add(self, person: Person) -> Person:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, person_id: UUID) -> Person | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_national_id_lookup_hash(self, lookup_hash: str) -> Person | None:
        raise NotImplementedError

    @abstractmethod
    async def list_active(self, *, limit: int, offset: int) -> list[Person]:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        person_id: UUID,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        additional_details: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> Person | None:
        raise NotImplementedError

    @abstractmethod
    async def update_national_id(
        self,
        person_id: UUID,
        protected: NationalIdProtectedValue,
    ) -> Person | None:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(self, person_id: UUID) -> Person | None:
        raise NotImplementedError


class FaceIdentityRepository(ABC):
    @abstractmethod
    async def add(self, face_identity: FaceIdentity) -> FaceIdentity:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, face_identity_id: UUID) -> FaceIdentity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_person_id(self, person_id: UUID) -> FaceIdentity | None:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(self, face_identity_id: UUID) -> FaceIdentity | None:
        raise NotImplementedError


class InferenceProfileRepository(ABC):
    @abstractmethod
    async def add(self, profile: InferenceProfile) -> InferenceProfile:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, profile_id: UUID) -> InferenceProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_name(self, profile_name: str) -> InferenceProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def get_active(self) -> InferenceProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def retire(self, profile_id: UUID) -> InferenceProfile | None:
        raise NotImplementedError


class ProcessRecordRepository(ABC):
    @abstractmethod
    async def add(self, record: ProcessRecord) -> ProcessRecord:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, process_id: UUID) -> ProcessRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_started(self, process_id: UUID) -> ProcessRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_completed(
        self,
        process_id: UUID,
        *,
        detected_face_count: int | None = None,
    ) -> ProcessRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_failed(
        self,
        process_id: UUID,
        *,
        error_code: str,
        error_message_sanitized: str,
    ) -> ProcessRecord | None:
        raise NotImplementedError


class PersonPhotoRepository(ABC):
    @abstractmethod
    async def add(self, photo: PersonPhoto) -> PersonPhoto:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, photo_id: UUID) -> PersonPhoto | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_person(self, person_id: UUID, *, limit: int, offset: int) -> list[PersonPhoto]:
        raise NotImplementedError

    @abstractmethod
    async def set_primary(self, photo_id: UUID) -> PersonPhoto | None:
        raise NotImplementedError

    @abstractmethod
    async def activate(self, photo_id: UUID) -> PersonPhoto | None:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(self, photo_id: UUID) -> PersonPhoto | None:
        raise NotImplementedError


class FaceSampleRepository(ABC):
    @abstractmethod
    async def add(self, sample: FaceSample) -> FaceSample:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, sample_id: UUID) -> FaceSample | None:
        raise NotImplementedError

    @abstractmethod
    async def list_active_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[FaceSample]:
        raise NotImplementedError

    @abstractmethod
    async def activate(self, sample_id: UUID) -> FaceSample | None:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(self, sample_id: UUID) -> FaceSample | None:
        raise NotImplementedError


class RecognitionResultRepository(ABC):
    @abstractmethod
    async def add(self, result: RecognitionResult) -> RecognitionResult:
        raise NotImplementedError

    @abstractmethod
    async def list_by_process(self, process_id: UUID) -> list[RecognitionResult]:
        raise NotImplementedError

    @abstractmethod
    async def list_history_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[RecognitionResult]:
        raise NotImplementedError


class ProcessEventRepository(ABC):
    @abstractmethod
    async def append(
        self,
        process_id: UUID,
        *,
        event_type: str,
        details: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> ProcessEvent:
        raise NotImplementedError

    @abstractmethod
    async def list_by_process(self, process_id: UUID, *, limit: int, offset: int) -> list[ProcessEvent]:
        raise NotImplementedError
```

#### `backend/src/mergenvision/infrastructure/database/repositories.py`

```python
from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError, MultipleResultsFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from mergenvision.domain import entities as domain
from mergenvision.domain.entities import (
    FaceIdentity,
    FaceSample,
    InferenceProfile,
    Person,
    PersonPhoto,
    ProcessEvent,
    ProcessRecord,
    RecognitionResult,
)
from mergenvision.domain.enums import (
    FaceIdentityStatus,
    PersonPhotoStatus,
    PersonStatus,
    ProcessStatus,
    SampleStatus,
)
from mergenvision.domain.errors import ConflictError, NotFoundError, RepositoryError
from mergenvision.domain.ids import new_uuid7
from mergenvision.infrastructure.database import mappers
from mergenvision.infrastructure.database import models as orm
from mergenvision.ports.national_id import NationalIdProtectedValue
from mergenvision.ports.repositories import (
    FaceIdentityRepository,
    FaceSampleRepository,
    InferenceProfileRepository,
    PersonPhotoRepository,
    PersonRepository,
    ProcessEventRepository,
    ProcessRecordRepository,
    RecognitionResultRepository,
)


def _handle_db_error(exc: Exception) -> None:
    if isinstance(exc, IntegrityError):
        raise ConflictError("Resource conflict or constraint violation") from exc
    if isinstance(exc, SQLAlchemyError):
        raise RepositoryError("Database operation failed") from exc
    raise exc


class PostgresPersonRepository(PersonRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, person: Person) -> Person:
        orm_obj = orm.Person(**dataclasses.asdict(person))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person(orm_obj)

    async def get_by_id(self, person_id: UUID) -> Person | None:
        stmt = (
            select(orm.Person)
            .where(orm.Person.person_id == person_id)
            .where(orm.Person.status == PersonStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_person(row) if row else None

    async def get_by_national_id_lookup_hash(self, lookup_hash: str) -> Person | None:
        stmt = select(orm.Person).where(orm.Person.national_id_lookup_hash == lookup_hash)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_person(row) if row else None

    async def list_active(self, *, limit: int, offset: int) -> list[Person]:
        stmt = (
            select(orm.Person)
            .where(orm.Person.status == PersonStatus.ACTIVE)
            .order_by(orm.Person.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_person(row) for row in result.scalars().all()]

    async def update(
        self,
        person_id: UUID,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        additional_details: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> Person | None:
        row = await self._get_active_orm(person_id)
        if row is None:
            return None
        if first_name is not None:
            row.first_name = first_name
        if last_name is not None:
            row.last_name = last_name
        if additional_details is not None:
            row.additional_details = additional_details
        if status is not None:
            row.status = status
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person(row)

    async def update_national_id(
        self,
        person_id: UUID,
        protected: NationalIdProtectedValue,
    ) -> Person | None:
        row = await self._get_active_orm(person_id)
        if row is None:
            return None
        row.national_id_ciphertext = protected.ciphertext
        row.national_id_lookup_hash = protected.lookup_hash
        row.national_id_masked = protected.masked
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person(row)

    async def deactivate(self, person_id: UUID) -> Person | None:
        row = await self._get_active_orm(person_id)
        if row is None:
            return None
        row.status = PersonStatus.INACTIVE
        row.deleted_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person(row)

    async def _get_active_orm(self, person_id: UUID) -> orm.Person | None:
        stmt = (
            select(orm.Person)
            .where(orm.Person.person_id == person_id)
            .where(orm.Person.status == PersonStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class PostgresFaceIdentityRepository(FaceIdentityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, face_identity: FaceIdentity) -> FaceIdentity:
        orm_obj = orm.FaceIdentity(**dataclasses.asdict(face_identity))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_identity(orm_obj)

    async def get_by_id(self, face_identity_id: UUID) -> FaceIdentity | None:
        stmt = (
            select(orm.FaceIdentity)
            .where(orm.FaceIdentity.face_identity_id == face_identity_id)
            .where(orm.FaceIdentity.status == FaceIdentityStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_face_identity(row) if row else None

    async def get_by_person_id(self, person_id: UUID) -> FaceIdentity | None:
        stmt = (
            select(orm.FaceIdentity)
            .where(orm.FaceIdentity.person_id == person_id)
            .where(orm.FaceIdentity.status == FaceIdentityStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_face_identity(row) if row else None

    async def deactivate(self, face_identity_id: UUID) -> FaceIdentity | None:
        stmt = (
            select(orm.FaceIdentity)
            .where(orm.FaceIdentity.face_identity_id == face_identity_id)
            .where(orm.FaceIdentity.status == FaceIdentityStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = FaceIdentityStatus.INACTIVE
        row.deleted_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_identity(row)


class PostgresInferenceProfileRepository(InferenceProfileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, profile: InferenceProfile) -> InferenceProfile:
        orm_obj = orm.InferenceProfile(**dataclasses.asdict(profile))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_inference_profile(orm_obj)

    async def get_by_id(self, profile_id: UUID) -> InferenceProfile | None:
        stmt = select(orm.InferenceProfile).where(
            orm.InferenceProfile.inference_profile_id == profile_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_inference_profile(row) if row else None

    async def get_by_name(self, profile_name: str) -> InferenceProfile | None:
        stmt = select(orm.InferenceProfile).where(
            orm.InferenceProfile.profile_name == profile_name
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_inference_profile(row) if row else None

    async def get_active(self) -> InferenceProfile | None:
        stmt = select(orm.InferenceProfile).where(
            orm.InferenceProfile.is_active.is_(True)
        )
        result = await self._session.execute(stmt)
        try:
            row = result.scalar_one_or_none()
        except MultipleResultsFound as exc:
            raise RepositoryError(
                "Multiple active inference profiles found; expected at most one"
            ) from exc
        return mappers.map_inference_profile(row) if row else None

    async def retire(self, profile_id: UUID) -> InferenceProfile | None:
        stmt = select(orm.InferenceProfile).where(
            orm.InferenceProfile.inference_profile_id == profile_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.is_active = False
        row.retired_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_inference_profile(row)


class PostgresProcessRecordRepository(ProcessRecordRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, record: ProcessRecord) -> ProcessRecord:
        orm_obj = orm.ProcessRecord(**dataclasses.asdict(record))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_record(orm_obj)

    async def get_by_id(self, process_id: UUID) -> ProcessRecord | None:
        stmt = select(orm.ProcessRecord).where(orm.ProcessRecord.process_id == process_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_process_record(row) if row else None

    async def mark_started(self, process_id: UUID) -> ProcessRecord | None:
        row = await self._get_orm(process_id)
        if row is None:
            return None
        row.status = ProcessStatus.PROCESSING
        row.started_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_record(row)

    async def mark_completed(
        self,
        process_id: UUID,
        *,
        detected_face_count: int | None = None,
    ) -> ProcessRecord | None:
        row = await self._get_orm(process_id)
        if row is None:
            return None
        row.status = ProcessStatus.COMPLETED
        row.completed_at = datetime.now(UTC)
        if detected_face_count is not None:
            row.detected_face_count = detected_face_count
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_record(row)

    async def mark_failed(
        self,
        process_id: UUID,
        *,
        error_code: str,
        error_message_sanitized: str,
    ) -> ProcessRecord | None:
        row = await self._get_orm(process_id)
        if row is None:
            return None
        row.status = ProcessStatus.FAILED
        row.completed_at = datetime.now(UTC)
        row.error_code = error_code
        row.error_message_sanitized = error_message_sanitized
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_record(row)

    async def _get_orm(self, process_id: UUID) -> orm.ProcessRecord | None:
        stmt = select(orm.ProcessRecord).where(orm.ProcessRecord.process_id == process_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class PostgresPersonPhotoRepository(PersonPhotoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, photo: PersonPhoto) -> PersonPhoto:
        orm_obj = orm.PersonPhoto(**dataclasses.asdict(photo))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person_photo(orm_obj)

    async def get_by_id(self, photo_id: UUID) -> PersonPhoto | None:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.photo_id == photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_person_photo(row) if row else None

    async def list_by_person(self, person_id: UUID, *, limit: int, offset: int) -> list[PersonPhoto]:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.person_id == person_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
            .order_by(orm.PersonPhoto.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_person_photo(row) for row in result.scalars().all()]

    async def set_primary(self, photo_id: UUID) -> PersonPhoto | None:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.photo_id == photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        await self._session.execute(
            update(orm.PersonPhoto)
            .where(orm.PersonPhoto.person_id == row.person_id)
            .where(orm.PersonPhoto.photo_id != row.photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
            .values(is_primary=False)
        )
        row.is_primary = True
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person_photo(row)

    async def activate(self, photo_id: UUID) -> PersonPhoto | None:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.photo_id == photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.INACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = PersonPhotoStatus.ACTIVE
        row.deleted_at = None
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person_photo(row)

    async def deactivate(self, photo_id: UUID) -> PersonPhoto | None:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.photo_id == photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = PersonPhotoStatus.INACTIVE
        row.deleted_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        if row.is_primary:
            row.is_primary = False
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person_photo(row)


class PostgresFaceSampleRepository(FaceSampleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, sample: FaceSample) -> FaceSample:
        orm_obj = orm.FaceSample(**dataclasses.asdict(sample))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_sample(orm_obj)

    async def get_by_id(self, sample_id: UUID) -> FaceSample | None:
        stmt = (
            select(orm.FaceSample)
            .where(orm.FaceSample.sample_id == sample_id)
            .where(orm.FaceSample.status == SampleStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_face_sample(row) if row else None

    async def list_active_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[FaceSample]:
        stmt = (
            select(orm.FaceSample)
            .where(orm.FaceSample.face_identity_id == face_identity_id)
            .where(orm.FaceSample.status == SampleStatus.ACTIVE)
            .order_by(orm.FaceSample.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_face_sample(row) for row in result.scalars().all()]

    async def activate(self, sample_id: UUID) -> FaceSample | None:
        stmt = (
            select(orm.FaceSample)
            .where(orm.FaceSample.sample_id == sample_id)
            .where(orm.FaceSample.status == SampleStatus.INACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = SampleStatus.ACTIVE
        row.deleted_at = None
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_sample(row)

    async def deactivate(self, sample_id: UUID) -> FaceSample | None:
        stmt = (
            select(orm.FaceSample)
            .where(orm.FaceSample.sample_id == sample_id)
            .where(orm.FaceSample.status == SampleStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = SampleStatus.INACTIVE
        row.deleted_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_sample(row)


class PostgresRecognitionResultRepository(RecognitionResultRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, result: RecognitionResult) -> RecognitionResult:
        orm_obj = orm.RecognitionResult(**dataclasses.asdict(result))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_recognition_result(orm_obj)

    async def list_by_process(self, process_id: UUID) -> list[RecognitionResult]:
        stmt = (
            select(orm.RecognitionResult)
            .where(orm.RecognitionResult.process_id == process_id)
            .order_by(orm.RecognitionResult.face_index.asc())
        )
        result = await self._session.execute(stmt)
        return [mappers.map_recognition_result(row) for row in result.scalars().all()]

    async def list_history_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[RecognitionResult]:
        stmt = (
            select(orm.RecognitionResult)
            .where(orm.RecognitionResult.matched_face_identity_id == face_identity_id)
            .order_by(orm.RecognitionResult.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_recognition_result(row) for row in result.scalars().all()]


class PostgresProcessEventRepository(ProcessEventRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        process_id: UUID,
        *,
        event_type: str,
        details: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> ProcessEvent:
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": self._process_lock_id(process_id)},
        )
        process_stmt = select(orm.ProcessRecord).where(
            orm.ProcessRecord.process_id == process_id
        )
        process_result = await self._session.execute(process_stmt)
        if process_result.scalar_one_or_none() is None:
            raise NotFoundError(f"Process {process_id} not found")
        next_sequence = await self._next_sequence_no(process_id)
        event = domain.ProcessEvent(
            event_id=new_uuid7(),
            process_id=process_id,
            sequence_no=next_sequence,
            event_type=event_type,
            details=details if details is not None else {},
            occurred_at=occurred_at if occurred_at is not None else datetime.now(UTC),
        )
        orm_obj = orm.ProcessEvent(**dataclasses.asdict(event))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_event(orm_obj)

    def _process_lock_id(self, process_id: UUID) -> int:
        return int(process_id.int % (1 << 63))

    async def list_by_process(
        self,
        process_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[ProcessEvent]:
        stmt = (
            select(orm.ProcessEvent)
            .where(orm.ProcessEvent.process_id == process_id)
            .order_by(orm.ProcessEvent.sequence_no.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_process_event(row) for row in result.scalars().all()]

    async def _next_sequence_no(self, process_id: UUID) -> int:
        stmt = select(
            func.coalesce(func.max(orm.ProcessEvent.sequence_no), 0) + 1
        ).where(orm.ProcessEvent.process_id == process_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
```

#### `backend/pyproject.toml`

```toml
[project]
name = "mergenvision-backend"
version = "0.1.0"
description = "MergenVision Phase 1 photo-based person recognition backend"
requires-python = ">=3.12"
dependencies = [
    "sqlalchemy[asyncio]>=2.0.0,<3.0.0",
    "alembic>=1.13.0,<2.0.0",
    "asyncpg>=0.29.0,<0.32.0",
    "cryptography>=42.0.0,<45.0.0",
    "pydantic-settings>=2.0.0,<3.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8,<9",
    "pytest-asyncio>=0.23.0,<1.5.0",
    "ruff>=0.5,<0.8",
    "mypy>=1.11,<1.12",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src/"]
include = ["mergenvision*"]

[tool.ruff]
target-version = "py312"
line-length = 100
exclude = [".venv", "build", "dist"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = ["E501", "B008"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-v"
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

#### `scripts/check_test_database_safety.py`

```python
#!/usr/bin/env python3
"""Validate MERGENVISION_TEST_DATABASE_URL before destructive migration tests.

Rejects non-PostgreSQL URLs and database names that do not start with ``test_``
or end with ``_test`` unless ``MERGENVISION_ALLOW_DESTRUCTIVE_TEST_DATABASE=YES``
is set explicitly.
"""

import os
import re
import sys
from urllib.parse import urlparse


def _database_name(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path.lstrip("/").split("?")[0]


def validate(url: str, *, allow_destructive: bool = False) -> None:
    if not re.match(r"^postgresql\+asyncpg://", url, re.IGNORECASE):
        raise ValueError(
            "MERGENVISION_TEST_DATABASE_URL must use the asyncpg driver "
            "(e.g., postgresql+asyncpg://...)"
        )

    db_name = _database_name(url)
    if not db_name:
        raise ValueError("MERGENVISION_TEST_DATABASE_URL does not contain a database name")

    if not (db_name.startswith("test_") or db_name.endswith("_test")):
        if not allow_destructive:
            raise ValueError(
                f"Database name '{db_name}' does not start with 'test_' or end with '_test'. "
                "Set MERGENVISION_ALLOW_DESTRUCTIVE_TEST_DATABASE=YES to override."
            )


def main() -> int:
    url = os.environ.get("MERGENVISION_TEST_DATABASE_URL")
    if not url:
        return 0

    allow_destructive = os.environ.get("MERGENVISION_ALLOW_DESTRUCTIVE_TEST_DATABASE") == "YES"
    try:
        validate(url, allow_destructive=allow_destructive)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

#### `scripts/run_postgres_integration_tests.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

CONTAINER_ID=""
EXIT_CODE=0
IMAGE="postgres:16-alpine"
DEFAULT_USER="test"
DEFAULT_PASSWORD="test"
DEFAULT_DB="mergenvision"

choose_port() {
    python3 - <<'PY'
import socket
with socket.socket() as s:
    s.bind(("", 0))
    print(s.getsockname()[1])
PY
}

cleanup() {
    if [[ -n "${CONTAINER_ID}" ]]; then
        echo "==> Stopping ephemeral PostgreSQL container ${CONTAINER_ID}"
        docker stop "${CONTAINER_ID}" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

run_migrations_and_tests() {
    local database_url="$1"
    echo "==> Running Alembic migrations"
    (
        cd backend
        MERGENVISION_DATABASE_URL="${database_url}" \
            "${REPO_ROOT}/.venv/bin/alembic" -c alembic.ini upgrade head
    )

    echo "==> Running integration tests"
    MERGENVISION_DATABASE_URL="${database_url}" \
        MERGENVISION_TEST_DATABASE_URL="${database_url}" \
        "${REPO_ROOT}/.venv/bin/python" -m pytest backend/tests/integration -v
}

if [[ -n "${MERGENVISION_TEST_DATABASE_URL:-}" ]]; then
    echo "==> Using provided MERGENVISION_TEST_DATABASE_URL"
    echo "==> Running test database safety check"
    PYTHONPATH="${REPO_ROOT}/backend/src" \
        "${REPO_ROOT}/.venv/bin/python" \
        "${REPO_ROOT}/scripts/check_test_database_safety.py"
    run_migrations_and_tests "${MERGENVISION_TEST_DATABASE_URL}"
    exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker is required to start ephemeral PostgreSQL" >&2
    exit 1
fi

TEST_PORT="$(choose_port)"
CONTAINER_NAME="mergenvision-test-postgres-$$-${RANDOM}"

echo "==> Starting ephemeral PostgreSQL on port ${TEST_PORT}"
CONTAINER_ID="$(docker run --rm -d \
    --name "${CONTAINER_NAME}" \
    -e POSTGRES_USER="${DEFAULT_USER}" \
    -e POSTGRES_PASSWORD="${DEFAULT_PASSWORD}" \
    -e POSTGRES_DB="${DEFAULT_DB}" \
    -p "${TEST_PORT}:5432" \
    "${IMAGE}")"

echo "==> Waiting for PostgreSQL to be ready"
for _ in {1..60}; do
    if docker exec "${CONTAINER_ID}" pg_isready -U "${DEFAULT_USER}" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

for _ in {1..60}; do
    if docker exec "${CONTAINER_ID}" psql -U "${DEFAULT_USER}" -d "${DEFAULT_DB}" -c "SELECT 1" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

if ! docker exec "${CONTAINER_ID}" psql -U "${DEFAULT_USER}" -d "${DEFAULT_DB}" -c "SELECT 1" >/dev/null 2>&1; then
    echo "ERROR: PostgreSQL did not become ready" >&2
    exit 1
fi

DATABASE_URL="postgresql+asyncpg://${DEFAULT_USER}:${DEFAULT_PASSWORD}@localhost:${TEST_PORT}/${DEFAULT_DB}"
run_migrations_and_tests "${DATABASE_URL}"
```

#### `backend/tests/unit/test_uuid7.py`

```python
from uuid import RFC_4122, UUID

import pytest

from mergenvision.domain.ids import new_uuid7


def test_new_uuid7_returns_version7():
    value = new_uuid7()
    assert isinstance(value, UUID)
    assert value.version == 7
    assert value.variant == RFC_4122


def test_new_uuid7_generates_unique_values():
    values = {new_uuid7() for _ in range(1000)}
    assert len(values) == 1000


def test_new_uuid7_timestamp_field_is_non_decreasing():
    ids = [new_uuid7() for _ in range(50)]
    timestamps = [value.int >> 80 for value in ids]
    for previous, current in zip(timestamps, timestamps[1:], strict=False):
        assert current >= previous
    for value in ids:
        assert value.version == 7
        assert value.variant == RFC_4122


def test_new_uuid7_fallback_path_produces_version7(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delattr("uuid.uuid7", raising=True)
    value = new_uuid7()
    assert isinstance(value, UUID)
    assert value.version == 7
    assert value.variant == RFC_4122


def test_new_uuid7_fallback_with_frozen_time_produces_unique_valid_uuids(
    monkeypatch: pytest.MonkeyPatch,
):
    fixed_ns = 1_725_000_000_000_000_000
    expected_ms = fixed_ns // 1_000_000

    monkeypatch.delattr("uuid.uuid7", raising=True)
    monkeypatch.setattr("time.time_ns", lambda: fixed_ns)

    values = [new_uuid7() for _ in range(1000)]
    assert len(set(values)) == 1000

    for value in values:
        assert value.version == 7
        assert value.variant == RFC_4122
        assert value.int >> 80 == expected_ms
```

> UUIDv7'ler `timestamp-sortable`dır; aynı milisaniye içinde sıralı üretim (strict total order) garanti edilmez. RFC 9562 uyumlu olup üretim anında unique kalmayı hedefler; deterministic monotonic counter Phase 1 kapsamında gereksinim değildir.

#### `backend/tests/unit/test_national_id_protection.py`

```python
import base64
import os

import pytest

from mergenvision.domain.errors import SecurityError
from mergenvision.infrastructure.security.national_id import AesGcmNationalIdProtector
from mergenvision.ports.national_id import NationalIdProtectedValue


def _key_b64() -> str:
    return base64.b64encode(os.urandom(32)).decode("ascii")


@pytest.fixture
def protector() -> AesGcmNationalIdProtector:
    return AesGcmNationalIdProtector(
        encryption_key_b64=_key_b64(),
        hmac_key_b64=_key_b64(),
    )


def test_encrypt_then_decrypt_round_trip(protector: AesGcmNationalIdProtector) -> None:
    raw = "12345678901"
    protected = protector.protect(raw)
    assert protector.reveal(protected) == raw


def test_repeated_encryption_produces_different_ciphertexts(
    protector: AesGcmNationalIdProtector,
) -> None:
    raw = "12345678901"
    first = protector.protect(raw)
    second = protector.protect(raw)
    assert first.ciphertext != second.ciphertext
    assert first.lookup_hash == second.lookup_hash


def test_hmac_is_deterministic_for_same_key(protector: AesGcmNationalIdProtector) -> None:
    raw = "12345678901"
    a = protector.protect(raw)
    b = protector.protect(raw)
    assert a.lookup_hash == b.lookup_hash


def test_different_hmac_key_produces_different_hash() -> None:
    raw = "12345678901"
    encryption_key = _key_b64()
    hmac_key_a = _key_b64()
    hmac_key_b = _key_b64()
    p1 = AesGcmNationalIdProtector(
        encryption_key_b64=encryption_key,
        hmac_key_b64=hmac_key_a,
    )
    p2 = AesGcmNationalIdProtector(
        encryption_key_b64=encryption_key,
        hmac_key_b64=hmac_key_b,
    )
    assert p1.protect(raw).lookup_hash != p2.protect(raw).lookup_hash


def test_masking_reveals_last_four_digits(protector: AesGcmNationalIdProtector) -> None:
    protected = protector.protect("12345678901")
    assert protected.masked == "*******8901"


def test_masking_short_value_is_fully_masked(protector: AesGcmNationalIdProtector) -> None:
    protected = protector.protect("1234")
    assert protected.masked == "****"


def test_normalization_trims_and_nfkc(protector: AesGcmNationalIdProtector) -> None:
    raw = "\u00A0  123456789  \u00A0"
    protected = protector.protect(raw)
    assert protector.reveal(protected) == "123456789"


def test_protected_repr_does_not_contain_raw_id(protector: AesGcmNationalIdProtector) -> None:
    raw = "12345678901"
    protected = protector.protect(raw)
    representation = repr(protected)
    assert raw not in representation
    assert "lookup_hash" in representation or "protected" in representation


def test_invalid_encryption_key_size_fails_closed() -> None:
    with pytest.raises(SecurityError):
        AesGcmNationalIdProtector(
            encryption_key_b64=base64.b64encode(os.urandom(16)).decode("ascii"),
            hmac_key_b64=_key_b64(),
        )


def test_invalid_hmac_key_size_fails_closed() -> None:
    with pytest.raises(SecurityError):
        AesGcmNationalIdProtector(
            encryption_key_b64=_key_b64(),
            hmac_key_b64=base64.b64encode(os.urandom(16)).decode("ascii"),
        )


def test_tampered_ciphertext_raises_security_error(
    protector: AesGcmNationalIdProtector,
) -> None:
    protected = protector.protect("12345678901")
    tampered = NationalIdProtectedValue(
        ciphertext=protected.ciphertext[:-1] + bytes([protected.ciphertext[-1] ^ 1]),
        lookup_hash=protected.lookup_hash,
        masked=protected.masked,
    )
    with pytest.raises(SecurityError):
        protector.reveal(tampered)


def test_wrong_encryption_key_raises_security_error() -> None:
    raw = "12345678901"
    encryption_key_a = _key_b64()
    encryption_key_b = _key_b64()
    hmac_key = _key_b64()
    p1 = AesGcmNationalIdProtector(
        encryption_key_b64=encryption_key_a,
        hmac_key_b64=hmac_key,
    )
    p2 = AesGcmNationalIdProtector(
        encryption_key_b64=encryption_key_b,
        hmac_key_b64=hmac_key,
    )
    protected = p1.protect(raw)
    with pytest.raises(SecurityError):
        p2.reveal(protected)


def test_same_encryption_and_hmac_key_rejected() -> None:
    key_b64 = _key_b64()
    with pytest.raises(SecurityError):
        AesGcmNationalIdProtector(
            encryption_key_b64=key_b64,
            hmac_key_b64=key_b64,
        )


def test_adapter_has_no_public_key_export_methods() -> None:
    protector = AesGcmNationalIdProtector(
        encryption_key_b64=_key_b64(),
        hmac_key_b64=_key_b64(),
    )
    assert not hasattr(protector, "encryption_key_b64")
    assert not hasattr(protector, "hmac_key_b64")


def test_protection_does_not_leak_raw_id_or_keys_in_errors_and_repr(
    caplog: pytest.LogCaptureFixture,
) -> None:
    raw = "12345678901"
    encryption_key_b64 = _key_b64()
    hmac_key_b64 = _key_b64()
    protector = AesGcmNationalIdProtector(
        encryption_key_b64=encryption_key_b64,
        hmac_key_b64=hmac_key_b64,
    )

    protected = protector.protect(raw)
    protected_repr = repr(protected)
    assert raw not in protected_repr
    assert encryption_key_b64 not in protected_repr
    assert hmac_key_b64 not in protected_repr

    tampered = NationalIdProtectedValue(
        ciphertext=protected.ciphertext[:-1] + bytes([protected.ciphertext[-1] ^ 1]),
        lookup_hash=protected.lookup_hash,
        masked=protected.masked,
    )
    with pytest.raises(SecurityError) as exc_info:
        protector.reveal(tampered)
    error_text = str(exc_info.value)
    assert raw not in error_text
    assert encryption_key_b64 not in error_text
    assert hmac_key_b64 not in error_text

    for record in caplog.records:
        message = record.getMessage()
        assert raw not in message
        assert encryption_key_b64 not in message
        assert hmac_key_b64 not in message
```

#### `backend/tests/unit/test_alembic_source_immutability.py`

```python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_SOURCE = REPO_ROOT / "backend" / "alembic" / "versions" / "0001_phase1_schema.py"


def test_initial_revision_source_is_independent_of_orm_metadata() -> None:
    assert MIGRATION_SOURCE.exists()
    source = MIGRATION_SOURCE.read_text()
    forbidden = ["Base.metadata", "create_all", "drop_all"]
    for token in forbidden:
        assert token not in source, f"Migration source must not contain {token!r}"


def test_initial_revision_uses_explicit_alembic_operations() -> None:
    source = MIGRATION_SOURCE.read_text()
    required = [
        "op.create_table",
        "op.create_index",
        "op.drop_table",
    ]
    for token in required:
        assert token in source, f"Migration source must contain {token!r}"
```

#### `backend/tests/unit/test_test_database_safety.py`

```python
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "check_test_database_safety.py"


def _run(url: str, *, allow_destructive: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["MERGENVISION_TEST_DATABASE_URL"] = url
    if allow_destructive:
        env["MERGENVISION_ALLOW_DESTRUCTIVE_TEST_DATABASE"] = "YES"
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_valid_test_prefixed_database_name_passes():
    result = _run("postgresql+asyncpg://user:pass@localhost:5432/test_mergenvision")
    assert result.returncode == 0, result.stderr


def test_valid_test_suffixed_database_name_passes():
    result = _run("postgresql+asyncpg://user:pass@localhost:5432/mergenvision_test")
    assert result.returncode == 0, result.stderr


def test_non_test_database_name_is_rejected():
    result = _run("postgresql+asyncpg://user:pass@localhost:5432/mergenvision")
    assert result.returncode != 0
    assert "test_" in result.stderr or "_test" in result.stderr


def test_non_asyncpg_postgresql_url_is_rejected():
    result = _run("postgresql://user:pass@localhost:5432/test_mergenvision")
    assert result.returncode != 0
    assert "asyncpg" in result.stderr


def test_destructive_override_allows_non_test_name():
    result = _run(
        "postgresql+asyncpg://user:pass@localhost:5432/mergenvision",
        allow_destructive=True,
    )
    assert result.returncode == 0, result.stderr
```

#### `backend/tests/integration/test_alembic_postgres.py`

```python
import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import inspect

from mergenvision.config.settings import Settings

EXPECTED_TABLES = {
    "person",
    "face_identity",
    "process_record",
    "inference_profile",
    "person_photo",
    "face_sample",
    "recognition_result",
    "process_event",
}

REPO_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC = REPO_ROOT / ".venv" / "bin" / "alembic"


def _run_alembic(*command: str) -> None:
    settings = Settings()
    env = os.environ.copy()
    env["MERGENVISION_DATABASE_URL"] = settings.database_url
    subprocess.run(
        [str(ALEMBIC), "-c", "backend/alembic.ini", *command],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )


def _table_names(sync_conn):
    return set(inspect(sync_conn).get_table_names())


@pytest.mark.asyncio
async def test_alembic_upgrade_downgrade_reupgrade(db_engine):
    async with db_engine.begin() as conn:
        _run_alembic("downgrade", "base")
        tables_after_downgrade = await conn.run_sync(_table_names)
        assert EXPECTED_TABLES.isdisjoint(tables_after_downgrade)

        _run_alembic("upgrade", "head")
        tables_after_upgrade = await conn.run_sync(_table_names)
        assert tables_after_upgrade == EXPECTED_TABLES | {"alembic_version"}

        _run_alembic("downgrade", "base")
        _run_alembic("upgrade", "head")
        tables_after_reupgrade = await conn.run_sync(_table_names)
        assert tables_after_reupgrade == EXPECTED_TABLES | {"alembic_version"}


@pytest.mark.asyncio
async def test_alembic_check_is_clean_after_upgrade(db_engine):
    _run_alembic("upgrade", "head")
    _run_alembic("check")


def _gather_constraints_and_indexes(sync_conn):
    inspector = inspect(sync_conn)
    data = {}
    for table in [
        "person",
        "face_identity",
        "person_photo",
        "face_sample",
        "recognition_result",
        "process_event",
    ]:
        data[table] = {
            "unique": {c["name"] for c in inspector.get_unique_constraints(table)},
            "indexes": {idx["name"] for idx in inspector.get_indexes(table)},
            "checks": {c["name"] for c in inspector.get_check_constraints(table)},
        }
    return data


@pytest.mark.asyncio
async def test_required_constraints_and_indexes_exist(db_engine):
    _run_alembic("upgrade", "head")

    async with db_engine.begin() as conn:
        data = await conn.run_sync(_gather_constraints_and_indexes)

    assert "uq_person_national_id_lookup_hash" in data["person"]["unique"]
    assert "ix_person_status" in data["person"]["indexes"]

    assert "uq_face_identity_person_id" in data["face_identity"]["unique"]

    assert "uq_person_photo_object_key" in data["person_photo"]["unique"]
    assert "uq_person_photo_person_id_content_sha256" in data["person_photo"]["unique"]
    assert "ix_person_photo_person_id_status" in data["person_photo"]["indexes"]
    assert "ix_uq_person_photo_active_primary" in data["person_photo"]["indexes"]

    assert "uq_face_sample_photo_id_inference_profile_id" in data["face_sample"]["unique"]
    assert "ix_face_sample_face_identity_id_status" in data["face_sample"]["indexes"]
    assert "ix_face_sample_inference_profile_id_status" in data["face_sample"]["indexes"]

    assert "uq_recognition_result_process_id_face_index" in data["recognition_result"]["unique"]
    assert "ix_recognition_result_matched_face_identity_id_created_at" in data["recognition_result"]["indexes"]
    assert "ix_recognition_result_matched_sample_id" in data["recognition_result"]["indexes"]
    assert "ix_recognition_result_recognition_status_created_at" in data["recognition_result"]["indexes"]

    assert "uq_process_event_process_id_sequence_no" in data["process_event"]["unique"]
    assert "ix_process_event_occurred_at" in data["process_event"]["indexes"]

    assert "ck_recognition_result_status_consistency" in data["recognition_result"]["checks"]
    assert "ck_recognition_result_status_values" in data["recognition_result"]["checks"]
```

#### `backend/tests/integration/test_postgres_constraints.py`

```python
import base64
import os
import random

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from mergenvision.domain.enums import (
    FaceIdentityStatus,
    PersonPhotoStatus,
    PersonStatus,
    ProcessStatus,
    RecognitionStatus,
    SampleStatus,
)
from mergenvision.domain.ids import new_uuid7
from mergenvision.infrastructure.database import models as orm
from mergenvision.infrastructure.security.national_id import AesGcmNationalIdProtector

PROTECTOR = AesGcmNationalIdProtector(
    encryption_key_b64=base64.b64encode(os.urandom(32)).decode("ascii"),
    hmac_key_b64=base64.b64encode(os.urandom(32)).decode("ascii"),
)


def _unique_national_id() -> str:
    return f"nat-{random.randint(100000000, 999999999)}"


def _make_person(national_id: str | None = None) -> orm.Person:
    raw = national_id or _unique_national_id()
    protected = PROTECTOR.protect(raw)
    return orm.Person(
        person_id=new_uuid7(),
        first_name="Ada",
        last_name="Lovelace",
        national_id_ciphertext=protected.ciphertext,
        national_id_lookup_hash=protected.lookup_hash,
        national_id_masked=protected.masked,
        additional_details={},
        status=PersonStatus.ACTIVE,
    )


def _make_face_identity(person_id) -> orm.FaceIdentity:
    return orm.FaceIdentity(
        face_identity_id=new_uuid7(),
        person_id=person_id,
        status=FaceIdentityStatus.ACTIVE,
    )


def _make_profile(name: str = "default") -> orm.InferenceProfile:
    return orm.InferenceProfile(
        inference_profile_id=new_uuid7(),
        profile_name=name,
        detector_name="retinaface",
        detector_version="1",
        detector_artifact_sha256="sha",
        alignment_version="v1",
        embedder_name="arcface",
        embedder_version="1",
        embedder_artifact_sha256="sha",
        preprocessing_version="v1",
        embedding_dimension=512,
        distance_metric="cosine",
        match_threshold=0.65,
        is_active=True,
    )


def _make_photo(
    person_id,
    object_key: str,
    *,
    is_primary: bool = False,
    content_sha256: str | None = None,
) -> orm.PersonPhoto:
    return orm.PersonPhoto(
        photo_id=new_uuid7(),
        person_id=person_id,
        object_key=object_key,
        content_sha256=content_sha256 or ("sha" + object_key),
        mime_type="image/jpeg",
        file_size_bytes=1234,
        width=100,
        height=100,
        is_primary=is_primary,
        status=PersonPhotoStatus.ACTIVE,
    )


def _make_sample(face_identity_id, photo_id, profile_id) -> orm.FaceSample:
    return orm.FaceSample(
        sample_id=new_uuid7(),
        face_identity_id=face_identity_id,
        photo_id=photo_id,
        inference_profile_id=profile_id,
        bbox_x=0,
        bbox_y=0,
        bbox_width=50,
        bbox_height=50,
        landmarks={},
        detection_confidence=0.99,
        quality_score=0.9,
        status=SampleStatus.ACTIVE,
    )


def _make_process() -> orm.ProcessRecord:
    return orm.ProcessRecord(
        process_id=new_uuid7(),
        process_type="identification",
        status=ProcessStatus.PENDING,
    )


@pytest.mark.asyncio
async def test_duplicate_national_id_lookup_hash_rejected(session):
    person1 = _make_person("same-id")
    person2 = _make_person("same-id")
    session.add(person1)
    await session.flush()
    session.add(person2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_second_face_identity_for_person_rejected(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    identity1 = _make_face_identity(person.person_id)
    identity2 = _make_face_identity(person.person_id)
    session.add(identity1)
    await session.flush()
    session.add(identity2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_duplicate_object_key_rejected(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo1 = _make_photo(person.person_id, "same-key")
    photo2 = _make_photo(person.person_id, "same-key")
    session.add(photo1)
    await session.flush()
    session.add(photo2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_duplicate_photo_content_rejected(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo1 = _make_photo(person.person_id, "key-1", content_sha256="dup-sha")
    photo2 = _make_photo(person.person_id, "key-2", content_sha256="dup-sha")
    session.add(photo1)
    await session.flush()
    session.add(photo2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_two_active_primary_photos_rejected(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo1 = _make_photo(person.person_id, "primary-1", is_primary=True)
    photo2 = _make_photo(person.person_id, "primary-2", is_primary=True)
    session.add(photo1)
    await session.flush()
    session.add(photo2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_two_active_primary_photos_different_persons_allowed(session):
    person1 = _make_person()
    person2 = _make_person()
    session.add_all([person1, person2])
    await session.flush()
    photo1 = _make_photo(person1.person_id, "primary-a", is_primary=True)
    photo2 = _make_photo(person2.person_id, "primary-b", is_primary=True)
    session.add_all([photo1, photo2])
    await session.flush()

    result = await session.execute(
        select(orm.PersonPhoto).where(orm.PersonPhoto.is_primary.is_(True))
    )
    assert len(result.scalars().all()) == 2


@pytest.mark.asyncio
async def test_duplicate_face_sample_photo_profile_rejected(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "sample-photo")
    session.add(photo)
    await session.flush()
    sample1 = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    sample2 = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    session.add(sample1)
    await session.flush()
    session.add(sample2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_duplicate_recognition_result_process_face_index_rejected(session):
    process = _make_process()
    session.add(process)
    await session.flush()
    result1 = orm.RecognitionResult(
        result_id=new_uuid7(),
        process_id=process.process_id,
        face_index=0,
        recognition_status=RecognitionStatus.UNKNOWN,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
    )
    result2 = orm.RecognitionResult(
        result_id=new_uuid7(),
        process_id=process.process_id,
        face_index=0,
        recognition_status=RecognitionStatus.UNKNOWN,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
    )
    session.add(result1)
    await session.flush()
    session.add(result2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_duplicate_process_event_sequence_rejected(session):
    process = _make_process()
    session.add(process)
    await session.flush()
    event1 = orm.ProcessEvent(
        event_id=new_uuid7(),
        process_id=process.process_id,
        sequence_no=1,
        event_type="started",
    )
    event2 = orm.ProcessEvent(
        event_id=new_uuid7(),
        process_id=process.process_id,
        sequence_no=1,
        event_type="completed",
    )
    session.add(event1)
    await session.flush()
    session.add(event2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_photo_file_size_must_be_positive(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo = _make_photo(person.person_id, "bad-size")
    photo.file_size_bytes = 0
    session.add(photo)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_photo_dimensions_must_be_positive(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo = _make_photo(person.person_id, "bad-width")
    photo.width = 0
    session.add(photo)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_face_sample_bbox_must_be_positive(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "sample-bad")
    session.add(photo)
    await session.flush()
    sample = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    sample.bbox_width = 0
    session.add(sample)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_detection_confidence_must_be_zero_to_one(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "sample-conf")
    session.add(photo)
    await session.flush()
    sample = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    sample.detection_confidence = 1.5
    session.add(sample)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_quality_score_must_be_zero_to_one_or_null(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "sample-quality")
    session.add(photo)
    await session.flush()
    sample = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    sample.quality_score = 1.5
    session.add(sample)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_inference_profile_dimension_must_be_positive(session):
    profile = _make_profile()
    profile.embedding_dimension = 0
    session.add(profile)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_process_input_size_positive(session):
    process = _make_process()
    process.input_size_bytes = 0
    session.add(process)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_process_input_width_positive(session):
    process = _make_process()
    process.input_width = 0
    session.add(process)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_process_detected_face_count_nonnegative(session):
    process = _make_process()
    process.detected_face_count = -1
    session.add(process)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_recognition_result_known_requires_references(session):
    process = _make_process()
    session.add(process)
    await session.flush()
    result = orm.RecognitionResult(
        result_id=new_uuid7(),
        process_id=process.process_id,
        face_index=0,
        recognition_status=RecognitionStatus.KNOWN,
        matched_face_identity_id=None,
        matched_sample_id=None,
        similarity_score=None,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
    )
    session.add(result)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_recognition_result_unknown_must_not_have_references(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "unknown-refs")
    session.add(photo)
    await session.flush()
    sample = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    session.add(sample)
    await session.flush()
    process = _make_process()
    session.add(process)
    await session.flush()
    result = orm.RecognitionResult(
        result_id=new_uuid7(),
        process_id=process.process_id,
        face_index=0,
        recognition_status=RecognitionStatus.UNKNOWN,
        matched_face_identity_id=identity.face_identity_id,
        matched_sample_id=sample.sample_id,
        similarity_score=0.5,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
    )
    session.add(result)
    with pytest.raises(IntegrityError):
        await session.flush()


def _get_foreign_keys(sync_conn):
    inspector = inspect(sync_conn)
    return {
        table: inspector.get_foreign_keys(table)
        for table in [
            "face_identity",
            "process_record",
            "person_photo",
            "face_sample",
            "recognition_result",
            "process_event",
        ]
    }


@pytest.mark.asyncio
async def test_no_broad_cascade_on_foreign_keys(db_engine):
    async with db_engine.begin() as conn:
        fks_by_table = await conn.run_sync(_get_foreign_keys)
    for _table, fks in fks_by_table.items():
        for fk in fks:
            assert fk.get("ondelete") is None
            assert fk.get("onupdate") is None
```

#### `backend/tests/integration/test_postgres_repositories.py`

```python
import asyncio
import base64
import os
import random
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from mergenvision.domain.entities import (
    FaceIdentity,
    FaceSample,
    InferenceProfile,
    Person,
    PersonPhoto,
    ProcessEvent,
    ProcessRecord,
    RecognitionResult,
)
from mergenvision.domain.enums import (
    FaceIdentityStatus,
    PersonPhotoStatus,
    PersonStatus,
    ProcessStatus,
    RecognitionStatus,
    SampleStatus,
)
from mergenvision.domain.errors import ConflictError, RepositoryError
from mergenvision.domain.ids import new_uuid7
from mergenvision.infrastructure.database import models as orm
from mergenvision.infrastructure.database.repositories import (
    PostgresFaceIdentityRepository,
    PostgresFaceSampleRepository,
    PostgresInferenceProfileRepository,
    PostgresPersonPhotoRepository,
    PostgresPersonRepository,
    PostgresProcessEventRepository,
    PostgresProcessRecordRepository,
    PostgresRecognitionResultRepository,
)
from mergenvision.infrastructure.security.national_id import AesGcmNationalIdProtector
from mergenvision.ports.national_id import NationalIdProtectedValue


def _key() -> str:
    return base64.b64encode(os.urandom(32)).decode("ascii")


@pytest.fixture
def protector() -> AesGcmNationalIdProtector:
    return AesGcmNationalIdProtector(
        encryption_key_b64=_key(),
        hmac_key_b64=_key(),
    )


def _unique_id() -> str:
    return f"id-{random.randint(100000000, 999999999)}"


def _make_person(protector: AesGcmNationalIdProtector, raw: str | None = None) -> Person:
    raw_id = raw or _unique_id()
    protected = protector.protect(raw_id)
    return Person(
        person_id=new_uuid7(),
        first_name="Ada",
        last_name="Lovelace",
        national_id_ciphertext=protected.ciphertext,
        national_id_lookup_hash=protected.lookup_hash,
        national_id_masked=protected.masked,
        additional_details={"department": "Research"},
        status=PersonStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_face_identity(person_id) -> FaceIdentity:
    return FaceIdentity(
        face_identity_id=new_uuid7(),
        person_id=person_id,
        status=FaceIdentityStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_profile(name: str = "profile") -> InferenceProfile:
    return InferenceProfile(
        inference_profile_id=new_uuid7(),
        profile_name=name,
        detector_name="retinaface",
        detector_version="1",
        detector_artifact_sha256="sha",
        alignment_version="v1",
        embedder_name="arcface",
        embedder_version="1",
        embedder_artifact_sha256="sha",
        preprocessing_version="v1",
        embedding_dimension=512,
        distance_metric="cosine",
        match_threshold=0.65,
        is_active=True,
        created_at=datetime.now(UTC),
    )


def _make_photo(person_id, object_key: str, *, is_primary: bool = False) -> PersonPhoto:
    return PersonPhoto(
        photo_id=new_uuid7(),
        person_id=person_id,
        object_key=object_key,
        content_sha256="sha" + object_key,
        mime_type="image/jpeg",
        file_size_bytes=1234,
        width=100,
        height=100,
        is_primary=is_primary,
        status=PersonPhotoStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_process(process_type: str = "identification") -> ProcessRecord:
    return ProcessRecord(
        process_id=new_uuid7(),
        process_type=process_type,
        status=ProcessStatus.PENDING,
        created_at=datetime.now(UTC),
    )


def _make_sample(identity_id, photo_id, profile_id) -> FaceSample:
    return FaceSample(
        sample_id=new_uuid7(),
        face_identity_id=identity_id,
        photo_id=photo_id,
        inference_profile_id=profile_id,
        bbox_x=0,
        bbox_y=0,
        bbox_width=50,
        bbox_height=50,
        landmarks={"left_eye": [10, 10]},
        detection_confidence=0.99,
        quality_score=0.9,
        status=SampleStatus.ACTIVE,
        created_at=datetime.now(UTC),
    )


def _make_result(
    process_id,
    face_index: int,
    status: str,
    *,
    identity_id=None,
    sample_id=None,
    similarity=None,
) -> RecognitionResult:
    return RecognitionResult(
        result_id=new_uuid7(),
        process_id=process_id,
        face_index=face_index,
        recognition_status=status,
        matched_face_identity_id=identity_id,
        matched_sample_id=sample_id,
        similarity_score=similarity,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_person_repository_crud(session: AsyncSession, protector: AesGcmNationalIdProtector):
    repo = PostgresPersonRepository(session)
    person = _make_person(protector)
    created = await repo.add(person)
    assert created.person_id == person.person_id

    fetched = await repo.get_by_id(created.person_id)
    assert fetched is not None
    assert fetched.national_id_lookup_hash == person.national_id_lookup_hash

    by_hash = await repo.get_by_national_id_lookup_hash(person.national_id_lookup_hash)
    assert by_hash is not None
    assert by_hash.person_id == person.person_id

    listed = await repo.list_active(limit=10, offset=0)
    assert any(p.person_id == person.person_id for p in listed)

    updated = await repo.update(
        person.person_id,
        first_name="Updated",
        additional_details={"department": "AI"},
    )
    assert updated is not None
    assert updated.first_name == "Updated"
    assert updated.additional_details == {"department": "AI"}

    deactivated = await repo.deactivate(person.person_id)
    assert deactivated is not None
    assert deactivated.status == PersonStatus.INACTIVE

    not_found = await repo.get_by_id(person.person_id)
    assert not_found is None


@pytest.mark.asyncio
async def test_person_repository_duplicate_national_id_raises_conflict(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    repo = PostgresPersonRepository(session)
    person1 = _make_person(protector, raw="duplicate")
    person2 = _make_person(protector, raw="duplicate")
    await repo.add(person1)
    with pytest.raises(ConflictError):
        await repo.add(person2)


@pytest.mark.asyncio
async def test_face_identity_repository(session: AsyncSession, protector: AesGcmNationalIdProtector):
    repo = PostgresFaceIdentityRepository(session)
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    identity = _make_face_identity(person.person_id)
    created = await repo.add(identity)
    assert created.face_identity_id == identity.face_identity_id

    fetched = await repo.get_by_id(created.face_identity_id)
    assert fetched is not None

    by_person = await repo.get_by_person_id(person.person_id)
    assert by_person is not None
    assert by_person.face_identity_id == created.face_identity_id

    deactivated = await repo.deactivate(created.face_identity_id)
    assert deactivated is not None
    assert deactivated.status == FaceIdentityStatus.INACTIVE


@pytest.mark.asyncio
async def test_inference_profile_repository(session: AsyncSession):
    repo = PostgresInferenceProfileRepository(session)
    profile = _make_profile("test-profile")
    created = await repo.add(profile)
    assert created.profile_name == "test-profile"

    fetched = await repo.get_by_id(created.inference_profile_id)
    assert fetched is not None

    by_name = await repo.get_by_name("test-profile")
    assert by_name is not None

    active = await repo.get_active()
    assert active is not None

    retired = await repo.retire(created.inference_profile_id)
    assert retired is not None
    assert retired.is_active is False


@pytest.mark.asyncio
async def test_process_record_repository(session: AsyncSession):
    repo = PostgresProcessRecordRepository(session)
    record = _make_process()
    created = await repo.add(record)
    assert created.status == ProcessStatus.PENDING

    started = await repo.mark_started(created.process_id)
    assert started is not None
    assert started.status == ProcessStatus.PROCESSING
    assert started.started_at is not None

    completed = await repo.mark_completed(
        created.process_id,
        detected_face_count=0,
    )
    assert completed is not None
    assert completed.status == ProcessStatus.COMPLETED
    assert completed.completed_at is not None
    assert completed.detected_face_count == 0

    failed_record = await repo.add(_make_process("identification"))
    failed = await repo.mark_failed(
        failed_record.process_id,
        error_code="ERR",
        error_message_sanitized="safe message",
    )
    assert failed is not None
    assert failed.status == ProcessStatus.FAILED


@pytest.mark.asyncio
async def test_person_photo_repository(session: AsyncSession, protector: AesGcmNationalIdProtector):
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    photo_repo = PostgresPersonPhotoRepository(session)
    photo1 = await photo_repo.add(_make_photo(person.person_id, "photo-1"))
    photo2 = await photo_repo.add(_make_photo(person.person_id, "photo-2"))

    listed = await photo_repo.list_by_person(person.person_id, limit=10, offset=0)
    assert len(listed) == 2

    primary = await photo_repo.set_primary(photo1.photo_id)
    assert primary is not None
    assert primary.is_primary is True

    switch = await photo_repo.set_primary(photo2.photo_id)
    assert switch is not None
    assert switch.is_primary is True

    refreshed = await photo_repo.get_by_id(photo1.photo_id)
    assert refreshed is not None
    assert refreshed.is_primary is False

    deactivated = await photo_repo.deactivate(photo2.photo_id)
    assert deactivated is not None
    assert deactivated.status == PersonPhotoStatus.INACTIVE


@pytest.mark.asyncio
async def test_face_sample_repository(session: AsyncSession, protector: AesGcmNationalIdProtector):
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    identity_repo = PostgresFaceIdentityRepository(session)
    identity = await identity_repo.add(_make_face_identity(person.person_id))

    profile_repo = PostgresInferenceProfileRepository(session)
    profile = await profile_repo.add(_make_profile("sample-profile"))

    photo_repo = PostgresPersonPhotoRepository(session)
    photo = await photo_repo.add(_make_photo(person.person_id, "sample-photo"))

    sample_repo = PostgresFaceSampleRepository(session)
    sample = await sample_repo.add(
        _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    )
    assert sample.sample_id is not None

    listed = await sample_repo.list_active_by_identity(
        identity.face_identity_id, limit=10, offset=0
    )
    assert len(listed) == 1

    deactivated = await sample_repo.deactivate(sample.sample_id)
    assert deactivated is not None
    assert deactivated.status == SampleStatus.INACTIVE


@pytest.mark.asyncio
async def test_recognition_result_repository(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    identity_repo = PostgresFaceIdentityRepository(session)
    identity = await identity_repo.add(_make_face_identity(person.person_id))

    profile_repo = PostgresInferenceProfileRepository(session)
    profile = await profile_repo.add(_make_profile("result-profile"))

    photo_repo = PostgresPersonPhotoRepository(session)
    photo = await photo_repo.add(_make_photo(person.person_id, "result-photo"))

    sample_repo = PostgresFaceSampleRepository(session)
    sample = await sample_repo.add(
        _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    )

    process_repo = PostgresProcessRecordRepository(session)
    process = await process_repo.add(_make_process())

    result_repo = PostgresRecognitionResultRepository(session)
    known = await result_repo.add(
        _make_result(
            process.process_id,
            0,
            RecognitionStatus.KNOWN,
            identity_id=identity.face_identity_id,
            sample_id=sample.sample_id,
            similarity=0.85,
        )
    )
    assert known.recognition_status == RecognitionStatus.KNOWN

    unknown = await result_repo.add(
        _make_result(process.process_id, 1, RecognitionStatus.UNKNOWN)
    )
    assert unknown.recognition_status == RecognitionStatus.UNKNOWN

    by_process = await result_repo.list_by_process(process.process_id)
    assert len(by_process) == 2

    history = await result_repo.list_history_by_identity(
        identity.face_identity_id, limit=10, offset=0
    )
    assert len(history) == 1
    assert history[0].result_id == known.result_id


@pytest.mark.asyncio
async def test_process_event_repository(session: AsyncSession):
    process_repo = PostgresProcessRecordRepository(session)
    process = await process_repo.add(_make_process())

    event_repo = PostgresProcessEventRepository(session)
    event1 = await event_repo.append(process.process_id, event_type="started")
    event2 = await event_repo.append(process.process_id, event_type="completed")

    assert event1.sequence_no == 1
    assert event2.sequence_no == 2

    listed = await event_repo.list_by_process(process.process_id, limit=10, offset=0)
    assert len(listed) == 2
    assert listed[0].sequence_no == 1
    assert listed[1].sequence_no == 2


@pytest.mark.asyncio
async def test_repository_does_not_auto_commit(
    session: AsyncSession,
    db_engine,
    protector: AesGcmNationalIdProtector,
):
    repo = PostgresPersonRepository(session)
    person = await repo.add(_make_person(protector))

    factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as new_session:
        result = await new_session.execute(
            select(orm.Person).where(orm.Person.person_id == person.person_id)
        )
        assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_raw_national_id_not_persisted(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    raw_id = "12345678901"
    repo = PostgresPersonRepository(session)
    person = await repo.add(_make_person(protector, raw=raw_id))

    result = await session.execute(
        select(
            orm.Person.national_id_ciphertext,
            orm.Person.national_id_lookup_hash,
            orm.Person.national_id_masked,
        ).where(orm.Person.person_id == person.person_id)
    )
    row = result.one()
    assert raw_id not in row.national_id_lookup_hash
    assert row.national_id_masked != raw_id
    assert row.national_id_masked == "*******8901"
    assert protector.reveal(
        protector.protect(raw_id)
    ) == raw_id


@pytest.mark.asyncio
async def test_stored_national_id_decrypts_to_normalized_raw_id_and_does_not_leak(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
    caplog: pytest.LogCaptureFixture,
):
    raw_id = "  12345678901  "
    repo = PostgresPersonRepository(session)
    person = await repo.add(_make_person(protector, raw=raw_id))

    result = await session.execute(
        select(
            orm.Person.national_id_ciphertext,
            orm.Person.national_id_lookup_hash,
            orm.Person.national_id_masked,
        ).where(orm.Person.person_id == person.person_id)
    )
    row = result.one()
    normalized_id = raw_id.strip()

    reconstructed = NationalIdProtectedValue(
        ciphertext=row.national_id_ciphertext,
        lookup_hash=row.national_id_lookup_hash,
        masked=row.national_id_masked,
    )
    revealed = protector.reveal(reconstructed)
    assert revealed == normalized_id

    assert normalized_id.encode("utf-8") not in row.national_id_ciphertext
    assert normalized_id not in row.national_id_lookup_hash
    assert normalized_id not in row.national_id_masked

    for record in caplog.records:
        message = record.getMessage()
        assert normalized_id not in message


@pytest.mark.asyncio
async def test_person_repository_atomic_national_id_update(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    repo = PostgresPersonRepository(session)
    person = await repo.add(_make_person(protector, raw="old-id-12345"))

    new_raw = "new-id-67890"
    new_protected = protector.protect(new_raw)
    updated = await repo.update_national_id(person.person_id, new_protected)
    assert updated is not None
    assert updated.national_id_lookup_hash == new_protected.lookup_hash
    assert updated.national_id_masked == new_protected.masked

    fetched = await session.execute(
        select(
            orm.Person.national_id_ciphertext,
            orm.Person.national_id_lookup_hash,
            orm.Person.national_id_masked,
        ).where(orm.Person.person_id == person.person_id)
    )
    row = fetched.one()
    assert row.national_id_lookup_hash == new_protected.lookup_hash
    revealed = protector.reveal(
        NationalIdProtectedValue(
            ciphertext=row.national_id_ciphertext,
            lookup_hash=row.national_id_lookup_hash,
            masked=row.national_id_masked,
        )
    )
    assert revealed == new_raw


@pytest.mark.asyncio
async def test_inference_profile_get_active_raises_on_multiple_active(session: AsyncSession):
    repo = PostgresInferenceProfileRepository(session)
    active_a = await repo.add(_make_profile(name="active-a"))
    active_b = await repo.add(_make_profile(name="active-b"))
    assert active_a.is_active is True
    assert active_b.is_active is True

    with pytest.raises(RepositoryError):
        await repo.get_active()


@pytest.mark.asyncio
async def test_person_photo_lifecycle_activate_and_deactivate(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    photo_repo = PostgresPersonPhotoRepository(session)
    photo = await photo_repo.add(_make_photo(person.person_id, "lifecycle-photo"))

    deactivated = await photo_repo.deactivate(photo.photo_id)
    assert deactivated is not None
    assert deactivated.status == PersonPhotoStatus.INACTIVE

    reactivated = await photo_repo.activate(photo.photo_id)
    assert reactivated is not None
    assert reactivated.status == PersonPhotoStatus.ACTIVE
    assert reactivated.deleted_at is None


@pytest.mark.asyncio
async def test_face_sample_lifecycle_activate_and_deactivate(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    identity_repo = PostgresFaceIdentityRepository(session)
    identity = await identity_repo.add(_make_face_identity(person.person_id))

    profile_repo = PostgresInferenceProfileRepository(session)
    profile = await profile_repo.add(_make_profile("lifecycle-profile"))

    photo_repo = PostgresPersonPhotoRepository(session)
    photo = await photo_repo.add(_make_photo(person.person_id, "lifecycle-sample-photo"))

    sample_repo = PostgresFaceSampleRepository(session)
    sample = await sample_repo.add(
        _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    )

    deactivated = await sample_repo.deactivate(sample.sample_id)
    assert deactivated is not None
    assert deactivated.status == SampleStatus.INACTIVE

    reactivated = await sample_repo.activate(sample.sample_id)
    assert reactivated is not None
    assert reactivated.status == SampleStatus.ACTIVE
    assert reactivated.deleted_at is None


@pytest.mark.asyncio
async def test_process_event_concurrent_appends_are_unique_and_sequential(db_engine):
    setup_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with setup_factory() as setup_session:
        process_repo = PostgresProcessRecordRepository(setup_session)
        process = await process_repo.add(_make_process())
        await setup_session.commit()

    async def append(event_type: str) -> ProcessEvent:
        factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with factory() as session:
            repo = PostgresProcessEventRepository(session)
            event = await repo.append(process.process_id, event_type=event_type)
            await session.commit()
            return event

    events = await asyncio.gather(append("a"), append("b"))
    sequence_numbers = sorted(e.sequence_no for e in events)
    assert sequence_numbers == [1, 2]

    verify_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with verify_factory() as verify_session:
        repo = PostgresProcessEventRepository(verify_session)
        listed = await repo.list_by_process(process.process_id, limit=10, offset=0)
        assert len(listed) == 2
        assert sorted(e.sequence_no for e in listed) == [1, 2]
```
