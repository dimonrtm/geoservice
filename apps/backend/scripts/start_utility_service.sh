set -euo pipefail

alembic upgrade head
python -m seeds.runners.seed_demo_users
python -m seeds.runners.seed_utility_dataset
python -m seeds.runners.seed_work_orders
python -m seeds.runners.upgrade_demo_fixture
uvicorn utility_service.web_api.main:app --host 0.0.0.0 --port 8000
