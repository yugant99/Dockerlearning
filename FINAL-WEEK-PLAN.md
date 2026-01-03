# 🎯 Final Week Interview Prep Plan
## Dodona Data - GCP + Kubernetes + Jupyter

**Constraints:** MacBook Air M3, No GCP credentials
**Goal:** Be interview-ready for K8s + GCP + Jupyter discussions

---

## 📊 Current Status

| Day | Topic | Status | Confidence |
|-----|-------|--------|------------|
| 1 | K8s Fundamentals | ✅ Done | 4/5 |
| 2 | Core Concepts | ✅ Done | 4/5 |
| 3 | Deep Dive | ✅ Done | 4/5 |
| 4 | GCP/GKE | ⚠️ Theory only | 3/5 |
| 5 | JupyterHub | ✅ Conceptual | 4/5 |
| 6 | ML Platform | ✅ Local hands-on | 4/5 |
| 7 | Interview Prep | ❌ Not started | 0/5 |

---

## 📅 This Week's Schedule

### Day 1-2: Review & Strengthen Foundations (4 hours)

**Morning:** Re-read these theory files:
- [ ] `theory/01-why-kubernetes.md` (30 min)
- [ ] `theory/02-pods-deep-dive.md` (30 min)
- [ ] `theory/03-storage-networking.md` (30 min)

**Afternoon:** GCP/GKE concepts (even without hands-on):
- [ ] `theory/04-gcp-fundamentals.md` (45 min)
- [ ] `theory/05-gke-deep-dive.md` (45 min)

**Key Interview Topics to Master:**
```
1. K8s architecture (control plane vs worker nodes)
2. Pod lifecycle and states
3. Service types (ClusterIP, NodePort, LoadBalancer)
4. PV vs PVC relationship
5. GKE Autopilot vs Standard clusters
```

---

### Day 3-4: ML & Jupyter Focus (4 hours)

**Why:** This is likely their main interest (data science platform)

**Read:**
- [ ] `theory/06-jobs-cronjobs.md` (30 min)
- [ ] `theory/07-hpa-autoscaling.md` (30 min)
- [ ] `theory/08-ml-on-kubernetes.md` (45 min)
- [ ] `practical/day5-jupyter-gke/README.md` (30 min) - Interview guide
- [ ] `practical/day6-ml-platform/README.md` (45 min)

**Practice Explaining:**
```
1. "How would you deploy JupyterHub for 50 data scientists?"
2. "How do you train ML models on Kubernetes?"
3. "How do you handle model serving with autoscaling?"
4. "What's the difference between Jobs and Deployments?"
```

---

### Day 5: Troubleshooting & Production (3 hours)

**Key Scenarios to Know:**
| Issue | Debug Command | What to Look For |
|-------|---------------|------------------|
| Pod Pending | `kubectl describe pod` | Resource requests, node capacity |
| CrashLoopBackOff | `kubectl logs --previous` | Application errors |
| ImagePullBackOff | `kubectl describe pod` | Wrong image name, registry auth |
| Service no endpoints | `kubectl get endpoints` | Label selector mismatch |
| OOM Killed | `kubectl describe pod` | Memory limits too low |

**Practice:**
- [ ] Read `practical/day6-gcp-production/README.md` for scenarios
- [ ] Memorize the troubleshooting cheat sheet

---

### Day 6: Interview Question Prep (4 hours)

**Architecture Questions:**
```
Q: Explain Kubernetes architecture.
A: K8s has a control plane (API server for all communication, etcd for 
   state storage, scheduler for pod placement, controller manager for 
   desired state) and worker nodes (kubelet runs pods, kube-proxy handles 
   networking). All communication goes through the API server.

Q: What happens when you run kubectl apply?
A: kubectl sends YAML to API server → validates and stores in etcd → 
   scheduler assigns to node → kubelet on node pulls image and starts 
   container → kube-proxy sets up networking.

Q: How does a Deployment differ from a Pod?
A: Pods are ephemeral. Deployments manage pod replicas, handle rolling 
   updates, maintain desired state, and auto-heal failed pods.
```

