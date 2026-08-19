# 08 — NaC API Catalog (harvested from the MCP schemas, 2026-07-06)

*Everything the "RapidAPI Hub – Network as Code" MCP exposes, organized for concept/gate decisions. Request shapes come straight from the tool schemas (authoritative). Response shapes are per CAMARA specs — the MCP hides response bodies, so **every response shape below carries an implicit "confirm on first live call"** (the spike script records them into `spike-results.json`).*

> **Wakalah tiering (Jul 14, doc 09 D23).** For the build, the identity APIs split into a **core spine** always run, and an **escalation toolkit** the agent's risk-tiered verification plan pulls only when warranted (doc 04 §3):
> - **Core spine (4):** Number Verification · KYC Match · SIM Swap · Device Swap.
> - **Escalation toolkit (6):** Call Forwarding Signal · Number Recycling · Tenure · Device Reachability · Roaming Status · Location Verification.
> - **Roadmap:** KYC Fill-in · Age Verification.
> All 18 operations are proven live on the sandbox (spike Jul 14) — tiering is a *demo-focus and cost* decision (per-risk-tier signal-TTL caching), not a capability limit.

## 0. How the platform hangs together

- **Two auth patterns.** Network-intelligence APIs (reachability, roaming, connectivity, location, congestion, QoD, geofencing, slices) authenticate app-side (RapidAPI key → app token) — callable server-to-server with just a device identifier. **Identity APIs carry an `authorization`/`code` parameter** (Number Verification, KYC Match, KYC Fill-in, Age Verification, Tenure, Number Recycling) — CAMARA's consent model: a **three-legged token from the operator's auth flow** is expected. SIM Swap, Device Swap, and Call Forwarding Signal take a bare `phoneNumber` (no auth param in schema) — likely app-token callable. **The single most important spike question: what does NaC's sandbox accept for the three-legged family?**
- **Paths:** identity/anti-fraud APIs live under `/passthrough/camara/v1/...` (NaC proxying CAMARA verbatim); network APIs live under native NaC paths (`/device-status/...`, `/location-retrieval/...`, `/qod/...`, `/slice/...`).
- **Versioned duplicates** in the MCP (`...-V080`, `-QoD-V1`, `-NV-V2`, `-DS-V0`): older and newer CAMARA versions coexist. Prefer the newest that works; record which one the sandbox honors.
- **MCP quirks (confirmed Jul 6):** fires real authenticated calls but **drops response bodies** (only 4xx errors render); `createSession` (QoD) schema is malformed. Use REST/SDK from the backend; MCP for smoke tests only.
- **Eventing:** four push channels exist — geofencing v0.3 (CloudEvents to a `sink` URL), device-status v0 (`webhook.notificationUrl`, event types below), reachability/roaming v0.8.0 subscriptions, congestion-insights subscriptions. All need a public HTTPS endpoint (cloudflared tunnel in dev).

## 0.5 Simulator roster & error model (portal API overview + live probe, Jul 7)

**Device IDs** — phone (`+99999991000` … `+99999990504`) or NAI (`8D8AC610-566D-4EF0-9C22-186B2A5ED793-<suffix>@testcsp.net`); IPv4/IPv6 also accepted. Personas are **fixed per number**:

| Number | Behavior |
|---|---|
| +99999991000 | "Compromised": swapped ✓ / device-swapped ✓ / forwarding ✓ / recycled ✓ / roaming ✓ / verify FALSE |
| +99999991001 | "Clean": all negative, CONNECTED_DATA, verify TRUE |
| +99999990400 / 0404 / 0422 | Every API returns 400 / 404 / 422 |
| +99999990500 / 0502 / 0503 / 0504 | Every API returns 500 / 502 / 503 / 504 |

Error body shape (canonical): `{"status": 4xx, "code": "INVALID_ARGUMENT|UNAUTHENTICATED|PERMISSION_DENIED|IDENTIFIER_NOT_FOUND", "message": "..."}`. Location-verify maps error-persona numbers to 500. All simulators "live" near Budapest (47.49, 19.08).

### 1a. Number Verification — the 3-legged recipe (verified prerequisites, Jul 7)

1. `GET {BASE}/oauth2/v1/auth/clientcredentials` (RapidAPI headers) → `{client_id, client_secret}` ✓ works
2. `GET {BASE}/.well-known/openid-configuration` → `authorization_endpoint` + `token_endpoint` (= `https://auth.eu.nac.nokia.io/oauth2/v1/...`) ✓ works
3. Browser/device GET: `{authorization_endpoint}?scope=dpv%3AFraudPreventionAndDetection%20number-verification%3Averify&response_type=code&client_id=...&redirect_uri={our backend callback}&login_hint={phone}&state=...` → redirects land `?code=...` on our callback
4. `POST {token_endpoint}` with `client_id, client_secret, grant_type=authorization_code, code` → `{access_token}` (single-use per verification)
5. `POST .../number-verification/v0/verify` with `Authorization: Bearer {token}` + `{"phoneNumber": "+..."}` → `{"devicePhoneNumberVerified": bool}`; or `GET .../device-phone-number` → the number itself

