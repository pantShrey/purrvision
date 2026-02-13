#!/bin/bash
set -e

echo "🚀 Deploying Purrvision to Production..."

# 1. Install Docker & Kind (if missing)
if ! command -v kind &> /dev/null; then
    echo "📥 Installing Kind..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

# 2. Create Cluster
if ! kind get clusters | grep -q "purrvision-cluster"; then
    echo "📦 Creating Cluster..."
    kind create cluster --config kind-config.yaml --name purrvision-cluster
    
    echo "🌐 Installing Ingress..."
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
    kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=90s
fi

# 3. NETWORKING 
# The backend container needs to talk to Kind, but '127.0.0.1' inside the container
# means the container itself, not the host. We patch the kubeconfig to use the Docker IP.
echo "🔧 Patching Kubeconfig..."
KIND_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' purrvision-cluster-control-plane)
sed -i "s/0.0.0.0:[0-9]*/$KIND_IP:6443/g" ~/.kube/config
sed -i "s/127.0.0.1:[0-9]*/$KIND_IP:6443/g" ~/.kube/config

# 4. Launch App
echo "🐳 Launching Containers..."
docker compose -f docker-compose.prod.yaml up -d --build

echo "✅ DEPLOYMENT COMPLETE!"
echo "👉 Access Dashboard at: http://$(curl -s ifconfig.me)"