# Calling this API from React Native

[API reference](API_REFERENCE.md) · [Walkthrough](REQUEST_WALKTHROUGH.md)

The API is ordinary HTTP JSON. On an iOS simulator use `http://localhost:8000`; Android emulator commonly reaches the host through `http://10.0.2.2:8000`. A physical device needs the computer's LAN IP. The default Compose binding is loopback-only: for a trusted local network, deliberately change the app port mapping to `8000:8000`, add the LAN IP to `ALLOWED_HOSTS`, and allow that port through your local firewall. Use HTTPS for deployed services. Your native platform's development HTTP restrictions may require a development-only network policy; don't disable transport security for release builds.

Native HTTP clients are not subject to browser CORS. A web/Expo-web build is: configure its exact origin in `CORS_ORIGINS`, such as `["http://localhost:8081"]`. This does not replace authentication.

```ts
const API = 'http://localhost:8000/api/v1';

async function login(email: string, password: string) {
  const response = await fetch(`${API}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw new Error('Login failed');
  return response.json(); // access_token, refresh_token, expires_in, token_type
}

async function request(path: string, accessToken: string, init: RequestInit = {}) {
  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
      ...init.headers,
    },
  });
  if (response.status === 204) return null;
  const body = await response.json();
  if (!response.ok) {
    // Also handle 422's body.detail validation entries in your form UI.
    throw new Error(body.error?.message ?? `Request failed (${response.status})`);
  }
  return body;
}

// Generate a UUID once using your app's UUID library and persist it with this attempt.
async function checkout(accessToken: string, attemptKey: string, addressId: string) {
  return request('/checkout', accessToken, {
    method: 'POST',
    headers: { 'Idempotency-Key': attemptKey },
    body: JSON.stringify({
      address_id: addressId,
      currency: 'USD',
      expected_total_minor: 1999, // derive from the displayed cart's current prices
    }),
  });
}
```

Store refresh tokens in an OS-backed secure store (Keychain/Keystore through your chosen native library). Avoid putting credentials in source, logs, Redux persistence or unencrypted AsyncStorage. Keep access tokens in memory where practical. The examples omit storage because it depends on your React Native stack.

On an expired access token, use `POST /auth/refresh` with `{"token":"<refresh token>"}`. It rotates both credentials and revokes the old session. Use one shared refresh promise/mutex so simultaneous API failures do not race to consume the same refresh token. Atomically save the replacement tokens. If refresh fails, require login; do not loop indefinitely. Logging out revokes the current session immediately.

Persist the checkout body and idempotency key until the outcome is known. A network timeout does not mean the server rolled back. Retry the same attempt with the same key/body, or inspect order history. A different cart purchase requires a new key. A retry returns the original order even if the cart subsequently changed. On `409` review the updated cart and start a new confirmed attempt when appropriate.

Format amounts using the currency exponent and locale for display only. Never send a floating-point dollar amount. Fetch product prices to display totals, but the backend is authoritative and checks your expected total at checkout. Lists use bounded `limit` and `offset`; append pages until fewer than `limit` items are returned. For very large datasets, migrate to cursor pagination with a stable sort key.
