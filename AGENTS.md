# MergenVision Agent Anayasası

Bu dosya repository genelindeki kalıcı çalışma kurallarını tanımlar. Kullanıcının güncel açık talimatı her zaman bu dosyadan üstündür. Sprint'e özel teslimatlar bu dosyaya eklenmez; `docs/implementation/CURRENT_SPRINT.md` içinde tutulur.

## 1. Aktif repository ve dil

- Tek yazılabilir proje `/home/user/Workspace/MergenVisionFinalVersion` repository'sidir.
- Eski repository'ler yalnızca salt-okunur referans ve lessons-learned kaynağıdır.
- Kullanıcı açıkça istemedikçe eski repository'leri değiştirme.
- Raporlar, planlar ve kullanıcıya açıklamalar Türkçe yazılır. Kod, identifier, API field ve teknik komutlar İngilizce kalabilir.
- Production source içinde `/home/user/...` gibi makineye özel absolute runtime path kullanma.

## 2. Her görevde zorunlu başlangıç

Her yeni görevde, kod veya doküman değiştirmeden önce:

1. Repository root'u ve `git status --short` çıktısını doğrula.
2. Bu `AGENTS.md` dosyasını tamamen oku.
3. `docs/implementation/CURRENT_SPRINT.md` dosyasını oku.
4. `using-superpowers` tarafından belirlenen skill kullanım akışını uygula.
5. Multi-file veya yeni sprint işinde `codebase-memory-mcp` ile aktif repository context'ini yükle.
6. Görevle ilgili requirement, architecture, source, test ve reference dosyalarını oku.
7. Mevcut kullanıcı değişikliklerini koru; unrelated dosyalara dokunma.

Context compaction sonrasında:

1. `AGENTS.md` ve `CURRENT_SPRINT.md` dosyalarını yeniden oku.
2. `codebase-memory-mcp` ile aktif repository context'ini geri yükle.
3. `git status --short` ve mevcut implementation ledger üzerinden tamamlanmış işi belirle.
4. Tamamlanmış adımları yeniden yapma ve sprint kapsamını genişletme.

`CURRENT_SPRINT.md` yoksa veya görevle çelişiyorsa implementation başlatma; kullanıcıya blocker'ı bildir.

## 3. Source-of-truth sırası

Çelişki halinde aşağıdaki sıra uygulanır:

1. Kullanıcının güncel açık kararı.
2. `requirements/phase1requirements.md` içindeki senior/client Phase 1 gereksinimleri.
3. Onaylanmış `architecture/01`–`architecture/06` belgeleri.
4. Onaylanmış `docs/implementation/CURRENT_SPRINT.md`.
5. `requirements/ProjectRequirements.md` içindeki çelişmeyen legacy davranışlar.
6. `requirements/phase2requirements.md`, yalnızca gelecekteki uyumluluk için.
7. `opensourcereferences/references.md`, resmi dokümanlar ve upstream source.
8. Eski repository kodları ve raporları.

Legacy `ProjectRequirements.md` içindeki “API-only / UI olmayacak” kararı geçersizdir. Phase 1 mandatory internal web UI içerir.

Onaylanmış mimari veya requirement değişikliği gerekiyorsa kendiliğinden değiştirme. Gerekçeyi ve etkisini kullanıcıya sun; açık onay bekle.

## 4. Scope ve çalışma temposu

- Phase 1 tamamen bitmeden Phase 2 implementation başlatma.
- Bir sprinti anlamlı, cohesive bir teslimat olarak yürüt. Gereksiz mikro-sprint veya mikro-onay üretme.
- Kullanıcıdan yalnızca mimariyi değiştiren karar, destructive işlem, secret, model indirme, sistem paketi/driver değişikliği veya Git publish yetkisi gerektiğinde onay iste.
- Normal in-scope implementasyon, test, lint ve read-only incelemelerde otonom devam et.
- Kapsam dışı adjacent feature, “ileride lazım olur” tablosu, endpoint veya abstraction ekleme.
- Dev raporları üretip ürünü ilerletmeme davranışından kaçın. Her implementation sprinti çalışan dikey bir sonuç veya açık bir teknik gate üretmelidir.

