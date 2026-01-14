---
description: Development environment configuration and standards for DevBridge
---

## Development Server Ports

- **Frontend (Next.js)**: `http://localhost:3001`
- **Backend (FastAPI)**: `http://localhost:8001`

## Starting Development

// turbo-all

1. Start all services with:
```bash
make dev
```

This runs both frontend and backend in parallel.

## API Endpoints

- API Base URL: `http://localhost:8001/api/v1`
- Frontend URL: `http://localhost:3001`

## Testing in Browser

When navigating to pages for testing:
- Dashboard: http://localhost:3001/dashboard
- Metrics: http://localhost:3001/metrics
- Reports: http://localhost:3001/reports
- Teams: http://localhost:3001/teams
- Chat: http://localhost:3001/chat
- Settings: http://localhost:3001/settings

## Dev Login (Testing)

To login quickly without email verification:

```bash
curl -X POST http://localhost:8001/api/v1/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}' \
  -c cookies.txt
```

Or use the browser to POST to: `http://localhost:8001/api/v1/auth/dev-login`

Default test email: `test@example.com`

**⚠️ This only works when ENVIRONMENT=development**
