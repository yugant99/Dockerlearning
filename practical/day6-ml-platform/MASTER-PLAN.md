# 🚀 Mini ML Platform on Kubernetes - Master Plan

## Overview

Build an end-to-end ML serving platform on Kubernetes that demonstrates:
- Model training as Jobs
- Model serving as Deployments
- Autoscaling with HPA
- Scheduled retraining with CronJobs
- Persistent storage for artifacts

**Total Time:** ~8 hours
**System Requirements:** 8GB RAM (3GB for minikube), Docker Desktop, minikube

---

## 📁 Complete Project Structure

```
dockerlearning/
│
├── theory/                              # THEORY FILES TO ADD
│   ├── (existing files...)
│   ├── 06-jobs-cronjobs.md             # NEW: Jobs & CronJobs deep dive
│   ├── 07-hpa-autoscaling.md           # NEW: Horizontal Pod Autoscaler
│   └── 08-ml-on-kubernetes.md          # NEW: ML-specific K8s patterns
│
└── practical/
    └── day6-ml-platform/                # THIS PROJECT
        │
        ├── MASTER-PLAN.md              # This file (you're reading it)
        ├── README.md                    # Step-by-step execution guide
        │
        ├── model/                       # TRAINING COMPONENT
        │   ├── train.py                 # Training script (sklearn)
        │   ├── requirements.txt         # pandas, scikit-learn, joblib
        │   └── Dockerfile               # Training container
        │
        ├── api/                         # SERVING COMPONENT
        │   ├── main.py                  # FastAPI prediction server
        │   ├── requirements.txt         # fastapi, uvicorn, joblib
        │   └── Dockerfile               # API container
        │
        └── k8s/                         # KUBERNETES MANIFESTS
            ├── namespace.yaml           # ml-platform namespace
            ├── configmap.yaml           # Hyperparameters, settings
            ├── pvc.yaml                 # Model storage (1Gi)
            ├── training-job.yaml        # One-time training Job
            ├── training-cronjob.yaml    # Scheduled retraining
            ├── api-deployment.yaml      # API Deployment with probes
            ├── api-service.yaml         # NodePort Service
            └── api-hpa.yaml             # Autoscaler config
```

---

## 📚 THEORY FILES TO CREATE

### File 1: `theory/06-jobs-cronjobs.md`

**Topics Covered:**
| Concept | Description | Interview Question |
|---------|-------------|-------------------|
| Jobs | One-time batch tasks | "How do you run ML training on K8s?" |
| completions | Run N successful pods | "How to run parallel training?" |
| parallelism | Concurrent pod execution | "Speed up batch processing?" |
| backoffLimit | Failure handling | "What if training fails?" |
| activeDeadlineSeconds | Timeout | "Prevent runaway jobs?" |
| CronJobs | Scheduled execution | "Automate daily retraining?" |
| concurrencyPolicy | Forbid/Allow/Replace | "What if previous job still running?" |
| successfulJobsHistoryLimit | Cleanup | "Manage old job pods?" |

**Key YAML Examples:**
```yaml
# Job basics
apiVersion: batch/v1
kind: Job
spec:
  completions: 1
  parallelism: 1
  backoffLimit: 3
  activeDeadlineSeconds: 600
  
# CronJob schedule
schedule: "0 2 * * *"  # Daily at 2 AM
concurrencyPolicy: Forbid
```

---

### File 2: `theory/07-hpa-autoscaling.md`

**Topics Covered:**
| Concept | Description | Interview Question |
|---------|-------------|-------------------|
| HPA basics | Scale pods on metrics | "Handle traffic spikes?" |
| CPU-based scaling | Most common trigger | "Scale on CPU usage?" |
| Memory-based scaling | Less common | "Scale on memory?" |
| Custom metrics | Prometheus, Stackdriver | "Scale on queue depth?" |
| minReplicas/maxReplicas | Bounds | "Prevent over-scaling?" |
| scaleDown stabilization | Prevent flapping | "Avoid scale thrashing?" |
| Cluster Autoscaler | Scale nodes (GKE) | "What if nodes full?" |
| VPA | Vertical scaling | "Right-size containers?" |

**Key YAML Examples:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

### File 3: `theory/08-ml-on-kubernetes.md`

