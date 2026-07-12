# Face Inference Contract v1

**Status:** Design-only contract. No generated code, no server/client implementation, no protobuf package installation in Foundation Sprint 0–1.

## Scope

Defines the typed boundary between:

- **Python control plane** (`mergenvision.application` services)
- **Native GPU worker** (`native/apps/runtime_server` future process)

## Design principles

- This is an **internal** contract.
- The native worker is **not** a public microservice.
- Communication is over a **Unix domain socket** within the same host/container.
- The contract carries **no PII**, no national ID, no database entity, no storage credential.
- The contract carries **no known/unknown business decision**; that belongs to the application service.

## Landmark order

All five-point landmark results use this canonical order:

1. left eye
2. right eye
3. nose
4. left mouth corner
5. right mouth corner

This matches the InsightFace/ArcFace `arcface_dst` convention.

## RPCs

- `Health` — liveness/readiness of the native runtime.
- `InferImage` — run the full decode → detect → align → embed pipeline on one verified image.

## Messages

See `face_inference.proto` for:

- `OperationMode` (ENROLLMENT / IDENTIFICATION / BENCHMARK)
- `InferImageRequest` / `InferImageResponse`
- `FaceResult` (bbox, landmarks, detection confidence, quality score, 512-D embedding)
- `HealthRequest` / `HealthResponse`

## Future validation

When the protobuf toolchain is available and approved for installation, validate with:

```bash
protoc --proto_path=contracts/face_inference/v1 face_inference.proto --python_out=/tmp/proto_check
```

For this sprint the schema is reviewed manually; the command above is not executed.
