# 🧪 Lab: Deploying Jupyter on Kubernetes
## Day 5 | Duration: ~90 minutes

---

## Why Jupyter on Kubernetes?

For data companies like Dodona Data:
- **Scalable** - Spin up notebooks on demand
- **Isolated** - Each user gets their own environment
- **Managed** - Auto-scaling, resource limits
- **GPU Access** - Schedule notebooks on GPU nodes

---

## ✅ Prerequisites
```bash
minikube start --memory=4096 --cpus=2
cd ~/dockerlearning/practical
mkdir -p day5-jupyter && cd day5-jupyter
```

---

## Part 1: Simple Single Jupyter Notebook

### Step 1.1: Deploy Basic Jupyter

```bash
nano jupyter-simple.yaml
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jupyter-notebook
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jupyter
  template:
    metadata:
      labels:
        app: jupyter
    spec:
      containers:
      - name: jupyter
        image: jupyter/scipy-notebook:latest
        ports:
        - containerPort: 8888
        env:
        - name: JUPYTER_TOKEN
          value: "mysecrettoken"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: notebooks
          mountPath: /home/jovyan/work
      volumes:
      - name: notebooks
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: jupyter-service
spec:
  selector:
    app: jupyter
  type: NodePort
  ports:
  - port: 8888
    targetPort: 8888
    nodePort: 30888
```

### Step 1.2: Apply & Wait

```bash
kubectl apply -f jupyter-simple.yaml
```

```bash
kubectl get pods -w
```

Wait for Running status (image pull takes a minute).

### Step 1.3: Access Jupyter!

```bash
minikube service jupyter-service
```

**Browser opens!**

**Login with token:** `mysecrettoken`

### Step 1.4: Test It

1. Click "New" → "Python 3"
2. Run: `import numpy as np; print(np.random.rand(5))`
3. It works! 🎉

---

## Part 2: Jupyter with Persistent Storage

### Step 2.1: Create Persistent Jupyter

```bash
nano jupyter-persistent.yaml
```

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: jupyter-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jupyter-persistent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jupyter-persistent
  template:
    metadata:
      labels:
        app: jupyter-persistent
    spec:
      containers:
      - name: jupyter
        image: jupyter/datascience-notebook:latest
        ports:
        - containerPort: 8888
        env:
        - name: JUPYTER_TOKEN
          value: "datatoken123"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: notebooks
          mountPath: /home/jovyan/work
      volumes:
      - name: notebooks
        persistentVolumeClaim:
          claimName: jupyter-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: jupyter-persistent-svc
spec:
  selector:
    app: jupyter-persistent
  type: NodePort
  ports:
  - port: 8888
    targetPort: 8888
    nodePort: 30889
```

### Step 2.2: Apply

```bash
kubectl apply -f jupyter-persistent.yaml
```

### Step 2.3: Access & Create Notebook

```bash
minikube service jupyter-persistent-svc
```

**Token:** `datatoken123`

1. Create a new notebook
2. Add some code cells
3. Save it

### Step 2.4: Test Persistence

```bash
# Delete pod (not deployment)
kubectl delete pod -l app=jupyter-persistent
```

```bash
# Wait for new pod
kubectl get pods -w
```

**Access again - your notebook is still there!** 🎉

---

## Part 3: Install Helm (for JupyterHub)

### Step 3.1: Install Helm

```bash
brew install helm
```

### Step 3.2: Verify

```bash
helm version
```

---

## Part 4: Deploy JupyterHub with Helm

### Step 4.1: Add JupyterHub Helm Repo

```bash
helm repo add jupyterhub https://hub.jupyter.org/helm-chart/
helm repo update
```

### Step 4.2: Create Config File

```bash
nano jupyterhub-config.yaml
```

```yaml
# JupyterHub configuration for local minikube
proxy:
  secretToken: "$(openssl rand -hex 32)"
  service:
    type: NodePort
    nodePorts:
      http: 30080
      
singleuser:
  image:
    name: jupyter/scipy-notebook
    tag: latest
  memory:
    limit: 1G
    guarantee: 512M
  cpu:
    limit: 1
    guarantee: 0.5
  storage:
    type: dynamic
    capacity: 1Gi
    
hub:
  config:
    Authenticator:
      admin_users:
        - admin
      allowed_users:
        - user1
        - user2
    DummyAuthenticator:
      password: password123
    JupyterHub:
      authenticator_class: dummy
```

### Step 4.3: Generate Secret Token

```bash
# Generate and update the config
SECRET_TOKEN=$(openssl rand -hex 32)
sed -i '' "s/\$(openssl rand -hex 32)/$SECRET_TOKEN/" jupyterhub-config.yaml
```

Or manually replace the line with a 64-character hex string.

### Step 4.4: Install JupyterHub

```bash
helm upgrade --install jupyterhub jupyterhub/jupyterhub \
    --namespace jupyterhub \
    --create-namespace \
    --values jupyterhub-config.yaml \
    --timeout 10m
