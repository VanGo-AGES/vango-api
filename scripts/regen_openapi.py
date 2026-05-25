"""Regenerate the versioned FastAPI OpenAPI schema."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = REPO_ROOT / "openapi.json"

sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    os.environ["DATABASE_URL"] = "sqlite:///./openapi-generation.db"

    from src.main import fastapi_app

    schema = fastapi_app.openapi()
    with OPENAPI_PATH.open("w", encoding="utf-8") as openapi_file:
        json.dump(schema, openapi_file, ensure_ascii=False, indent=2, sort_keys=True)
        openapi_file.write("\n")


if __name__ == "__main__":
    main()
