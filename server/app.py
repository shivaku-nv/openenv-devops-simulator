"""OpenEnv-compatible server entrypoint for root repository."""

import sys
from pathlib import Path


# `uv run server` executes the installed console script, which may import this
# module with only the `server/` package path available. Add the repository root
# so sibling source directories like `api/` remain importable.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.server import app


def main(host: str = "0.0.0.0", port: int = 7860):
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