## 5. Phase 1 ürün sınırı

Phase 1 şunları tamamlar:

- Fotoğraf tabanlı person enrollment ve identification.
- Çoklu yüz detection ve her yüz için bağımsız known/unknown sonucu.
- No-face durumunun başarılı iş sonucu olarak dönmesi.
- Person/photo/sample ve process/history yönetimi.
- FastAPI backend ve `/api/v1` contract'ı.
- Mandatory internal React + TypeScript UI.
- PostgreSQL, MinIO ve Qdrant entegrasyonu.
- Docker Compose, testler, gerçek runtime kanıtı ve dokümantasyon.
- Dataset tabanlı doğruluk ve bulk enrollment benchmark altyapısı.

Phase 1 dışında:

- Video, RTSP/live stream, GStreamer/DeepStream, tracker ve NVENC.
- Object detection ve segmentation.
- Oracle'ın online request hot path'e bağlanması.
- Premature Kubernetes, distributed microservices veya 10M sharding platformu.

Oracle yalnızca gelecekteki bulk import source boundary'sidir. Phase 1 online dependency değildir.

## 6. Dondurulmuş veri ve storage kararları

Phase 1 PostgreSQL tabloları tam olarak:

- `person`
- `face_identity`
- `process_record`
- `inference_profile`
- `person_photo`
- `face_sample`
- `recognition_result`
- `process_event`

Yeni tablo veya kolon ihtiyacı frozen ERD ile çelişiyorsa önce kullanıcı onayı gerekir.

Ownership:

- PostgreSQL relational/business source of truth'tür.
- MinIO binary object owner'dır.
- Qdrant derived ve rebuildable 512-D vector search index'idir.
- PostgreSQL'e embedding veya image binary yazılmaz.
- Qdrant'a PII veya geniş person metadata yazılmaz.
- MinIO object key'leri yalnızca sistem UUID'leri ve teknik segmentler içerir.

Identity kuralları:

- Bir `person`, Phase 1'de en fazla bir aktif `face_identity` taşır.
- Bir `face_identity`, çok sayıda `face_sample` taşıyabilir.
- Qdrant point ID tam olarak `face_sample.sample_id` olur.
- Recognition status yalnızca `known` veya `unknown` olur.
- Unknown yüz Phase 1'de otomatik person/identity/sample olarak persist edilmez.
- Silinmiş veya inactive Qdrant sonucu final karar öncesi PostgreSQL lifecycle ile doğrulanır.

Qdrant collection, vector, HNSW ve payload index kararları `architecture/05-phase1-qdrant-vector-design.md` ile uyumlu olmalıdır. Ölçüm olmadan parametre değiştirme.

## 7. Cross-store consistency

PostgreSQL, MinIO ve Qdrant tek transaction paylaşmaz. Bu nedenle multi-store workflow'lar şunları açıkça tasarlamalıdır:

- Deterministic UUID ve object key.
- Idempotent retry.
- Bounded batch/concurrency.
- Explicit lifecycle/indexing state.
- Failure event ve sanitized error.
- Compensation veya reconciliation yolu.
- Partial failure integration testi.

MinIO/Qdrant başarılı olup PostgreSQL başarısız olduğunda orphan bırakmayı normal kabul etme. Qdrant upsert tamamlanmadan sample'ı indexed/ready gösterme.

## 8. Privacy ve security baseline

Raw national ID:

- Log, event, response, MinIO key/metadata, Qdrant payload veya benchmark output'a yazılmaz.
- Yalnız kontrollü request boundary'de kabul edilir.
- PostgreSQL'de approved contract'a göre ciphertext + lookup HMAC/hash + masked display tutulur.
- Encryption key ve HMAC pepper secret/config üzerinden gelir; boş veya hardcoded default kullanılamaz.

