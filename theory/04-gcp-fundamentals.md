# 🌐 GCP Fundamentals for Kubernetes

## What is Google Cloud Platform?

GCP is Google's cloud computing platform, offering:
- **Compute:** VMs, Kubernetes, serverless
- **Storage:** Object storage, databases
- **Big Data:** BigQuery, Dataflow, Pub/Sub
- **ML/AI:** Vertex AI, AutoML

---

## GCP Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│                    Organization                          │
│              (your-company.com)                         │
│                                                          │
│    ┌──────────────────────────────────────────────┐    │
│    │              Folder (Optional)                │    │
│    │           (e.g., "Engineering")               │    │
│    │                                               │    │
│    │    ┌────────────┐    ┌────────────┐         │    │
│    │    │  Project A │    │  Project B │         │    │
│    │    │  (prod)    │    │  (staging) │         │    │
│    │    └────────────┘    └────────────┘         │    │
│    │                                               │    │
│    └──────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Projects
- **Billing boundary** - costs tracked per project
- **Resource container** - VMs, clusters, buckets belong to a project
- **IAM boundary** - permissions set at project level

---

## Key GCP Services to Know

### Compute Services

| Service | What It Is | When to Use |
|---------|------------|-------------|
| **Compute Engine** | Virtual Machines | Full control, custom setups |
| **GKE** | Managed Kubernetes | Container orchestration |
| **Cloud Run** | Serverless containers | Simple stateless apps |
| **Cloud Functions** | Serverless functions | Event-driven tasks |

### Storage Services

| Service | Type | When to Use |
|---------|------|-------------|
| **Cloud Storage (GCS)** | Object storage | Files, backups, data lakes |
| **Persistent Disk** | Block storage | VM/GKE storage |
| **Filestore** | NFS | Shared file system |
| **Cloud SQL** | Managed SQL | PostgreSQL, MySQL |
| **BigQuery** | Data warehouse | Analytics, large queries |

### Networking

| Service | What It Is |
|---------|------------|
| **VPC** | Virtual Private Cloud - your network |
| **Cloud Load Balancing** | Global load balancers |
| **Cloud CDN** | Content delivery network |
| **Cloud NAT** | Outbound internet for private instances |

---

## IAM (Identity and Access Management)

### Key Concepts

```
WHO (Identity)  +  WHAT (Role)  =  Access to RESOURCE
```

### Identities

- **Google Account** - person@gmail.com
- **Service Account** - myapp@project.iam.gserviceaccount.com
- **Google Group** - team@company.com
- **Cloud Identity domain** - company.com

### Roles

```
┌─────────────────────────────────────────────────┐
│               Role Types                         │
├─────────────────────────────────────────────────┤
│ Basic Roles (Avoid in production!)              │
│   • Owner - Full access                         │
│   • Editor - Modify resources                   │
│   • Viewer - Read-only                          │
├─────────────────────────────────────────────────┤
│ Predefined Roles (Use these!)                   │
│   • roles/compute.admin                         │
│   • roles/container.admin                       │
│   • roles/storage.objectViewer                  │
├─────────────────────────────────────────────────┤
│ Custom Roles                                     │
│   • Create your own with specific permissions   │
└─────────────────────────────────────────────────┘
```

### Service Accounts

Used by applications/services to authenticate.

```bash
# Create a service account
gcloud iam service-accounts create my-sa \
    --display-name="My Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:my-sa@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"
```

---

## Cloud Storage (GCS)

Object storage for any amount of data.

### Bucket Structure
```
gs://my-bucket/
├── data/
│   ├── file1.csv
│   └── file2.json
└── models/
    └── model.pkl
```

### Storage Classes

| Class | Use Case | Availability | Cost |
|-------|----------|--------------|------|
| Standard | Frequent access | Highest | Highest |
| Nearline | Monthly access | High | Medium |
| Coldline | Quarterly access | High | Lower |
| Archive | Yearly access | Lower | Lowest |

### Commands

```bash
# Create bucket
gsutil mb gs://my-bucket

# Copy files
gsutil cp file.txt gs://my-bucket/
gsutil cp gs://my-bucket/file.txt ./

# List contents
gsutil ls gs://my-bucket/

# Sync directories
gsutil -m rsync -r ./local-dir gs://my-bucket/remote-dir
```

---

## gcloud CLI Essentials

### Installation
```bash
# macOS with Homebrew
brew install google-cloud-sdk

# Initialize
gcloud init
```

### Configuration

