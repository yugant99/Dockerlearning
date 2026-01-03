# 🚀 Day 5: Deploy JupyterHub to GKE with Authentication (4 hours)

## 🎯 Goal
Deploy JupyterHub on GKE with Google OAuth authentication, persistent storage, and GPU support for data science workloads.

---

## 📋 Prerequisites

- Day 4 GKE cluster running
- Helm installed locally
- kubectl connected to GKE
- Basic understanding of JupyterHub concepts

---

## Phase 1: Install Helm and Add JupyterHub Repo (30 mins)

### 1.1 Install Helm on Mac M3

```bash
# Check if Helm is installed
helm version

# If not installed, install via Homebrew
brew install helm

# Verify installation
helm version
```

**Expected Output:**
```bash
version.BuildInfo{Version:"v3.15.2", GitCommit:"1a500d562a9", ...}
```

### 1.2 Add JupyterHub Helm Repository

```bash
# Add the JupyterHub Helm repository
helm repo add jupyterhub https://hub.jupyter.org/helm-chart/
helm repo update

# Verify the repo was added
helm search repo jupyterhub
```

**Expected Output:**
```bash
NAME                    CHART VERSION   APP VERSION     DESCRIPTION
jupyterhub/jupyterhub   3.3.8          4.1.5          Multi-user Jupyter installation
```

### 1.3 Create Namespace for JupyterHub

```bash
# Create dedicated namespace
kubectl create namespace jupyterhub

# Verify namespace
kubectl get namespaces
```

---

## Phase 2: Configure JupyterHub for GKE (60 mins)

### 2.1 Create Helm Values File

Create `jupyterhub-values.yaml`:

```yaml
# JupyterHub configuration for GKE
hub:
  image:
    name: jupyterhub/k8s-hub
    tag: "4.1.5"
  db:
    type: sqlite-pvc
    pvc:
      storageClassName: standard-rwo  # GKE optimized storage
      accessModes:
        - ReadWriteOnce
      storage: 1Gi
  config:
    JupyterHub:
      authenticator_class: oauthenticator.GoogleOAuthenticator
      GoogleOAuthenticator:
        client_id: "your-google-oauth-client-id"
        client_secret: "your-google-oauth-client-secret"
        oauth_callback_url: "https://your-domain/hub/oauth_callback"
        hosted_domain: "your-domain.com"  # Optional: restrict to domain
        login_service: "Google"

proxy:
  service:
    type: LoadBalancer  # GKE LoadBalancer for external access
  chp:
    resources:
      requests:
        cpu: 200m
        memory: 512Mi
      limits:
        cpu: 500m
        memory: 1Gi

singleuser:
  image:
    name: jupyter/scipy-notebook
    tag: "2024-08-17"
  cpu:
    limit: 2
    guarantee: 0.5
  memory:
    limit: "4Gi"
    guarantee: "1Gi"
  storage:
    type: dynamic
    homeMountPath: /home/jovyan
    dynamic:
      storageClass: standard-rwo
      pvcNameTemplate: claim-{username}
      volumeNameTemplate: volume-{username}
      capacity: 5Gi

cull:
  enabled: true
  timeout: 3600  # 1 hour idle timeout
  every: 300     # Check every 5 minutes

ingress:
  enabled: true
  hosts:
    - your-jupyterhub-domain.com
  tls:
    - secretName: jupyterhub-tls
      hosts:
        - your-jupyterhub-domain.com
```

### 2.2 Set Up Google OAuth (Required for Authentication)

**Step 1: Create Google OAuth Credentials**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
4. Choose **Web application**
5. Add authorized redirect URIs:
   - `https://your-domain/hub/oauth_callback`
   - `http://localhost:8000/hub/oauth_callback` (for local testing)

**Step 2: Update values.yaml**

Replace in `jupyterhub-values.yaml`:
- `client_id`: Your OAuth client ID
- `client_secret`: Your OAuth client secret
- `oauth_callback_url`: Your domain callback URL

### 2.3 Configure Custom Data Science Environment

Create `singleuser-profileList.yaml`:

