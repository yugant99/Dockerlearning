# 🚀 Day 4: GCP Fundamentals + GKE Hands-on (4 hours)

## 🎯 Goal
Get hands-on experience with GCP Console, create your first GKE cluster, and understand GCP services relevant to ML workloads.

---

## 📋 Prerequisites

- GCP account with free tier access
- gcloud CLI installed and authenticated
- kubectl installed
- Your existing ML platform from day6-ml-platform

---

## Phase 1: GCP Console Navigation & Free Tier Setup (45 mins)

### 1.1 Explore GCP Console

```bash
# Open GCP Console
open https://console.cloud.google.com/

# Or via gcloud
gcloud auth login --launch-browser
```

**Navigate to:**
1. **Home Dashboard** - Overview of your project
2. **Billing** → **Budgets & alerts** - Set up free tier monitoring
3. **IAM & Admin** → **Service Accounts** - Where you'll create identities
4. **APIs & Services** → **Library** - Enable services as needed

### 1.2 Create Budget Alert (Cost Protection)

**Via Console:**
1. Go to **Billing** → **Budgets & alerts**
2. Click **Create Budget**
3. Name: `Interview-Prep-Budget`
4. Budget amount: `$10` (should never reach this on free tier)
5. Set alert at 50% ($5)

**Expected Output:**
```
✅ Budget created successfully
Alert threshold: $5.00 USD
```

### 1.3 Check Current Project Resources

```bash
# Check your current project
gcloud config get-value project

# List all projects you have access to
gcloud projects list

# Check billing account
gcloud billing accounts list
```

**Expected Output:**
```bash
# gcloud config get-value project
your-project-123456

# gcloud projects list
PROJECT_ID          NAME            PROJECT_NUMBER
your-project-123456 My Project      123456789012
```

---

## Phase 2: Create Your First GKE Autopilot Cluster (60 mins)

### 2.1 Create Free GKE Autopilot Cluster

```bash
# Create FREE Autopilot cluster (no cost!)
gcloud container clusters create-auto ml-interview-cluster \
    --region=us-central1 \
    --project=$(gcloud config get-value project)
```

**Expected Output:**
```bash
# This will take 5-10 minutes
Creating cluster ml-interview-cluster in us-central1...
Cluster is being created...
⠼ Creating cluster ml-interview-cluster...done.
✅ Created cluster: ml-interview-cluster
```

### 2.2 Connect kubectl to Your GKE Cluster

```bash
# Get cluster credentials (updates ~/.kube/config)
gcloud container clusters get-credentials ml-interview-cluster \
    --region=us-central1

# Verify connection
kubectl get nodes
kubectl cluster-info
```

**Expected Output:**
```bash
# kubectl get nodes
NAME                                             STATUS   ROLES    AGE   VERSION
gk3-ml-interview-cluster-pool-1-abc123de-xyz9   Ready    <none>   2m    v1.27.3-gke.100

# kubectl cluster-info
Kubernetes control plane is running at https://34.102.136.180
GLBCDefaultBackend is running at https://34.102.136.180/api/v1/namespaces/kube-system/services/default-http-backend:http/proxy
KubeDNS is running at https://34.102.136.180/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

### 2.3 Explore GKE Cluster Features

```bash
# Check cluster details
gcloud container clusters describe ml-interview-cluster --region=us-central1

# List available storage classes (GCP-specific)
kubectl get storageclass

# Check cluster events
kubectl get events --sort-by=.metadata.creationTimestamp
```

**Expected Output:**
```bash
# kubectl get storageclass
NAME                 PROVISIONER            RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
premium-rwo          pd.csi.storage.gke.io  Delete          WaitForFirstConsumer   true                   5m
standard             kubernetes.io/gce-pd   Delete          Immediate               true                   5m
standard-rwo (default)  pd.csi.storage.gke.io  Delete          WaitForFirstConsumer   true                   5m
```

### 2.4 Test Basic Deployment on GKE

```bash
# Deploy nginx test app
kubectl create deployment nginx-test --image=nginx:alpine

# Expose it
kubectl expose deployment nginx-test --port=80 --type=LoadBalancer

# Wait for external IP
kubectl get service nginx-test -w
```

**Expected Output:**
```bash
# kubectl get service nginx-test
NAME          TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)        AGE
nginx-test    LoadBalancer   10.100.200.30  34.102.136.180  80:30080/TCP  2m
```

---

## Phase 3: Deploy Your ML Platform to GKE (75 mins)

### 3.1 Create Namespace

```bash
# Create namespace for your ML platform
kubectl create namespace ml-platform
```

### 3.2 Deploy ConfigMap

```bash
# Use your existing config from day6
kubectl apply -f ../../day6-ml-platform/k8s/configmap.yaml -n ml-platform
```

**Expected Output:**
```bash
configmap/ml-config created
```

### 3.3 Deploy PVC (GCP Persistent Disk)

```bash
# This will create a GCP Persistent Disk
kubectl apply -f ../../day6-ml-platform/k8s/pvc.yaml -n ml-platform

# Watch PVC creation
kubectl get pvc -n ml-platform -w
```

**Expected Output:**
```bash
# kubectl get pvc -n ml-platform
NAME        STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
model-pvc   Bound    pvc-abc123de-xyz9-4567-8901-abcdef123456   1Gi        RWO            standard-rwo   30s
```

### 3.4 Build and Push Docker Images to GCR

```bash
# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker

