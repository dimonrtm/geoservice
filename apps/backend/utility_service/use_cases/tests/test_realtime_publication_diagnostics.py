import asyncio
import json
from uuid import uuid4

from utility_service.use_cases.services.feature_service import FeatureService
from utility_service.use_cases.tests.test_feature_realtime_publisher import build_feature


def diagnostic_records(caplog):
    return [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "utility_service.realtime"
    ]


def test_feature_service_logs_unknown_recipients_on_publisher_failure(caplog):
    class FailingPublisher:
        async def publish_feature_updated(self, *args, **kwargs):
            raise RuntimeError("SECRET")

    feature, layer = build_feature(), uuid4()
    service = FeatureService(None, None, FailingPublisher())
    asyncio.run(service.publish_feature_updated(layer, feature))
    records = diagnostic_records(caplog)
    assert len(records) == 1
    assert records[0]["event"] == "realtime_publication_failed"
    assert records[0]["featureId"] == str(feature.id)
    assert records[0]["featureVersion"] == 2
    assert records[0]["eventType"] == "feature_updated"
    assert records[0]["eventId"].startswith("evt_")
    assert "connectionId" not in records[0]
