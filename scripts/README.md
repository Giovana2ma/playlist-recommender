# CI/CD Testing Infrastructure

Complete testing suite for evaluating ArgoCD deployment performance in the Playlist Recommender System.

## Overview

This testing infrastructure measures the CI/CD pipeline's performance across three scenarios:
1. **Kubernetes Deployment Changes** - Replica scaling
2. **Code Updates** - Container image version updates
3. **Training Dataset Updates** - ML model regeneration

## Files

```
scripts/
├── test_cicd.py           # Main monitoring and testing script
├── analyze_results.py     # Results analysis tool
├── visualize_results.py   # Generate charts and graphs
├── run_tests.sh          # Interactive test execution script
├── test_procedures.md     # Detailed testing procedures
└── report_template.tex    # LaTeX template for PDF report
```

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install requests matplotlib

# Optional: Install LaTeX for PDF generation
sudo apt-get install texlive-full  # Ubuntu/Debian
```

### 2. Setup Port Forwarding

```bash
# Forward the service to localhost
kubectl port-forward svc/playlist-recommender-svc 50013:50013 -n giovanamachado
```

### 3. Run Tests

#### Option A: Interactive Menu (Recommended)

```bash
chmod +x scripts/run_tests.sh
./scripts/run_tests.sh
```

The interactive menu will guide you through:
- Prerequisites check
- Port forwarding setup
- Running all three tests
- Generating reports

#### Option B: Manual Testing

**Test 1: Replica Scaling**
```bash
# Terminal 1: Start monitoring
python3 scripts/test_cicd.py http://localhost:50013/api/recommend -d 15 -o test1_replicas.json

# Terminal 2: Make changes
# Edit k8s/base/deployment.yaml (change replicas)
git add k8s/base/deployment.yaml
git commit -m "Test: Scale replicas"
git push
```

**Test 2: Code Update**
```bash
# Terminal 1: Start monitoring
python3 scripts/test_cicd.py http://localhost:50013/api/recommend -d 20 -o test2_code.json

# Terminal 2: Build and push new image
cd api
docker build -t docker.io/giovana2ma/playlists-frontend:0.2 .
docker push docker.io/giovana2ma/playlists-frontend:0.2

# Update deployment.yaml and configmap.yaml
git add k8s/base/deployment.yaml k8s/base/configmap.yaml
git commit -m "Test: Update to v0.2"
git push
```

**Test 3: Dataset Update**
```bash
# Terminal 1: Start monitoring
python3 scripts/test_cicd.py http://localhost:50013/api/recommend -d 30 -o test3_dataset.json

# Terminal 2: Update dataset
# Edit k8s/base/configmap.yaml (change DATASET_NAME from ds1 to ds2)
git add k8s/base/configmap.yaml
git commit -m "Test: Switch to ds2"
git push

# Monitor ML job
kubectl get jobs -n giovanamachado -w
```

### 4. Analyze Results

```bash
# Analyze individual test
python3 scripts/analyze_results.py test1_replicas.json

# Analyze all tests
python3 scripts/analyze_results.py test1_replicas.json test2_code.json test3_dataset.json

# Generate comparison report
python3 scripts/analyze_results.py test1_replicas.json test2_code.json test3_dataset.json -o comparison_report.txt
```

### 5. Generate Visualizations

```bash
# Generate timeline and response time plots
python3 scripts/visualize_results.py test1_replicas.json --all

# Generate comparison chart
python3 scripts/visualize_results.py test1_replicas.json test2_code.json test3_dataset.json --comparison comparison.png

# Specific plots
python3 scripts/visualize_results.py test1_replicas.json --timeline timeline1.png
python3 scripts/visualize_results.py test1_replicas.json --response-times response1.png
```

### 6. Create PDF Report

```bash
# Edit the LaTeX template with your results
cd scripts
nano report_template.tex

# Compile to PDF
pdflatex report_template.tex
pdflatex report_template.tex  # Run twice for table of contents

# View the PDF
xdg-open report_template.pdf
```

## Tools Documentation

### test_cicd.py

Continuously monitors the service and detects changes.

**Features:**
- Sends requests at regular intervals (default: 2 seconds)
- Detects version changes in API responses
- Detects model date changes
- Measures response times
- Identifies downtime periods
- Saves detailed results to JSON

**Usage:**
```bash
python3 scripts/test_cicd.py <service_url> [options]

Options:
  -d, --duration MINUTES    Duration to monitor (default: 10)
  -o, --output FILE        Output JSON file
  -i, --interval SECONDS   Request interval (default: 2.0)
