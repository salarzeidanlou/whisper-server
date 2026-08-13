# Whisper Server

[![CI](https://github.com/salarzeidanlou/whisper-server/actions/workflows/ci.yml/badge.svg)](https://github.com/salarzeidanlou/whisper-server/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

A self-hosted FastAPI relay for end-to-end encrypted messaging, presence, offline delivery, encrypted media, and WebRTC voice calls.

The server is a **relay only** — it never sees plaintext messages or decrypts anything. All content is encrypted on the client using NaCl (Curve25519 + XSalsa20-Poly1305) before it arrives here.

> [!NOTE]
> Despite the name, this project is an encrypted-messaging backend. It is not an OpenAI Whisper speech-to-text or transcription server.

> [!IMPORTANT]
> End-to-end encryption depends on the client implementation and correct key verification. This repository provides the relay backend, not a complete audited cryptographic system. Production deployments must use HTTPS/WSS and properly secured PostgreSQL, Redis, and TURN services.

## Project status

Whisper Server is actively developed and ready for self-hosted evaluation. The application currently reports version `1.2.0` in its OpenAPI metadata, but the project has not undergone an independent security audit. Review the [security model and limitations](#security-model-and-limitations) before exposing a deployment to the internet.

## Features

- **E2EE messaging** — server relays ciphertext, never plaintext
- **Encrypted media** — relay client-encrypted voice notes and images; negotiate large peer-to-peer file transfers
- **WebRTC voice calls** — peer-to-peer audio via coturn TURN relay
- **Real-time presence** — push-based online/offline events (no polling)
- **Offline queue** — messages held up to 7 days for offline users
- **Multi-worker safe** — Redis pub/sub routes signals across all server workers
- **Single-use WS tickets** — no JWT tokens in WebSocket URLs

## Architecture

```
Client A ──► REST (auth, keys, TURN creds) ──► PostgreSQL (users, keys)
    │                                                  │
    └──► WebSocket ◄──── Redis Pub/Sub ────► WebSocket ──► Client B
          │   (chat relay, call signals,                    │
          │    presence events)                             │
          └──────────────── coturn ─────────────────────────┘
                        (STUN / TURN relay for WebRTC)
```

**Stack:**

- **FastAPI** — async REST + WebSocket
- **PostgreSQL** — users and public keys (SQLAlchemy 2.0 async)
- **Redis** — sessions, rate limiting, pub/sub routing, offline queue, presence
- **Uvicorn** — production ASGI server with optional multiple workers
- **coturn** — self-hosted STUN/TURN for WebRTC NAT traversal
- **Alembic** — database migrations

---

## Quick Start (with Docker)

### Prerequisites

- Docker and Docker Compose

### Setup

```bash
git clone https://github.com/salarzeidanlou/whisper-server.git
cd whisper-server

# Copy environment template and fill in your values
cp .env.example .env

# Generate secrets (run each command, copy output to .env)
python3 -c "import secrets; print(secrets.token_hex(32))"  # JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"  # COTURN_SECRET

# Start all services (API, PostgreSQL, Redis, coturn)
docker compose up -d

# Run database migrations
docker compose exec api alembic upgrade head

# Confirm every service is healthy
docker compose ps
```

The API is now available at `http://localhost:8000`. Set `ENVIRONMENT=development` before startup to expose interactive API documentation at `http://localhost:8000/docs`.

> [!NOTE]
> The bundled coturn service uses host networking and is intended for Linux hosts. PostgreSQL and Redis are bound to localhost by default; do not expose them directly to the internet.

---

## Quick Start (without Docker)

Install Python 3.11 or newer and provide reachable PostgreSQL and Redis instances.

```bash
git clone https://github.com/salarzeidanlou/whisper-server.git
cd whisper-server

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start PostgreSQL and Redis separately, then:
cp .env.example .env   # edit with your DB/Redis URLs and secrets

alembic upgrade head

# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Set `ENVIRONMENT=development` in `.env` to enable the interactive API docs at `/docs`.

For container orchestration, run one Uvicorn process per container and scale the container count. The included Docker Compose setup starts one API process.

---

## coturn (STUN/TURN)

WebRTC voice calls need STUN/TURN for NAT traversal when peers are on different networks (e.g. phone on mobile data, PC on LAN).

### Install on Ubuntu

```bash
sudo apt-get install -y coturn
sudo sed -i 's/#TURNSERVER_ENABLED=1/TURNSERVER_ENABLED=1/' /etc/default/coturn
```

### Configure `/etc/turnserver.conf`

```
listening-port=3478
external-ip=<YOUR_PUBLIC_IP>
realm=<YOUR_PUBLIC_IP_OR_DOMAIN>
use-auth-secret
static-auth-secret=<COTURN_SECRET from .env>
min-port=49152
max-port=65535
no-multicast-peers
denied-peer-ip=127.0.0.0-127.255.255.255
log-file=/var/log/turnserver.log
```

### Open firewall ports

```bash
sudo ufw allow 3478/udp
sudo ufw allow 3478/tcp
sudo ufw allow 49152:65535/udp
```

```bash
sudo systemctl enable coturn && sudo systemctl start coturn
```

### Configure `.env`

```
COTURN_EXTERNAL_IP=1.2.3.4
COTURN_REALM=1.2.3.4           # or your domain
COTURN_SECRET=<same secret as turnserver.conf>
```

---

## API Reference

All endpoints are currently unprefixed. Treat the WebSocket message shapes below as the public protocol when building a client.

### Authentication

| Method | Endpoint                 | Auth | Description                                           |
| ------ | ------------------------ | ---- | ----------------------------------------------------- |
| `POST` | `/auth/register`         | No   | Create account (`username`, `password`, `public_key`) |
| `POST` | `/auth/login`            | No   | Get access token                                      |
| `POST` | `/auth/logout`           | Yes  | Invalidate session                                    |
| `POST` | `/auth/ws-ticket`        | Yes  | Single-use WebSocket ticket (30s TTL)                 |
| `POST` | `/auth/turn-credentials` | Yes  | Time-limited TURN credentials (1h TTL)                |

### Users

| Method | Endpoint                       | Auth | Description                     |
| ------ | ------------------------------ | ---- | ------------------------------- |
| `PUT`  | `/users/me/public-key`         | Yes  | Rotate your public key          |
| `GET`  | `/users/{username}/public-key` | Yes  | Fetch a user's public key       |
| `GET`  | `/users/{username}/exists`     | Yes  | Check existence + online status |

### Health

| Method | Endpoint  | Description                                |
| ------ | --------- | ------------------------------------------ |
| `GET`  | `/health` | Liveness — process is running              |
| `GET`  | `/ready`  | Readiness — PostgreSQL and Redis reachable |

### WebSocket

```
WS /ws/chat?ticket=<ticket>
```

Obtain a ticket first via `POST /auth/ws-ticket`.

---

## WebSocket Protocol

### Authentication flow

```
1. POST /auth/login        → { access_token }
2. POST /auth/ws-ticket    → { ticket }
3. WS   /ws/chat?ticket=…
```

On connect the server immediately delivers:

1. Any queued offline messages
2. A `presence_snapshot` of all currently online users

---

### Chat messages

**Send:**

```json
{
  "type": "chat_message",
  "to": "alice",
  "ciphertext": "<base64>",
  "nonce": "<base64>"
}
```

**Receive:**

```json
{
  "type": "chat_message",
  "from": "bob",
  "ciphertext": "<base64>",
  "nonce": "<base64>",
  "timestamp": 1700000000,
  "msg_id": "abc123"
}
```

**Delivery ack (back to sender):**

```json
{ "type": "status", "to": "alice", "delivered": true, "timestamp": 1700000000 }
```

---

### Presence events

**On connect** — server sends current snapshot:

```json
{ "type": "presence_snapshot", "online": ["alice", "bob"] }
```

**When any user comes online/offline:**

```json
{ "type": "user_online",  "username": "alice" }
{ "type": "user_offline", "username": "alice" }
```

No polling needed — all clients receive presence updates in real time.

---

### Encrypted media and file transfer

Voice notes use the same envelope as chat messages with `"type": "voice"`. Images and small encrypted files use `"type": "image"` or `"type": "file"` and support ciphertext up to approximately 15 MiB before base64 overhead.

Large files are transferred peer-to-peer over WebRTC. The server relays only the negotiation messages: `file_rtc_offer`, `file_rtc_answer`, `file_rtc_ice`, and `file_cancel`. Both peers must be online; these signals are not added to the offline queue.

---

### WebRTC call signaling

Call signals are relayed peer-to-peer through the WebSocket. The server routes them via Redis pub/sub across workers but never inspects SDP or ICE candidates.

#### Outgoing call

```json
{ "type": "call_offer",   "call_id": "…", "to": "alice", "sdp": { "type": "offer", "sdp": "…" } }
{ "type": "call_ice_candidate", "call_id": "…", "to": "alice", "candidate": { … } }
```

#### Incoming call responses

```json
{ "type": "call_answer",  "call_id": "…", "to": "bob",   "sdp": { "type": "answer", "sdp": "…" } }
{ "type": "call_decline", "call_id": "…", "to": "bob" }
{ "type": "call_end",     "call_id": "…", "to": "bob" }
```

#### Server → client notifications

| Type               | Meaning                                       |
| ------------------ | --------------------------------------------- |
| `call_offer`       | Incoming call from peer                       |
| `call_answer`      | Peer accepted                                 |
| `call_decline`     | Peer declined                                 |
| `call_end`         | Peer hung up (also synthesized on disconnect) |
| `call_busy`        | Peer already in another call                  |
| `call_unavailable` | Peer is offline                               |

---

## Environment Variables

| Variable            | Required | Default | Description                                       |
| ------------------- | -------- | ------- | ------------------------------------------------- |
| `DATABASE_URL`      | Yes      | —       | `postgresql+asyncpg://user:pass@host/db`          |
| `REDIS_URL`         | Yes      | —       | `redis://:pass@host:6379/0`                       |
| `JWT_SECRET_KEY`    | Yes      | —       | Strong random secret (min 32 bytes hex)           |
| `JWT_ALGORITHM`     | No       | `HS256` | JWT signing algorithm                             |
| `JWT_EXPIRE_DAYS`   | No       | `7`     | Token lifetime in days                            |
| `LOGIN_RATE_LIMIT`  | No       | `5`     | Max attempts per window                           |
| `LOGIN_RATE_WINDOW` | No       | `300`   | Rate limit window (seconds)                       |
| `CORS_ORIGINS`      | No       | `""`    | Comma-separated allowed origins                   |
| `ENVIRONMENT`       | No       | `""`    | `development` enables `/docs`                     |
| `WS_TICKET_TTL`     | No       | `30`    | WebSocket ticket TTL (seconds)                    |
| `TRUSTED_PROXIES`   | No       | `""`    | Comma-separated proxy CIDRs for `X-Forwarded-For` |
| `COTURN_EXTERNAL_IP` | Docker   | —                  | Public IPv4 address advertised by coturn          |
| `COTURN_SECRET`      | No       | `""`               | TURN REST API shared secret                       |
| `COTURN_REALM`       | No       | `turn.example.com` | TURN realm (your domain or IP)                    |

Generate required secrets:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Database Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after changing models
alembic revision --autogenerate -m "describe the change"

# Roll back one step
alembic downgrade -1
```

---

## Security

For vulnerability-reporting instructions and the supported-version policy, see [SECURITY.md](./SECURITY.md).

| Mechanism            | Detail                                                            |
| -------------------- | ----------------------------------------------------------------- |
| **E2EE**             | Server relays ciphertext only; never holds decryption keys        |
| **Passwords**        | bcrypt hashed; never stored or logged in plaintext                |
| **Timing safety**    | Dummy bcrypt check when username not found (prevents enumeration) |
| **Rate limiting**    | Atomic Redis sorted-set sliding window                            |
| **Sessions**         | JWT + Redis double-check; logout invalidates immediately          |
| **WS auth**          | Single-use 30s tickets via `GETDEL` — no JWT in query string      |
| **Payload limits**   | 700KB ciphertext max, 64B nonce max, raw frame size checked first |
| **TURN credentials** | HMAC-SHA1 time-limited (1h), signed server-side                   |
| **Swagger**          | Disabled in production (`ENVIRONMENT != development`)             |
| **Docker**           | Non-root container user                                           |
| **CORS**             | Strict — only origins listed in `CORS_ORIGINS`                    |

### Security model and limitations

End-to-end encryption protects message contents only when the client encrypts, authenticates, and verifies keys correctly. This server still handles metadata needed to operate the relay, including usernames, public keys, IP addresses, online status, sender/recipient relationships, timestamps, payload sizes, and WebRTC signaling. A TURN relay can also observe peers' network addresses and traffic volume, although WebRTC media remains encrypted in transit.

Operators should assume that application, proxy, Redis, PostgreSQL, and coturn logs may contain sensitive metadata. Use TLS, restrict infrastructure access, minimize log retention, rotate secrets, and review the client cryptography before production use.

---

## Project Structure

```
whisper-server/
├── .github/                 # CI and contribution templates
├── alembic/
│   └── versions/            # Migration scripts
├── app/
│   ├── middleware/
│   │   └── auth.py          # JWT validation, WS tickets, rate limiting
│   ├── models/
│   │   └── user.py          # SQLAlchemy User model
│   ├── routers/
│   │   ├── auth.py          # Auth + TURN credential endpoints
│   │   └── users.py         # User lookup endpoints
│   ├── schemas/
│   │   └── auth.py          # Pydantic request/response models
│   ├── security/
│   │   ├── jwt.py           # JWT create/decode
│   │   └── password.py      # bcrypt helpers
│   ├── ws/
│   │   └── chat.py          # WebSocket handler, Redis pub/sub,
│   │                        # presence, offline queue, call signaling
│   ├── config.py            # Settings from .env
│   ├── database.py          # SQLAlchemy async engine
│   ├── main.py              # FastAPI app, CORS, lifespan
│   └── redis.py             # Redis connection pool
├── coturn/
│   └── turnserver.conf      # Standalone coturn config template
├── tests/                    # Unit tests for config, schemas, and passwords
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml            # Test and lint configuration
├── requirements-dev.txt
└── requirements.txt
```

---

## Contributing

Issues and pull requests are welcome. Read [CONTRIBUTING.md](./CONTRIBUTING.md) and the [Code of Conduct](./CODE_OF_CONDUCT.md) before participating.

---

## License

[MIT](./LICENSE)
