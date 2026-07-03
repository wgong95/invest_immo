#!/bin/bash
# Démarrage de l'application Invest Immo Paris

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== Invest Immo Paris ==="
echo ""

# Backend
echo "[1/2] Démarrage du backend Python (port 8000)..."
cd "$ROOT/backend"

if ! command -v uvicorn &>/dev/null; then
  echo "  Installation des dépendances Python..."
  pip install -r requirements.txt -q
fi

uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

sleep 2

# Frontend
echo "[2/2] Démarrage du frontend Next.js (port 3000)..."
cd "$ROOT/frontend"

if [ ! -d "node_modules" ]; then
  echo "  Installation des dépendances Node.js..."
  npm install
fi

npm run dev &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"

echo ""
echo "==================================="
echo "  Backend  → http://localhost:8000"
echo "  Frontend → http://localhost:3000"
echo "==================================="
echo ""
echo "Ctrl+C pour arrêter les deux serveurs"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
