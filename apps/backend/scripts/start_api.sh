set -euo pipefail

uvicorn utility_service.web_api.main:app --host 0.0.0.0 --port 8000
