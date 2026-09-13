# Kafka, the outbox, and background workers

[Root](../README.md) · [Workers](../src/app/workers/README.md) · [Events](../src/app/domains/events/README.md)

Kafka transports events to independently running consumers. It is useful for notifications, warehouse integration and analytics pipelines. It does not replace the transactional database. This project works without Kafka running: the API writes durable `outbox_events` rows in the same transaction as each business change.

The outbox worker reads unpublished rows with `FOR UPDATE SKIP LOCKED`, publishes to `marketplace.events`, then marks them published. A failed publish rolls back those marks. If the broker receives an event but the worker crashes before commit, it will send that event again: this is **at-least-once delivery**. Kafka producer idempotence helps broker retry handling but does not eliminate this database/Kafka crash window.

Every event includes `event_id`, `schema_version`, `occurred_at`, `type`, and `resource_id`. Kafka's message key is the aggregate/order ID. Consumers must use a table with a unique event ID and commit their business effect with the deduplication record before acknowledging progress. Multiple outbox workers can publish different batches concurrently; consumers must tolerate business events arriving out of order. This implementation does not promise aggregate-level total ordering across workers.

```bash
docker compose --profile events up -d
# Watch publisher logs:
docker compose logs -f outbox
# Inspect the stream inside the local broker:
docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 --topic marketplace.events --from-beginning
```

The local broker uses one node, plaintext transport, and automatic topic creation. Production requires authenticated/encrypted connections, replication, explicit topic retention/partitions, monitoring and consumer ownership. Add client TLS/SASL settings to `kafka/producer.py` when configuring a secured broker; the included local producer does not yet expose those settings.

Monitor the count and age of unpublished events, publish failure rate, consumer lag, and dead-letter records. The current worker retries indefinitely with a short delay; an unsupported or oversized event needs an operator fix. Add bounded retries, a quarantine/dead-letter workflow and an alert if your event payloads become extensible. Define retention/purge jobs for published events and audit data according to your operational requirements.

The reservation worker is independent: it locks one expired pending order per transaction, restores inventory, cancels the order and writes an event. Run it whenever checkout is available. Stopping it does not allow expired orders to be paid, but stock remains reserved until it resumes.

`core/audit_client.py` is retained from the base template as a best-effort Kafka example. Active marketplace mutations use `domains/events/service.py` because audit/event persistence must participate in the database transaction.
