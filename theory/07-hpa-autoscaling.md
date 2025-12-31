# 📈 Horizontal Pod Autoscaler (HPA) Deep Dive

## What is HPA?

HPA automatically scales the number of pods based on observed metrics.

```
┌─────────────────────────────────────────────────────────────────┐
│                         HPA in Action                            │
│                                                                  │
│   Traffic ↑↑↑                                                   │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────┐    "CPU > 70%"    ┌─────────────────────┐        │
│   │   HPA   │───────────────────►│  Scale 2 → 5 pods  │        │
│   │ Monitor │                    └─────────────────────┘        │
│   └─────────┘                                                    │
│        │                                                         │
│        ▼                                                         │
│   Traffic ↓↓↓                                                   │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────┐    "CPU < 30%"    ┌─────────────────────┐        │
│   │   HPA   │───────────────────►│  Scale 5 → 2 pods  │        │
│   │ Monitor │                    └─────────────────────┘        │
│   └─────────┘                                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## HPA Components

### 1. Metrics Server
Collects resource metrics from kubelets.

```bash
# Enable in minikube
minikube addons enable metrics-server

# Verify it's running
kubectl get pods -n kube-system | grep metrics

# Check metrics working
kubectl top nodes
kubectl top pods
```

### 2. HPA Controller
Part of kube-controller-manager. Queries metrics, calculates desired replicas.

### 3. Target Deployment
The Deployment (or other scalable resource) to scale.

---

## Basic HPA Configuration

### CPU-Based Scaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
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
        averageUtilization: 70  # Target 70% CPU
```

### Memory-Based Scaling

```yaml
metrics:
- type: Resource
  resource:
    name: memory
    target:
      type: Utilization
      averageUtilization: 80  # Target 80% memory
```

### Multiple Metrics

```yaml
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
```

When using multiple metrics, HPA scales based on whichever requires more replicas.

---

## Target Types

### Utilization (Percentage)
Scale based on percentage of resource request.

```yaml
target:
  type: Utilization
  averageUtilization: 70  # 70% of requested CPU
```

**Requires:** Pods must have resource requests set!

### AverageValue (Absolute)
Scale based on absolute metric value.

```yaml
target:
  type: AverageValue
  averageValue: 500m  # 500 millicores per pod
```

### Value (Total)
Scale based on total value across all pods.

```yaml
target:
  type: Value
  value: 10  # Total value of 10
```

---

## How HPA Calculates Replicas

### The Formula

```
desiredReplicas = ceil(currentReplicas × (currentMetricValue / targetMetricValue))
```

### Example

```
Current state:
- 3 pods running
- Each pod using 90% CPU
- Target: 70% CPU

Calculation:
desiredReplicas = ceil(3 × (90 / 70))
desiredReplicas = ceil(3 × 1.29)
desiredReplicas = ceil(3.87)
desiredReplicas = 4

Result: Scale from 3 to 4 pods
```

---

## Scaling Behavior

### Default Behavior
- **Scale up:** Fast (every 15 seconds)
- **Scale down:** Slow (5-minute stabilization window)

Why slow scale-down? Prevent flapping (rapid scale up/down cycles).

### Custom Behavior

```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
    policies:
    - type: Percent
      value: 10           # Scale down 10% at a time
      periodSeconds: 60   # Every 60 seconds
    - type: Pods
      value: 2            # Or max 2 pods at a time
      periodSeconds: 60
    selectPolicy: Min     # Use the more conservative policy
  
  scaleUp:
    stabilizationWindowSeconds: 0  # Scale up immediately
    policies:
    - type: Percent
      value: 100          # Can double pods
      periodSeconds: 15
    - type: Pods
      value: 4            # Or add max 4 pods
      periodSeconds: 15
    selectPolicy: Max     # Use the more aggressive policy
```

### selectPolicy Options

| Policy | Behavior |
|--------|----------|
| Max | Use policy that changes most replicas |
| Min | Use policy that changes fewest replicas |
| Disabled | Disable scaling in this direction |

---

## Custom Metrics

### Why Custom Metrics?

CPU isn't always the best indicator:
- Queue depth (messages waiting)
- Request latency
- Active connections
- Business metrics (orders per minute)

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Application │────►│ Prometheus  │────►│   Custom    │
│  (exports   │     │  (scrapes)  │     │   Metrics   │
│   metrics)  │     │             │     │   Adapter   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │     HPA     │
                                        │ (queries)   │
                                        └─────────────┘
```

### Custom Metric Example

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: queue-based-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: worker
  minReplicas: 1
  maxReplicas: 20
  metrics:
  - type: External
    external:
      metric:
        name: queue_messages_total
        selector:
          matchLabels:
            queue: jobs
      target:
        type: AverageValue
        averageValue: 30  # 30 messages per pod
```

---

## HPA + Cluster Autoscaler (GKE)

### The Problem

HPA wants more pods, but nodes are full!

```
HPA: "I need 10 pods"
Scheduler: "Only room for 5 on current nodes"
Pods: 5 in Pending state 😢
```

