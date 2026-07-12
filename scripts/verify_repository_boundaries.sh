#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root relative to this script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

FORBIDDEN_PATTERNS=(
    "deepface"
    "FaceAnalysis"
    "paddle"
    "nvidia\.dali"
    "DALI"
    "cv2\.VideoCapture"
    "CPUExecutionProvider"
)

VIDEO_PHASE2_PATTERNS=(
    "VideoCapture"
    "DeepStream"
    "NvDCF"
    "ByteTrack"
    "rtsp://"
    "ffmpeg_nvdec_cpu_frames"
)

BINARY_EXTENSIONS=(
    "\.onnx"
    "\.trt"
    "\.engine"
    "\.pth"
    "\.pt"
    "\.ckpt"
    "\.safetensors"
    "\.h5"
    "\.pb"
)

SECRET_PATTERNS=(
    "\.env$"
    "\.key$"
    "\.pem$"
    "\.p12$"
    "\.pfx$"
)

failures=()

announce() {
    echo "==> $1"
}

# -----------------------------------------------------------------------------
# 1. Frozen architecture and requirement docs exist and are unchanged.
# -----------------------------------------------------------------------------
announce "Checking frozen architecture/requirement files"
for doc in \
    "architecture/01-phase1-high-level-architecture.md" \
    "architecture/02-phase1-component-diagram.md" \
    "architecture/03-phase1-postgresql-erd.md" \
    "architecture/04-phase1-minio-object-layout.md" \
    "architecture/05-phase1-qdrant-vector-design.md" \
    "architecture/06-phase1-api-contract.md" \
    "requirements/phase1requirements.md" \
    "requirements/ProjectRequirements.md" \
    "requirements/phase2requirements.md" \
    "opensourcereferences/references.md" \
    "whatwentwrong.md"
do
    if [[ ! -f "${doc}" ]]; then
        failures+=("missing frozen file: ${doc}")
    fi
done

# Only complain if tracked files were modified; newly added files are fine at this stage.
if git diff --quiet HEAD -- architecture/ requirements/ whatwentwrong.md opensourcereferences/references.md 2>/dev/null; then
    : # no tracked modifications
else
    while IFS= read -r changed; do
        failures+=("frozen tracked file modified: ${changed}")
    done < <(git diff --name-only HEAD -- architecture/ requirements/ whatwentwrong.md opensourcereferences/references.md 2>/dev/null || true)
fi

# -----------------------------------------------------------------------------
# 1b. Frozen file SHA-256 integrity check.
# -----------------------------------------------------------------------------
announce "Checking frozen file SHA-256 hashes"
if [[ -f "architecture/FROZEN_SHA256SUMS" ]]; then
    if command -v sha256sum >/dev/null 2>&1; then
        hash_failures=""
        if ! hash_failures=$(sha256sum --check architecture/FROZEN_SHA256SUMS 2>&1 | grep -E ': FAILED' || true); then
            : # grep returns non-zero when no matches; that's the success state
        fi
        if [[ -n "${hash_failures}" ]]; then
            while IFS= read -r line; do
                failures+=("hash mismatch: ${line}")
            done <<< "${hash_failures}"
        fi
    else
        failures+=("sha256sum not available; cannot verify frozen hashes")
    fi
else
    failures+=("missing architecture/FROZEN_SHA256SUMS")
fi

# -----------------------------------------------------------------------------
# 2. Forbidden runtime dependencies not in production source.
# -----------------------------------------------------------------------------
announce "Scanning production source for forbidden dependencies"

scan_source() {
    local label="$1"
    shift
    local paths=("$@")

    for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
        # Capture matches; grep returns 1 when no matches, which is the desired success state.
        scan_matches=""
        if scan_matches=$(grep -R --include='*.py' --include='*.cpp' --include='*.cc' --include='*.c' --include='*.h' --include='*.hpp' -n "${pattern}" "${paths[@]}" 2>/dev/null || true); then
            if [[ -n "${scan_matches}" ]]; then
                failures+=("${label}: forbidden match for '${pattern}':
${scan_matches}")
            fi
        fi
    done
}

if [[ -d backend/src ]]; then
    scan_source "backend/src" backend/src
fi
if [[ -d native/include ]]; then
    scan_source "native/include" native/include
fi
if [[ -d native/src ]]; then
    scan_source "native/src" native/src
fi

# -----------------------------------------------------------------------------
# 3. Phase 2 video runtime not leaking into production source.
# -----------------------------------------------------------------------------
announce "Checking for Phase 2/video runtime leakage"

for pattern in "${VIDEO_PHASE2_PATTERNS[@]}"; do
    phase_matches=""
    if phase_matches=$(grep -R --include='*.py' --include='*.cpp' --include='*.cc' --include='*.c' --include='*.h' --include='*.hpp' -n "${pattern}" backend/src native/src native/include 2>/dev/null || true); then
        if [[ -n "${phase_matches}" ]]; then
            failures+=("Phase 2 leakage for '${pattern}':
${phase_matches}")
        fi
    fi
done

# -----------------------------------------------------------------------------
# 4. No old-repo absolute paths in production source.
# -----------------------------------------------------------------------------
announce "Checking for old-repo absolute runtime paths"

for dir in backend/src native/src native/include; do
    if [[ ! -d "${dir}" ]]; then
        continue
    fi
    path_matches=""
    if path_matches=$(grep -R --include='*.py' --include='*.cpp' --include='*.cc' --include='*.c' --include='*.h' --include='*.hpp' -n '/home/user/' "${dir}" 2>/dev/null || true); then
        if [[ -n "${path_matches}" ]]; then
            failures+=("absolute old-repo path found in ${dir}:
${path_matches}")
        fi
    fi
done

# -----------------------------------------------------------------------------
# 5. No model/dataset/engine binaries tracked by git.
# -----------------------------------------------------------------------------
announce "Checking for tracked model/dataset/engine artefacts"

ext_pattern=$(IFS='|'; echo "${BINARY_EXTENSIONS[*]}")
tracked_binaries=""
if tracked_binaries=$(git ls-files 2>/dev/null | grep -E "(${ext_pattern})$" || true); then
    if [[ -n "${tracked_binaries}" ]]; then
        failures+=("tracked binary artefacts found:
${tracked_binaries}")
    fi
fi

# No dataset folders committed.
if git ls-files 2>/dev/null | grep -qE '^datasets/'; then
    failures+=("datasets/ folder must not be tracked")
fi
if git ls-files 2>/dev/null | grep -qE '^models/'; then
    failures+=("models/ folder must not be tracked")
fi

# -----------------------------------------------------------------------------
# 6. No secret files tracked.
# -----------------------------------------------------------------------------
announce "Checking for tracked secret files"

secret_pattern=$(IFS='|'; echo "${SECRET_PATTERNS[*]}")
tracked_secrets=""
if tracked_secrets=$(git ls-files 2>/dev/null | grep -E "(${secret_pattern})" || true); then
    if [[ -n "${tracked_secrets}" ]]; then
        failures+=("tracked secret-looking files:
${tracked_secrets}")
    fi
fi

# -----------------------------------------------------------------------------
# 7. Report.
# -----------------------------------------------------------------------------
if [[ ${#failures[@]} -gt 0 ]]; then
    echo "FAIL: repository boundary violations found:" >&2
    for failure in "${failures[@]}"; do
        echo "  - ${failure}" >&2
    done
    exit 1
fi

echo "PASS: repository boundaries verified."