**✅ Whole recipe executed successfully on the sandbox (Jul 14, `backend/spike/nv_flow_probe.ps1`):** auto-approved redirect chain (no browser/login needed on simulators), arbitrary redirect_uri accepted, verify returned `devicePhoneNumberVerified: true`. Tokens are single-use — mint per verification.

QoD extras from the overview: `GET /qod/v0/sessions?device=...` lists sessions; `POST /qod/v0/sessions/{id}/extend` with `{"requestedAdditionalDuration": s}`; sessions expire on their own.

## 1. Identity & anti-fraud family (the underexploited goldmine)

| API | Endpoint (POST unless noted) | Request essentials | Expected response (CAMARA) | The agent decision it powers |
|---|---|---|---|---|
| SIM Swap — check | `/passthrough/camara/v1/sim-swap/sim-swap/v0/check` | `phoneNumber`, `maxAge` (h, ≤2400) | `{"swapped": bool}` | "Was this identity hijacked recently?" — block/step-up |
| SIM Swap — date | `.../sim-swap/v0/retrieve-date` | `phoneNumber` | `{"latestSimChange": datetime}` | Risk-weight by recency, not just yes/no |
| Device Swap — check | `/passthrough/camara/v1/device-swap/device-swap/v1/check` | `phoneNumber`, `maxAge` | `{"swapped": bool}` | Same SIM, new handset → re-verify |
| Device Swap — date | `.../device-swap/v1/retrieve-date` | `phoneNumber` | `{"latestDeviceChange": datetime}` | — |
| Number Verification — verify | `/passthrough/camara/v1/number-verification/number-verification/v0/verify` | `phoneNumber` **or** `hashedPhoneNumber` + **`code`/`authorization`** (3-legged) | `{"devicePhoneNumberVerified": bool}` | Cryptographic SIM↔user binding at enrollment |
| Number Verification — share | `GET .../number-verification/v0/device-phone-number` | **`code`/`authorization`** | `{"devicePhoneNumber": "+.."}` | Silent number discovery post-consent |
| **KYC Match** v0.3 | `/passthrough/camara/v1/kyc-match/kyc-match/v0.3/match` | `phoneNumber` + any of: `name`, `givenName`, `familyName`, `idDocument`, `birthdate`, `address` parts, `email`, `gender` (+auth) | per-attribute `true / false / not_available` (some operators require `idDocument` first) | "Does the claimed identity match the SIM's registered owner?" — onboarding & mandate proofing |
| **KYC Fill-in** v0.4 | `/passthrough/camara/v1/kyc-fill-in/kyc-fill-in/v0.4/fill-in` | `phoneNumber` (+auth) | operator-held registration data (name, address, birthdate…) | One-tap onboarding — operator autofills the form |
| **Age Verification** v0.1 | `/passthrough/camara/v1/kyc-age-verification/.../v0.1/verify` | `ageThreshold` (req.), optional identity hints (+auth) | `{"ageCheck": true/false/not_available, "verifiedStatus", "identityMatchScore", "contentLock"?, "parentalControl"?}` | Age-gating; vulnerable-user modes; note the bonus `parentalControl` signal |
| **Tenure** v0.1 | `/passthrough/camara/v1/kyc-tenure/kyc-tenure/v0.1/check-tenure` | `tenureDate` (req.), `phoneNumber` (+auth) | `{"tenureDateCheck": bool, "contractType"?: PAYG/PAYM/Business}` | Account longevity as a trust prior — 10-year subscriber ≠ week-old burner |
| **Number Recycling** v0.2 | `/passthrough/camara/v1/number-recycling/number-recycling/v0.2/check` | `specifiedDate` (req.), `phoneNumber` (+auth) | `{"phoneNumberRecycled": bool}` | "Is this still the same human?" — kills the reassigned-number account-takeover class |
| **Call Forwarding Signal** v0.3 | `/passthrough/camara/v1/call-forwarding-signal/.../unconditional-call-forwardings` (also a general variant) | `phoneNumber` | `{"active": bool}` (general: list of active forwarding types) | OTP/voice-interception detector — classic vishing/scam precondition |

**Strategic note:** rows 7–12 were *not in the hackathon brief's API list*. Almost no other team will find, let alone orchestrate, KYC Match + Tenure + Number Recycling + Call Forwarding. Together with SIM/Device Swap + NV they form a **complete operator-grade identity bureau** — nine identity signals, one platform.

## 2. Device status & network intelligence

