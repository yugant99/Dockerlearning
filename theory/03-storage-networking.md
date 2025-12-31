# 🎯 Kubernetes Storage & Networking

## Part 1: Storage in Kubernetes

### The Problem

Containers are **ephemeral** - when they die, their data dies with them.

```
Container starts → writes data → crashes → GONE! 💀
```

Kubernetes solves this with **Volumes**.

---

## Volume Types

### 1. emptyDir
Temporary storage that lives as long as the pod.

```yaml
spec:
  containers:
  - name: app
    volumeMounts:
    - name: cache
      mountPath: /cache
  volumes:
  - name: cache
    emptyDir: {}
```

**Use cases:** Scratch space, sharing files between containers in a pod

### 2. hostPath
Maps a directory from the host node.

```yaml
volumes:
- name: host-data
  hostPath:
    path: /data
    type: Directory
```

**⚠️ Warning:** Not portable! Pod tied to specific node.

### 3. configMap / secret
Inject configuration as files.

```yaml
volumes:
- name: config
  configMap:
    name: my-config
```

### 4. persistentVolumeClaim (Most Important!)
Request storage that outlives the pod.

```yaml
volumes:
- name: data
  persistentVolumeClaim:
    claimName: my-pvc
```

---

## PersistentVolume (PV) & PersistentVolumeClaim (PVC)

### The Relationship

```
┌──────────────────────────────────────────────────────────┐
│                        CLUSTER                            │
│                                                           │
│  ┌─────────────────┐         ┌─────────────────┐        │
│  │ PersistentVolume│◄────────│    PVC (Claim)  │        │
│  │  (Admin creates)│  binds  │  (User creates) │        │
│  │                 │         │                 │        │
│  │  - 100Gi disk   │         │  - Requests 50Gi│        │
│  │  - AWS EBS      │         │  - ReadWriteOnce│        │
│  │  - ReadWriteOnce│         │                 │        │
│  └─────────────────┘         └────────┬────────┘        │
│                                        │                  │
│                                        ▼                  │
│                              ┌─────────────────┐        │
│                              │      Pod        │        │
│                              │  (Uses the PVC) │        │
│                              └─────────────────┘        │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Creating a PersistentVolume

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: standard
  hostPath:
    path: /mnt/data
```

### Creating a PersistentVolumeClaim

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
      storage: 5Gi
  storageClassName: standard
```

### Using PVC in a Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /usr/share/nginx/html
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: my-pvc
```

---

## Access Modes

| Mode | Short | Description |
|------|-------|-------------|
| ReadWriteOnce | RWO | Single node read/write |
| ReadOnlyMany | ROX | Multiple nodes read-only |
| ReadWriteMany | RWX | Multiple nodes read/write |

**GCP Note:** Most GCP disks only support RWO. For RWX, use Filestore.

---

## Storage Classes (Dynamic Provisioning)

Instead of manually creating PVs, let Kubernetes create them automatically!

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/gce-pd  # GCP
parameters:
  type: pd-ssd
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

Then in PVC:
```yaml
spec:
  storageClassName: fast-ssd  # Uses the StorageClass
  resources:
    requests:
      storage: 10Gi
```

---

## Part 2: Kubernetes Networking

### Networking Model

Every Pod gets its own IP address. No NAT needed for pod-to-pod communication.

```
┌─────────────────────────────────────────────────────────┐
│                   Kubernetes Cluster                     │
│                                                          │
│  ┌──────────────┐        ┌──────────────┐              │
│  │   Pod A      │        │   Pod B      │              │
│  │  10.244.1.5  │◄──────►│  10.244.2.8  │              │
│  └──────────────┘        └──────────────┘              │
│         ▲                        ▲                      │
│         │    Pod Network         │                      │
│         │   (10.244.0.0/16)      │                      │
│         └────────────────────────┘                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Key Networking Rules

1. **Pods can communicate without NAT**
2. **Nodes can communicate with all pods**
3. **Pod's IP is the same inside and outside**

---

## Services

Services provide stable endpoints for pods.

### Why Services?

Pods are ephemeral:
- Pod dies → new IP
- Scaling up → multiple IPs
- How do clients find pods?

**Services solve this!**

```
┌────────────────────────────────────────────────────────┐
│                                                         │
│   Client ──────► Service ──────► Pod 1                 │
│                  (stable IP)     Pod 2                 │
│                                  Pod 3                 │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