Ek kurallar:

- Dataset kişi adı/folder adı public log, object key veya benchmark result'a yazılmaz.
- Raw exception, SQL, credential, filesystem path ve secret client response'a dönülmez.
- Demo login ekranını gerçek authentication kanıtı gibi sunma.
- Secret, token, model weight, engine ve dataset Git'e eklenmez.

## 9. Reference-first engineering

Production implementasyonu model hafızasından veya rastgele yeni pattern ile yazma.

İlgili implementasyondan önce:

1. `opensourcereferences/references.md` içindeki uygun kaynakları belirle.
2. Öncelikle official/current documentation incele.
3. Upstream repository'nin gerçek source veya sample implementasyonunu incele.
4. Aynı davranış eski repository'de varsa salt-okunur karşılaştır.
5. Seçilen ve reddedilen yaklaşımı `docs/implementation/REFERENCE_DECISION_LOG.md` içine kısa biçimde kaydet.
6. Failing test ile başlayıp minimum production implementation yap.

Kopyalanan/adapte edilen kod için upstream URL, commit/tag, lisans ve yapılan değişiklik kaydedilir. Reference list gereksinim kaynağı değildir; requirements ve architecture üstündür.

Eski repository “çalışıyor” diye kodunu körlemesine taşıma. Özellikle eski DALI, alignment, TensorRT CPU-copy, bulk persistence, identity creation ve Qdrant lifecycle kodları production oracle değildir.

## 10. ML model ve doğruluk gate'i

Mevcut aday yön:

- Batch-capable face detector; öncelikli aday dynamic RetinaFace.
- Canonical five-point face alignment.
- ArcFace 512-D embedding.
- GPU L2 normalization ve cosine similarity.

Bu modeller final değildir. Model artifact, tensor name/shape, preprocessing, landmark order, license ve accuracy parity kanıtlanmadan seçim “locked” veya “production-ready” sayılmaz.

Alignment ayrı release gate'idir. En az şunlar doğrulanır:

- Detector output tensor isimleri ve shape'leri.
- Bounding-box ve landmark reverse mapping.
- Exact landmark order.
- ArcFace canonical template.
- Similarity transform yönü.
- Pixel-center ve `align_corners` davranışı.
- Reference crop parity ve contact sheet.
- Batch 1 ile batch N parity.
- Same-person / different-person cosine dağılımı ve threshold calibration.

Detector candidate'ları model hatası diye değiştirmeden önce coordinate mapping, landmark order, NMS, quality gate ve alignment kontrol edilir.

## 11. Production GPU hot path

Hedef ayrım:

- Python control plane: FastAPI, business workflow, PostgreSQL, MinIO, Qdrant, orchestration.
- Native C++/CUDA/TensorRT data plane: decode, preprocess, detect, post-process/NMS, align, embed, L2 normalize.

Hedef hot path:

encoded image → NVIDIA GPU decode → GPU tensor → TensorRT detector → GPU decode/NMS/landmarks → GPU quality gate → CUDA five-point alignment → TensorRT ArcFace → GPU L2 normalization → compact embedding/metadata CPU boundary

Production hot path'te yasak:

- `deepface`
- `FaceAnalysis`
- Paddle runtime
- DALI
- `cv2.VideoCapture`
- PIL/OpenCV full-frame decode/resize fallback
- Sessiz `CPUExecutionProvider` fallback
- TensorRT output'un sırf post-process için NumPy/CPU'ya taşınması
- Frame başına zorunlu CUDA synchronize
- Fake/monkeypatched inference'ın gerçek runtime kanıtı sayılması

Reference/oracle testinde CPU yolu kullanılabilir; production path'ten açıkça ayrılır ve performans kanıtına dahil edilmez.

