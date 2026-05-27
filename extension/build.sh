#!/usr/bin/env bash
# Heillon Legal — Browser Extension build script (Linux/macOS/Git-Bash).
#
# Packages the extension into a .zip ready for Chrome Web Store submission
# OR for direct distribution to beta testers ("Load unpacked" alternative).
#
# Usage:
#   ./build.sh           → outputs dist/heillon-extension-v<version>.zip
#   ./build.sh --clean   → removes dist/ first

set -euo pipefail

cd "$(dirname "$0")"

ROOT_DIR="$(pwd)"
DIST_DIR="${ROOT_DIR}/dist"
MANIFEST="${ROOT_DIR}/manifest.json"

# Parse version from manifest.json (POSIX awk; no jq dep)
VERSION="$(awk -F'"' '/"version"/{print $4; exit}' "${MANIFEST}")"
if [[ -z "${VERSION}" ]]; then
    echo "ERROR: Could not parse version from manifest.json" >&2
    exit 1
fi

OUTPUT="${DIST_DIR}/heillon-extension-v${VERSION}.zip"

if [[ "${1:-}" == "--clean" ]]; then
    echo "Cleaning ${DIST_DIR}..."
    rm -rf "${DIST_DIR}"
fi

mkdir -p "${DIST_DIR}"

# Generate icons if missing
if [[ ! -f "${ROOT_DIR}/icons/icon-128.png" ]]; then
    echo "Icons missing — generating with PIL..."
    python "${ROOT_DIR}/icons/generate_icons.py"
fi

echo "Building ${OUTPUT} (version ${VERSION})..."

# Use Python's zipfile module (always available, no zip CLI dependency)
ROOT_DIR_ESCAPED="${ROOT_DIR}" OUTPUT_ESCAPED="${OUTPUT}" python - <<'PYZIP'
import os
import zipfile
from pathlib import Path

root = Path(os.environ["ROOT_DIR_ESCAPED"])
output = Path(os.environ["OUTPUT_ESCAPED"])

# Files included in the package (NEVER include dev artefacts)
include_paths = [
    "manifest.json",
    "src",
    "icons/icon-16.png",
    "icons/icon-48.png",
    "icons/icon-128.png",
    "README.md",
    "PRIVACY.md",
]
exclude_patterns = ["__pycache__", ".pyc", "generate_icons.py", ".DS_Store", ".gitignore"]


def included(p: Path) -> bool:
    s = str(p)
    return not any(pat in s for pat in exclude_patterns)


with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for rel in include_paths:
        src = root / rel
        if not src.exists():
            print(f"  WARNING: {rel} missing - skipped")
            continue
        if src.is_file():
            z.write(src, arcname=rel)
            print(f"  + {rel}")
        else:
            for child in src.rglob("*"):
                if child.is_file() and included(child):
                    arc = child.relative_to(root)
                    z.write(child, arcname=str(arc))
                    print(f"  + {arc}")

size = output.stat().st_size
print(f"\n{output.name}: {size:,} bytes ({size/1024:.1f} KB)")
PYZIP

echo ""
echo "Done. Distribute via:"
echo "  - Chrome Web Store:  upload ${OUTPUT}"
echo "  - Beta testers:      send ${OUTPUT} + instructions"
echo "  - Dev mode:          chrome://extensions -> 'Load unpacked' -> select this folder"