### The Solution: Cluster Autoscaler

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   HPA: "Scale to 10 pods"                                       │
│         │                                                        │
│         ▼                                                        │
│   Scheduler: "5 pods Pending - no room"                         │
│         │                                                        │
│         ▼                                                        │
│   Cluster Autoscaler: "Adding 2 nodes..."                       │
│         │                                                        │
│         ▼                                                        │
│   New nodes ready → Pending pods scheduled ✓                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Enable in GKE

```bash
gcloud container clusters update my-cluster \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=10 \
    --zone=us-central1-a
```

---

## Vertical Pod Autoscaler (VPA)

### HPA vs VPA

| HPA | VPA |
|-----|-----|
| Scales **number** of pods | Scales **size** of pods |
| Horizontal scaling | Vertical scaling |
| More pods, same size | Same pods, more resources |

### When to Use VPA

- Single-replica workloads
- Workloads that can't scale horizontally
- Right-sizing resource requests

### VPA Modes

| Mode | Behavior |
|------|----------|
| Off | Only recommendations, no action |
| Initial | Set on pod creation only |
| Auto | Recreate pods with new resources |

### VPA Example

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: my-app-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  updatePolicy:
    updateMode: Auto
  resourcePolicy:
    containerPolicies:
    - containerName: '*'
      minAllowed:
        cpu: 100m
        memory: 50Mi
      maxAllowed:
        cpu: 1
        memory: 500Mi
```

---

## HPA Best Practices

### 1. Always Set Resource Requests

```yaml
# HPA needs requests to calculate utilization!
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### 2. Set Sensible Min/Max

```yaml
minReplicas: 2   # At least 2 for HA
maxReplicas: 10  # Cap for cost control
```

### 3. Don't Set Target Too High

```yaml
# Bad: 95% target leaves no headroom
averageUtilization: 95

# Good: 70% leaves room for traffic spikes
averageUtilization: 70
```

### 4. Use Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-app-pdb
spec:
  minAvailable: 2  # Always keep at least 2 running
  selector:
    matchLabels:
      app: my-app
```

### 5. Don't Mix HPA with Manual Scaling

```bash
# This will fight with HPA!
kubectl scale deployment my-app --replicas=5

# HPA will override your setting
```

---

## Troubleshooting HPA

### HPA shows "<unknown>" for metrics

```bash
kubectl get hpa
# TARGETS shows <unknown>/70%
```

**Causes:**
1. Metrics server not running
2. Pods don't have resource requests
3. Pods just started (need ~15s for metrics)

**Fix:**
```bash
# Check metrics server
kubectl get pods -n kube-system | grep metrics

# Check resource requests on deployment
kubectl describe deployment my-app | grep -A5 Requests
```

### HPA not scaling up

```bash
kubectl describe hpa my-hpa
# Check Events section
```

**Common causes:**
- Already at maxReplicas
- Metric below threshold
- Pods in Pending (no node capacity)

### HPA scaling too aggressively

```yaml
# Add stabilization window
behavior:
  scaleUp:
    stabilizationWindowSeconds: 60  # Wait 60s
```

---

## 📝 Quick Commands

```bash
# Get HPA status
kubectl get hpa

# Detailed HPA info
kubectl describe hpa my-hpa

# Watch HPA in real-time
kubectl get hpa -w

# Check if metrics-server is working
kubectl top pods

# Create HPA imperatively (quick test)
kubectl autoscale deployment my-app --min=2 --max=10 --cpu-percent=70

# Delete HPA
kubectl delete hpa my-hpa
```

---

## 🎯 Interview Questions

**Q: How does HPA work?**
> HPA monitors metrics (CPU, memory, custom) via metrics-server or custom adapters. It calculates desired replicas using the formula: desired = current × (currentMetric / targetMetric). It then updates the Deployment's replica count.

**Q: What's the difference between HPA and VPA?**
> HPA scales horizontally (more pods, same size). VPA scales vertically (same pods, more resources). Use HPA for stateless apps that can scale out. Use VPA for single-instance apps or to right-size resource requests.

**Q: Your HPA shows "unknown" for CPU. How do you debug?**
> 1. Check metrics-server is running: `kubectl get pods -n kube-system | grep metrics`
> 2. Verify pods have resource requests set
> 3. Wait 15-30 seconds for metrics to be collected
> 4. Check `kubectl describe hpa` for events

**Q: How do you prevent HPA from scaling down too quickly?**
> Use the `behavior` field with `scaleDown.stabilizationWindowSeconds`. Default is 300 seconds (5 min). You can also use percentage-based policies to scale down gradually.

**Q: How does HPA work with Cluster Autoscaler?**
> HPA scales pods, Cluster Autoscaler scales nodes. When HPA requests more pods than current nodes can handle, pods go to Pending. Cluster Autoscaler sees pending pods and adds nodes. Once nodes are ready, pending pods get scheduled.

---

**Next: ML on Kubernetes →**

