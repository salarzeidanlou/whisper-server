# Contributing to Whisper Server

Thanks for helping improve Whisper Server. Bug reports, documentation fixes, tests, and focused feature proposals are welcome.

## Before you start

- Search existing issues before opening a new one.
- Keep changes focused; discuss large behavioral or protocol changes in an issue first.
- Do not include credentials, private keys, production data, or vulnerability details in issues or pull requests.
- For security vulnerabilities, follow [SECURITY.md](./SECURITY.md).

## Local setup

```bash
git clone https://github.com/salarzeidanlou/whisper-server.git
cd whisper-server
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

Generate a development-only JWT secret, update `.env`, then start PostgreSQL and Redis or use Docker Compose as described in the [README](./README.md).

## Validate your change

Run the checks that match your change before opening a pull request:

```bash
ruff check .
python -m pytest
python -m compileall -q app alembic
python -m pip check
docker compose --env-file .env.example config --quiet
```

If you change runtime behavior, add or update tests when a test harness is available and explain any manual verification in the pull request.

## Pull requests

- Use a clear title and explain both what changed and why.
- Mention related issues with `Closes #123` when applicable.
- Document new environment variables, API endpoints, WebSocket messages, and migrations.
- Keep the public protocol backward-compatible when practical; call out breaking changes prominently.

By contributing, you agree that your contribution is licensed under the repository's [MIT License](./LICENSE).
