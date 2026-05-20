# Mobile Spec — AutoFounder AI

> Expo conventions, project structure, EAS build profiles, push notification
> architecture, and mobile-specific API patterns.

---

## Overview

The AutoFounder AI mobile app (`mobile-app/`) gives founders on-the-go access to:
- Submitting new ideas (text, voice, file attachment)
- Monitoring active run progress via live WebSocket stream
- Approving or rejecting HITL gates without opening a browser
- Receiving push notifications when their attention is required

The app targets **iOS 16+** and **Android 13+**. It is built with **Expo SDK** (managed workflow)
and **Expo Router** for file-based navigation.

---

## Project Structure

```
mobile-app/
├── app/                         Expo Router file-based routes
│   ├── (auth)/
│   │   ├── login.tsx
│   │   └── callback.tsx
│   ├── (tabs)/
│   │   ├── _layout.tsx          Bottom tab navigator
│   │   ├── index.tsx            Run dashboard (home)
│   │   ├── workspaces.tsx       Workspace list
│   │   └── settings.tsx
│   ├── runs/
│   │   ├── [run_id]/
│   │   │   ├── index.tsx        Run detail + live log stream
│   │   │   ├── gates/
│   │   │   │   └── [gate_id].tsx  Gate approval screen
│   │   │   └── artifacts.tsx    Artifact viewer
│   │   └── new.tsx              Idea intake form
│   └── _layout.tsx              Root layout (auth guard)
├── components/                  Shared UI components
│   ├── runs/
│   ├── gates/
│   └── ui/                      Design system primitives
├── hooks/                       Custom React hooks
│   ├── useRun.ts
│   ├── useGate.ts
│   └── useWebSocket.ts
├── lib/
│   ├── api-client.ts            Typed REST client (shared logic)
│   ├── auth.ts                  Auth0 native + SecureStore wrapper
│   ├── notifications.ts         FCM token registration
│   └── ws-client.ts             WebSocket hook
├── constants/
│   └── colors.ts                Design tokens (light + dark)
├── app.config.ts                Expo config (dynamic, reads env vars)
├── eas.json                     EAS Build + Submit profiles
└── package.json
```

---

## Navigation

Expo Router with typed routes (`expo-router/typed-routes` enabled in `app.config.ts`).

```
/                       → (tabs)/index.tsx  (run dashboard)
/runs/new               → Idea intake
/runs/[run_id]          → Run detail
/runs/[run_id]/gates/[gate_id]  → Gate approval
/runs/[run_id]/artifacts        → Artifact viewer
/(auth)/login           → Auth0 login
```

Auth guard wraps `(tabs)` layout: if no valid session, redirect to `/(auth)/login`.

---

## Authentication

Auth0 native PKCE flow via `react-native-auth0`.

```typescript
// lib/auth.ts
import Auth0 from 'react-native-auth0';
import * as SecureStore from 'expo-secure-store';

const auth0 = new Auth0({
  domain: process.env.EXPO_PUBLIC_AUTH0_DOMAIN!,
  clientId: process.env.EXPO_PUBLIC_AUTH0_CLIENT_ID!,
});

export async function login() {
  const credentials = await auth0.webAuth.authorize({
    scope: 'openid profile email offline_access',
    audience: process.env.EXPO_PUBLIC_API_AUDIENCE!,
  });
  await SecureStore.setItemAsync('access_token', credentials.accessToken);
  await SecureStore.setItemAsync('refresh_token', credentials.refreshToken!);
}
```

**Rules**:
- Tokens stored in `expo-secure-store` — hardware-backed on supported devices.
- Never `AsyncStorage` for auth tokens.
- Access token refreshed silently before expiry. On refresh failure → force re-login.
- `EXPO_PUBLIC_*` prefix for env vars that are safe to embed in the JS bundle.
  Secret values go through the backend, never the mobile app directly.

---

## API Client

The mobile app uses the same typed API client pattern as `frontend-web`, adapted for React Native's
`fetch` (no `axios` — avoids a native dependency).

```typescript
// lib/api-client.ts
const BASE_URL = process.env.EXPO_PUBLIC_API_URL; // e.g. https://api.autofounder.ai/v1

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await SecureStore.getItemAsync('access_token');
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const err = await res.json();
    throw new ApiError(err.error.code, err.error.message, res.status);
  }
  return res.json().then(r => r.data);
}
```

