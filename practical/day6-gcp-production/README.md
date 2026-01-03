# 🚀 Day 6: Production Patterns & Troubleshooting on GCP (4 hours)

## 🎯 Goal
Learn production deployment patterns, monitoring, logging, and debugging on GCP/GKE for ML workloads.

---

## 📋 Prerequisites

- Day 4 GKE experience completed
- Free GKE Autopilot cluster ready
- Your ML platform deployed
- Understanding of basic kubectl debugging

---

## Phase 1: Production-Ready Deployment Patterns (60 mins)

### 1.1 Create Production Namespace with Resource Quotas

```bash
# Create production namespace
kubectl create namespace production

# Apply resource quotas
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ml-platform-quota
  namespace: production
spec:
  hard:
    requests.cpu: "4"
    requests.memory: "8Gi"
    limits.cpu: "8"
    limits.memory: "16Gi"
    persistentvolumeclaims: "5"
    pods: "20"
    services: "10"
EOF

# Check quota
kubectl describe resourcequota ml-platform-quota -n production
```

**Expected Output:**
```bash
# kubectl describe resourcequota ml-platform-quota -n production
Name:       ml-platform-quota
Namespace:  production
Resource    Used  Hard
--------    ----  ----
limits.cpu  0     8
limits.memory  0  16Gi
pods        0     20
persistentvolumeclaims  0  5
requests.cpu  0  4
requests.memory  0  8Gi
services    0     10
```

### 1.2 Deploy with Proper Security (Service Accounts)

```bash
# Create GCP service account for ML workloads
gcloud iam service-accounts create ml-production-sa \
    --display-name="ML Production Service Account" \
    --project=$(gcloud config get-value project)

# Grant minimal permissions (Storage access for models)
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:ml-production-sa@$(gcloud config get-value project).iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"

# Create Kubernetes service account
kubectl create serviceaccount ml-k8s-sa -n production

# Bind GCP and K8s service accounts (Workload Identity)
gcloud iam service-accounts add-iam-policy-binding \
    ml-production-sa@$(gcloud config get-value project).iam.gserviceaccount.com \
    --role=roles/iam.workloadIdentityUser \
    --member="serviceAccount:$(gcloud config get-value project).svc.id.goog[production/ml-k8s-sa]"
```

**Expected Output:**
```bash
# Service account creation
Created service account [ml-production-sa].

# IAM binding
bindings:
- members:
  - serviceAccount:your-project.svc.id.goog[production/ml-k8s-sa]
  role: roles/iam.workloadIdentityUser
```

### 1.3 Deploy ML Platform with Production Config

```bash
# Create production configmap
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: ml-config
  namespace: production
data:
  LOG_LEVEL: "INFO"
  MODEL_PATH: "/models/model.joblib"
  MAX_WORKERS: "4"
  BATCH_SIZE: "32"
  ENVIRONMENT: "production"
EOF

# Create production PVC with backup
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ml-model-storage
  namespace: production
  annotations:
    kubernetes.io/reclaimPolicy: "Retain"  # Don't delete data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi  # Larger for production
  storageClassName: standard-rwo
EOF

# Check resources
kubectl get all,configmaps,pvc -n production
```

**Expected Output:**
```bash
# kubectl get pvc -n production
NAME               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
ml-model-storage   Bound    pvc-abc123de-xyz9-4567-8901-abcdef123456   5Gi        RWO            standard-rwo   30s
```

---

## Phase 2: Monitoring & Observability Setup (60 mins)

### 2.1 Enable GKE Cloud Monitoring

```bash
# Enable Cloud Monitoring for your cluster (via Console)
# GCP Console → Kubernetes Engine → Clusters → your-cluster
# Enable "Cloud Monitoring" and "Cloud Logging"

# Check if monitoring is working
kubectl get pods -n kube-system | grep stackdriver

# View basic metrics
kubectl top nodes
kubectl top pods -n production
```

**Expected Output:**
```bash
# kubectl top nodes
NAME                                             CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
gk3-ml-interview-cluster-pool-1-abc123de-xyz9   45m          4%     678Mi           15%

# kubectl top pods -n production (after deployment)
NAME                           CPU(cores)   MEMORY(bytes)
ml-api-abc123def-xyz45         15m          120Mi
ml-api-abc123def-ghi67         12m          115Mi
```

### 2.2 Set Up Custom Metrics for HPA

```bash
# Deploy metrics server (usually pre-installed on GKE)
kubectl get deployment metrics-server -n kube-system

# Create custom metrics (request rate)
cat <<EOF | kubectl apply -f -
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ml-api-hpa-custom
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF
```

### 2.3 Set Up Logging

