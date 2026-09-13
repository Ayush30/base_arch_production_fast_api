# API reference

All routes below are generated from the running FastAPI OpenAPI definition. Base URL: `/api/v1`. Interactive field-level schemas and examples are at `/docs`; machine-readable schema is at `/openapi.json`.

Lists support bounded limit/offset where shown by Swagger. Authentication is a Bearer access token; role and ownership rules are documented by domain and enforced in dependencies/services. Local payment endpoints simulate money movement.

| Method | Path | Access | Summary |
|---|---|---|---|
| GET | `/api/v1/health` | Public | Liveness probe |
| GET | `/api/v1/ready` | Public | Readiness probe |
| POST | `/api/v1/auth/register` | Public, rate limited | Register |
| POST | `/api/v1/auth/login` | Public, rate limited | Login |
| POST | `/api/v1/auth/refresh` | Public, rate limited | Refresh |
| POST | `/api/v1/auth/logout` | Authenticated | Logout |
| GET | `/api/v1/auth/me` | Authenticated | Me |
| POST | `/api/v1/auth/verification/request` | Public, rate limited | Request Verification |
| POST | `/api/v1/auth/verification/confirm` | Public, rate limited | Verify |
| POST | `/api/v1/auth/password/request` | Public, rate limited | Request Reset |
| POST | `/api/v1/auth/password/reset` | Public, rate limited | Reset |
| GET | `/api/v1/products` | Public | Products |
| GET | `/api/v1/products/{product_id}` | Public | Product |
| GET | `/api/v1/seller/products` | Approved seller, own records | Seller Products |
| POST | `/api/v1/seller/products` | Approved seller, own records | Create |
| PATCH | `/api/v1/seller/products/{product_id}` | Approved seller, own records | Update |
| POST | `/api/v1/products/{product_id}/reviews` | Buyer, own records | Review |
| GET | `/api/v1/products/{product_id}/reviews` | Public | Reviews |
| GET | `/api/v1/addresses` | Buyer, own records | Addresses |
| POST | `/api/v1/addresses` | Buyer, own records | Address |
| DELETE | `/api/v1/addresses/{address_id}` | Buyer, own records | Delete Address |
| GET | `/api/v1/cart` | Buyer, own records | Cart |
| PUT | `/api/v1/cart/items/{product_id}` | Buyer, own records | Put |
| DELETE | `/api/v1/cart/items/{product_id}` | Buyer, own records | Remove |
| POST | `/api/v1/checkout` | Buyer, verified email | Checkout |
| GET | `/api/v1/orders` | Buyer, own records | Orders |
| GET | `/api/v1/orders/{order_id}` | Buyer, own records | Order |
| POST | `/api/v1/orders/{order_id}/cancel` | Buyer, own records | Cancel |
| POST | `/api/v1/orders/{order_id}/returns` | Buyer, own records | Request Return |
| GET | `/api/v1/returns` | Buyer, own records | Returns |
| GET | `/api/v1/seller/fulfillments` | Approved seller, own records | Fulfillments |
| POST | `/api/v1/seller/fulfillments/{item_id}` | Approved seller, own records | Fulfill |
| POST | `/api/v1/orders/{order_id}/payments/local` | Buyer, own records | Pay Local |
| GET | `/api/v1/finance/payments` | Finance or admin | Payments |
| GET | `/api/v1/finance/returns` | Finance or admin | Returns |
| POST | `/api/v1/finance/orders/{order_id}/refund/local` | Finance or admin | Refund |
| POST | `/api/v1/finance/orders/{order_id}/settlements` | Finance or admin | Settle |
| GET | `/api/v1/finance/ledger` | Finance or admin | Ledger |
| GET | `/api/v1/finance/settlements` | Finance or admin | Settlements |
| GET | `/api/v1/seller/settlements` | Approved seller, own records | Seller Settlements |
| GET | `/api/v1/analytics/sales` | Analytics or admin | Sales |
| GET | `/api/v1/analytics/products` | Analytics or admin | Products |
| GET | `/api/v1/analytics/sellers` | Analytics or admin | Sellers |
| GET | `/api/v1/seller/sales` | Approved seller, own records | Seller Sales |
| GET | `/api/v1/admin/users` | Admin | Users |
| PATCH | `/api/v1/admin/users/{user_id}` | Admin | Update User |
| POST | `/api/v1/admin/products/{product_id}/moderation` | Admin | Moderate |
| GET | `/api/v1/admin/audit` | Admin | Audit |

See [role matrix and examples](../README.md), [mobile integration](REACT_NATIVE.md) and [request walkthrough](REQUEST_WALKTHROUGH.md).