```yaml
singleuser:
  profileList:
    - display_name: "Data Science Environment"
      description: "Full data science stack with ML libraries"
      default: true
      kubespawner_override:
        image: gcr.io/your-project/jupyter-datascience:v1
        cpu_limit: 2
        mem_limit: "4Gi"
        cpu_guarantee: 0.5
        mem_guarantee: "1Gi"

    - display_name: "GPU Environment (Experimental)"
      description: "GPU-enabled environment for deep learning"
      kubespawner_override:
        image: gcr.io/your-project/jupyter-gpu:v1
        cpu_limit: 4
        mem_limit: "8Gi"
        cpu_guarantee: 1
        mem_guarantee: "2Gi"
        extra_resource_limits:
          nvidia.com/gpu: "1"
```

---

## Phase 3: Build Custom Jupyter Images (45 mins)

### 3.1 Create Custom Data Science Image

Create `Dockerfile.datascience`:

```dockerfile
FROM jupyter/scipy-notebook:latest

USER root

# Install additional data science packages
RUN pip install --no-cache-dir \
    pandas \
    scikit-learn \
    matplotlib \
    seaborn \
    plotly \
    xgboost \
    lightgbm \
    tensorflow \
    torch \
    torchvision \
    google-cloud-bigquery \
    google-cloud-storage \
    google-cloud-aiplatform

# Install system packages
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

USER jovyan

# Set working directory
WORKDIR /home/jovyan/work
```

### 3.2 Build and Push to GCR

```bash
# Build for x86_64 (GKE architecture)
docker buildx build --platform linux/amd64 \
  -f Dockerfile.datascience \
  -t gcr.io/$(gcloud config get-value project)/jupyter-datascience:v1 \
  --push .

# Verify image was pushed
gcloud container images list-tags gcr.io/$(gcloud config get-value project)/jupyter-datascience
```

**Expected Output:**
```bash
DIGEST        TAGS    TIMESTAMP
abc123...     v1      2025-01-02T20:30:00
```

### 3.3 Optional: GPU-Enabled Image

Create `Dockerfile.gpu`:

```dockerfile
FROM gcr.io/deeplearning-platform-release/tf-gpu.2-11

USER root

# Install Jupyter and additional packages
RUN pip install --no-cache-dir \
    jupyterhub \
    jupyterlab \
    pandas \
    scikit-learn

# Switch back to user
USER jupyter
```

---

## Phase 4: Deploy JupyterHub to GKE (60 mins)

### 4.1 Deploy with Helm

```bash
# Install JupyterHub with custom values
helm upgrade --install jupyterhub jupyterhub/jupyterhub \
  --namespace jupyterhub \
  --values jupyterhub-values.yaml \
  --values singleuser-profileList.yaml \
  --wait \
  --timeout 600s
```

**Expected Output:**
```bash
Release "jupyterhub" does not exist. Installing it now.
NAME: jupyterhub
LAST DEPLOYED: Thu Jan  2 20:45:30 2025
NAMESPACE: jupyterhub
STATUS: deployed
REVISION: 1
TEST SUITE: None
```

### 4.2 Verify Deployment

```bash
# Check all resources
kubectl get all -n jupyterhub

# Check LoadBalancer service
kubectl get service -n jupyterhub -w
```

**Expected Output:**
```bash
NAME                       READY   STATUS    RESTARTS   AGE
pod/hub-abc123def-xyz45     1/1     Running   0          2m
pod/proxy-abc123def-xyz45   1/1     Running   0          2m

NAME               TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
service/proxy-public LoadBalancer   10.100.200.30   <pending>     80:30080/TCP     2m

NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/hub   1/1     1            1           2m
deployment.apps/proxy 1/1     1            1           2m
```

### 4.3 Wait for External IP

```bash
# Wait for LoadBalancer to get external IP (takes 2-5 minutes)
kubectl get service proxy-public -n jupyterhub -w
```

**Expected Output:**
```bash
NAME           TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)          AGE
proxy-public   LoadBalancer   10.100.200.30   35.202.122.12   80:30080/TCP     5m
```

### 4.4 Test JupyterHub Access

```bash
# Open JupyterHub in browser
EXTERNAL_IP=$(kubectl get service proxy-public -n jupyterhub -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "JupyterHub URL: http://$EXTERNAL_IP"

# Or open directly
open http://$EXTERNAL_IP
```

**Expected Result:**
- JupyterHub login page with Google OAuth
- After authentication, user spawns personal Jupyter server
- Pre-configured data science environment with custom packages

