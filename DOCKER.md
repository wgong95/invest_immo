# Docker local

Build and start the app locally on macOS:

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

Run in detached mode:

```bash
docker compose up --build -d
```

Stop:

```bash
docker compose down
```

Rebuild after code changes:

```bash
docker compose up --build
```