| API | Endpoint | Request | Expected response | Agent decision |
|---|---|---|---|---|
| Reachability | `/device-status/device-reachability-status/v1/retrieve` | `device{phoneNumber\|NAI\|ip}` | `{"reachabilityStatus": CONNECTED_DATA/CONNECTED_SMS/NOT_CONNECTED (v1) or {"reachable": bool} (v0)}` + `lastStatusTime` | Welfare-check ladder; liveness context |
| Roaming | `/device-status/device-roaming-status/v1/retrieve` | `device` | `{"roaming": bool, "countryCode", "countryName"}` | Travel-mode trust; geo-consistency |
| Connectivity | `/device-status/v0/connectivity` | `device` | `{"connectivityStatus": CONNECTED_DATA/CONNECTED_SMS/NOT_CONNECTED}` | Distinguishes data-dark vs fully dark |
| Device-status **events** | `/device-status/v0/subscriptions` | `subscriptionDetail{device, type}` + `webhook{notificationUrl}` | subscription id; events: `roaming-status/-on/-off/-change-country`, `connectivity-data/-sms/-disconnected` | Push, not poll: "device went dark," "device landed abroad" |
| Reachability/Roaming subs v0.8.0 | `...-DS-RES-V080 / DS-ROS-V080` create/retrieve/delete | CAMARA-style subscription | CloudEvents | Newer-spec variant of the above |
| Congestion Insights — query | `/congestion-insights/v0/query` | `device`, optional `start`/`end` (none → predict next 15 min) | time-sliced `{"congestionLevel": none/low/medium/high, "confidence"}` | Pre-position comms; site network health |
| Congestion Insights — subscribe | `createSubscription-ConI-V1` family | device + webhook | push on threshold | — |

## 3. Location family

| API | Endpoint | Request | Expected response | Agent decision |
|---|---|---|---|---|
| Location Retrieval | `/location-retrieval/v0/retrieve` | `device`, `maxAge≥60s` | `{"area": {CIRCLE, center, radius}, "lastLocationTime"}` | Rescue targeting; last-known position, no app needed |
| Location Verification | `/location-verification/v1/verify` | `device`, `area` (CIRCLE center+radius), `maxAge` | `{"verificationResult": TRUE/FALSE/UNKNOWN/PARTIAL, "matchRate"?, "lastLocationTime"}` | Presence proof for permits / geo-consistency for transactions |
| Geofencing subscriptions v0.3 | `/geofencing-subscriptions/v0.3/subscriptions` (+ retrieve/list/delete) | `protocol:"HTTP"`, `sink` URL, `types:[area-entered/area-left]`, `config{subscriptionDetail{device, area}, initialEvent, subscriptionMaxEvents, subscriptionExpireTime}` | 201 + subscription; CloudEvents POSTed to sink | Zone entry/exit as agent triggers; **`initialEvent:true` fires instantly if already inside — deterministic demo moment** |

## 4. Programmable connectivity

| API | Endpoint | Request | Expected response | Agent decision |
|---|---|---|---|---|
| QoD — create session | `/qod/v0/sessions` (use REST; MCP schema broken; also `-QoD-V1` variant) | `qosProfile` (e.g. QOS_E), `device`, `applicationServer{ipv4}`, `duration` | `{"sessionId", "qosStatus": REQUESTED→AVAILABLE, "expiresAt"...}` | Provision guaranteed bandwidth when the agent declares an incident |
| QoD — get/extend/delete | `/qod/v0/sessions/{id}` | sessionId | session object | Lifecycle control |
| Slices | `/slice/v1/slices` create/get/all/activate/deactivate/delete | `networkIdentifier{mcc,mnc}`, `sliceInfo{serviceType}`, `notificationUrl`, optional QoS/throughput/`maxDevices`/`areaOfService` | slice object with state machine (PENDING→AVAILABLE→OPERATING) | Standing guaranteed lanes (vs QoD's per-session) |
| Device attach | `/device-attach/v0/attachments` (+ status, detach) | `device`, `sliceId` | attachment record | Put a responder's device onto the emergency slice |
| Subscriber mgmt | `/device-attach/v0/attachments/subscribers/{create\|remove}` | `device{phoneNumber/imsi/...}`, `sliceId` | — | Slice-scoped test-subscriber management (sandbox utility) |

## 5. What this catalog changes strategically

1. **Wakalah's ceiling just rose.** The §1 goldmine (KYC Match, Fill-in, Age, Tenure, Recycling, Call-Forwarding) upgrades it from "SIM-swap with a token" to a genuine **identity bureau for the agent economy** — 9–11 load-bearing APIs across every trust dimension: *binding* (NV), *hijack* (SIM/device swap, call-forwarding), *identity* (KYC match), *continuity* (recycling, tenure), *context* (reachability, roaming, location). No other team will surface half of these.
2. **MIZAN gains too, more modestly:** device-status **push events** (`connectivity-disconnected`) replace polling in the rescue ladder; KYC Match strengthens check-in identity; congestion query is cheap. Its core (geofencing sink + WBGT policy) is unchanged.
3. **The decisive spike question is now singular:** does the NaC sandbox let us drive the **three-legged consent flow** (the `code`/`authorization` family)? It gates Wakalah's core chain and both concepts' KYC/NV usage. Everything else has confirmed shapes and fallbacks.
4. **Webhooks confirmed everywhere** → the cloudflared tunnel is week-1 infrastructure, not an afterthought.
