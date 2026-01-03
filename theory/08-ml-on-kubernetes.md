# 🤖 Machine Learning on Kubernetes

## Why Run ML on Kubernetes?

| Challenge | K8s Solution |
|-----------|--------------|
| "Training takes hours, blocks my laptop" | Run as Job on cluster |
| "Need GPUs but only sometimes" | Node pools with autoscaling |
| "Model needs to handle 1000 req/sec" | HPA scales pods automatically |
| "Data scientists need isolated environments" | JupyterHub spawns per-user pods |
| "Need to version and rollback models" | Deployments with image tags |
| "Different teams, different resources" | Namespaces + ResourceQuotas |

---

## ML Workflow on Kubernetes

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ML WORKFLOW ON KUBERNETES                         │
│                                                                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│  │  DATA    │   │ TRAINING │   │  MODEL   │   │ SERVING  │        │
│  │          │──►│          │──►│ STORAGE  │──►│          │        │
│  │ (GCS/S3) │   │  (Job)   │   │  (PVC)   │   │  (API)   │        │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘        │
│       │              │              │              │                │
│       │         ┌────┴────┐        │         ┌────┴────┐          │
│       │         │ CronJob │        │         │   HPA   │          │
│       │         │(retrain)│        │         │ (scale) │          │
│       │         └─────────┘        │         └─────────┘          │
│       │                            │                               │
│       └────────────────────────────┴───────────────────────────────│
│                    Monitoring (Prometheus/Stackdriver)              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Architecture Patterns

### Pattern 1: Simple (What We're Building)

```
┌─────────────────────────────────────────┐
│                                          │
│   Job ──────► PVC ◄────── Deployment    │
│  (train)    (model)        (serve)      │
│                                          │
│   CronJob triggers Job weekly           │
│   HPA scales Deployment on load         │
│                                          │
└─────────────────────────────────────────┘
```

**Best for:** Simple models, single team, getting started

---

### Pattern 2: With Model Registry

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│   Job ──────► MLflow/Vertex ◄────── Deployment              │
│  (train)      (registry)            (serve)                 │
│     │              │                    │                    │
│     └── Logs ──────┴── Versions ────────┘                   │
│                                                              │
│   Benefits:                                                  │
│   • Model versioning                                        │
│   • Experiment tracking                                     │
│   • Easy rollbacks                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Best for:** Teams with multiple experiments, need tracking

---

### Pattern 3: Feature Store + Serving

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│  │ Feature  │──►│ Training │──►│  Model   │──►│ Serving  │        │
│  │  Store   │   │  (Job)   │   │ Registry │   │  (API)   │        │
│  │ (Feast)  │   │          │   │ (MLflow) │   │          │        │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘        │
│       ▲                                            │               │
│       │                                            │               │
│       └────────── Online Features ─────────────────┘               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Best for:** Production systems, feature consistency, real-time features

---

## Model Storage Options

### Option 1: PersistentVolumeClaim (Simple)

```yaml
# Create PVC

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

```yaml
# Training Job writes model
volumeMounts:
- name: models
  mountPath: /models
volumes:
- name: models
  persistentVolumeClaim:
    claimName: model-storage
```

```yaml
# Serving reads model (same PVC)
volumeMounts:
- name: models
  mountPath: /models
  readOnly: true
```

**Pros:** Simple, fast, no external dependencies
**Cons:** Single-node access (RWO), no versioning

---

### Option 2: Cloud Storage (GCS/S3)

```python
# In training script
from google.cloud import storage

def save_model(model, bucket_name, model_path):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(model_path)
    
    # Save locally first, then upload
    model.save('/tmp/model.joblib')
    blob.upload_from_filename('/tmp/model.joblib')
```

```yaml
# Pod with Workload Identity (GKE)
spec:
  serviceAccountName: ml-service-account  # Has GCS access
  containers:
  - name: trainer
    image: training:v1
    env:
    - name: MODEL_BUCKET
      value: "my-models-bucket"
```

**Pros:** Versioning, multi-node access, durable
**Cons:** Latency, requires cloud credentials

---

### Option 3: Model Registry (MLflow)

```python
import mlflow

# During training
with mlflow.start_run():
    mlflow.log_params({"n_estimators": 100})
    mlflow.log_metrics({"rmse": 0.45})
    mlflow.sklearn.log_model(model, "model")
```

```python
# During serving
model = mlflow.sklearn.load_model("models:/my-model/Production")
```

**Pros:** Full versioning, A/B testing, experiment tracking
**Cons:** Additional component to deploy/manage

---

## Model Serving Patterns

### Pattern 1: Direct Deployment (FastAPI)

```python
# main.py
from fastapi import FastAPI
import joblib