```bash
# View structured logs
kubectl logs -f deployment/ml-api -n production --tail=50

# Check GCP Cloud Logging
# GCP Console → Logging → Logs Explorer
# Filter: resource.type="k8s_container"
#         resource.labels.cluster_name="ml-interview-cluster"

# Search for specific logs
kubectl logs -l app=ml-api -n production --since=1h | grep ERROR
```

---

## Phase 3: Troubleshooting Common Production Issues (75 mins)

### 3.1 Scenario 1: Pod Stuck in Pending

**Create the problem:**
```bash
# Deploy pod with impossible resource requirements
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: trouble-pod
  namespace: production
spec:
  containers:
  - name: trouble
    image: nginx
    resources:
      requests:
        cpu: "100"  # Impossible request
        memory: "1Ti"
EOF
```

**Debug the issue:**
```bash
# Check pod status
kubectl get pods -n production

# Describe the pod for events
kubectl describe pod trouble-pod -n production

# Check cluster resource availability
kubectl describe nodes | grep -A 10 "Allocated resources"

# Check resource quota
kubectl describe resourcequota -n production
```

**Expected Output:**
```bash
# kubectl get pods -n production
NAME          READY   STATUS    RESTARTS   AGE
trouble-pod   0/1     Pending   0          2m

# kubectl describe pod trouble-pod -n production
Events:
  Type     Reason            Age   From               Message
  ----     ------            ----  ----               -------
  Warning  FailedScheduling  2m    default-scheduler  0/1 nodes are available: insufficient cpu, insufficient memory.
```

**Fix the issue:**
```bash
# Fix resource requests
kubectl patch pod trouble-pod -n production --type='json' \
  -p='[{"op": "replace", "path": "/spec/containers/0/resources/requests/cpu", "value": "100m"}]'

kubectl patch pod trouble-pod -n production --type='json' \
  -p='[{"op": "replace", "path": "/spec/containers/0/resources/requests/memory", "value": "128Mi"}]'

# Verify fix
kubectl get pods -n production
```

### 3.2 Scenario 2: CrashLoopBackOff

**Create the problem:**
```bash
# Deploy pod that crashes immediately
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: crash-pod
  namespace: production
spec:
  containers:
  - name: crash
    image: busybox
    command: ["sh", "-c", "exit 1"]  # Always fails
EOF
```

**Debug the issue:**
```bash
# Check pod status
kubectl get pods -n production

# Check logs (including previous attempts)
kubectl logs crash-pod -n production --previous

# Describe pod for restart policy and events
kubectl describe pod crash-pod -n production

# Check if it's hitting restart limits
kubectl get pods -n production -o yaml | grep restartPolicy
```

**Expected Output:**
```bash
# kubectl get pods -n production
NAME        READY   STATUS             RESTARTS   AGE
crash-pod   0/1     CrashLoopBackOff   5          3m

# kubectl logs crash-pod -n production --previous
sh: can't open 'exit': No such file or directory
```

**Fix the issue:**
```bash
# Fix the command
kubectl patch pod crash-pod -n production --type='json' \
  -p='[{"op": "replace", "path": "/spec/containers/0/command", "value": ["sh", "-c", "echo hello && sleep 3600"]}]'

# Or delete and redeploy with correct spec
kubectl delete pod crash-pod -n production
```

### 3.3 Scenario 3: Service Not Accessible

**Create the problem:**
```bash
# Create deployment and service with mismatched labels
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
  namespace: production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-app
  template:
    metadata:
      labels:
        app: test-app  # Correct label
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: test-service
  namespace: production
spec:
  selector:
    app: wrong-label  # Wrong selector!
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF
```

**Debug the issue:**
```bash
# Check service endpoints
kubectl get endpoints -n production

# Describe service
kubectl describe service test-service -n production

# Check pod labels vs service selector
kubectl get pods -n production --show-labels
kubectl get service test-service -n production -o yaml | grep selector
```

**Expected Output:**
```bash
# kubectl get endpoints -n production
NAME           ENDPOINTS   AGE
test-service   <none>      2m  # No endpoints!

# kubectl describe service test-service -n production
Selector: app=wrong-label  # Doesn't match pod labels
```

**Fix the issue:**
```bash
# Fix service selector
kubectl patch service test-service -n production --type='json' \
  -p='[{"op": "replace", "path": "/spec/selector/app", "value": "test-app"}]'

# Verify fix
kubectl get endpoints -n production
```

### 3.4 Scenario 4: ImagePullBackOff

**Create the problem:**
```bash
# Try to pull non-existent image
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: bad-image-pod
  namespace: production
spec:
  containers:
  - name: bad
    image: nonexistent-image:999
EOF
```

