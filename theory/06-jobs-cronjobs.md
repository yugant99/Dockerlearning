# ⚙️ Kubernetes Jobs & CronJobs

## Why Jobs?

Regular Pods and Deployments are for **long-running** services (web servers, APIs).
Jobs are for **run-to-completion** tasks (training, ETL, batch processing).

```
Deployment: "Keep 3 nginx pods running forever"
Job:        "Run this training script once, exit when done"
```

---

## Job Basics

### Simple Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: training-job
spec:
  template:
    spec:
      containers:
      - name: trainer
        image: my-training-image
        command: ["python", "train.py"]
      restartPolicy: Never  # Jobs use Never or OnFailure
```

### Job vs Deployment

| Aspect | Deployment | Job |
|--------|------------|-----|
| Purpose | Run forever | Run to completion |
| Replicas | Maintained count | Target completions |
| Restart | Always | Never/OnFailure |
| Use case | Web servers, APIs | Training, ETL, migrations |

---

## Job Configuration Options

### Completions & Parallelism

```yaml
spec:
  completions: 5      # Need 5 successful completions
  parallelism: 2      # Run 2 pods at a time
```

```
Timeline:
┌─────┐ ┌─────┐
│Pod 1│ │Pod 2│  ← 2 parallel
└──┬──┘ └──┬──┘
   ✓      ✓
┌─────┐ ┌─────┐
│Pod 3│ │Pod 4│  ← next 2
└──┬──┘ └──┬──┘
   ✓      ✓
┌─────┐
│Pod 5│            ← final one
└──┬──┘
   ✓
Done! 5 completions
```

### Patterns

| completions | parallelism | Pattern |
|-------------|-------------|---------|
| 1 | 1 | Single job (default) |
| N | 1 | Sequential queue |
| N | M | Parallel batch |
| unset | N | Work queue (external coordination) |

---

## Failure Handling

### backoffLimit

```yaml
spec:
  backoffLimit: 3  # Retry up to 3 times on failure
```

Backoff is exponential: 10s, 20s, 40s, ...

### activeDeadlineSeconds

```yaml
spec:
  activeDeadlineSeconds: 600  # Kill job after 10 minutes
```

Useful for:
- Preventing runaway jobs
- Cost control
- SLA enforcement

### restartPolicy

```yaml
spec:
  template:
    spec:
      restartPolicy: Never    # Don't restart, create new pod
      # OR
      restartPolicy: OnFailure  # Restart same pod on failure
```

| Policy | Behavior | Use When |
|--------|----------|----------|
| Never | New pod on failure | Need fresh environment each try |
| OnFailure | Restart in place | Faster, keeps local state |

---

## Job Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│                      JOB STATES                          │
│                                                          │
│   Created ──► Active ──► Succeeded                      │
│                 │              │                         │
│                 │              └──► Complete ✓          │
│                 │                                        │
│                 └──► Failed (backoffLimit reached)      │
│                            │                             │
│                            └──► Failed ✗                │
└─────────────────────────────────────────────────────────┘
```

### Check Job Status

```bash
# List jobs
kubectl get jobs

# Output:
# NAME           COMPLETIONS   DURATION   AGE
# training-job   1/1           45s        2m

# Detailed status
kubectl describe job training-job

# Get pods created by job
kubectl get pods -l job-name=training-job

# Logs from job pod
kubectl logs job/training-job
```

---

## Real Example: ML Training Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: model-training
  namespace: ml-platform
spec:
  backoffLimit: 2
  activeDeadlineSeconds: 3600  # 1 hour max
  template:
    metadata:
      labels:
        app: training
    spec:
      restartPolicy: Never
      containers:
      - name: trainer
        image: ml-training:v1
        command: ["python", "train.py"]
        env:
        - name: MODEL_PATH
          value: "/models/model.joblib"
        - name: EPOCHS
          valueFrom:
            configMapKeyRef:
              name: training-config
              key: epochs
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        volumeMounts:
        - name: model-storage
          mountPath: /models
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: model-pvc
```

---

## CronJobs

### What is a CronJob?

A CronJob creates Jobs on a schedule. Perfect for:
- Automated retraining
- Daily ETL
- Periodic cleanup
- Report generation

```
CronJob ──► Creates Job ──► Creates Pod ──► Runs Task
   │              │               │
   │         (at scheduled       (runs to
   │           times)           completion)
   │
   └── Schedule: "0 2 * * *" (daily at 2 AM)
```

---

### Cron Schedule Syntax

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday = 0)
│ │ │ │ │
* * * * *
```

### Common Schedules

| Schedule | Meaning |
|----------|---------|
| `0 * * * *` | Every hour |
| `0 2 * * *` | Daily at 2 AM |
| `0 2 * * 0` | Weekly on Sunday at 2 AM |
| `0 0 1 * *` | Monthly on 1st at midnight |
| `*/15 * * * *` | Every 15 minutes |
| `0 9-17 * * 1-5` | Hourly 9AM-5PM, Mon-Fri |

---

### CronJob Configuration

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: model-retrain
spec:
  schedule: "0 2 * * 0"           # Weekly Sunday 2 AM
  concurrencyPolicy: Forbid        # Don't overlap
  successfulJobsHistoryLimit: 3    # Keep last 3 successful
  failedJobsHistoryLimit: 1        # Keep last 1 failed
  startingDeadlineSeconds: 200     # Must start within 200s of schedule
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: trainer
            image: ml-training:v1
            command: ["python", "train.py"]
