import json
from pathlib import Path

from f1_api.config import Settings
from f1_api.main import create_app

OUT = Path(__file__).resolve().parents[3] / "packages" / "contract" / "openapi.json"

if __name__ == "__main__":
    spec = create_app(Settings()).openapi()
    OUT.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT}")
