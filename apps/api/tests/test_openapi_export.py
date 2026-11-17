import json
from pathlib import Path

from f1_api.config import Settings
from f1_api.main import create_app

SPEC = Path(__file__).resolve().parents[3] / "packages" / "contract" / "openapi.json"


def test_committed_openapi_matches_app() -> None:
    app = create_app(Settings())
    assert json.loads(SPEC.read_text()) == app.openapi()
