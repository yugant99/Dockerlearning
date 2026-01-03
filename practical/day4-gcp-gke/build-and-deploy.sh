#!/bin/bash

# Build and Deploy ML Platform to GKE
# Usage: ./build-and-deploy.sh

set -e

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
if [ "$PROJECT_ID" = "(unset)" ]; then
    echo "❌ Error: No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "🚀 Building and deploying ML Platform to GKE"
echo "📍 Project: $PROJECT_ID"

# Configure Docker for GCR
echo "🔧 Configuring Docker for GCR..."
gcloud auth configure-docker --quiet

# Build training image
echo "🏗️  Building training image..."
cd ../day6-ml-platform/model
docker build -t gcr.io/$PROJECT_ID/ml-training:v1 .
echo "📤 Pushing training image..."
docker push gcr.io/$PROJECT_ID/ml-training:v1

# Build API image
echo "🏗️  Building API image..."
cd ../api
docker build -t gcr.io/$PROJECT_ID/ml-api:v1 .
echo "📤 Pushing API image..."
docker push gcr.io/$PROJECT_ID/ml-api:v1

# Return to GKE deployment directory
cd ../../day4-gcp-gke/gke-deployment

# Update image references in YAML files (temporary - replace YOUR_PROJECT)
echo "📝 Updating image references..."
sed -i.bak "s/YOUR_PROJECT/$PROJECT_ID/g" training-job.yaml
sed -i.bak "s/YOUR_PROJECT/$PROJECT_ID/g" api-deployment.yaml

# Deploy to GKE
echo "🚀 Deploying to GKE..."

# Create namespace
kubectl apply -f namespace.yaml

# Deploy config and storage
kubectl apply -f configmap.yaml
kubectl apply -f pvc.yaml

echo "⏳ Waiting for PVC to be ready..."
kubectl wait --for=condition=bound pvc/model-pvc -n ml-platform --timeout=300s

# Run training job
echo "🎯 Running training job..."
kubectl apply -f training-job.yaml

echo "⏳ Waiting for training to complete..."
kubectl wait --for=condition=complete job/model-training -n ml-platform --timeout=600s

# Deploy API
echo "🌐 Deploying API..."
kubectl apply -f api-deployment.yaml
kubectl apply -f api-service.yaml
kubectl apply -f api-hpa.yaml

# Wait for rollout
echo "⏳ Waiting for API rollout..."
kubectl rollout status deployment/ml-api -n ml-platform --timeout=300s

# Get service URL
echo "🔗 Getting service URL..."
kubectl get service ml-api-service -n ml-platform -w &
SERVICE_PID=$!

# Give it a moment to get external IP
sleep 10
kill $SERVICE_PID 2>/dev/null || true

SERVICE_IP=$(kubectl get service ml-api-service -n ml-platform -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
SERVICE_URL="http://$SERVICE_IP:8000"

echo ""
echo "✅ Deployment Complete!"
echo "🌐 API URL: $SERVICE_URL"
echo ""
echo "🧪 Test commands:"
echo "curl -X POST \"$SERVICE_URL/predict\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"values\": [100, 105, 103, 108, 110]}'"
echo ""
echo "🔍 Check status:"
echo "kubectl get all -n ml-platform"
echo "kubectl logs -f deployment/ml-api -n ml-platform"