Python/native transport mekanizması ve bulk batching biçimi native runtime sprintinde benchmark ile kararlaştırılır. Mevcut single-image proto'nun bulk için yeterli olduğu varsayılmaz.

## 12. Üç GPU bulk enrollment

- Her native worker/process tam olarak bir fiziksel GPU'ya sahip olur.
- Host GPU identity/UUID ile container GPU index ayrı kaydedilir.
- Sharding `stable_hash(personId) mod workerCount` kullanır.
- Python built-in `hash()` doğrudan kullanılmaz; processler arasında stabil hash gerekir.
- `photoId` ile sharding yasaktır; aynı kişinin bütün fotoğrafları aynı worker'a gider.
- Compute, persistence ve result handling bounded queue'larla ayrılır.
- PostgreSQL, MinIO ve Qdrant yazıları batched ve bounded olur.
- Persistence yavaşladığında backpressure uygulanır; sınırsız RAM birikimi olmaz.
- Worker retry/restart duplicate person, photo, sample veya vector üretmez.

Benchmark modları birbirinden ayrılır:

- Reference correctness.
- GPU compute only.
- End-to-end enrollment.
- Three-GPU scale.

“Full GPU utilization”, “3× scaling” veya “10M ready” ifadeleri gerçek ölçüm olmadan kullanılamaz.

## 13. Katman ve source kuralları

- `domain` hiçbir outer layer'a bağımlı olmaz.
- `ports` domain contract'larını kullanabilir; application/infrastructure/api import etmez.
- `application` yalnız domain ve ports üzerinden workflow yürütür; concrete infrastructure veya API import etmez.
- `infrastructure` ports'u implement eder; API veya application'a bağımlı olmaz.
- `api` application servislerini çağırır; direct SQL, Qdrant, MinIO veya ML runtime kullanmaz.
- Router/controller içinde business logic veya repository query bulunmaz.
- Infrastructure modelleri domain/business kararlarının sahibi olmaz.
- Gereksiz DDD, generic base repository ve premature abstraction oluşturma.

Mevcut dependency boundary testlerini yeni katman/kod geldikçe genişlet; testleri yalnız boş skeleton üzerinde PASS bırakma.

## 14. Test ve acceptance disiplini

Production davranışı için normal sıra:

1. Failing test veya reproducer.
2. Minimum implementation.
3. Targeted unit test.
4. İlgili integration/contract testi.
5. Gerçek dependency/runtime smoke.
6. Lint/type/build.
7. Git diff ve scope incelemesi.

Mock test şunların kanıtı değildir:

- Gerçek PostgreSQL migration/repository.
- Gerçek MinIO veya Qdrant entegrasyonu.
- Gerçek GPU/TensorRT inference.
- ML accuracy, alignment veya throughput.
- Docker runtime.

Build success runtime success değildir. Engine deserialize inference success değildir. Provider list GPU hot-path kanıtı değildir. Output dosyası üretmek correctness kanıtı değildir.

Her completion claim'i çalıştırılmış komut, gerçek output ve mümkünse persisted artifact ile desteklenir. Çalışmayan veya çalıştırılmayan test açıkça `NOT_RUN`, `BLOCKED` veya `SKIPPED` yazılır.

## 15. MCP accountability

Bağlı MCP'ler:

- `codebase-memory-mcp`
- `context7`
- `deepwiki`
- `exa`
- `playwright`
- `postman`
- `21st`

Temel ilke: Her bağlı MCP'yi her görevde göstermelik kullanma. Her görevde bütün MCP'ler final accountability listesinde yer alır; yalnız relevant olanlar gerçekten çağrılır. Kullanılmayanlar doğru gerekçeyle `skipped` yazılır. MCP çağrılmadıysa `used` denilemez.

### codebase-memory-mcp

Zorunlu kullanım:

