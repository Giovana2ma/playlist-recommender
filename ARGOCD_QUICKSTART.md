# ArgoCD Quick Start

## Files Overview

### Kubernetes Manifests (in repository root)
- `deployment.yaml` - Frontend API deployment
- `service.yaml` - ClusterIP service
- `pvc.yaml` - Persistent Volume Claim
- `configmap.yaml` - Configuration (dataset, parameters)
- `ml-job.yaml` - ML model generation job

### ArgoCD Configuration
- `argocd-app.yaml` - ArgoCD application definition
- `argocd-application.yaml` - Alternative ArgoCD config

### Helper Scripts
- `switch-dataset.sh` - Switch between ds1 and ds2
- `build-images.sh` - Build Docker images
- `push-images.sh` - Push images to registry

## Quick Commands

### Initial Setup
```bash
# 1. Update argocd-app.yaml with your Git repo URL

# 2. Create ArgoCD application
kubectl apply -f argocd-app.yaml

# Or use CLI:
argocd app create giovanamachado-playlist-recommender \
  --repo https://github.com/YOUR-USERNAME/YOUR-REPO.git \
  --path . \
  --project giovanamachado-project \
  --dest-namespace giovanamachado \
  --dest-server https://kubernetes.default.svc \
  --sync-policy automated \
  --auto-prune \
  --self-heal
```

### Check Status
```bash
# ArgoCD app status
argocd app get giovanamachado-playlist-recommender

# Kubernetes resources
kubectl -n giovanamachado get all
kubectl -n giovanamachado get jobs
kubectl -n giovanamachado get pvc

# Pod logs
kubectl -n giovanamachado logs -l app=giovanamachado-playlist-recommender
```

### Update Code
```bash
# 1. Build and push new image
docker build -t docker.io/giovana2ma/playlists-frontend:0.2 api/
docker push docker.io/giovana2ma/playlists-frontend:0.2

# 2. Update deployment.yaml
sed -i 's|:0.1|:0.2|' deployment.yaml

# 3. Commit and push
git add deployment.yaml
git commit -m "Update to v0.2"
git push

# ArgoCD auto-syncs within ~3 minutes
```

### Switch Dataset
```bash
# Use helper script
./switch-dataset.sh ds2

# Commit and push
git add configmap.yaml ml-job.yaml
git commit -m "Switch to ds2"
git push
```

### Test API
```bash
# Get cluster IP
CLUSTER_IP=$(kubectl -n giovanamachado get svc playlist-recommender-svc -o jsonpath='{.spec.clusterIP}')

# Test request
curl -X POST http://${CLUSTER_IP}:50013/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"songs":["all me","antidote"]}'
```

### Troubleshooting
```bash
# Force sync
argocd app sync giovanamachado-playlist-recommender

# Check job logs
kubectl -n giovanamachado logs job/ml-job-ds1-v1

# Restart deployment
kubectl -n giovanamachado rollout restart deployment playlist-recommender

# Check model in PVC
kubectl -n giovanamachado exec -it deployment/playlist-recommender -- ls -lh /model/
```

## Workflow for Dataset Changes

1. **Run script**: `./switch-dataset.sh ds2`
2. **Commit**: `git add configmap.yaml ml-job.yaml && git commit -m "Switch to ds2"`
3. **Push**: `git push`
4. **ArgoCD will**:
   - Update ConfigMap
   - Create new Job with unique name
   - Job generates `rules_ds2.pkl`
   - Restart frontend to load new model
5. **Verify**: Check job completed and frontend uses new model

## Key Points

- ✅ Job names must be unique (includes timestamp/version)
- ✅ Auto-prune enabled (old jobs cleaned up after 1 hour)
- ✅ Self-heal enabled (auto-sync on drift)
- ✅ ConfigMap controls dataset selection
- ✅ Frontend auto-restarts when ConfigMap changes

## See Also
- `ARGOCD_GUIDE.md` - Comprehensive setup guide
- `ARGOCD_SETUP.md` - Additional setup notes
