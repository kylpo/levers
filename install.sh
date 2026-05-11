#!/usr/bin/env bash
# install.sh — symlink the `levers` script onto PATH.
#
# Usage:
#   bash install.sh                    # symlinks into ~/.local/bin
#   bash install.sh --prefix <dir>     # symlinks into <dir>
#   bash install.sh --force            # overwrite an existing non-symlink at the target
#
# The symlink points at this clone's `levers` script. Updates land via
# `git pull` automatically — no re-install needed.

set -euo pipefail

PREFIX="${HOME}/.local/bin"
FORCE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prefix)
            if [[ -z "${2:-}" ]]; then
                echo "error: --prefix requires a directory" >&2
                exit 2
            fi
            PREFIX="$2"; shift 2 ;;
        --force)
            FORCE=1; shift ;;
        -h|--help)
            sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "error: unknown argument: $1" >&2
            exit 2 ;;
    esac
done

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE="${REPO_DIR}/levers"
TARGET="${PREFIX}/levers"

if [[ ! -x "$SOURCE" ]]; then
    echo "error: $SOURCE is not executable (or missing)" >&2
    exit 2
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "warning: \`uv\` not found on PATH — the levers script will fail at runtime." >&2
    echo "         install uv: https://docs.astral.sh/uv/" >&2
fi

mkdir -p "$PREFIX"

if [[ -e "$TARGET" || -L "$TARGET" ]]; then
    if [[ -L "$TARGET" ]]; then
        existing="$(readlink "$TARGET")"
        if [[ "$existing" == "$SOURCE" ]]; then
            echo "ok: $TARGET already points at $SOURCE"
            exit 0
        fi
        echo "info: replacing existing symlink $TARGET (was → $existing)"
        rm "$TARGET"
    elif [[ "$FORCE" -eq 1 ]]; then
        echo "info: --force given; removing existing file at $TARGET"
        rm "$TARGET"
    else
        echo "error: $TARGET exists and is not a symlink. Pass --force to overwrite." >&2
        exit 1
    fi
fi

ln -s "$SOURCE" "$TARGET"
echo "ok: linked $TARGET → $SOURCE"

case ":$PATH:" in
    *":$PREFIX:"*) ;;
    *)
        echo "note: $PREFIX is not on your PATH. Add to your shell rc:"
        echo "      export PATH=\"$PREFIX:\$PATH\""
        ;;
esac