- Yeni sprint veya multi-file implementation başlangıcı.
- Repository architecture/package keşfi.
- Existing implementation, test ve dependency path discovery.
- Context compaction sonrası context recovery.
- Büyük refactor öncesi caller/callee ve etki alanı keşfi.

Kurallar:

- Önce codebase-memory ile keşfet, sonra yalnız gereken dosyaları filesystem üzerinden doğrula.
- Knowledge graph sonucunu gerçek source yerine kesin kanıt sayma.
- Aktif repo index'i stale ise yeniden doğrula; eski repository graph'ını aktif source-of-truth sanma.

### context7

Zorunlu kullanım:

- Bir library/framework API'si, version davranışı veya config seçimi implementasyonu etkiliyorsa.
- FastAPI, SQLAlchemy, Alembic, PostgreSQL driver, MinIO SDK, Qdrant client, React/Vite, CMake, Protobuf, CUDA/TensorRT gibi version-sensitive davranışlarda.

Kurallar:

- Öncelik official/current documentation'dır.
- Context7 yeterliyse aynı konuyu gereksiz web aramasıyla uzatma.
- Context7 sonucu kullanılan exact library version ile uyuşmuyorsa bunu limitation olarak yaz.

### deepwiki

Zorunlu kullanım:

- `opensourcereferences/references.md` içindeki GitHub projesinden pattern veya kod adapte edilecekse.
- Upstream repository architecture, call path veya implementation detayı anlaşılacaksa.
- InsightFace/RetinaFace/ArcFace, NVIDIA sample veya diğer açık kaynak davranışı karşılaştırılacaksa.

Kurallar:

- DeepWiki özetini tek başına kopyalama izni sayma; upstream source dosyasını doğrula.
- Source URL, commit/tag ve license kaydet.

### exa

Kullanım:

- Context7 veya DeepWiki eksik/kararsız kaldığında.
- Current, niche veya hızla değişebilen teknik bilgi gerektiğinde.
- Official vendor docs, primary research paper veya upstream release/provenance aramak için.

Kurallar:

- Teknik kararları blog/SEO içeriğine dayandırma; primary/official source tercih et.
- Model license, CUDA/TensorRT compatibility ve current version iddialarında source kaydet.

### postman

Zorunlu kullanım yalnızca:

- API endpoint implementation/acceptance sprintinde.
- Frozen API contract'ın gerçek çalışan servisle doğrulanmasında.

Auth nedeniyle çalışmıyorsa exact error raporlanır; curl/TestClient fallback çalıştırılır ve Postman PASS iddiası yapılmaz. DB-only, native-only veya dokümantasyon sprintinde `skipped_not_relevant` olur.

### playwright

Zorunlu kullanım yalnızca:

- Gerçek React UI mevcut olduğunda UI smoke/E2E acceptance için.
- Page load, critical user flow, loading/error/empty state ve fatal console error kontrolünde.

UI yokken veya backend-only sprintte çağrılmaz. Mock-only Playwright sonucu gerçek backend E2E kanıtı sayılmaz.

### 21st

Durum:

- `CONNECTED_BUT_FORBIDDEN`
- Kullanıcı bu MCP'yi buggy ve güvenilmez olarak yasaklamıştır.
- 21st çağrılmaz, önerilmez ve UI code generation için kullanılmaz.
- Final raporda her zaman `21st: FORBIDDEN_NOT_USED` yazılır.

Ruflo da kalıcı olarak yasaktır ve mevcut MCP listesinde olmasa dahi kullanılmaz veya önerilmez.

## 16. Skill accountability

Mevcut skill'ler:

- `using-superpowers`
- `brainstorming`
- `writing-plans`
- `executing-plans`
- `subagent-driven-development`
- `test-driven-development`
- `systematic-debugging`
- `verification-before-completion`
- `codebase-memory`
- `context7-mcp`
- `dispatching-parallel-agents`
- `finishing-a-development-branch`
- `receiving-code-review`
- `requesting-code-review`