**Topics Covered:**
| Concept | Description | Interview Question |
|---------|-------------|-------------------|
| ML workflow on K8s | Train → Store → Serve | "End-to-end ML pipeline?" |
| Model storage patterns | PVC, GCS, S3 | "Where store models?" |
| Model versioning | Labels, paths | "Handle model versions?" |
| Inference optimization | Resources, batching | "Low-latency serving?" |
| GPU workloads | Node selectors, tolerations | "Run GPU training?" |
| Init containers for ML | Wait for model | "Ensure model loaded?" |
| Sidecar patterns | Logging, monitoring | "Monitor predictions?" |
| A/B testing | Multiple deployments | "Test new models?" |
| Canary deployments | Gradual rollout | "Safe model updates?" |
| JupyterHub on K8s | Data scientist environments | "Multi-user notebooks?" |

**Architecture Patterns:**
```
Pattern 1: Simple (Our Project)
┌─────────┐     ┌─────────┐     ┌─────────┐
│   Job   │────►│   PVC   │◄────│   API   │
│ (Train) │     │ (Model) │     │ (Serve) │
└─────────┘     └─────────┘     └─────────┘

Pattern 2: With Registry (Production)
┌─────────┐     ┌──────────┐     ┌─────────┐
│   Job   │────►│  MLflow  │◄────│   API   │
│ (Train) │     │ Registry │     │ (Serve) │
└─────────┘     └──────────┘     └─────────┘

Pattern 3: Full Platform (Enterprise)
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Feature  │──►│ Training │──►│  Model   │──►│ Serving  │
│  Store   │   │ Pipeline │   │ Registry │   │  Fleet   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
```

---

## 🛠️ PRACTICAL FILES TO CREATE

### Component 1: Model Training (`model/`)

#### `model/train.py`
```python
# What it does:
# - Generates synthetic time-series data (or loads from file)
# - Trains sklearn RandomForestRegressor
# - Saves model to /models/model.joblib
# - Prints metrics (MAE, RMSE)

# Key concepts demonstrated:
# - Reproducible training script
# - Model serialization with joblib
# - Environment variable configuration
```

#### `model/Dockerfile`
```dockerfile
# What it does:
# - Python 3.11 slim base
# - Install dependencies
# - Copy training script
# - Run train.py on container start

# Key concepts demonstrated:
# - Multi-stage builds (optional optimization)
# - Non-root user (security)
# - Minimal image size
```

---

### Component 2: API Server (`api/`)

#### `api/main.py`
```python
# What it does:
# - FastAPI app with /predict endpoint
# - Loads model from /models/model.joblib on startup
# - /health and /ready endpoints for probes
# - Returns predictions as JSON

# Endpoints:
# GET  /health  → {"status": "healthy"}
# GET  /ready   → {"status": "ready", "model_loaded": true}
# POST /predict → {"prediction": 123.45}
```

#### `api/Dockerfile`
```dockerfile
# What it does:
# - Python 3.11 slim base
# - Install FastAPI, uvicorn
# - Expose port 8000
# - Run uvicorn server
```

---

### Component 3: Kubernetes Manifests (`k8s/`)

#### `k8s/namespace.yaml`
```yaml
# Creates: ml-platform namespace
# Why: Isolate project resources, easy cleanup
# Interview: "How do you organize K8s resources?"
```

#### `k8s/configmap.yaml`
```yaml
# Contains: Hyperparameters, model path, settings
# Why: Externalize configuration
# Interview: "How do you manage ML hyperparameters in K8s?"

# Example keys:
# - MODEL_PATH=/models/model.joblib
# - N_ESTIMATORS=100
# - MAX_DEPTH=10
```

#### `k8s/pvc.yaml`
```yaml
# Creates: 1Gi PersistentVolumeClaim
# Access: ReadWriteOnce (RWO)
# Why: Store trained model between Job and Deployment
# Interview: "Where do you persist ML models?"
```

#### `k8s/training-job.yaml`
```yaml
# Creates: One-time training Job
# Mounts: PVC at /models
# Resources: 512Mi memory, 500m CPU
# Why: Run training to completion, then exit
# Interview: "How do you run batch training on K8s?"

# Key specs:
# - restartPolicy: Never (Jobs don't restart on success)
# - backoffLimit: 3 (retry on failure)
```

#### `k8s/training-cronjob.yaml`
```yaml
# Creates: Scheduled retraining
# Schedule: "0 2 * * 0" (Weekly Sunday 2 AM)
# Why: Automated model refresh
# Interview: "How do you automate retraining?"

# Key specs:
# - concurrencyPolicy: Forbid (don't overlap)
# - successfulJobsHistoryLimit: 3
```