**Debug the issue:**
```bash
# Check pod status
kubectl get pods -n production

# Describe pod for image pull errors
kubectl describe pod bad-image-pod -n production

# Check image pull secrets
kubectl get secrets -n production

# Verify image exists
docker pull nonexistent-image:999  # Should fail
```

**Expected Output:**
```bash
# kubectl describe pod bad-image-pod -n production
Events:
  Type     Reason     Age   From              Message
  ----     ------     ----  ----              -------
  Normal   Pulling    1m    kubelet           Pulling image "nonexistent-image:999"
  Warning  Failed     1m    kubelet           Failed to pull image "nonexistent-image:999": rpc error: code = NotFound desc = manifest unknown
  Warning  Failed     1m    kubelet           Error: ErrImagePull
  Normal   BackOff    1m    kubelet           Back-off pulling image "nonexistent-image:999"
```

**Fix the issue:**
```bash
# Use correct image
kubectl patch pod bad-image-pod -n production --type='json' \
  -p='[{"op": "replace", "path": "/spec/containers/0/image", "value": "nginx:alpine"}]'
```

---

## Phase 4: CI/CD Concepts for Kubernetes (45 mins)

### 4.1 Cloud Build for Container Builds

```bash
# Create cloudbuild.yaml for automated builds
cat <<EOF > cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/\$PROJECT_ID/ml-api:\$COMMIT_SHA', './api']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/\$PROJECT_ID/ml-api:\$COMMIT_SHA']

  - name: 'gcr.io/cloud-builders/kubectl'
    args:
      - 'set'
      - 'image'
      - 'deployment/ml-api'
      - 'api=gcr.io/\$PROJECT_ID/ml-api:\$COMMIT_SHA'
    env:
      - 'CLOUDSDK_COMPUTE_REGION=us-central1'
      - 'CLOUDSDK_CONTAINER_CLUSTER=ml-interview-cluster'
EOF

# Test build locally (without deploying)
gcloud builds submit --config=cloudbuild.yaml --no-source --substitutions=COMMIT_SHA=test .
```

### 4.2 GitOps with Config Sync (Concept)

```bash
# Show how to structure GitOps repo
tree -a gitops-repo/
# gitops-repo/
# ├── clusters/
# │   └── ml-interview-cluster/
# │       ├── namespaces/
# │       │   └── production/
# │       │       ├── ml-platform/
# │       │       │   ├── deployment.yaml
# │       │       │   ├── service.yaml
# │       │       │   └── hpa.yaml
# │       │       └── resource-quota.yaml
# │       └── cluster-config.yaml
# └── README.md
```

---

## 🧹 Comprehensive Cleanup

```bash
# Delete all resources
kubectl delete namespace production

# Delete service accounts
gcloud iam service-accounts delete ml-production-sa@$(gcloud config get-value project).iam.gserviceaccount.com --quiet

# Stop cluster to save costs
gcloud container clusters delete ml-interview-cluster --region=us-central1 --quiet

# Check final costs
gcloud billing export projects describe $(gcloud config get-value project)
```

---

## ✅ Day 6 Checkpoint

You should be able to:

- [ ] Set up production namespaces with resource quotas
- [ ] Configure Workload Identity for secure GCP access
- [ ] Debug common Kubernetes issues (Pending, CrashLoopBackOff, etc.)
- [ ] Use GCP Cloud Monitoring and Logging
- [ ] Understand CI/CD concepts for Kubernetes
- [ ] Deploy with security best practices

---

## 📝 Key Production Takeaways

1. **Always use ResourceQuotas** to prevent resource exhaustion
2. **Workload Identity** eliminates the need for service account keys
3. **Monitor costs daily** - GKE can get expensive quickly
4. **Structured logging** makes debugging much easier
5. **Test deployments in non-production namespaces first**
6. **Use GitOps** for declarative, auditable deployments

---

## 🐛 Troubleshooting Cheat Sheet

| Issue | Check Command | Common Causes |
|-------|---------------|---------------|
| Pod Pending | `kubectl describe pod` | Insufficient resources, node issues |
| CrashLoopBackOff | `kubectl logs --previous` | Application errors, missing dependencies |
| ImagePullBackOff | `kubectl describe pod` | Wrong image name, registry access |
| Service no endpoints | `kubectl get endpoints` | Label mismatch between service and pods |
| OOM Killed | `kubectl describe pod` | Memory limits too low, memory leaks |
| HPA not scaling | `kubectl get hpa` | Metrics server issues, wrong metrics |

---

**Time: ~4 hours | Cost: $0.00 (Free tier) | Skills: Production debugging, monitoring, security**