### Zorunlu skill seçimi

- `using-superpowers`: Skill invocation ve workflow governance için varsayılan olarak yüklenir/uygulanır.
- `brainstorming`: Yeni architecture, model/runtime tasarımı, product behavior veya yaratıcı çözüm kararı öncesinde zorunludur. Frozen ve approved kararı sebepsiz yeniden açmak için kullanılmaz.
- `writing-plans`: Birden fazla dosya/katman içeren implementation başlamadan önce zorunludur. Plan `CURRENT_SPRINT.md` ile uyumlu olmalı ve mikro-adımlarla işi gereksiz uzatmamalıdır.
- `executing-plans`: Kullanıcı tarafından onaylanmış plan uygulanırken kullanılır. Plan dışına çıkma yetkisi vermez.
- `test-driven-development`: Production behavior ve bug fix için önce failing test/reproducer yazılmasını yönetir; zorunludur.
- `systematic-debugging`: Test/runtime hatasında rastgele config değiştirmek yerine root-cause-first debugging için zorunludur.
- `verification-before-completion`: Her completion claim'inden önce zorunludur.
- `codebase-memory`: `codebase-memory-mcp` kullanılan repo discovery ve compaction recovery görevlerinde zorunludur.
- `context7-mcp`: Context7 kullanılan version-sensitive library/framework görevlerinde zorunludur.
- `receiving-code-review`: Kullanıcı veya reviewer finding verdiğinde finding'i önce doğrulamak ve sonra uygulamak için kullanılır.
- `requesting-code-review`: Büyük sprint, security/data model değişikliği veya release gate sonunda self/code review istemek için kullanılır.
- `finishing-a-development-branch`: Yalnız kullanıcı merge/PR/branch cleanup istediğinde kullanılır. Kendi başına commit, push, merge veya cleanup yetkisi vermez.

### Subagent ve parallel skill sınırı

- `subagent-driven-development` varsayılan olarak kullanılmaz.
- `dispatching-parallel-agents` varsayılan olarak kullanılmaz.
- Bu iki skill yalnız kullanıcı o görev için açıkça subagent/parallel work onayı verirse kullanılabilir.
- Onay verilse bile bağımsız ve çakışmayan read-only inceleme/test işleri için tercih edilir; aynı source dosyalarında paralel edit yapılmaz.
- Subagent sonucu root agent tarafından source ve test üzerinden doğrulanmadan kabul edilmez.

Her sprint finalinde kullanılan skill'ler ve gerçekten nasıl etkiledikleri kısa yazılır. Kullanılmayan skill'leri sırf listeyi doldurmak için çağırma veya `used` gösterme.

## 17. Destructive ve external-state işlemleri

Kullanıcı açıkça onaylamadan:

- `git add`, commit, push veya history rewrite yapma.
- Tracked dosya, artifact, model veya engine silme.
- `docker compose down -v`, volume deletion veya system prune yapma.
- Model weight veya dataset indirme.
- System CUDA, driver veya global package değiştirme.
- Secret/API key üretme veya ekleme.
- Eski repository'yi değiştirme.
- Onaylanmış architecture/requirements hash baseline'ını güncelleme.

Geçici build/cache çıktıları repo ignore sınırında tutulur. Dirty worktree'de kullanıcı değişikliklerini koru.


## 18. Sprint dokümantasyonu

`docs/implementation/CURRENT_SPRINT.md` yalnız aktif işin objective, exact deliverables, acceptance commands, non-goals ve blocker’larını içerir.

Dosya değiştiren **her kullanıcı promptu tamamlandığında** `docs/implementation/IMPLEMENTATION_DETAILS.md` güncellenir. Yeni bir rapor dosyası oluşturulmaz.

Her kayıt şunları içermelidir:

