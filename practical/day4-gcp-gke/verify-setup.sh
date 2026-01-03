#!/bin/bash

# GKE Setup Verification Script
# Run this to check if your GCP/GKE setup is working

set -e

echo "🔍 Verifying GCP/GKE Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check gcloud installation
echo "1. Checking gcloud CLI..."
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud not found. Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
echo "✅ gcloud installed: $(gcloud version --short | head -1)"

# Check authentication
echo ""
echo "2. Checking GCP authentication..."
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ "$PROJECT_ID" = "(unset)" ] || [ -z "$PROJECT_ID" ]; then
    echo "❌ No project set. Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi
echo "✅ Project set: $PROJECT_ID"

# Check billing
echo ""
echo "3. Checking billing status..."
if gcloud billing accounts list --format="value(name)" | grep -q .; then
    echo "✅ Billing account found"
else
    echo "⚠️  No billing account found. Make sure billing is enabled!"
fi

# Check required APIs
echo ""
echo "4. Checking required APIs..."
APIS=("container.googleapis.com" "containerregistry.googleapis.com")
for api in "${APIS[@]}"; do
    if gcloud services list --enabled --filter="config.name:$api" --format="value(config.name)" | grep -q "$api"; then
        echo "✅ $api enabled"
    else
        echo "❌ $api not enabled. Enable with: gcloud services enable $api"
    fi
done

# Check Docker authentication
echo ""
echo "5. Checking Docker GCR authentication..."
if docker info 2>/dev/null | grep -q "gcr.io"; then
    echo "✅ Docker authenticated with GCR"
else
    echo "⚠️  Docker may not be authenticated. Run: gcloud auth configure-docker"
fi

# Check cluster existence
echo ""
echo "6. Checking GKE cluster..."
if gcloud container clusters list --region=us-central1 --filter="name:ml-interview-cluster" --format="value(name)" | grep -q "ml-interview-cluster"; then
    echo "✅ GKE cluster 'ml-interview-cluster' exists"

    # Check kubectl connection
    echo ""
    echo "7. Checking kubectl connection..."
    if kubectl cluster-info &>/dev/null; then
        echo "✅ kubectl connected to cluster"

        # Check node count
        NODE_COUNT=$(kubectl get nodes --no-headers | wc -l)
        echo "✅ Nodes available: $NODE_COUNT"

        # Check if ML platform is deployed
        if kubectl get namespace ml-platform &>/dev/null; then
            echo ""
            echo "8. Checking ML platform deployment..."
            PODS_READY=$(kubectl get pods -n ml-platform --no-headers 2>/dev/null | grep -c "Running" || echo "0")
            echo "✅ ML platform namespace exists"
            echo "✅ Running pods: $PODS_READY"

            # Check service
            if kubectl get service ml-api-service -n ml-platform &>/dev/null; then
                EXTERNAL_IP=$(kubectl get service ml-api-service -n ml-platform -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
                if [ "$EXTERNAL_IP" != "pending" ] && [ -n "$EXTERNAL_IP" ]; then
                    echo "✅ API service available at: http://$EXTERNAL_IP:8000"
                else
                    echo "⏳ API service LoadBalancer pending external IP"
                fi
            fi
        else
            echo "ℹ️  ML platform not deployed yet. Run: ./build-and-deploy.sh"
        fi
    else
        echo "❌ kubectl not connected. Run: gcloud container clusters get-credentials ml-interview-cluster --region=us-central1"
    fi
else
    echo "ℹ️  GKE cluster not created yet. Run: gcloud container clusters create-auto ml-interview-cluster --region=us-central1"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Setup verification complete!"
echo ""
echo "💡 Quick start commands:"
echo "• Create cluster: gcloud container clusters create-auto ml-interview-cluster --region=us-central1"
echo "• Connect kubectl: gcloud container clusters get-credentials ml-interview-cluster --region=us-central1"
echo "• Deploy platform: ./build-and-deploy.sh"
echo "• Check costs: ./check-costs.sh"
