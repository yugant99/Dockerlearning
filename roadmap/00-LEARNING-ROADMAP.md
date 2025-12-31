# 🚀 Kubernetes + GCP + Jupyter Interview Prep Roadmap
## Dodona Data - Toronto | 7-Day Intensive Plan

---

## 📅 Schedule Overview (7 Days × 7-8 Hours)

| Day | Focus Area | Hours | Key Outcomes |
|-----|-----------|-------|--------------|
| **Day 1** | Docker Refresh + K8s Fundamentals | 8h | Understand containers → orchestration |
| **Day 2** | Kubernetes Core Concepts | 8h | Pods, Deployments, Services mastery |
| **Day 3** | Kubernetes Deep Dive | 7h | ConfigMaps, Secrets, Volumes, Networking |
| **Day 4** | GCP Fundamentals + GKE Setup | 8h | GCP console, GKE cluster creation |
| **Day 5** | Jupyter on Kubernetes | 7h | JupyterHub deployment, GPU config |
| **Day 6** | Production Patterns + Troubleshooting | 8h | Monitoring, logging, debugging |
| **Day 7** | Interview Prep + Mock Scenarios | 7h | Common questions, hands-on demos |

**Total: ~53 hours**

---

## 🎯 Day 1: Docker Refresh + Kubernetes Fundamentals (8 hours)

### Morning Session (4 hours)
- [ ] **Hour 1-2:** Docker Quick Refresh
  - Container lifecycle (build, run, stop, rm)
  - Dockerfile best practices
  - Docker Compose basics
  - **Practical:** Build a simple Python/Jupyter container

- [ ] **Hour 3-4:** Why Kubernetes?
  - The problem K8s solves (scaling, self-healing, rollouts)
  - Architecture overview: Control Plane vs Worker Nodes
  - Key components: API Server, etcd, Scheduler, Controller Manager, Kubelet
  - **Read:** `theory/01-why-kubernetes.md`

### Afternoon Session (4 hours)
- [ ] **Hour 5-6:** Setting Up Local K8s
  - Install minikube on M3 Mac
  - Understanding kubectl
  - First cluster creation
  - **Practical:** `practical/day1-setup/`

- [ ] **Hour 7-8:** Your First K8s Deployment
  - Creating a Pod manually
  - Understanding YAML manifests
  - kubectl basics: get, describe, logs, exec
  - **Checkpoint:** Deploy nginx, access it locally

### 📋 Day 1 Checkpoint
```
✅ Can explain Docker vs K8s difference
✅ Minikube running locally
✅ Deployed first pod
✅ Can use kubectl get/describe/logs
```

---

## 🎯 Day 2: Kubernetes Core Concepts (8 hours)

### Morning Session (4 hours)
- [ ] **Hour 1-2:** Pods Deep Dive
  - Pod anatomy and lifecycle
  - Multi-container pods (sidecar, init containers)
  - Resource requests and limits
  - **Read:** `theory/02-pods-deep-dive.md`

- [ ] **Hour 3-4:** Deployments & ReplicaSets
  - Why not run Pods directly?
  - Deployment strategies (RollingUpdate, Recreate)
  - Scaling applications
  - **Practical:** Deploy a scalable web app

### Afternoon Session (4 hours)
- [ ] **Hour 5-6:** Services & Networking
  - ClusterIP, NodePort, LoadBalancer
  - Service discovery and DNS
  - Exposing applications
  - **Practical:** Expose your deployment

- [ ] **Hour 7-8:** Namespaces & Labels
  - Organizing workloads
  - Label selectors
  - Resource quotas
  - **Practical:** Create dev/staging namespaces

### 📋 Day 2 Checkpoint
```
✅ Can create Deployment from scratch
✅ Understand scaling (kubectl scale)
✅ Can expose services
✅ Understand namespace isolation
```

---

## 🎯 Day 3: Kubernetes Deep Dive (7 hours)