## Service Types

### 1. ClusterIP (Default)
Internal cluster access only.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: ClusterIP
  selector:
    app: my-app
  ports:
  - port: 80           # Service port
    targetPort: 8080   # Container port
```

```
Internal: my-service.default.svc.cluster.local:80
```

### 2. NodePort
Exposes on each node's IP at a static port.

```yaml
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080    # External port (30000-32767)
```

```
Access: <any-node-ip>:30080
```

### 3. LoadBalancer
Creates cloud load balancer (GKE, EKS, AKS).

```yaml
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8080
```

```
Access: <external-lb-ip>:80
```

### 4. ExternalName
Maps to external DNS name.

```yaml
spec:
  type: ExternalName
  externalName: my-database.example.com
```

---

## Service Discovery

### DNS

Kubernetes provides built-in DNS. Every Service gets a DNS name:

```
<service-name>.<namespace>.svc.cluster.local
```

Examples:
```bash
# From same namespace
curl http://my-service

# From different namespace
curl http://my-service.other-namespace

# Fully qualified
curl http://my-service.default.svc.cluster.local
```

### Environment Variables

Kubernetes injects service info as env vars:

```bash
MY_SERVICE_SERVICE_HOST=10.96.0.1
MY_SERVICE_SERVICE_PORT=80
```

---

## Ingress

Exposes HTTP/HTTPS routes from outside the cluster.

```
                    ┌─────────────┐
    Internet ──────►│   Ingress   │
                    │  Controller │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ /api     │    │ /web     │    │ /admin   │
    │ Service  │    │ Service  │    │ Service  │
    └──────────┘    └──────────┘    └──────────┘
```

### Ingress Resource

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### TLS with Ingress

```yaml
spec:
  tls:
  - hosts:
    - myapp.example.com
    secretName: my-tls-secret
  rules:
  - host: myapp.example.com
    # ...
```

---

## ConfigMaps & Secrets

### ConfigMap
Store non-sensitive configuration.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_HOST: "postgres"
  LOG_LEVEL: "info"
  config.json: |
    {
      "key": "value"
    }
```

### Using ConfigMap

```yaml
# As environment variables
env:
- name: DATABASE_HOST
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: DATABASE_HOST

# As a file
volumeMounts:
- name: config
  mountPath: /etc/config
volumes:
- name: config
  configMap:
    name: app-config
```

### Secrets
Store sensitive data (base64 encoded, not encrypted by default!).

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-secret
type: Opaque
data:
  username: YWRtaW4=      # base64 of "admin"
  password: cGFzc3dvcmQ=  # base64 of "password"
```

### Using Secrets

```yaml
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: my-secret
      key: password
```

---

## Network Policies

Control traffic flow between pods.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-allow
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: web
    ports:
    - protocol: TCP
      port: 8080
```

This allows only pods with `app: web` label to access `app: api` on port 8080.

---

## 📝 Quick Commands

```bash
# Storage
kubectl get pv
kubectl get pvc
kubectl get storageclass

# Services
kubectl get services
kubectl describe service <name>
kubectl get endpoints

# ConfigMaps & Secrets
kubectl create configmap my-config --from-file=config.txt
kubectl create secret generic my-secret --from-literal=password=secret
kubectl get configmaps
kubectl get secrets

# Networking
kubectl get ingress
kubectl describe ingress <name>
kubectl get networkpolicies
```

---

## 🎯 Interview Questions

**Q: What's the difference between PV and PVC?**
> PV (PersistentVolume) is the actual storage resource in the cluster. PVC (PersistentVolumeClaim) is a request for storage by a user. PVC binds to a matching PV, decoupling storage provisioning from consumption.

**Q: When would you use a StatefulSet instead of a Deployment?**
> StatefulSets are for stateful applications that need: stable network identities, persistent storage that follows the pod, and ordered deployment/scaling. Examples: databases, Kafka, Zookeeper.

**Q: What's the difference between ClusterIP, NodePort, and LoadBalancer?**
> ClusterIP: Internal only, default type
> NodePort: External access via node IP:port (30000-32767)
> LoadBalancer: Cloud provider's load balancer with external IP

**Q: How does Kubernetes DNS work?**
> CoreDNS provides cluster DNS. Services get DNS names: `<service>.<namespace>.svc.cluster.local`. Pods can use short names within same namespace.

---

**Next: GCP Fundamentals →**

