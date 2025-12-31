# 🎯 Pods Deep Dive

## What is a Pod?

A Pod is the **smallest deployable unit** in Kubernetes. It's a wrapper around one or more containers.

```
┌─────────────────────────────────────────┐
│                  POD                     │
│  ┌─────────────┐    ┌─────────────┐     │
│  │ Container 1 │    │ Container 2 │     │
│  │  (main app) │    │  (sidecar)  │     │
│  └─────────────┘    └─────────────┘     │
│                                          │
│  Shared:                                 │
│  • Network (same IP, localhost)          │
│  • Storage (shared volumes)              │
│  • Process namespace                     │
└─────────────────────────────────────────┘
```

### Why Pods, Not Just Containers?

1. **Co-located containers** - Some apps need helper containers
2. **Shared resources** - Containers in a pod share network/storage
3. **Atomic scheduling** - All containers in pod scheduled together
4. **Common lifecycle** - Start/stop together

---

## Pod Anatomy

```yaml
apiVersion: v1           # API version
kind: Pod                # Resource type
metadata:
  name: my-pod           # Pod name (must be unique in namespace)
  namespace: default     # Which namespace
  labels:                # Key-value pairs for organization
    app: web
    tier: frontend
  annotations:           # Non-identifying metadata
    description: "This is my web app"
spec:
  containers:            # List of containers
  - name: main-container
    image: nginx:1.21
    ports:
    - containerPort: 80
    env:                 # Environment variables
    - name: MY_VAR
      value: "hello"
    resources:           # Resource requests/limits
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
    volumeMounts:        # Where to mount volumes
    - name: config-volume
      mountPath: /etc/config
  volumes:               # Volume definitions
  - name: config-volume
    configMap:
      name: my-config
```

---

## Pod Lifecycle

```
  ┌─────────┐
  │ Pending │ ─── Scheduling, pulling images
  └────┬────┘
       │
       ▼
  ┌─────────┐
  │ Running │ ─── At least one container running
  └────┬────┘
       │
       ├──────────────────────┐
       ▼                      ▼
  ┌───────────┐        ┌──────────┐
  │ Succeeded │        │  Failed  │
  │ (Jobs)    │        │          │
  └───────────┘        └──────────┘
```

### Pod Phases

| Phase | Description |
|-------|-------------|
| **Pending** | Accepted but not running. Waiting for scheduling or image pull |
| **Running** | At least one container is running |
| **Succeeded** | All containers terminated successfully (exit 0) |
| **Failed** | All containers terminated, at least one failed |
| **Unknown** | State cannot be determined (usually node communication issue) |

---

## Container States (Within a Pod)

### Waiting
Container not yet running. Check `reason` field:
- `ContainerCreating` - Normal startup
- `ImagePullBackOff` - Can't pull image
- `CrashLoopBackOff` - Keeps crashing

### Running
Container executing without problems.

### Terminated
Container finished execution. Check `reason`:
- `Completed` - Exited successfully
- `Error` - Exited with error
- `OOMKilled` - Ran out of memory

---

## Multi-Container Pod Patterns

### 1. Sidecar Pattern
Helper container that extends/enhances main container.

```yaml
spec:
  containers:
  - name: main-app
    image: my-app
  - name: log-shipper      # Sidecar
    image: fluentd
    volumeMounts:
    - name: logs
      mountPath: /var/log
  volumes:
  - name: logs
    emptyDir: {}
```

**Use cases:**
- Log shipping
- Proxy/service mesh (Istio)
- Configuration refresh

### 2. Init Container Pattern
Runs BEFORE main containers start. Must complete successfully.

```yaml
spec:
  initContainers:
  - name: init-db
    image: busybox
    command: ['sh', '-c', 'until nc -z db-service 5432; do sleep 2; done']
  containers:
  - name: main-app
    image: my-app
```

**Use cases:**
- Wait for dependencies
- Setup/initialization
- Download config files
- Database migrations

### 3. Ambassador Pattern
Proxy that simplifies external service access.

```yaml
spec:
  containers:
  - name: main-app
    image: my-app
    # Talks to localhost:6379
  - name: redis-ambassador
    image: redis-proxy
    # Handles connection to actual Redis cluster
```

---

## Resource Management

### Requests vs Limits

