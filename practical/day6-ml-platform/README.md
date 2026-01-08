# 🚀 Mini ML Platform on Kubernetes

## What We're Building

An end-to-end ML serving platform with:
- **Training Job** - Trains a time-series forecasting model
- **Model Storage** - PVC to persist trained model
- **Serving API** - FastAPI for real-time predictions
- **Autoscaling** - HPA scales based on load
- **Scheduled Retraining** - CronJob for weekly updates

```
┌─────────────────────────────────────────────────────────────────┐
│                     ML PLATFORM ARCHITECTURE                     │
│                                                                  │
│   ┌──────────┐        ┌──────────┐        ┌──────────┐         │
│   │ Training │───────►│   PVC    │◄───────│   API    │         │
│   │   Job    │ write  │  (1Gi)   │  read  │ Serving  │         │
│   └──────────┘        └──────────┘        └──────────┘         │
│        ▲                                        │               │
│        │                                        ▼               │
│   ┌──────────┐                           ┌──────────┐          │
│   │ CronJob  │                           │   HPA    │          │
│   │ (weekly) │                           │ (scale)  │          │
│   └──────────┘                           └──────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Docker Desktop running
- minikube installed
- kubectl configured

---

## Phase 1: Setup (15 mins)

### 1.1 Start Docker Desktop

Make sure Docker is running (check menu bar icon).

### 1.2 Start Minikube

```bash
# Start with conservative resources for 8GB Mac
# Note: Docker Desktop limits available memory (~3.9GB), so we use 3GB
minikube start --driver=docker --memory=3072 --cpus=2

# Verify
minikube status
kubectl get nodes
```

> ⚠️ **Memory Error?** If you see "Docker Desktop has only XXXMB memory", reduce `--memory` further or increase Docker Desktop's memory limit in Docker Desktop → Settings → Resources.

### 1.3 Enable Metrics Server (for HPA)

```bash
minikube addons enable metrics-server

# Verify (takes ~1 min to be ready)
kubectl get pods -n kube-system | grep metrics
```

### 1.4 Configure Docker to Use Minikube's Daemon

```bash
# This lets us build images directly in minikube
eval $(minikube docker-env)

# Verify (should show minikube's Docker)
docker info | grep Name
```

> ⚠️ **Note:** Run this in every new terminal, or images won't be found!

---

## Phase 2: Create Namespace & Storage (10 mins)

### 2.1 Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2.2 Create ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

### 2.3 Create PVC

```bash
kubectl apply -f k8s/pvc.yaml

# Verify
kubectl get pvc -n ml-platform
```

**Expected output:**
```
NAME        STATUS   VOLUME   CAPACITY   ACCESS MODES
model-pvc   Bound    ...      1Gi        RWO
```

---

## Phase 3: Build Training Container (20 mins)

### 3.1 Build the Training Image

```bash
# Make sure you're using minikube's Docker!
eval $(minikube docker-env)

# Build
cd model
docker build -t ml-training:v1 .
cd ..

# Verify
docker images | grep ml-training
```

### 3.2 Run Training Job

```bash
kubectl apply -f k8s/training-job.yaml

# Watch progress
kubectl get jobs -n ml-platform -w

# Check logs
kubectl logs -n ml-platform job/model-training -f
```

**Expected output:**
```
Starting model training...
Generated 1000 samples of time-series data
Training RandomForestRegressor...
Model trained successfully!
MAE: 0.XX
RMSE: 0.XX
Model saved to /models/model.joblib
Training complete!
```

### 3.3 Verify Model Saved

```bash
# Create a debug pod to check PVC
kubectl run debug --image=busybox -n ml-platform --rm -it --restart=Never -- ls -la /models
# (mount the PVC in this command or check via job pod)

# Or check job completed
kubectl get jobs -n ml-platform
```

**Expected:**
```
NAME             COMPLETIONS   DURATION
model-training   1/1           30s
```

---

## Phase 4: Build & Deploy API (25 mins)

### 4.1 Build API Image

```bash
# Ensure minikube Docker context
eval $(minikube docker-env)

# Build
cd api
docker build -t ml-api:v1 .
cd ..

# Verify
docker images | grep ml-api
```

### 4.2 Deploy API

```bash
kubectl apply -f k8s/api-deployment.yaml

# Watch pods start
kubectl get pods -n ml-platform -w

# Check logs
kubectl logs -n ml-platform -l app=ml-api -f
```

**Expected logs:**
```
INFO:     Loading model from /models/model.joblib
INFO:     Model loaded successfully!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4.3 Expose API Service

```bash
kubectl apply -f k8s/api-service.yaml

# Get service URL
minikube service ml-api-service -n ml-platform --url
```

### 4.4 Test the API

```bash
# Get the URL
SERVICE_URL=$(minikube service ml-api-service -n ml-platform --url)

# Health check
curl $SERVICE_URL/health

# Readiness check
curl $SERVICE_URL/ready

# Make a prediction!
curl -X POST "http://127.0.0.1:56121/predict" \
  -H "Content-Type: application/json" \
  -d '{"values": [100, 105, 103, 108, 110]}'
```

**Expected response:**
```json
{
  "prediction": 112.34,
  "model_version": "v1",
  "timestamp": "2024-12-30T10:00:00"
}
```

---

## Phase 5: Setup Autoscaling (15 mins)

