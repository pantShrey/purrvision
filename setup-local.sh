#!/bin/bash
set -e
echo "🚀 Setting up Local Dev Environment..."

# 1. Start DBs
docker compose up -d

# 2. Create Cluster
if ! kind get clusters | grep -q "purrvision-cluster"; then
    kind create cluster --config kind-config.yaml --name purrvision-cluster
fi

# 3. Install Ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
echo "⏳ Waiting for Ingress..."
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=90s

# 4. Add Repos
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

echo "✅ Ready! Open two terminals:"
echo "1. Backend: uvicorn app.main:app --reload"
echo "2. Frontend: cd frontend && npm run dev"