### Morning Session (3.5 hours)
- [ ] **Hour 1-2:** ConfigMaps & Secrets
  - Externalizing configuration
  - Creating and mounting ConfigMaps
  - Secret management best practices
  - **Practical:** Configure an app with env vars

- [ ] **Hour 3-3.5:** Persistent Storage
  - PersistentVolumes (PV) and PersistentVolumeClaims (PVC)
  - Storage classes
  - StatefulSets introduction
  - **Read:** `theory/03-storage-networking.md`

### Afternoon Session (3.5 hours)
- [ ] **Hour 4-5:** Kubernetes Networking
  - Pod-to-Pod communication
  - Ingress controllers
  - Network policies basics
  - **Practical:** Set up Ingress for your app

- [ ] **Hour 6-7:** Jobs & CronJobs
  - Batch processing in K8s
  - Job parallelism
  - Scheduled tasks
  - **Practical:** Create a data processing job

### 📋 Day 3 Checkpoint
```
✅ Can inject config via ConfigMaps
✅ Understand PV/PVC relationship
✅ Can set up basic Ingress
✅ Can schedule CronJobs
```

---

## 🎯 Day 4: GCP Fundamentals + GKE (8 hours)

### Morning Session (4 hours)
- [ ] **Hour 1-2:** GCP Overview
  - GCP Console navigation
  - Projects, IAM, and billing
  - Key services: Compute, Storage, GKE, BigQuery
  - **Read:** `theory/04-gcp-fundamentals.md`

- [ ] **Hour 3-4:** Google Kubernetes Engine (GKE)
  - GKE vs self-managed K8s
  - Autopilot vs Standard clusters
  - Node pools and autoscaling
  - **Practical:** Create your first GKE cluster (free tier)

### Afternoon Session (4 hours)
- [ ] **Hour 5-6:** GKE Networking & Security
  - VPC-native clusters
  - Workload Identity
  - Private clusters
  - **Read:** `theory/05-gke-deep-dive.md`

- [ ] **Hour 7-8:** GCP Storage + GKE
  - Cloud Storage (GCS) buckets
  - Persistent Disks with GKE
  - Connecting to Cloud SQL
  - **Practical:** Deploy app with GCS backend

### 📋 Day 4 Checkpoint
```
✅ Can navigate GCP Console
✅ Created GKE cluster
✅ Understand Autopilot vs Standard
✅ Can connect GKE to GCS
```

---

## 🎯 Day 5: Jupyter on Kubernetes (7 hours)

### Morning Session (3.5 hours)
- [ ] **Hour 1-2:** JupyterHub Architecture
  - Hub, Proxy, and single-user servers
  - Why K8s for Jupyter?
  - Zero to JupyterHub project
  - **Read:** `theory/06-jupyter-on-kubernetes.md`

- [ ] **Hour 3-3.5:** Deploying JupyterHub on Minikube
  - Helm charts introduction
  - JupyterHub Helm chart
  - Basic configuration
  - **Practical:** Local JupyterHub deployment

### Afternoon Session (3.5 hours)
- [ ] **Hour 4-5:** JupyterHub on GKE
  - Production configuration
  - Authentication (Google OAuth)
  - Resource management per user
  - **Practical:** Deploy JupyterHub to GKE

- [ ] **Hour 6-7:** Data Science Workflows
  - Custom Docker images for Jupyter
  - GPU support on GKE
  - Connecting to BigQuery/GCS
  - **Practical:** Create custom data science environment

### 📋 Day 5 Checkpoint
```
✅ JupyterHub running on minikube
✅ Understand Helm basics
✅ Can configure user resources
✅ Know GPU provisioning concepts
```

---

## 🎯 Day 6: Production Patterns & Troubleshooting (8 hours)

### Morning Session (4 hours)
- [ ] **Hour 1-2:** Monitoring & Observability
  - Kubernetes metrics
  - Prometheus & Grafana basics
  - GKE Cloud Monitoring
  - **Read:** `theory/07-monitoring-logging.md`

