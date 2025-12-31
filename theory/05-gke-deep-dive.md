# ☸️ Google Kubernetes Engine (GKE) Deep Dive

## What is GKE?

GKE is Google's **managed Kubernetes service**. Google handles:
- Control plane management (API server, etcd, scheduler)
- Upgrades and security patches
- High availability
- Integration with GCP services

You focus on: **deploying and running your apps**

---

## GKE vs Self-Managed Kubernetes

| Aspect | GKE | Self-Managed |
|--------|-----|--------------|
| Control plane | Google manages | You manage |
| Upgrades | Automatic or scheduled | Manual |
| Scaling | Built-in autoscaling | Configure yourself |
| Cost | Pay per node + management fee | Just compute costs |
| Complexity | Lower | Higher |
| Customization | Some limits | Full control |

---

## GKE Cluster Modes

### 1. Autopilot (Recommended for most cases)

Google manages everything including nodes.

```bash
gcloud container clusters create-auto my-cluster \
    --region=us-central1
```

**Pros:**
- No node management
- Pay per pod (not per node)
- Built-in best practices
- Automatic scaling

**Cons:**
- Less customization
- Some workloads not supported (DaemonSets, host access)
- Slightly higher per-pod cost

### 2. Standard

You manage node pools.

```bash
gcloud container clusters create my-cluster \
    --zone=us-central1-a \
    --num-nodes=3 \
    --machine-type=e2-medium
```

**Pros:**
- Full control over nodes
- Custom machine types
- DaemonSets, privileged containers
- Potentially cheaper at scale

**Cons:**
- More management overhead
- You handle node scaling, upgrades

---

## Creating a GKE Cluster

### Via Console

1. Go to **Kubernetes Engine** → **Clusters**
2. Click **Create**
3. Choose **Autopilot** or **Standard**
4. Configure settings
5. Click **Create**

### Via gcloud

```bash
# Autopilot cluster
gcloud container clusters create-auto my-autopilot \
    --region=us-central1 \
    --project=my-project

# Standard cluster
gcloud container clusters create my-standard \
    --zone=us-central1-a \
    --num-nodes=3 \
    --machine-type=e2-medium \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=5
```

### Connect kubectl to GKE

```bash
# Get credentials (updates ~/.kube/config)
gcloud container clusters get-credentials my-cluster \
    --zone=us-central1-a

# Verify connection
kubectl get nodes
```

---

## Node Pools

Groups of nodes with same configuration.

```
┌─────────────────────────────────────────────────────────┐
│                     GKE Cluster                          │
│                                                          │
│   ┌─────────────────┐      ┌─────────────────┐         │
│   │  Default Pool   │      │   GPU Pool      │         │
│   │  e2-medium (3)  │      │  n1-standard-8  │         │
│   │  General apps   │      │  + Tesla T4     │         │
│   └─────────────────┘      └─────────────────┘         │
│                                                          │
│   ┌─────────────────┐                                   │
│   │ High-Memory Pool│                                   │
│   │  n2-highmem-4   │                                   │
│   │  Data processing│                                   │
│   └─────────────────┘                                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Creating Node Pools

```bash
# Add GPU pool
gcloud container node-pools create gpu-pool \
    --cluster=my-cluster \
    --zone=us-central1-a \
    --machine-type=n1-standard-8 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --num-nodes=1 \
    --enable-autoscaling \
    --min-nodes=0 \
    --max-nodes=3
```

### Using Node Selectors

```yaml
spec:
  nodeSelector:
    cloud.google.com/gke-accelerator: nvidia-tesla-t4
  containers:
  - name: ml-training
    image: my-ml-image
    resources:
      limits:
        nvidia.com/gpu: 1
```

---

## GKE Networking

### VPC-Native Clusters (Default)

Pods get IPs from the VPC subnet (not overlay network).

```
┌──────────────────────────────────────────────────────┐
│                        VPC                            │
│                                                       │
│   Node Subnet: 10.0.0.0/24                           │
│   Pod Subnet:  10.1.0.0/16                           │
│   Service Subnet: 10.2.0.0/20                        │
│                                                       │
│   ┌─────────────────┐                                │
│   │      Node       │                                │
│   │   10.0.0.5      │                                │
│   │                 │                                │
│   │  ┌─────┐ ┌─────┐│                               │
│   │  │Pod 1│ │Pod 2││                               │
│   │  │10.1.│ │10.1.││                               │
│   │  │0.5  │ │0.6  ││                               │
│   │  └─────┘ └─────┘│                                │
│   └─────────────────┘                                │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### Private Clusters

Nodes don't have public IPs. More secure!

```bash
gcloud container clusters create private-cluster \
    --enable-private-nodes \
    --enable-private-endpoint \
    --master-ipv4-cidr=172.16.0.0/28
```

### Cloud Load Balancing

GKE automatically creates GCP load balancers for `LoadBalancer` services:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
```

```bash
kubectl get svc my-service
# EXTERNAL-IP will be a GCP load balancer IP
```

---

## Workload Identity

**The right way** to access GCP services from GKE.

```
┌────────────────────────────────────────────────────────┐
│                                                         │
│   K8s Service Account ──────► GCP Service Account      │
│   (my-k8s-sa)                 (my-gcp-sa@proj.iam)     │
│                                                         │
│   Pod uses K8s SA ────► Gets GCP permissions           │
│                                                         │
└────────────────────────────────────────────────────────┘
```

### Setup

```bash
# 1. Create GCP service account
gcloud iam service-accounts create my-gcp-sa