**GCP/GKE Questions:**
```
Q: GKE Autopilot vs Standard?
A: Autopilot: Google manages nodes, pay per pod, simpler but less control.
   Standard: You manage node pools, more flexibility, better for specific 
   workloads like GPU or custom node configurations.

Q: How do you connect GKE to other GCP services?
A: Workload Identity - maps K8s service accounts to GCP service accounts.
   No need for JSON keys, more secure.

Q: What storage options does GKE support?
A: Persistent Disks (block storage), Filestore (NFS), Cloud Storage (GCS) 
   via CSI drivers or sidecar containers.
```

**JupyterHub Questions:**
```
Q: How would you deploy Jupyter for a data science team?
A: JupyterHub on Kubernetes via Helm chart. Each user gets their own pod 
   with resource limits. OAuth for auth, PVCs for persistent storage, 
   idle culling to save costs. Profile selection for different 
   environments (CPU vs GPU).

Q: How do you handle GPU notebooks?
A: Separate node pool with GPU instances, taints to prevent non-GPU pods.
   JupyterHub profile with GPU resource request and toleration.
```

**ML Platform Questions:**
```
Q: How do you train models on Kubernetes?
A: Kubernetes Jobs for one-time training, CronJobs for scheduled retraining.
   Models saved to PVC, loaded by serving deployment. HPA scales serving 
   pods based on CPU/request rate.

Q: How do you update a model without downtime?
A: Rolling deployment of new serving pods, or blue-green with service 
   selector switch. Version models in PVC paths (/models/v1, /models/v2).
```

---

### Day 7: Mock Interview & Rest (3 hours)

**Morning (2 hours):**
- [ ] Talk through your ML platform architecture out loud
- [ ] Practice whiteboarding (paper is fine)
- [ ] Time yourself explaining concepts (aim for 2-3 min each)

**Afternoon:**
- [ ] Light review of weak areas
- [ ] Rest and mental prep
- [ ] Prepare questions to ask them!

**Questions to Ask Them:**
```
1. "What does your current Kubernetes infrastructure look like?"
2. "How do data scientists currently access Jupyter notebooks?"
3. "What's the biggest challenge with your ML infrastructure?"
4. "What would my first project be?"
```

---

## 🎤 Key Soundbites (Memorize These)

### On Kubernetes:
> "Kubernetes solves the problem of running containers at scale. It handles scheduling, self-healing, rolling updates, and service discovery automatically."

### On GKE:
> "GKE is managed Kubernetes - Google handles the control plane, upgrades, and security patches. Autopilot goes further by managing nodes too, so you just define pods."

### On JupyterHub:
> "JupyterHub on Kubernetes provides isolated environments per user with resource limits. It scales dynamically - users get pods when they login, and idle pods get culled to save costs."

### On ML Platforms:
> "For ML on Kubernetes, I use Jobs for training, Deployments for serving, and PVCs for model storage. HPA handles inference scaling, and CronJobs automate retraining."

---

## ✅ Pre-Interview Checklist

- [ ] Can explain K8s architecture in 2 minutes
- [ ] Know the difference between Pod, Deployment, Service, Job
- [ ] Can describe JupyterHub architecture
- [ ] Know GKE Autopilot vs Standard trade-offs
- [ ] Can troubleshoot common K8s issues
- [ ] Have 3 questions ready to ask them
- [ ] Got good sleep!

---

## 📚 Quick Reference Files

| Need to Review | File |
|---------------|------|
| K8s basics | `theory/01-why-kubernetes.md` |
| Pod details | `theory/02-pods-deep-dive.md` |
| GCP overview | `theory/04-gcp-fundamentals.md` |
| GKE specifics | `theory/05-gke-deep-dive.md` |
| JupyterHub | `practical/day5-jupyter-gke/README.md` |
| ML platform | `practical/day6-ml-platform/README.md` |
| Troubleshooting | `practical/day6-gcp-production/README.md` |

---

**You've got this! The hands-on work you've done locally teaches the same concepts as cloud deployment. Focus on being able to explain WHY, not just WHAT.** 🚀

