#!/bin/bash

# GCP Cost Monitoring Script
# Run daily to stay within free tier

PROJECT_ID=$(gcloud config get-value project)

echo "💰 GCP Cost Check - $(date)"
echo "📍 Project: $PROJECT_ID"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check current bill (may take a few days to update)
echo "📊 Current Billing Status:"
gcloud billing export projects describe $PROJECT_ID 2>/dev/null || echo "Billing data not available yet (normal for new projects)"

echo ""
echo "🔍 Active Resources:"

# Check GKE clusters
echo "GKE Clusters:"
gcloud container clusters list --format="table(name,location,status)"

# Check Compute instances (should be empty)
echo ""
echo "Compute Instances:"
gcloud compute instances list --format="table(name,zone,status)"

# Check Persistent Disks
echo ""
echo "Persistent Disks:"
gcloud compute disks list --format="table(name,zone,sizeGb,status)"

# Check Load Balancers
echo ""
echo "Load Balancers:"
gcloud compute forwarding-rules list --format="table(name,region,target)"

echo ""
echo "✅ Free Tier Limits Reminder:"
echo "• GKE Autopilot: 1 free cluster forever"
echo "• Cloud Storage: 5GB free"
echo "• Cloud Monitoring: Free"
echo "• Container Registry: Free storage"
echo ""
echo "⚠️  Costly Services (Avoid):"
echo "• GKE Standard clusters: ~$0.10/hour"
echo "• Compute Engine VMs: ~$0.01/hour"
echo "• Persistent Disks: ~$0.04/GB/month"

echo ""
echo "🧹 Cleanup Commands (if needed):"
echo "gcloud container clusters delete ml-interview-cluster --region=us-central1 --quiet"
echo "kubectl delete namespace ml-platform"