### 5.1 Deploy HPA

```bash
kubectl apply -f k8s/api-hpa.yaml

# Check HPA status
kubectl get hpa -n ml-platform
```

**Expected output:**
```
NAME         REFERENCE              TARGETS   MINPODS   MAXPODS   REPLICAS
ml-api-hpa   Deployment/ml-api      10%/70%   2         5         2
```

### 5.2 Test Autoscaling (Optional)

```bash
# Generate load (run in separate terminal)
SERVICE_URL=$(minikube service ml-api-service -n ml-platform --url)

# Simple load test
for i in {1..1000}; do
  curl -s -X POST "$SERVICE_URL/predict" \
    -H "Content-Type: application/json" \
    -d '{"values": [100, 105, 103, 108, 110]}' &
done

# Watch scaling
kubectl get pods -n ml-platform -w
kubectl get hpa -n ml-platform -w
```

---

## Phase 6: Setup Scheduled Retraining (10 mins)

### 6.1 Deploy CronJob

```bash
kubectl apply -f k8s/training-cronjob.yaml

# Verify
kubectl get cronjobs -n ml-platform
```

### 6.2 Test CronJob Manually

```bash
# Trigger a manual run
kubectl create job --from=cronjob/model-retrain manual-retrain -n ml-platform

# Watch it run
kubectl get jobs -n ml-platform -w
kubectl logs -n ml-platform job/manual-retrain -f
```

### 6.3 Clean Up Test Job

```bash
kubectl delete job manual-retrain -n ml-platform
```

---

## 📊 Verify Everything Works

### Full System Check

```bash
# 1. Check all resources
kubectl get all -n ml-platform

# 2. Check PVC
kubectl get pvc -n ml-platform

# 3. Check HPA
kubectl get hpa -n ml-platform

# 4. Check CronJob
kubectl get cronjobs -n ml-platform

# 5. Test API
SERVICE_URL=$(minikube service ml-api-service -n ml-platform --url)
curl -X POST "http://127.0.0.1:56121/predict" \
  -H "Content-Type: application/json" \
  -d '{"values": [100, 105, 103, 108, 110]}'
```

### Expected Resource State

```
NAME                          READY   STATUS
pod/ml-api-xxxxx              1/1     Running
pod/ml-api-yyyyy              1/1     Running

NAME                    TYPE       CLUSTER-IP      PORT(S)
service/ml-api-service  NodePort   10.x.x.x        8000:30800/TCP

NAME                     READY   UP-TO-DATE   AVAILABLE
deployment.apps/ml-api   2/2     2            2

NAME                          COMPLETIONS   DURATION
job.batch/model-training      1/1           30s

NAME                        SCHEDULE      SUSPEND   ACTIVE
cronjob.batch/model-retrain 0 2 * * 0     False     0
```

---

## 🧹 Cleanup

```bash
# Delete all resources in namespace
kubectl delete namespace ml-platform

# Stop minikube (preserves data)
minikube stop

# Full reset (if needed)
minikube delete
```

---

## 🎯 Interview Talking Points

### Architecture Overview
> "I built an ML platform with training, serving, and automation. Training runs as a K8s Job, saves the model to a PVC. The FastAPI server loads the model and serves predictions. HPA handles traffic spikes, and a CronJob retrains weekly."

### Why This Architecture?
> "Jobs are perfect for training - they run to completion. Deployments with HPA handle variable inference load. PVC provides fast model access without cloud storage latency. CronJob automates retraining without manual intervention."

### How Would You Improve This?
> "For production: add MLflow for model versioning, Prometheus for metrics, proper CI/CD pipeline, A/B testing for model rollouts, and move to GCS for distributed access."

---

## 🐛 Troubleshooting

### Pod stuck in Pending
```bash
kubectl describe pod <pod-name> -n ml-platform
# Check Events section for: insufficient resources, PVC not bound
```

### ImagePullBackOff
```bash
# Make sure you built with minikube's Docker
eval $(minikube docker-env)
docker images | grep ml-

# Rebuild if needed
docker build -t ml-api:v1 ./api
```

### API returns "Model not loaded"
```bash
# Check if training job completed
kubectl get jobs -n ml-platform

# Check PVC has the model
kubectl exec -it deployment/ml-api -n ml-platform -- ls -la /models/
```

### HPA shows "unknown" for metrics
```bash
# Enable metrics-server
minikube addons enable metrics-server

# Wait 1-2 minutes, then check
kubectl top pods -n ml-platform
```

---

## 📁 Project Structure

```
day6-ml-platform/
├── MASTER-PLAN.md          # Project overview
├── README.md               # This file
├── model/
│   ├── train.py            # Training script
│   ├── requirements.txt
│   └── Dockerfile
├── api/
│   ├── main.py             # FastAPI server
│   ├── requirements.txt
│   └── Dockerfile
└── k8s/
    ├── namespace.yaml
    ├── configmap.yaml
    ├── pvc.yaml
    ├── training-job.yaml
    ├── training-cronjob.yaml
    ├── api-deployment.yaml
    ├── api-service.yaml
    └── api-hpa.yaml
```

---

**Total Time:** ~1.5-2 hours (following this guide)

**Next Steps:** Read theory/06-jobs-cronjobs.md and theory/08-ml-on-kubernetes.md for deep understanding!

*Last updated: January 7, 2026*

