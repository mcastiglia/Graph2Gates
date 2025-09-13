#!/usr/bin/env bash
# Build an Apptainer SIF from a .def, then sanity check it
# Usage: scripts/build_sif.sh [--def openroad.def] [--out openroad.sif] [--no-force]
set -euo pipefail

DEF="openroad.def"
OUT="openroad.sif"
FORCE="-F"   # replace output if exists

while [[ $# -gt 0 ]]; do
  case "$1" in
    --def) DEF="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --no-force) FORCE=""; shift ;;
    -h|--help)
      echo "Usage: $0 [--def openroad.def] [--out openroad.sif] [--no-force]"
      exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

[[ -f "$DEF" ]] || { echo "ERROR: def file not found: $DEF" >&2; exit 1; }
command -v apptainer >/dev/null || { echo "ERROR: apptainer not in PATH" >&2; exit 1; }

echo "==> Apptainer version:"
apptainer version

echo "==> Building $OUT from $DEF"

# Fetch base image
apptainer pull  "$OUT" docker://ubuntu:22.04

apptainer build $FORCE "$OUT" "$DEF"

echo "==> Built $OUT ($(du -h "$OUT" | awk '{print $1}'))"
echo "==> SHA256:"
sha256sum "$OUT" || shasum -a 256 "$OUT" || true

echo "==> Quick runtime sanity check (openroad -version)"
set +e
apptainer run "$OUT" -version
RC=$?
set -e
if [[ $RC -ne 0 ]]; then
  echo "!! Sanity check failed (exit $RC). Try inspecting missing libs:"
  apptainer exec "$OUT" bash -lc '
    for f in $(command -v openroad) /opt/openroad-root/usr/lib/x86_64-linux-gnu/*.so* /opt/ortools/lib/*.so*; do
      [ -e "$f" ] || continue
      ldd "$f" 2>/dev/null | awk -v T="$f" "/not found/{print T\": \"$1}"
    done | sort -u || true
  '
  exit $RC
fi

echo "==> Done."