# Build training image
cd ../../day6-ml-platform/model
docker build -t gcr.io/$(gcloud config get-value project)/ml-training:v1 .

# Build API image
cd ../api
docker build -t gcr.io/$(gcloud config get-value project)/ml-api:v1 .

# Push both images
docker push gcr.io/$(gcloud config get-value project)/ml-training:v1
docker push gcr.io/$(gcloud config get-value project)/ml-api:v1
```

**Expected Output:**
```bash
# docker push gcr.io/your-project/ml-training:v1
The push refers to repository [gcr.io/your-project/ml-training:v1]
latest: digest: sha256:abc123... size: 1234

# docker push gcr.io/your-project/ml-api:v1
The push refers to repository [gcr.io/your-project/ml-api:v1]
latest: digest: sha256:def456... size: 5678
```

### 3.5 Deploy Training Job

```bash
# Update image references in training-job.yaml to use GCR
# Change: image: ml-training:v1
# To: image: gcr.io/YOUR_PROJECT/ml-training:v1

kubectl apply -f ../../day6-ml-platform/k8s/training-job.yaml -n ml-platform

# Watch job progress
kubectl get jobs -n ml-platform -w
kubectl logs -f job/model-training -n ml-platform
```

**Expected Output:**
```bash
# kubectl get jobs -n ml-platform
NAME             COMPLETIONS   DURATION   AGE
model-training   1/1           45s        1m

# Logs should show successful training completion
==================================================
ML Training Pipeline
==================================================
Started at: 2024-12-30T15:30:00.000000
Model path: /models/model.joblib
...
Model saved successfully!
Training complete!
==================================================
```

### 3.6 Deploy API with HPA

```bash
# Update image reference in api-deployment.yaml
# Change: image: ml-api:v1
# To: image: gcr.io/YOUR_PROJECT/ml-api:v1

kubectl apply -f ../../day6-ml-platform/k8s/api-deployment.yaml -n ml-platform
kubectl apply -f ../../day6-ml-platform/k8s/api-service.yaml -n ml-platform
kubectl apply -f ../../day6-ml-platform/k8s/api-hpa.yaml -n ml-platform

# Wait for rollout
kubectl rollout status deployment/ml-api -n ml-platform
```

**Expected Output:**
```bash
# kubectl get all -n ml-platform
NAME                           READY   STATUS    RESTARTS   AGE
pod/ml-api-abc123def-xyz45     1/1     Running   0          2m
pod/ml-api-abc123def-ghi67     1/1     Running   0          2m

NAME                   TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)        AGE
service/ml-api-service LoadBalancer   10.100.200.31  34.102.136.181  8000:30081/TCP 2m

NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/ml-api    2/2     2            2           2m

NAME                                DESIRED   CURRENT   READY   AGE
replicaset.apps/ml-api-abc123def     2         2         2       2m

NAME                                REFERENCE           TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/ml-api-hpa   Deployment/ml-api   8%/70%   2         5         2          1m
```

### 3.7 Test Your ML API on GKE

```bash
# Get the external IP
kubectl get service ml-api-service -n ml-platform

# Test the API
curl -X POST "http://EXTERNAL_IP:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"values": [100, 105, 103, 108, 110]}'
```

**Expected Output:**
```json
{
  "prediction": 112.34,
  "model_version": "v1",
  "timestamp": "2024-12-30T15:45:00"
}
```

---

## Phase 4: Understanding GKE vs Local Differences (30 mins)

### 4.1 Compare GKE Autopilot Features

```bash
# Check node details (GKE manages nodes)
kubectl describe node

# Check storage classes available
kubectl get storageclass -o wide

# Check cluster events
kubectl get events -n ml-platform --sort-by=.metadata.creationTimestamp | tail -10
```

### 4.2 GKE-Specific Monitoring

```bash
# Check GKE Cloud Monitoring integration
kubectl top nodes
kubectl top pods -n ml-platform

# View logs in GCP Console
# Go to: Kubernetes Engine → Clusters → ml-interview-cluster → Logs
```

---

## 🧹 Cleanup (Important!)

```bash
# Delete your ML platform
kubectl delete namespace ml-platform

# Delete test resources
kubectl delete deployment nginx-test
kubectl delete service nginx-test

# Delete cluster (recreate anytime for free)
gcloud container clusters delete ml-interview-cluster --region=us-central1 --quiet

# Check costs (should still be $0.00)
gcloud billing export projects describe $(gcloud config get-value project)
```

**Expected Output:**
```bash
# gcloud container clusters delete...
Deleting cluster ml-interview-cluster...done.

# Billing check should show $0.00
```

---

## ✅ Day 4 Checkpoint

You should be able to:

- [ ] Navigate GCP Console confidently
- [ ] Create GKE Autopilot clusters (free!)
- [ ] Deploy complex applications to GKE
- [ ] Use GCP Container Registry for images
- [ ] Understand GKE vs local Kubernetes differences
- [ ] Monitor costs and stay within free tier

---

## 📝 Key Takeaways

1. **GKE Autopilot is FREE** for learning - perfect for interviews
2. **Container Registry** is free for storage, minimal pull costs
3. **Always set budget alerts** to avoid surprise bills
4. **GKE manages nodes** - you focus on applications
5. **Same kubectl commands** work on GKE as local clusters

---

## 🔗 Next Steps

**Day 5:** Deploy JupyterHub to GKE with authentication
**Day 6:** Production patterns and troubleshooting on GCP

---

**Time: ~4 hours | Cost: $0.00 (Free tier only)**
