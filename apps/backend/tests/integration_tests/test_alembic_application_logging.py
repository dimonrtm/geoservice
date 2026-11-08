import asyncio
import json
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config

from tests.integration_tests.network_db_support import require_db_tests
from utility_service.use_cases.services.feature_service import FeatureService
from utility_service.use_cases.tests.test_feature_realtime_publisher import build_feature


def test_alembic_command_preserves_application_diagnostics(capfd):
    require_db_tests()

    class FailingPublisher:
        async def publish_feature_updated(self, *args, **kwargs):
            raise RuntimeError("SECRET publication failure")

    # The application logger already exists when migrations run in the same process.
    service = FeatureService(None, None, FailingPublisher())
    feature = build_feature()
    command.current(Config(str(Path(__file__).resolve().parents[2] / "alembic.ini")))
    capfd.readouterr()

    asyncio.run(service.publish_feature_updated(uuid4(), feature))

    output = capfd.readouterr().err
    records = [
        json.loads(line[line.index("{") :])
        for line in output.splitlines()
        if '"event": "realtime_publication_failed"' in line
    ]
    assert len(records) == 1
    assert records[0]["featureId"] == str(feature.id)
    assert records[0]["reason"] == "publication_failed"
    assert "SECRET" not in output
