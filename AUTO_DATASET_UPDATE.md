# Automatic Dataset Update Solution

## Overview

This solution automatically detects ConfigMap changes and triggers ML model regeneration **without requiring any bash scripts**. When someone updates the dataset configuration in Git, the system automatically:

1. Detects the ConfigMap change
2. Creates a new ML Job with unique name
3. Generates the new model
4. Restarts the frontend to use the new model

## Architecture

```
Git (ConfigMap change)
    ↓
ArgoCD (syncs ConfigMap)
    ↓
ML Config Watcher (detects change)
    ↓
Creates new ML Job (unique name with timestamp)
    ↓
ML Job runs → generates model → saves to PVC
    ↓
Watcher restarts Frontend Deployment
    ↓
Frontend loads new model from PVC
```

## Components

### 1. ML Config Watcher (`ml-watcher.yaml`)
- **Type**: Deployment (always running)
- **Function**: Monitors ConfigMap for changes every 30 seconds
- **Action**: When change detected, creates new Job and restarts deployment
- **Advantages**:
  - No manual intervention needed
  - Automatic job naming with timestamp
  - Immediate response to changes

### 2. ServiceAccount & RBAC (`ml-updater-rbac.yaml`)
- Grants watcher permission to:
  - Read ConfigMaps
  - Create Jobs
  - Restart Deployments

### 3. Alternative: CronJob (`ml-cronjob.yaml`)
- **Type**: CronJob (runs every 5 minutes)
- **Function**: Periodic check for dataset changes
- **Use**: If you prefer periodic checks over continuous monitoring

## Usage

### Automatic Mode (Recommended)

Just update the ConfigMap in Git:

```yaml
# configmap.yaml
data:
  DATASET_URL: "/home/datasets/spotify/2023_spotify_ds2.csv"  # Changed
  DATASET_NAME: "ds2"  # Changed
  MODEL_FILENAME: "rules_ds2.pkl"  # Changed
```

Commit and push:
```bash
git add configmap.yaml
git commit -m "Switch to ds2"
git push
```

**What happens automatically:**
1. ArgoCD syncs the new ConfigMap (~3 min)
2. Watcher detects ConfigMap hash change (~30 sec)
3. Watcher creates Job: `ml-job-ds2-20251112-153045`
4. Job generates `rules_ds2.pkl` in PVC
5. Watcher restarts deployment
6. Frontend loads new model

**No bash script needed!** ✅

### Manual kubectl (Also works)

```bash
# Update ConfigMap directly
kubectl edit configmap playlist-config -n giovanamachado

# Change DATASET_URL, DATASET_NAME, MODEL_FILENAME
# Save and exit

# Watcher will detect and trigger rebuild automatically
```

## Deployment

### Deploy the Watcher Solution

```bash
# 1. Apply RBAC
kubectl apply -f ml-updater-rbac.yaml

# 2. Deploy the watcher
kubectl apply -f ml-watcher.yaml

# 3. Verify it's running
kubectl -n giovanamachado get pods -l app=ml-config-watcher
kubectl -n giovanamachado logs -l app=ml-config-watcher -f
```

### Or Deploy the CronJob Solution

```bash
# 1. Apply RBAC
kubectl apply -f ml-updater-rbac.yaml

# 2. Deploy the cronjob
kubectl apply -f ml-cronjob.yaml

# 3. Verify
kubectl -n giovanamachado get cronjobs
```

## Verification

```bash
# Watch for new jobs being created
kubectl -n giovanamachado get jobs -w

# Check watcher logs
kubectl -n giovanamachado logs -l app=ml-config-watcher -f

# Verify model file
kubectl -n giovanamachado exec -it deployment/playlist-recommender -- ls -lh /model/
```

## How It Solves the Requirements

### ✅ Unique Job Names
- **Requirement**: "change your Pod's name every time the playlist is updated"
- **Solution**: Jobs named `ml-job-${DATASET}-${TIMESTAMP}`
- **Example**: `ml-job-ds2-20251112-153045`

### ✅ Automatic Pruning
- **Requirement**: "configure ArgoCD to automatically prune the ML containers"
- **Solution**: `ttlSecondsAfterFinished: 3600` in Job spec
- **Result**: Jobs auto-delete 1 hour after completion

### ✅ No Manual Intervention
- **Requirement**: Continuous delivery
- **Solution**: Watcher automatically detects changes and triggers rebuild
- **Result**: Just push ConfigMap change to Git, everything else is automatic

### ✅ Lightweight
- **Requirement**: "creating a Pod is a lightweight operation"
- **Solution**: Only creates Job pod, no image rebuild needed
- **Result**: Fast model updates

## Comparison: Solutions

| Solution | Pros | Cons |
|----------|------|------|
| **Watcher** | Immediate response, continuous monitoring | One extra pod running |
| **CronJob** | Periodic checks, less resources | 5-min delay, may miss rapid changes |
| **Bash Script** | Simple, manual control | Requires manual execution |

## Recommended: Watcher + ArgoCD

For fully automatic operation:
1. Deploy `ml-watcher.yaml` (continuous monitoring)
2. Enable ArgoCD auto-sync
3. Update ConfigMap in Git
4. Everything else happens automatically!

## Example Workflow

```bash
# Developer updates dataset
vim configmap.yaml
# Changes DATASET_NAME from ds1 to ds2

git add configmap.yaml
git commit -m "Update to ds2"
git push

# === AUTOMATIC FROM HERE ===
# ArgoCD syncs ConfigMap (3 min)
# Watcher detects change (30 sec)
# Job created: ml-job-ds2-20251112-153045
# Model generated: rules_ds2.pkl
# Frontend restarted
# New model loaded
# === DONE ===
```

**No bash scripts. No manual steps. Fully automatic!** 🚀
