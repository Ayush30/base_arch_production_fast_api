class KafkaTopics:
    """Placeholder — add this service's own topics here after cloning the template.

    The one topic every service is expected to publish to is the shared audit
    topic, consumed by audit-service. See app/core/audit_client.py.
    """

    class Audit:
        USER_ACTIVITY = "audit.user.activity"