# 2. Grant GCP permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:my-gcp-sa@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"

# 3. Create K8s service account
kubectl create serviceaccount my-k8s-sa

# 4. Bind them together
gcloud iam service-accounts add-iam-policy-binding \
    my-gcp-sa@PROJECT_ID.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/my-k8s-sa]"

# 5. Annotate K8s SA
kubectl annotate serviceaccount my-k8s-sa \
    iam.gke.io/gcp-service-account=my-gcp-sa@PROJECT_ID.iam.gserviceaccount.com
```

### Using in Pod

```yaml
spec:
  serviceAccountName: my-k8s-sa
  containers:
  - name: my-app
    image: my-app
    # Now has access to GCS!
```

---

## GKE Autoscaling

### 1. Horizontal Pod Autoscaler (HPA)
Scale pods based on metrics.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
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

### 2. Cluster Autoscaler
Add/remove nodes based on demand.

```bash
gcloud container clusters update my-cluster \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=10
```

### 3. Vertical Pod Autoscaler (VPA)
Adjust pod resource requests.

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: my-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  updatePolicy:
    updateMode: Auto
```

---

## GKE + GCP Storage

### Persistent Disks

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: standard-rwo  # GKE default
```

### Storage Classes

| Class | Type | Use Case |
|-------|------|----------|
| standard-rwo | pd-balanced | General purpose |
| premium-rwo | pd-ssd | High performance |
| standard-rwx | Filestore | Shared storage |

### Cloud Storage (GCS) with GKE

Option 1: **GCS FUSE** (mount as filesystem)
```yaml
# Requires gke-gcs-fuse-sidecar
volumes:
- name: gcs
  csi:
    driver: gcsfuse.csi.storage.gke.io
    volumeAttributes:
      bucketName: my-bucket
```

Option 2: **In application** (recommended)
```python
from google.cloud import storage
client = storage.Client()
bucket = client.bucket('my-bucket')
```

---

## Deploying to GKE - Full Example

### 1. Build and Push Image

```bash
# Enable Artifact Registry
gcloud services enable artifactregistry.googleapis.com

# Create repository
gcloud artifacts repositories create my-repo \
    --repository-format=docker \
    --location=us-central1

# Configure Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build and push
docker build -t us-central1-docker.pkg.dev/PROJECT/my-repo/my-app:v1 .
docker push us-central1-docker.pkg.dev/PROJECT/my-repo/my-app:v1
```

### 2. Deploy to GKE

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: us-central1-docker.pkg.dev/PROJECT/my-repo/my-app:v1
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
```

```bash
kubectl apply -f deployment.yaml
kubectl get svc my-app-service  # Get external IP
```

---

## GKE Monitoring

### Cloud Monitoring (Stackdriver)

Automatic metrics for:
- Cluster health
- Node utilization
- Pod metrics
- Container logs

```bash
# Enable
gcloud container clusters update my-cluster \
    --enable-stackdriver-kubernetes
```

### Cloud Logging

```bash
# View logs
gcloud logging read "resource.type=k8s_container" --limit=10

# Or in Console: Logging → Logs Explorer
# Filter: resource.type="k8s_container"
```

---

## Cost Optimization

1. **Use Autopilot** - Pay only for pods, no idle nodes

2. **Spot VMs** (formerly Preemptible)
   ```bash
   gcloud container node-pools create spot-pool \
       --spot
   ```

3. **Right-size nodes** - Match machine types to workloads

4. **Scale to zero** - Use cluster autoscaler min-nodes=0

5. **Committed Use Discounts** - 1 or 3 year commitments

---

## 📝 Essential Commands

```bash
# Cluster management
gcloud container clusters list
gcloud container clusters create NAME
gcloud container clusters delete NAME
gcloud container clusters get-credentials NAME

# Node pools
gcloud container node-pools list --cluster=CLUSTER
gcloud container node-pools create NAME --cluster=CLUSTER
gcloud container node-pools delete NAME --cluster=CLUSTER

# Upgrades
gcloud container clusters upgrade CLUSTER --master
gcloud container node-pools upgrade POOL --cluster=CLUSTER
```

---

## 🎯 Interview Questions

**Q: When would you choose Autopilot vs Standard GKE?**
> Autopilot for most workloads - simpler, cost-effective, best practices built-in. Standard when you need: custom node configurations, DaemonSets, privileged containers, or specific hardware (GPUs with special requirements).

**Q: How do you securely access GCP services from GKE pods?**
> Use Workload Identity. It binds Kubernetes service accounts to GCP service accounts, so pods can access GCP APIs without managing keys. More secure than key files.

**Q: How does GKE handle persistent storage?**
> GKE uses GCP Persistent Disks via CSI driver. Create PVCs with appropriate storage classes (standard-rwo, premium-rwo). For shared storage (RWX), use Filestore.

**Q: How would you set up autoscaling in GKE?**
> Three levels: HPA for pods (scale replicas based on metrics), Cluster Autoscaler for nodes (add/remove based on pending pods), VPA for right-sizing resource requests.

---

**Next: Jobs & CronJobs →**

