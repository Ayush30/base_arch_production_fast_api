# Money, currencies, and payment boundaries

[Root](../README.md) · [Order code](../src/app/domains/orders/service.py) · [Finance code](../src/app/domains/finance/service.py)

`price_minor`, `total_minor`, and ledger amounts are integers. Each monetary record also stores a currency code. [core/money.py](../src/app/core/money.py) defines exponents: USD/EUR/GBP use 2 decimals, JPY uses 0, KWD uses 3. Never use binary floating point for financial calculations. SQL BigInteger stores order totals; React Native may parse supported totals as JavaScript numbers because this API's bounds are below `Number.MAX_SAFE_INTEGER`.

Enable another listed currency with `SUPPORTED_CURRENCIES=["USD","EUR"]` in `.env`. Sellers can then create separately priced products in that currency. The cart may hold products from different currencies, but checkout rejects a mixed-currency cart; the client should guide the buyer to one currency. Existing product currency is immutable. Reports group by currency. This is multi-currency pricing, not foreign exchange: no rate conversion is performed.

To add FX later, introduce dated rate records with source, timestamp and decimal rate; explicit display versus settlement currency; a quote expiry; agreed rounding rules; and an order snapshot of the accepted quote. Keep the original amount and currency for refunds. To add a new currency code, define its minor-unit exponent, validation, formatting, provider support and boundary tests together.

Commission uses basis points (`1000` = 10%) and half-up rounding on each line subtotal. The rate is applied at checkout and the resulting commission is snapshotted on each order item. A later configuration change never changes a past order's seller share. Settlement sums line gross and line commission for that seller.

## Implemented local behavior

The local payment endpoint locks the order, verifies ownership/status/expiry, inserts one Payment and one capture ledger entry, then marks the order paid in the same database transaction. The order ID is the stable payment identity. A repeated call returns the original payment. A full refund similarly locks the order, requires an open return and goods receipt, adds one refund ledger entry and restores stock once.

The ledger is a transaction journal of captures and refunds. It is **not double-entry accounting**, a bank reconciliation system, or a tax ledger. Settlement records document a transfer made elsewhere; they do not send a payout. The 14-day settlement hold prevents the implemented return flow from refunding funds already recorded as settled. Late chargebacks, partial refunds, payout failures and negative seller balances require a richer financial design.

## Connecting a real provider

There is no live payment adapter included. Select a marketplace-capable provider and account model before implementing one. Keep provider calls out of a long-lived inventory transaction: save the pending order/payment operation first, then call the provider with a stable idempotency key. Add a provider event table with a unique provider event ID.

A webhook must verify its signature against the raw request body, validate the expected provider account, amount, currency and order reference, then atomically deduplicate and update payment/order/ledger state. Do not trust a successful mobile screen as proof of payment. Handle retries, late successful payments after reservation expiry, out-of-order events and reconciliation jobs. Extend refunds and seller transfers with explicit pending/succeeded/failed states instead of marking success before provider confirmation. See [Stripe webhook documentation](https://docs.stripe.com/webhooks) for signature and duplicate-event requirements; these are integration references, not a claim that Stripe is integrated.

Tax and shipping are not calculated. Current totals are product subtotals, with no assertion that zero tax or free shipping is appropriate for a real sale. Add explicit quoted tax and shipping line items, jurisdiction/address rules, provider integration and refund allocation before accepting real customers.