```bash
# Set project
gcloud config set project PROJECT_ID

# Set region/zone
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a

# List configurations
gcloud config list

# Multiple configurations
gcloud config configurations create dev
gcloud config configurations activate dev
```

### Common Commands

```bash
# Authentication
gcloud auth login                    # User login
gcloud auth application-default login  # App credentials
gcloud auth list                     # Show accounts

# Projects
gcloud projects list
gcloud projects create my-project

# Compute
gcloud compute instances list
gcloud compute instances create my-vm \
    --machine-type=e2-medium \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud

# GKE (covered in next section)
gcloud container clusters list
```

---

## Networking Basics

### VPC (Virtual Private Cloud)

```
┌─────────────────────────────────────────────────────────┐
│                        VPC                               │
│                                                          │
│   ┌─────────────────┐      ┌─────────────────┐         │
│   │    Subnet       │      │    Subnet       │         │
│   │  us-central1    │      │  us-east1       │         │
│   │  10.0.0.0/24    │      │  10.0.1.0/24    │         │
│   │                 │      │                 │         │
│   │  ┌───┐  ┌───┐  │      │  ┌───┐         │         │
│   │  │VM1│  │VM2│  │      │  │VM3│         │         │
│   │  └───┘  └───┘  │      │  └───┘         │         │
│   └─────────────────┘      └─────────────────┘         │
│                                                          │
│   Firewall Rules control traffic                        │
└─────────────────────────────────────────────────────────┘
```

### Firewall Rules

```bash
# Allow SSH
gcloud compute firewall-rules create allow-ssh \
    --allow tcp:22 \
    --source-ranges 0.0.0.0/0

# Allow HTTP
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --target-tags http-server
```

---

## GCP Free Tier

Great for learning!

### Always Free
- 1 f1-micro VM (us regions)
- 5 GB Cloud Storage
- 1 GB Cloud Functions invocations
- BigQuery: 1 TB queries/month

### Free Trial
- $300 credit for 90 days
- Full access to all services

**Tip:** Create a new project for learning to track costs separately.

---

## GCP for Data & ML

### BigQuery
Serverless data warehouse - crucial for data companies!

```sql
-- Query public dataset
SELECT name, SUM(number) as total
FROM `bigquery-public-data.usa_names.usa_1910_current`
GROUP BY name
ORDER BY total DESC
LIMIT 10;
```

### Vertex AI
Managed ML platform.
- AutoML: No-code ML
- Custom training: Your own code
- Prediction: Serve models

### Pub/Sub
Message queue for data pipelines.

```bash
# Create topic
gcloud pubsub topics create my-topic

# Publish message
gcloud pubsub topics publish my-topic --message="Hello"
```

---

## Cost Management Tips

1. **Set budget alerts**
   ```
   Console → Billing → Budgets & alerts
   ```

2. **Use preemptible VMs** (up to 80% cheaper)

3. **Delete unused resources**
   ```bash
   gcloud compute instances list --filter="status=TERMINATED"
   ```

4. **Use committed use discounts** for production

5. **Enable resource recommendations**

---

## 📝 Essential Commands Cheat Sheet

```bash
# Auth
gcloud auth login
gcloud auth application-default login

# Project
gcloud config set project PROJECT_ID
gcloud projects list

# Compute
gcloud compute instances list
gcloud compute ssh INSTANCE_NAME

# Storage
gsutil ls
gsutil cp LOCAL_FILE gs://BUCKET/
gsutil mb gs://NEW_BUCKET

# IAM
gcloud iam service-accounts list
gcloud projects get-iam-policy PROJECT_ID

# GKE (next chapter!)
gcloud container clusters list
gcloud container clusters get-credentials CLUSTER_NAME
```

---

## 🎯 Interview Questions

**Q: What's the difference between a Project and a Folder in GCP?**
> Projects are the fundamental organizational unit containing resources. Folders are optional groupings of projects for larger organizations. Projects have billing, IAM, and resources; Folders just group projects.

**Q: What's the difference between a Service Account and a User Account?**
> User accounts are for humans (interactive login). Service accounts are for applications/services (programmatic access). Service accounts use key files or Workload Identity for authentication.

**Q: When would you use Cloud Storage vs Cloud SQL?**
> Cloud Storage for unstructured data (files, images, backups). Cloud SQL for structured, relational data that needs SQL queries, transactions, and relationships.

**Q: How do you secure resources in GCP?**
> Use IAM for access control, VPC for network isolation, firewall rules for traffic control, and encryption (default for data at rest, configurable for data in transit).

---

**Next: GKE Deep Dive →**