```

---

### concurrencyPolicy

What happens if a new job is scheduled while previous still running?

| Policy | Behavior |
|--------|----------|
| **Allow** | Run both (default) |
| **Forbid** | Skip new job |
| **Replace** | Kill old, start new |

```yaml
# For ML training, usually want Forbid
# Don't want two trainings fighting for GPU/resources
concurrencyPolicy: Forbid
```

---

### History Limits

```yaml
successfulJobsHistoryLimit: 3  # Keep 3 successful job records
failedJobsHistoryLimit: 1      # Keep 1 failed job record
```

Why limit history?
- Each Job creates Pods
- Pods consume etcd storage
- Old pods clutter `kubectl get pods`

---

## CronJob Real Example: Automated Retraining

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: weekly-retrain
  namespace: ml-platform
spec:
  schedule: "0 2 * * 0"  # Sunday 2 AM
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 2
  jobTemplate:
    spec:
      backoffLimit: 2
      activeDeadlineSeconds: 7200  # 2 hour max
      template:
        metadata:
          labels:
            app: retrain
        spec:
          restartPolicy: OnFailure
          containers:
          - name: trainer
            image: ml-training:v1
            command: ["python", "train.py", "--retrain"]
            env:
            - name: MODEL_VERSION
              value: "$(date +%Y%m%d)"
            resources:
              requests:
                memory: "1Gi"
                cpu: "1000m"
              limits:
                memory: "2Gi"
                cpu: "2000m"
            volumeMounts:
            - name: models
              mountPath: /models
          volumes:
          - name: models
            persistentVolumeClaim:
              claimName: model-pvc
```

---

## Managing Jobs & CronJobs

### Commands

```bash
# List CronJobs
kubectl get cronjobs

# Describe CronJob (see last schedule time)
kubectl describe cronjob weekly-retrain

# Manually trigger a CronJob (for testing)
kubectl create job --from=cronjob/weekly-retrain manual-run

# Suspend a CronJob (pause scheduling)
kubectl patch cronjob weekly-retrain -p '{"spec":{"suspend":true}}'

# Resume
kubectl patch cronjob weekly-retrain -p '{"spec":{"suspend":false}}'

# Delete (also deletes child jobs/pods)
kubectl delete cronjob weekly-retrain
```

---

## Job Patterns for ML

### Pattern 1: Train Once, Serve Forever
```
Job (train) ──► PVC (model) ◄── Deployment (serve)
```

### Pattern 2: Scheduled Retraining
```
CronJob ──► Job (train) ──► PVC (model) ◄── Deployment (serve)
                                               │
                                    (rolling restart to load new model)
```

### Pattern 3: Parallel Hyperparameter Search
```yaml
spec:
  completions: 10    # Try 10 combinations
  parallelism: 3     # 3 at a time
```

### Pattern 4: Data Pipeline Stages
```
CronJob ──► Job (extract) ──► Job (transform) ──► Job (load)
                   │                │                 │
                   └────── Sequential with depends ───┘
```

---

## Debugging Jobs

### Job stuck in "Active"

```bash
# Check pod status
kubectl get pods -l job-name=my-job

# Common issues:
# - ImagePullBackOff: wrong image name
# - Pending: no resources available
# - Error: container crashed
```

### Job keeps failing

```bash
# Check pod logs
kubectl logs job/my-job

# Check events
kubectl describe job my-job | grep -A 20 Events
```

### CronJob not running

```bash
# Check if suspended
kubectl get cronjob my-cron -o jsonpath='{.spec.suspend}'

# Check last schedule
kubectl describe cronjob my-cron | grep "Last Schedule"

# Check for startingDeadlineSeconds issues
```

---

## 📝 Quick Reference

```bash
# Jobs
kubectl get jobs
kubectl describe job NAME
kubectl logs job/NAME
kubectl delete job NAME

# CronJobs
kubectl get cronjobs
kubectl describe cronjob NAME
kubectl create job --from=cronjob/NAME test-run  # Manual trigger
kubectl patch cronjob NAME -p '{"spec":{"suspend":true}}'  # Pause
```

---

## 🎯 Interview Questions

**Q: When would you use a Job vs a Deployment?**
> Jobs are for run-to-completion tasks: training, migrations, batch processing. Deployments are for long-running services that should always be running.

**Q: How do you handle Job failures?**
> Use `backoffLimit` for retries, `activeDeadlineSeconds` for timeout. Check pod logs for debugging. For CronJobs, `failedJobsHistoryLimit` keeps failed records for investigation.

**Q: What's the difference between restartPolicy Never and OnFailure?**
> `Never`: Creates a new pod on failure (clean slate). `OnFailure`: Restarts the same pod (faster, keeps ephemeral storage).

**Q: How would you run ML training weekly with CronJobs?**
> Create a CronJob with `schedule: "0 2 * * 0"`, use `concurrencyPolicy: Forbid` to prevent overlapping runs, mount a PVC for model output.

**Q: Your CronJob ran but the Job is still "Active" for hours. What do you check?**
> 1. `kubectl describe job` for events
> 2. Check pod status (ImagePullBackOff, OOMKilled?)
> 3. Check `activeDeadlineSeconds` if set
> 4. Look at pod logs for application errors

---

**Next: HPA & Autoscaling →**