```

**Output Format:**
```json
{
  "test_info": {
    "service_url": "...",
    "start_time": "...",
    "duration_seconds": 600
  },
  "summary": {
    "total_requests": 300,
    "successful": 295,
    "errors": 5,
    "downtime_count": 3,
    "downtime_seconds": 6,
    "success_rate": 0.983
  },
  "changes": {
    "version_changes": [...],
    "model_changes": [...]
  },
  "detailed_results": [...]
}
```

### analyze_results.py

Analyzes test results and generates reports.

**Features:**
- Calculates statistics (success rate, downtime, response times)
- Identifies downtime periods
- Detects deployment changes
- Generates comparison reports

**Usage:**
```bash
python3 scripts/analyze_results.py <json_files...> [options]

Options:
  -o, --output FILE    Generate comparison report to file
```

### visualize_results.py

Creates charts and graphs from test results.

**Features:**
- Timeline showing request success/failure
- Response time plots
- Comparison bar charts
- Marks version and model changes

**Usage:**
```bash
python3 scripts/visualize_results.py <json_files...> [options]

Options:
  --timeline FILE          Generate timeline plot
  --response-times FILE    Generate response time plot
  --comparison FILE        Generate comparison chart
  --all                    Generate all visualizations
```

### run_tests.sh

Interactive script to guide through testing process.

**Features:**
- Prerequisites check
- Automated port forwarding setup
- Step-by-step test execution
- Report generation

**Usage:**
```bash
./scripts/run_tests.sh
```

## Metrics Collected

### Deployment Time
- Time from git push to ArgoCD sync
- Time from sync to pod ready
- Total end-to-end deployment time

### Availability
- Success rate (percentage)
- Number of failed requests
- Downtime duration (seconds)

### Performance
- Response time statistics (min, max, mean, median)
- Response time over time
- Impact of deployments on performance

### Changes
- Version change detection and timing
- Model update detection and timing
- Number of deployment events

## Expected Results

### Test 1: Replica Scaling
- **Deployment Time:** 3-5 minutes
- **Downtime:** 0 seconds
- **Availability:** 100%
- **Notes:** Rolling update maintains availability

### Test 2: Code Update
- **Deployment Time:** 3-5 minutes
- **Downtime:** 10-30 seconds
- **Availability:** 98-99%
- **Notes:** Brief downtime during pod replacement

### Test 3: Dataset Update
- **Deployment Time:** 10-20 minutes (depending on dataset size)
- **Downtime:** 30-60 seconds
- **Availability:** 97-99%
- **Notes:** ML job execution dominates total time

## Troubleshooting

### Port forwarding fails
```bash
# Kill existing port-forward
pkill -f "port-forward.*playlist-recommender"

# Restart
kubectl port-forward svc/playlist-recommender-svc 50013:50013 -n giovanamachado
```

### No changes detected
```bash
# Check ArgoCD sync status
kubectl get applications -n argocd

# Force sync
argocd app sync <app-name>

# Check ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
```

### ML job not created
```bash
# Check watcher logs
kubectl logs -l app=ml-config-watcher -n giovanamachado

# Check ConfigMap
kubectl get configmap playlist-config -n giovanamachado -o yaml

# Manually create job (for testing)
kubectl apply -f k8s/ml-automation/ml-watcher.yaml
```

### Service not responding
```bash
# Check pod status
kubectl get pods -n giovanamachado -l app=giovanamachado-playlist-recommender

# Check logs
kubectl logs -l app=giovanamachado-playlist-recommender -n giovanamachado

# Describe service
kubectl describe svc playlist-recommender-svc -n giovanamachado
```

## Best Practices

1. **Run tests during low-traffic periods** to minimize user impact
2. **Keep monitoring running** for the entire duration to capture all events
3. **Document your changes** in git commit messages
4. **Take screenshots** of key moments for the report
5. **Run each test multiple times** to get consistent results
6. **Monitor ArgoCD UI** alongside the scripts for visual confirmation

## Report Submission Checklist

For your PDF submission, ensure you include:

- [ ] Architecture diagram showing all components
- [ ] Description of CI/CD pipeline flow
- [ ] Results table for all three tests
- [ ] Timeline graphs showing request status
- [ ] Response time charts
- [ ] Comparison charts across tests
- [ ] Screenshots of ArgoCD UI during sync
- [ ] Screenshots of pod changes (kubectl output)
- [ ] Analysis of downtime causes
- [ ] Recommendations for improvements
- [ ] Discussion of trade-offs
- [ ] Conclusions and lessons learned

## Additional Resources

- [Test Procedures Document](test_procedures.md) - Detailed step-by-step procedures
- [LaTeX Report Template](report_template.tex) - Pre-formatted report structure
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Kubernetes Rolling Updates](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/)

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the test_procedures.md for detailed guidance
3. Verify all prerequisites are installed
4. Ensure cluster connectivity and permissions

## License

This testing infrastructure is provided for educational purposes.