- Promptun amacı ve sonucu: PASS / PARTIAL / BLOCKED.
- Yapılanların açık teknik özeti.
- Oluşturulan, değiştirilen ve silinen dosyaların listesi.
- Önemli class, function, route, model, migration ve testlerin açıklaması.
- Gerçek çalışma/data flow’u.
- Çalışan ve henüz implement edilmemiş davranışlar.
- Çalıştırılan validation/test komutları ve gerçek sonuçları.
- Testlerin neyi ispatladığı ve neyi ispatlamadığı.
- Bilinen hata, risk ve sınırlamalar.
- MCP ve skill accountability.

Bu promptta oluşturulan veya değiştirilen her source, test, migration, config, contract ve script dosyasının **final tam içeriği**, dosya yolu başlık olarak yazılarak Markdown code block içinde `IMPLEMENTATION_DETAILS.md` dosyasına eklenir.

Yalnız bu promptta değişen dosyaların source kodu eklenir; değişmeyen dosyalar tekrar kopyalanmaz. Binary, model, dataset, secret, generated output ve lockfile içerikleri kopyalanmaz. Silinen dosyalar yalnız path ve silinme nedeni ile belirtilir.

Source code `...`, “omitted”, pseudo-code veya özet kullanılarak kısaltılamaz. Dosya çok büyükse değişen class/function bloklarının tam final içeriği ile ilgili diff eklenir ve eksik bırakılan kısım açıkça belirtilir.

Hiçbir dosya değişmediyse `IMPLEMENTATION_DETAILS.md` güncellenmez.

Bu dokümantasyon aynı promptun son adımıdır; ayrı bir report-only sprint veya üçüncü rapor dosyası oluşturulmaz.

## 19. Completion formatı

Sprint sonunda önce outcome'u yaz:

- `PASS`: bütün zorunlu acceptance kanıtları geçti.
- `PARTIAL`: değer üretildi fakat zorunlu gate veya reproducibility eksiği var.
- `BLOCKED`: güvenli biçimde ilerlemek için kullanıcı kararı/yetkisi gerekiyor.
- `NOT_TESTED`: implementasyon var fakat gerçek runtime kanıtı yok.

Final cevap kısa ve denetlenebilir olmalıdır:

1. Outcome ve çalışan sonuç.
2. Gerçek validation komutları ve sonuçları.
3. Değişen dosya grupları.
4. Bilinen sınırlamalar.
5. Bütün bağlı MCP'ler için used/skipped/forbidden accountability.
6. Kullanılan skill'ler ve etkileri.
7. Tek önerilen sonraki sprint.

Kanıt olmadan `production-ready`, `GPU-only`, `fully optimized`, `10M-ready`, `accuracy verified` veya `release candidate` deme.

Her final raporda şu MCP satırları açıkça bulunur:

- `codebase-memory-mcp:`
- `context7:`
- `deepwiki:`
- `exa:`
- `postman:`
- `playwright:`
- `21st: FORBIDDEN_NOT_USED`

## 20. Foundation sonrası tempo kuralı

Foundation tamamlandıktan sonra aynı foundation'ı tekrar tekrar yeniden tasarlama. Yeni bir bulgu ürün correctness, security, data loss veya reproducibility açısından blocker değilse ayrı correction sprint açma; ilgili implementation sprintinin içine al.

Sonraki sprintler meaningful vertical progress üretmelidir. Önerilen sıra:

1. PostgreSQL + Alembic + national-ID security + gerçek repository integration testleri.
2. MinIO + Qdrant adapters + cross-store lifecycle/reconciliation.
3. FastAPI application services ve frozen `/api/v1` contract.
4. Model/alignment reference gate.
5. Native single-GPU TensorRT pipeline.
6. Three-GPU bulk enrollment ve benchmark.
7. Internal React UI.
8. Docker Compose ve Phase 1 end-to-end acceptance.

Kullanıcı onayı olmadan Phase 2'ye geçme.
