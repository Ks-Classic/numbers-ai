"""
Simple Python proxy that reuses the FastAPI app via TestClient.
The script reads a JSON payload from STDIN:
{
  "endpoint": "/api/predict/axis" or "/api/predict/combination",
  "body": {...}
}
and writes the FastAPI response JSON to STDOUT.
"""

import json
import sys
from typing import Dict, Any

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def main():
    try:
        payload: Dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"invalid json: {exc}"}))
        sys.exit(1)

    endpoint = payload.get("endpoint")
    body = payload.get("body", {})

    if endpoint not in {"/api/predict/axis", "/api/predict/combination"}:
        print(json.dumps({"error": "unsupported endpoint", "endpoint": endpoint}))
        sys.exit(1)

    response = client.post(endpoint, json=body, timeout=60)
    result = {
        "status_code": response.status_code,
        "body": response.json(),
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()