app = FastAPI()
model = None

@app.on_event("startup")
async def load_model():
    global model
    model = joblib.load("/models/model.joblib")

@app.post("/predict")
async def predict(data: dict):
    features = preprocess(data)
    prediction = model.predict([features])
    return {"prediction": prediction[0]}
```

**Pros:** Simple, full control, easy debugging
**Cons:** Must implement health checks, scaling yourself

---

### Pattern 2: Model Mesh / Seldon

```yaml
apiVersion: machinelearning.seldon.io/v1
kind: SeldonDeployment
metadata:
  name: sklearn-model
spec:
  predictors:
  - graph:
      name: classifier
      implementation: SKLEARN_SERVER
      modelUri: gs://my-bucket/model
    replicas: 3
```

**Pros:** Built-in scaling, A/B testing, monitoring
**Cons:** More complex, additional learning curve

---

### Pattern 3: Serverless (KNative/Cloud Run)

```yaml
# Scale to zero when no traffic
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ml-model
spec:
  template:
    spec:
      containers:
      - image: my-model:v1
        resources:
          limits:
            memory: 1Gi
      containerConcurrency: 10
```

**Pros:** Scale to zero (cost savings), automatic scaling
**Cons:** Cold starts, less control

---

## Resource Management for ML

### Training Resources (High)

```yaml
# Training jobs need more resources
resources:
  requests:
    memory: "2Gi"
    cpu: "2000m"
  limits:
    memory: "4Gi"
    cpu: "4000m"
```

### Serving Resources (Balanced)

```yaml
# Serving needs quick response, not heavy compute
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### GPU Resources

```yaml
# Request GPU for training
resources:
  limits:
    nvidia.com/gpu: 1

# Node selector for GPU pool
nodeSelector:
  cloud.google.com/gke-accelerator: nvidia-tesla-t4
```

---

## Health Checks for ML

### Why ML Needs Custom Probes

Standard web apps: `/health` returns 200 = healthy
ML apps: Model must be **loaded and ready**

```python
# main.py
model = None
model_loaded = False`

@app.on_event("startup")
async def load_model():
    global model, model_loaded
    model = joblib.load("/models/model.joblib")
    model_loaded = True

@app.get("/health")
async def health():
    """Liveness: Is the process alive?"""
    return {"status": "alive"}

@app.get("/ready")
async def ready():
    """Readiness: Can we serve traffic?"""
    if not model_loaded:
        raise HTTPException(503, "Model not loaded")
    return {"status": "ready", "model_loaded": True}
```

```yaml
# Deployment with ML-aware probes
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 15

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5   # Start checking early
  periodSeconds: 5
  failureThreshold: 3      # Remove from LB after 3 failures
```

---

## Init Containers for ML

### Wait for Model to Exist

```yaml
spec:
  initContainers:
  - name: wait-for-model
    image: busybox
    command: ['sh', '-c', 'until [ -f /models/model.joblib ]; do echo waiting for model; sleep 5; done']
    volumeMounts:
    - name: models
      mountPath: /models
  containers:
  - name: api
    image: serving-api:v1
    volumeMounts:
    - name: models
      mountPath: /models
```

### Download Model from GCS

```yaml
initContainers:
- name: download-model
  image: google/cloud-sdk:slim
  command:
  - gsutil
  - cp
  - gs://my-bucket/models/latest.joblib
  - /models/model.joblib
  volumeMounts:
  - name: models
    mountPath: /models
```

---

## Model Updates & Rollouts

### Blue-Green Deployment

```yaml
# v1 deployment (current)
metadata:
  name: model-v1
  labels:
    version: v1

# v2 deployment (new)
metadata:
  name: model-v2
  labels:
    version: v2

# Service switches between them
spec:
  selector:
    version: v2  # Change to switch
```

### Canary Deployment

```yaml
# 90% traffic to v1
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
spec:
  http:
  - route:
    - destination:
        host: model-service
        subset: v1
      weight: 90
    - destination:
        host: model-service
        subset: v2
      weight: 10
```

### Rolling Update (Default)

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 25%
      maxSurge: 25%
```

---

## Monitoring ML on Kubernetes

### Key Metrics to Track

| Metric | Why | Tool |
|--------|-----|------|
| Prediction latency | User experience | Prometheus |
| Request throughput | Capacity planning | Prometheus |
| Model accuracy | Model health | Custom metrics |
| Feature drift | Data quality | Custom/Evidently |
| Pod restarts | Stability | K8s metrics |
| Memory usage | OOM prevention | cAdvisor |

