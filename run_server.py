import uvicorn
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root))
    from api.server import app

    uvicorn.run(app, host="0.0.0.0", port=7860)
