# MergenVision Implementation Details

## Belgenin kullanım amacı

- Bu belge **kodun yerine geçmez**. Gerçek kaynak ve testler her zaman en güncel source-of-truth’tur.
- Her sprint sonunda bu belgeye `append/update` edilecektir; böylece projenin teknik detaylarına hakim olmayan proje sahibi de "şu anda gerçekten ne çalışıyor?" sorusuna somut yanıt bulabilir.
- Her sprintte neyin tamamlandığı, neyin henüz başlamadığı, kanıt dosyaları ve bilinen kısıtlar burada izlenecektir.

## Current Product Status

| Katman | Durum | Kısa açıklama | Kanıt dosyası / komut |
|---|---|---|---|
| Foundation | VERIFIED | Build/test çalışan repo iskeleti, katman import kuralları, C++ native library proto-contract’ı oluşturuldu. | `make verify-foundation` |
| PostgreSQL | NOT_STARTED | SQLAlchemy model, Alembic migration ve repository yok. | — |
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