- [ ] **Hour 3-4:** Logging & Debugging
  - kubectl logs deep dive
  - Container debugging
  - GKE Cloud Logging
  - **Practical:** Debug a failing deployment

### Afternoon Session (4 hours)
- [ ] **Hour 5-6:** CI/CD for Kubernetes
  - GitOps concepts
  - Cloud Build with GKE
  - Deployment automation
  - **Read:** `theory/08-cicd-patterns.md`

- [ ] **Hour 7-8:** Troubleshooting Scenarios
  - Pod stuck in Pending/CrashLoopBackOff
  - Service not accessible
  - Resource exhaustion
  - **Practical:** Fix broken deployments

### 📋 Day 6 Checkpoint
```
✅ Can read and interpret metrics
✅ Know debugging workflow
✅ Understand CI/CD for K8s
✅ Can troubleshoot common issues
```

---

## 🎯 Day 7: Interview Prep & Mock Scenarios (7 hours)

### Morning Session (3.5 hours)
- [ ] **Hour 1-2:** Common Interview Questions
  - K8s architecture questions
  - GCP/GKE specific questions
  - Jupyter deployment scenarios
  - **Read:** `theory/09-interview-questions.md`

- [ ] **Hour 3-3.5:** Whiteboard/Design Scenarios
  - "Design a scalable Jupyter platform"
  - "How would you handle 1000 concurrent users?"
  - "Explain your deployment strategy"

### Afternoon Session (3.5 hours)
- [ ] **Hour 4-5:** Hands-on Demo Prep
  - Prepare a live demo
  - Quick deployment scripts
  - Talking points while deploying

- [ ] **Hour 6-7:** Final Review
  - Review all checkpoints
  - Key terminology flashcards
  - Rest and mental prep

### 📋 Day 7 Checkpoint
```
✅ Can answer 20 common K8s questions
✅ Have demo ready
✅ Confident in terminology
✅ Ready to crush it! 🎯
```

---

## 🛠️ Quick Reference Commands

```bash
# Minikube
minikube start --driver=docker
minikube status
minikube dashboard

# kubectl basics
kubectl get pods -A
kubectl describe pod <name>
kubectl logs <pod> -f
kubectl exec -it <pod> -- /bin/sh

# Deployments
kubectl create deployment nginx --image=nginx
kubectl scale deployment nginx --replicas=3
kubectl rollout status deployment/nginx

# Services
kubectl expose deployment nginx --port=80 --type=NodePort
kubectl get svc

# GKE (gcloud)
gcloud container clusters create my-cluster
gcloud container clusters get-credentials my-cluster
```

---

## 📚 File Structure

```
dockerlearning/
├── roadmap/
│   └── 00-LEARNING-ROADMAP.md (this file)
├── theory/
│   ├── 01-why-kubernetes.md
│   ├── 02-pods-deep-dive.md
│   ├── 03-storage-networking.md
│   ├── 04-gcp-fundamentals.md
│   ├── 05-gke-deep-dive.md
│   ├── 06-jupyter-on-kubernetes.md
│   ├── 07-monitoring-logging.md
│   ├── 08-cicd-patterns.md
│   └── 09-interview-questions.md
├── practical/
│   ├── day1-setup/
│   ├── day2-core-concepts/
│   ├── day3-deep-dive/
│   ├── day4-gcp-gke/
│   ├── day5-jupyter/
│   └── day6-production/
└── checkpoints/
    └── daily-progress.md
```

---

## 💡 Pro Tips for the Interview

1. **Always explain WHY** - Don't just say what K8s does, explain why it matters
2. **Use real examples** - Reference your hands-on experience
3. **Acknowledge trade-offs** - "Autopilot is easier but less flexible..."
4. **Ask clarifying questions** - Shows you think about requirements
5. **Stay calm with unknowns** - "I'd research that, but my approach would be..."

---

**Let's get started! 🚀**

First step: Install minikube and get your local K8s running.