---

## Push Notifications

### Flow

```
1. App registers with FCM via Expo Notifications
2. Expo token + raw FCM token sent to backend: POST /v1/devices/token
3. Backend stores token in platform.user_devices
4. Agent pipeline event → backend publishes to Pub/Sub topic `push-notifications`
5. Cloud Function reads topic → calls FCM HTTP v1 API
6. Device receives notification → tap deep-links to relevant screen
```

### Setup in app

```typescript
// lib/notifications.ts
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';

export async function registerForPushNotifications() {
  if (!Device.isDevice) return; // simulator — skip

  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== 'granted') return;

  const token = (await Notifications.getExpoPushTokenAsync({
    projectId: process.env.EXPO_PUBLIC_EAS_PROJECT_ID!,
  })).data;

  await apiFetch('/v1/devices/token', {
    method: 'POST',
    body: JSON.stringify({ token, platform: Platform.OS }),
  });
}
```

### Notification → deep link mapping

| Notification type | Deep link |
|-------------------|-----------|
| `gate.required` | `/runs/{run_id}/gates/{gate_id}` |
| `run.completed` | `/runs/{run_id}` |
| `run.failed` | `/runs/{run_id}` |
| `build.artifact_ready` | `/runs/{run_id}/artifacts` |

Handled via `Notifications.addNotificationResponseReceivedListener` in root layout.

---

## Offline & Reconnection

Gate decisions made while offline are queued in `AsyncStorage` (gate decisions are not sensitive —
only the decision intent, not the token). On reconnect, the queue is flushed in order.

WebSocket reconnects with `Last-Event-ID` header to replay missed events. The `useWebSocket` hook
handles this automatically with exponential backoff (1 s, 2 s, 4 s, max 30 s).

---

## EAS Build Profiles

```jsonc
// eas.json
{
  "cli": { "version": ">= 10.0.0" },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "env": { "EXPO_PUBLIC_API_URL": "http://localhost:8000/v1" }
    },
    "preview": {
      "distribution": "internal",
      "channel": "preview",
      "env": { "EXPO_PUBLIC_API_URL": "https://api-staging.autofounder.ai/v1" }
    },
    "production": {
      "autoIncrement": true,
      "channel": "production",
      "env": { "EXPO_PUBLIC_API_URL": "https://api.autofounder.ai/v1" }
    }
  },
  "submit": {
    "production": {
      "ios": { "appleId": "team@autofounder.ai", "ascAppId": "...", "appleTeamId": "..." },
      "android": { "serviceAccountKeyPath": "./google-services-key.json", "track": "production" }
    }
  }
}
```

### Build triggers

| Profile | When | Who |
|---------|------|-----|
| `development` | On demand | Engineer needs a dev client |
| `preview` | Push to `testing` branch | CI automatically |
| `production` | Push to `main` after approval | CI + manual gate |

### OTA updates

JS-only changes (no new native modules) use Expo Updates for instant delivery without App Store review.

```bash
# Push OTA update to production channel
eas update --branch production --message "Fix gate approval loading state"
```

OTA is **disabled** when native code changes (new Expo modules, `app.config.ts` changes to
plugins). Those require a full EAS build + store submission.

---

## Conventions

### File & component naming

- Expo Router files: `kebab-case.tsx` (required by Expo Router)
- Components: `PascalCase.tsx`, named exports
- Hooks: `camelCase.ts`, prefixed with `use`

### State management

- Server data: React Query (`@tanstack/react-query`)
- Real-time data: WebSocket hook merged into React Query cache (same pattern as web)
- UI state: `useState` / `useReducer` — no global store for UI state
- Auth state: `SecureStore` + React context (single `AuthProvider`)

### Styling

- `StyleSheet.create` for all styles — no inline style objects (except truly dynamic values)
- Design tokens in `constants/colors.ts` — no hardcoded hex values in components
- Dark mode via `useColorScheme()` — all tokens have light/dark variants

### Testing

- Unit tests: Jest + `@testing-library/react-native`
- E2E tests: Maestro (runs on EAS Device Farm before `production` build promotion)
- Run locally: `pnpm --filter mobile-app test`