```

### Step 4.5: Wait for Deployment

```bash
kubectl get pods -n jupyterhub -w
```

Wait until `hub` and `proxy` pods are Running.

### Step 4.6: Access JupyterHub

```bash
minikube service proxy-public -n jupyterhub
```

**Login:**
- Username: `admin` (or `user1`, `user2`)
- Password: `password123`

### Step 4.7: Test Multi-User

1. Login as `admin`
2. Server starts automatically
3. Create a notebook
4. Open incognito window, login as `user1`
5. Each user has isolated environment!

---

## Part 5: Understanding JupyterHub Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    JupyterHub Cluster                    │
│                                                          │
│   ┌─────────────┐                                       │
│   │    Hub      │ ◄── Manages users, spawns servers    │
│   │   (Pod)     │                                       │
│   └──────┬──────┘                                       │
│          │                                               │
│   ┌──────▼──────┐                                       │
│   │   Proxy     │ ◄── Routes traffic to user servers   │
│   │   (Pod)     │                                       │
│   └──────┬──────┘                                       │
│          │                                               │
│    ┌─────┴─────┬─────────────┐                         │
│    ▼           ▼             ▼                          │
│ ┌──────┐   ┌──────┐     ┌──────┐                       │
│ │User 1│   │User 2│     │User N│  ◄── Each user gets  │
│ │Server│   │Server│     │Server│      their own pod   │
│ │(Pod) │   │(Pod) │     │(Pod) │                       │
│ └──────┘   └──────┘     └──────┘                       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Components:**
- **Hub:** Authentication, user management, spawns servers
- **Proxy:** Routes requests to correct user server
- **User Servers:** Individual Jupyter notebooks per user

---

## Part 6: Custom Jupyter Image

### Step 6.1: Create Custom Dockerfile

```bash
nano Dockerfile
```

```dockerfile
FROM jupyter/scipy-notebook:latest

USER root

# Install system packages
RUN apt-get update && apt-get install -y \
    vim \
    && rm -rf /var/lib/apt/lists/*

USER jovyan

# Install Python packages
RUN pip install --no-cache-dir \
    pandas \
    scikit-learn \
    matplotlib \
    seaborn \
    plotly \
    google-cloud-bigquery \
    google-cloud-storage

# Set working directory
WORKDIR /home/jovyan/work
```

### Step 6.2: Build Image

```bash
# Point Docker to minikube's Docker daemon
eval $(minikube docker-env)

# Build
docker build -t my-jupyter:v1 .
```

### Step 6.3: Use Custom Image

Update your deployment to use `my-jupyter:v1` with `imagePullPolicy: Never`

```yaml
containers:
- name: jupyter
  image: my-jupyter:v1
  imagePullPolicy: Never  # Use local image
```

---

## Part 7: Resource Management for Data Science

### Step 7.1: Set Resource Limits

```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
    # nvidia.com/gpu: 1  # For GPU workloads
  limits:
    memory: "8Gi"
    cpu: "4000m"
    # nvidia.com/gpu: 1
```

### Step 7.2: Understanding Limits

| Resource | Request | Limit | Meaning |
|----------|---------|-------|---------|
| Memory | 2Gi | 8Gi | Guaranteed 2GB, can use up to 8GB |
| CPU | 1 core | 4 cores | Guaranteed 1 core, can burst to 4 |

---

## Part 8: Clean Up

```bash
# Delete JupyterHub
helm uninstall jupyterhub -n jupyterhub
kubectl delete namespace jupyterhub

# Delete simple deployments
kubectl delete -f jupyter-persistent.yaml
kubectl delete -f jupyter-simple.yaml

# Clean up PVC
kubectl delete pvc jupyter-pvc
```

---

## 🎯 What You Learned

✅ Deploying single Jupyter notebook on K8s
✅ Persistent storage for notebooks
✅ Using Helm for complex deployments
✅ JupyterHub for multi-user environments
✅ Building custom Jupyter images
✅ Resource management for data science workloads

---

## 🎯 Interview Talking Points

**"How would you deploy Jupyter for a data team?"**
> "I'd use JupyterHub on Kubernetes. It provides multi-user isolation, automatic scaling, and resource management. Each user gets their own pod with persistent storage. We can use Helm for deployment and customize images with required packages."

**"How do you handle resource allocation for ML workloads?"**
> "Kubernetes lets us set resource requests (guaranteed) and limits (maximum). For GPU workloads, we'd use node pools with GPUs and node selectors. JupyterHub can be configured to spawn different pod types based on user needs."

---

## 🚀 Next Steps

For GKE deployment, you would:
1. Create GKE cluster with appropriate node pools
2. Set up Cloud Storage for persistent notebooks
3. Configure Workload Identity for GCP access
4. Use Cloud Load Balancer for HTTPS
5. Set up Google OAuth for authentication