```yaml
resources:
  requests:        # Guaranteed minimum
    memory: "128Mi"
    cpu: "500m"    # 0.5 CPU cores
  limits:          # Maximum allowed
    memory: "256Mi"
    cpu: "1000m"   # 1 CPU core
```

| Concept | What It Means |
|---------|---------------|
| **Request** | Scheduler uses this to find a node with capacity |
| **Limit** | Container is killed/throttled if it exceeds this |

### CPU Units
- `1` = 1 CPU core
- `500m` = 0.5 cores (500 millicores)
- `100m` = 0.1 cores

### Memory Units
- `Ki` = Kibibytes (1024 bytes)
- `Mi` = Mebibytes (1024 Ki)
- `Gi` = Gibibytes (1024 Mi)

### What Happens When Limits Exceeded?

| Resource | Behavior |
|----------|----------|
| **CPU** | Throttled (slowed down) |
| **Memory** | Container is OOMKilled (restarted) |

---

## Health Checks (Probes)

### Liveness Probe
"Is the container alive?" - Restarts if failed.

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 10
  failureThreshold: 3
```

### Readiness Probe
"Is the container ready for traffic?" - Removes from Service if failed.

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Startup Probe
"Has the container started?" - For slow-starting apps.

```yaml
startupProbe:
  httpGet:
    path: /startup
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
```

### Probe Types

```yaml
# HTTP GET
httpGet:
  path: /health
  port: 8080

# TCP Socket
tcpSocket:
  port: 3306

# Execute Command
exec:
  command:
  - cat
  - /tmp/healthy
```

---

## Common Pod Issues & Debugging

### Pod Stuck in Pending

```bash
kubectl describe pod <pod-name>
```

**Common reasons:**
- Insufficient resources on nodes
- Node selector/affinity not matching
- PVC not bound

### CrashLoopBackOff

```bash
kubectl logs <pod-name>
kubectl logs <pod-name> --previous  # Logs from crashed container
```

**Common reasons:**
- Application error
- Missing config/secrets
- Database connection failed

### ImagePullBackOff

```bash
kubectl describe pod <pod-name>
```

**Common reasons:**
- Image doesn't exist
- Private registry, no imagePullSecrets
- Typo in image name

---

## Quick Commands Reference

```bash
# Create pod from YAML
kubectl apply -f pod.yaml

# List pods
kubectl get pods
kubectl get pods -o wide  # More info (node, IP)
kubectl get pods -w       # Watch changes

# Describe pod (events, status)
kubectl describe pod <name>

# Pod logs
kubectl logs <pod>
kubectl logs <pod> -c <container>  # Specific container
kubectl logs <pod> -f              # Follow/stream
kubectl logs <pod> --previous      # Previous container

# Execute in pod
kubectl exec -it <pod> -- /bin/sh
kubectl exec -it <pod> -c <container> -- /bin/sh

# Delete pod
kubectl delete pod <name>
kubectl delete pod <name> --force --grace-period=0  # Force delete

# Port forward (access from local machine)
kubectl port-forward <pod> 8080:80
```

---

## 📝 Practice Exercises

1. Create a pod with nginx that has liveness and readiness probes
2. Create a multi-container pod with nginx and a sidecar that writes "Hello" to a shared volume
3. Create an init container that waits for a service to be ready
4. Cause an OOMKill by setting low memory limits and loading data
5. Debug a CrashLoopBackOff scenario

---

## 🎯 Interview Questions

**Q: What's the difference between a Pod and a Container?**
> A Pod is a Kubernetes abstraction that wraps one or more containers. Containers in a pod share network (same IP), storage, and lifecycle. You deploy Pods, not containers directly.

**Q: When would you use multiple containers in a Pod?**
> Use multi-container pods when containers must share resources tightly: sidecar for logging/proxying, init containers for setup, or ambassador pattern for service access.

**Q: What's the difference between liveness and readiness probes?**
> Liveness: "Should I restart this container?" - Failed = container restarted
> Readiness: "Should I send traffic here?" - Failed = removed from Service endpoints

**Q: What happens when a container exceeds its memory limit?**
> The container is OOMKilled (Out Of Memory Killed) and Kubernetes restarts it according to the pod's restart policy.

---

**Next: Deployments & ReplicaSets →**