### Prometheus Metrics in FastAPI

```python
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

PREDICTIONS = Counter('predictions_total', 'Total predictions')
LATENCY = Histogram('prediction_latency_seconds', 'Prediction latency')

@app.post("/predict")
async def predict(data: dict):
    with LATENCY.time():
        result = model.predict(data)
    PREDICTIONS.inc()
    return result

# Auto-instrument
Instrumentator().instrument(app).expose(app)
```

---

## Common Issues & Solutions

### Issue: OOMKilled During Training

```yaml
# Increase memory limits
resources:
  limits:
    memory: "4Gi"  # Was 2Gi

# Or use memory-efficient approaches:
# - Batch processing
# - Memory-mapped files
# - Streaming data
```

### Issue: Model Load Time Causes Probe Failures

```yaml
# Increase initial delay
readinessProbe:
  initialDelaySeconds: 60  # Give time to load
  failureThreshold: 5      # More attempts

# Or use startup probe
startupProbe:
  httpGet:
    path: /ready
  failureThreshold: 30
  periodSeconds: 10        # 5 minutes to start\
```

### Issue: Cold Starts After Scale-Down

```yaml
# Keep minimum replicas
spec:
  minReplicas: 2  # Never scale to zero

# Or use PodDisruptionBudget
apiVersion: policy/v1
kind: PodDisruptionBudget
spec:
  minAvailable: 1
```

### Issue: Different Models for Different Clients

```yaml
# Deploy multiple versions, route by header
# Using Istio:
http:
- match:
  - headers:
      model-version:
        exact: "v2"
  route:
  - destination:
      host: model-v2

- route:  # default
  - destination:
      host: model-v1
```

---

## GKE-Specific ML Features

### GPU Node Pools

```bash
gcloud container node-pools create gpu-pool \
    --cluster=ml-cluster \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --num-nodes=1 \
    --enable-autoscaling \
    --min-nodes=0 \
    --max-nodes=3
```

### Workload Identity for GCS Access

```bash
# No key files needed!
gcloud iam service-accounts add-iam-policy-binding \
    ml-sa@PROJECT.iam.gserviceaccount.com \
    --role=roles/iam.workloadIdentityUser \
    --member="serviceAccount:PROJECT.svc.id.goog[ml-namespace/ml-k8s-sa]"
```

### Vertex AI Integration

```python
from google.cloud import aiplatform

# Deploy model to Vertex AI from GKE
aiplatform.init(project='my-project', location='us-central1')
model = aiplatform.Model.upload(
    display_name='my-model',
    artifact_uri='gs://my-bucket/models/',
    serving_container_image_uri='us-docker.pkg.dev/...'
)
```

---

## 📝 Quick Reference

```bash
# Training Job
kubectl apply -f training-job.yaml
kubectl logs job/training
kubectl delete job training

# Check model in PVC
kubectl exec -it serving-pod -- ls /models/

# Scale serving
kubectl scale deployment serving --replicas=5

# Rolling update with new model
kubectl set image deployment/serving api=serving:v2

# Rollback if issues
kubectl rollout undo deployment/serving
```

---

## 🎯 Interview Questions

**Q: How would you deploy an ML model on Kubernetes?**
> Containerize the model with FastAPI, create a Deployment with proper resource limits and health probes, expose via Service. For training, use Jobs; for automated retraining, use CronJobs. Store models on PVC or cloud storage.

**Q: How do you handle model updates without downtime?**
> Use rolling updates (default in Deployments) or blue-green deployments. For critical models, use canary deployments to test with a percentage of traffic first. Always have rollback ready.

**Q: Your model is OOMKilled in production. How do you debug?**
> 1. Check `kubectl describe pod` for OOMKilled reason
> 2. Review memory limits vs actual usage
> 3. Check for memory leaks in code
> 4. Consider batching predictions
> 5. Increase limits or optimize model

**Q: How do you scale ML inference?**
> HPA based on CPU or custom metrics (request latency, queue depth). For bursty workloads, combine with Cluster Autoscaler. Consider caching frequent predictions. For extreme scale, use model serving platforms like Seldon.

**Q: Training takes 4 hours but often fails halfway. How do you handle this?**
> 1. Use checkpointing (save progress periodically)
> 2. Set `activeDeadlineSeconds` appropriately
> 3. Use `backoffLimit` for retries
> 4. Consider distributed training for speed
> 5. Monitor resource usage to prevent OOM

---

**Next: Build the ML Platform! →**