#### `k8s/api-deployment.yaml`
```yaml
# Creates: API Deployment with 2 replicas
# Mounts: PVC at /models (readOnly)
# Probes: liveness + readiness
# Resources: 256Mi request, 512Mi limit
# Interview: "How do you deploy ML models for serving?"

# Key specs:
# - livenessProbe: /health every 10s
# - readinessProbe: /ready every 5s
# - imagePullPolicy: Never (local minikube)
```

#### `k8s/api-service.yaml`
```yaml
# Creates: NodePort Service
# Port: 8000 → 30800
# Why: Expose API outside cluster
# Interview: "How do you expose ML APIs?"
```

#### `k8s/api-hpa.yaml`
```yaml
# Creates: HorizontalPodAutoscaler
# Target: api-deployment
# Min/Max: 2-5 replicas
# Metric: CPU 70% utilization
# Interview: "How do you handle variable inference load?"
```

---

## 🎯 EXECUTION PHASES

### Phase 1: Foundation (1 hr)
**Build:** namespace.yaml, pvc.yaml, configmap.yaml
**Theory:** Read 06-jobs-cronjobs.md (Jobs section)
**Learn:** Namespaces, PVCs, ConfigMaps

### Phase 2: Training Pipeline (2 hrs)
**Build:** model/*, training-job.yaml
**Theory:** Read 06-jobs-cronjobs.md (full)
**Learn:** Containerizing ML, K8s Jobs

### Phase 3: Serving API (2 hrs)
**Build:** api/*, api-deployment.yaml, api-service.yaml
**Theory:** Read 08-ml-on-kubernetes.md
**Learn:** ML serving patterns, Probes

### Phase 4: Autoscaling (1 hr)
**Build:** api-hpa.yaml
**Theory:** Read 07-hpa-autoscaling.md
**Learn:** HPA, metrics-server

### Phase 5: Automation (1 hr)
**Build:** training-cronjob.yaml
**Theory:** Review 06-jobs-cronjobs.md (CronJobs)
**Learn:** Scheduled tasks, automation

### Phase 6: Integration & Testing (1 hr)
**Do:** End-to-end test, load testing, documentation
**Prepare:** Interview talking points

---

## 🗣️ INTERVIEW TALKING POINTS

After completing this project, you can discuss:

### Architecture Question
> "Walk me through how you'd deploy an ML model on Kubernetes"

**Your Answer:**
1. Containerize training script with dependencies
2. Run as K8s Job, save model to PersistentVolume
3. API server loads model, serves predictions
4. HPA scales based on request load
5. CronJob handles automated retraining

### Debugging Question
> "Your model serving API is returning errors. How do you debug?"

**Your Answer:**
1. `kubectl get pods` - check pod status
2. `kubectl describe pod` - see events, probe failures
3. `kubectl logs` - check application errors
4. Check if PVC mounted, model file exists
5. Check resource limits (OOMKilled?)

### Scaling Question
> "Traffic increased 10x overnight. What happens?"

**Your Answer:**
1. HPA detects CPU spike
2. Scales pods from 2 → 5 (our max)
3. If nodes full, Cluster Autoscaler adds nodes (GKE)
4. New pods pull from same PVC
5. Service load balances across all replicas

---

## 📊 SKILLS MATRIX

| Skill | Before | After | Interview Ready |
|-------|--------|-------|-----------------|
| K8s Jobs | ❌ | ✅ | "Run batch training" |
| K8s CronJobs | ❌ | ✅ | "Automate retraining" |
| PVC for ML | ⚠️ | ✅ | "Persist models" |
| HPA | ❌ | ✅ | "Handle load spikes" |
| Probes | ⚠️ | ✅ | "Health monitoring" |
| ML on K8s | ❌ | ✅ | "End-to-end pipeline" |
| Docker for ML | ⚠️ | ✅ | "Containerize training" |

---

## ❓ DECISION POINTS

Before we build, let's discuss:

### 1. Which phases to build?
- [ ] All phases (full 8 hours)
- [ ] Phases 1-3 only (foundation + core, 5 hours)
- [ ] Skip Phase 4-5 (no HPA/CronJob, simpler)

### 2. Which theory files first?
- [ ] 06-jobs-cronjobs.md (most relevant)
- [ ] 07-hpa-autoscaling.md
- [ ] 08-ml-on-kubernetes.md (comprehensive)

### 3. ML use case preference?
- [ ] Time-series forecasting (matches your BigBasket exp)
- [ ] Simple regression (faster to build)
- [ ] Classification (different but common)

---

## 🚦 NEXT STEPS

Tell me:
1. **Which phases** do you want to build?
2. **Which theory file** should I create first?
3. **Any modifications** to the plan?

Then I'll start creating the actual files!

