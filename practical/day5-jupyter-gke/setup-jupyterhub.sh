#!/bin/bash

# JupyterHub on GKE Setup Script
# This script helps deploy JupyterHub with proper configuration

set -e

echo "🚀 Setting up JupyterHub on GKE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check prerequisites
echo "1. Checking prerequisites..."

# Check gcloud authentication
if ! gcloud config get-value project &>/dev/null; then
    echo "❌ Error: Not authenticated with GCP. Run: gcloud auth login"
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project)
echo "✅ GCP Project: $PROJECT_ID"

# Check kubectl connection
if ! kubectl cluster-info &>/dev/null; then
    echo "❌ Error: kubectl not connected to cluster"
    exit 1
fi
echo "✅ kubectl connected to cluster"

# Check Helm
if ! command -v helm &> /dev/null; then
    echo "❌ Error: Helm not installed. Install with: brew install helm"
    exit 1
fi
echo "✅ Helm installed"

# Check JupyterHub Helm repo
if ! helm repo list | grep -q jupyterhub; then
    echo "📦 Adding JupyterHub Helm repository..."
    helm repo add jupyterhub https://hub.jupyter.org/helm-chart/
    helm repo update
fi
echo "✅ JupyterHub Helm repo ready"

echo ""
echo "2. Building custom Jupyter images..."

# Build data science image
echo "🏗️  Building data science image..."
docker buildx build --platform linux/amd64 \
  -f Dockerfile.datascience \
  -t gcr.io/$PROJECT_ID/jupyter-datascience:v1 \
  --push .

echo "✅ Data science image built and pushed"

echo ""
echo "3. Configuring JupyterHub..."

# Update values files with project ID
sed -i.bak "s/YOUR_PROJECT/$PROJECT_ID/g" jupyterhub-values.yaml
sed -i.bak "s/YOUR_PROJECT/$PROJECT_ID/g" singleuser-profileList.yaml

echo "✅ Configuration files updated"

echo ""
echo "4. Creating namespace..."
kubectl create namespace jupyterhub --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "🎯 Ready to deploy! Run the following commands:"
echo ""
echo "# Deploy JupyterHub"
echo "helm upgrade --install jupyterhub jupyterhub/jupyterhub \\"
echo "  --namespace jupyterhub \\"
echo "  --values jupyterhub-values.yaml \\"
echo "  --values singleuser-profileList.yaml \\"
echo "  --wait \\"
echo "  --timeout 600s"
echo ""
echo "# Get external IP (wait 2-5 minutes)"
echo "kubectl get service proxy-public -n jupyterhub -w"
echo ""
echo "# Access JupyterHub"
echo "EXTERNAL_IP=\$(kubectl get service proxy-public -n jupyterhub -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"
echo "echo \"JupyterHub URL: http://\$EXTERNAL_IP\""
echo "open http://\$EXTERNAL_IP"
echo ""
echo "⚠️  IMPORTANT: Before deploying, update the OAuth settings in jupyterhub-values.yaml:"
echo "   - Replace 'your-google-oauth-client-id' with actual OAuth client ID"
echo "   - Replace 'your-google-oauth-client-secret' with actual OAuth client secret"
echo "   - Replace 'your-domain' with your actual domain"
echo ""
echo "🔗 OAuth Setup: https://console.cloud.google.com/apis/credentials"