---

## Phase 5: Configure Advanced Features (45 mins)

### 5.1 Set Up Persistent Storage per User

```yaml
# Add to jupyterhub-values.yaml
singleuser:
  storage:
    type: dynamic
    extraVolumes:
      - name: user-data
        persistentVolumeClaim:
          claimName: '{username}-data'
    extraVolumeMounts:
      - name: user-data
        mountPath: /home/jovyan/data
```

### 5.2 Configure Resource Limits per User

```yaml
# Add to jupyterhub-values.yaml
singleuser:
  profileList:
    - display_name: "Basic User"
      kubespawner_override:
        cpu_limit: 1
        mem_limit: "2Gi"
        cpu_guarantee: 0.2
        mem_guarantee: "512Mi"

    - display_name: "Power User"
      kubespawner_override:
        cpu_limit: 4
        mem_limit: "8Gi"
        cpu_guarantee: 1
        mem_guarantee: "2Gi"
        extra_resource_limits:
          nvidia.com/gpu: "1"
```

### 5.3 Enable GPU Support

```yaml
# Add GPU node pool first
gcloud container node-pools create gpu-pool \
    --cluster $(kubectl config current-context | cut -d'_' -f4) \
    --region us-central1 \
    --machine-type n1-standard-8 \
    --accelerator type=nvidia-tesla-t4,count=1 \
    --num-nodes 1 \
    --enable-autoscaling \
    --min-nodes 0 \
    --max-nodes 3

# Then add GPU toleration to values.yaml
singleuser:
  extraTolerations:
    - key: "nvidia.com/gpu"
      operator: "Exists"
      effect: "NoSchedule"
```

---

## Phase 6: Monitoring and Scaling (30 mins)

### 6.1 Set Up Basic Monitoring

```bash
# Enable Cloud Monitoring for JupyterHub namespace
# GCP Console → Kubernetes Engine → Clusters → your-cluster
# Enable "Cloud Monitoring" for jupyterhub namespace

# Check resource usage
kubectl top pods -n jupyterhub
kubectl top nodes
```

### 6.2 Configure Auto-scaling

```yaml
# Add to jupyterhub-values.yaml for user pod autoscaling
hub:
  config:
    JupyterHub:
      services:
        - name: cull
          admin: true
          command:
            - python
            - -m
            - jupyterhub.services.cull
            - --cull-every=300
            - --timeout=3600
```

### 6.3 View Logs

```bash
# Hub logs
kubectl logs -f deployment/hub -n jupyterhub

# User server logs
kubectl logs -f deployment/user-scheduler -n jupyterhub

# GCP Cloud Logging
# GCP Console → Logging → Logs Explorer
# Filter: resource.labels.namespace_name="jupyterhub"
```

---

## 🧹 Cleanup

```bash
# Delete JupyterHub
helm uninstall jupyterhub -n jupyterhub

# Delete namespace
kubectl delete namespace jupyterhub

# Delete GPU node pool (if created)
gcloud container node-pools delete gpu-pool \
    --cluster your-cluster-name \
    --region us-central1

# Check costs
gcloud billing export projects describe $(gcloud config get-value project)
```

---

## ✅ Day 5 Checkpoint

You should be able to:

- [ ] Install and configure Helm
- [ ] Deploy JupyterHub to GKE with LoadBalancer
- [ ] Set up Google OAuth authentication
- [ ] Create custom data science Docker images
- [ ] Configure persistent storage per user
- [ ] Access JupyterHub via external IP
- [ ] Understand user pod scaling and resource limits

---

## 🎯 Key JupyterHub Concepts Learned

1. **Multi-user architecture**: Hub, Proxy, User servers
2. **OAuth integration**: Google authentication for enterprise
3. **Resource management**: CPU/memory limits per user
4. **Persistent storage**: User data persistence across sessions
5. **Custom images**: Data science environments with specific packages
6. **GKE integration**: LoadBalancers, storage classes, node pools

---

## 🔗 Next Steps

**Day 6:** Production patterns and advanced troubleshooting
**Interview Prep:** Practice explaining your JupyterHub deployment

---

**Time: ~4 hours | Cost: ~$0.05/hour (LoadBalancer) | Skills: Multi-user platforms, OAuth, container orchestration**
