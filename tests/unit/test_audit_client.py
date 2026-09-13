from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID

from app.core.audit_client import emit_audit_event
from app.core.config import settings
from app.kafka.constants import KafkaTopics


class TestEmitAuditEvent:
    async def test_publishes_to_configured_topic(self) -> None:
        with patch("app.core.audit_client.publish", new_callable=AsyncMock) as mock_publish:
            await emit_audit_event(actor_type="admin", action="create", status="success")

        mock_publish.assert_awaited_once()
        topic, event = mock_publish.call_args.args
        assert topic == KafkaTopics.Audit.USER_ACTIVITY
        assert event["service_name"] == settings.app_name
        assert event["action"] == "create"
        assert event["status"] == "success"

    async def test_uses_actor_id_as_partition_key(self) -> None:
        actor_id = UUID("00000000-0000-0000-0000-000000000001")

        with patch("app.core.audit_client.publish", new_callable=AsyncMock) as mock_publish:
            await emit_audit_event(
                actor_type="admin", action="update", status="success", actor_id=actor_id
            )

        assert mock_publish.call_args.kwargs["key"] == str(actor_id)
        _, event = mock_publish.call_args.args
        assert event["actor_id"] == str(actor_id)

    async def test_publish_failure_is_swallowed_and_logged(self) -> None:
        with (
            patch(
                "app.core.audit_client.publish",
                new_callable=AsyncMock,
                side_effect=RuntimeError("boom"),
            ),
            patch("app.core.audit_client.logger") as mock_logger,
        ):
            await emit_audit_event(actor_type="admin", action="create", status="failure")

        mock_logger.warning.assert_called_once()
        assert mock_logger.warning.call_args.args[0] == "audit_event_publish_failed"
