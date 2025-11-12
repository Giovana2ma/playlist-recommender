# CI/CD Testing Infrastructure - Summary

## What Has Been Created

A complete testing infrastructure for evaluating your ArgoCD CI/CD pipeline performance:

### 1. Testing Scripts

**`scripts/test_cicd.py`** - Main monitoring tool
- Continuously sends requests to your service
- Detects version and model changes
- Measures response times and downtime
- Saves detailed results to JSON

**`scripts/analyze_results.py`** - Analysis tool
- Processes test results
- Calculates statistics
- Identifies downtime periods
- Generates comparison reports

**`scripts/visualize_results.py`** - Visualization tool
- Creates timeline graphs
- Plots response times
- Generates comparison charts
- Requires matplotlib

**`scripts/run_tests.sh`** - Interactive testing assistant
- Guides you through all tests
- Checks prerequisites
- Sets up port forwarding
- Helps generate reports

### 2. Documentation

**`scripts/README.md`** - Complete documentation
- Tool descriptions
- Usage examples
- Expected results
- Troubleshooting guide

**`scripts/QUICK_START.md`** - Step-by-step guide
- Complete testing workflow
- Terminal-by-terminal instructions
- Common issues and solutions
- Timeline estimates

**`scripts/test_procedures.md`** - Detailed procedures
- Test descriptions
- Execution steps
- Analysis guidelines
- Requirements for PDF

### 3. Report Template

**`scripts/report_template.tex`** - LaTeX report
- Pre-formatted sections
- Tables for results
- Space for graphs
- Professional structure

### 4. Server Improvements

**Health check endpoints added to `api/server.py`:**
- `GET /api/health` - For Kubernetes probes
- `GET /api/stats` - Model statistics

## How to Use This Infrastructure

### Quick Path (4-5 hours total)

1. **Setup (15 min)**
   ```bash
   pip install requests matplotlib
   chmod +x scripts/run_tests.sh
   kubectl port-forward svc/playlist-recommender-svc 50013:50013 -n giovanamachado &
   ```

2. **Run Tests (80 min)**
   ```bash
   # Test 1: 15 min monitoring + 5 min analysis
   python3 scripts/test_cicd.py http://localhost:50013/api/recommend -d 15 -o test1_replicas.json
   # (in another terminal: edit deployment, change replicas, git push)
   
   # Test 2: 20 min monitoring + 5 min analysis
   python3 scripts/test_cicd.py http://localhost:50013/api/recommend -d 20 -o test2_code.json
   # (in another terminal: build new image, update deployment, git push)
   
   # Test 3: 30 min monitoring + 5 min analysis
   python3 scripts/test_cicd.py http://localhost:50013/api/recommend -d 30 -o test3_dataset.json
   # (in another terminal: update configmap dataset, git push)
   ```

3. **Analyze (30 min)**
   ```bash
   # Analyze each test
   python3 scripts/analyze_results.py test1_replicas.json
   python3 scripts/analyze_results.py test2_code.json
   python3 scripts/analyze_results.py test3_dataset.json
   
   # Generate visualizations
   python3 scripts/visualize_results.py test1_replicas.json --all
   python3 scripts/visualize_results.py test2_code.json --all
   python3 scripts/visualize_results.py test3_dataset.json --all
   python3 scripts/visualize_results.py test*.json --comparison comparison.png
   ```

4. **Write Report (2-3 hours)**
   - Edit `scripts/report_template.tex`
   - Fill in your actual results
   - Add generated graphs
   - Compile with pdflatex

### Alternative: Interactive Path

```bash
./scripts/run_tests.sh
```

Follow the interactive menu to run all tests and generate reports.

## Three Test Scenarios

### Test 1: Kubernetes Deployment Changes
**What:** Change replica count from 2 to 3 (or 3 to 2)
**Duration:** 15 minutes monitoring
**Expected:** No downtime, 3-5 min deployment

### Test 2: Code Updates
**What:** Build new container image v0.2 and update deployment
**Duration:** 20 minutes monitoring
**Expected:** 10-30s downtime, 3-5 min deployment

### Test 3: Dataset Updates
**What:** Switch from ds1 to ds2 (or vice versa)
**Duration:** 30 minutes monitoring
**Expected:** 30-60s downtime, 10-15 min total (ML job + restart)

## Key Metrics to Report

For each test, you should measure and report:

1. **Deployment Time**
   - ArgoCD sync time (usually 2-3 min)
   - Pod creation/restart time
   - Total end-to-end time

2. **Downtime**
   - Number of failed requests
   - Duration in seconds
   - Percentage of requests affected

3. **Availability**
   - Success rate percentage
   - Uptime percentage

4. **Change Detection**
   - When version/model changed
   - How quickly detected
   - Impact on service

## What Your Report Should Include

### Required Sections

1. **Introduction**
   - Background on your system
   - CI/CD pipeline description
   - Test objectives

2. **System Architecture**
   - Component diagram
   - Deployment flow
   - ArgoCD configuration

3. **Test Results** (for each test)
   - Test description
   - Execution procedure
   - Results table
   - Timeline graph
   - Analysis

4. **Comparative Analysis**
   - Comparison table
   - Discussion of differences
   - Trade-offs analysis

5. **Discussion**
   - Downtime causes
   - Mitigation strategies
   - Best practices

6. **Recommendations**
   - Short-term improvements
   - Long-term improvements
   - Cost-benefit analysis

7. **Conclusions**
   - Summary of findings
   - Lessons learned
   - Future work

### Required Artifacts

- [ ] Results tables for all three tests
- [ ] Timeline graphs showing request status
- [ ] Response time plots
- [ ] Comparison bar charts
- [ ] Screenshots of ArgoCD UI
- [ ] Screenshots of kubectl commands
- [ ] Discussion of downtime causes
- [ ] Recommendations for zero-downtime deployments

## Expected Results Summary

Based on typical Kubernetes behavior:

| Test | Time | Downtime | Availability | Notes |
|------|------|----------|--------------|-------|
| Replica Scaling | 3-5 min | 0s | 100% | Rolling update works well |
| Code Update | 3-5 min | 10-30s | 98-99% | Pod replacement causes brief downtime |
| Dataset Update | 10-15 min | 30-60s | 97-99% | ML job + pod restart |

## Tips for Success

1. **Start early** - Allow 4-5 hours for complete testing
2. **Use multiple terminals** - One for monitoring, one for changes
3. **Document everything** - Screenshots, timestamps, observations
4. **Be patient** - ML jobs take time
5. **Run tests multiple times** - Ensures consistent results
6. **Watch ArgoCD UI** - Visual confirmation of sync
7. **Check pod logs** - Understand what's happening

## Troubleshooting

### Common Problems

1. **Port forward dies**
   ```bash
   pkill -f port-forward
   kubectl port-forward svc/playlist-recommender-svc 50013:50013 -n giovanamachado
   ```

2. **No changes detected**
   - Wait for ArgoCD sync (3 min polling interval)
   - Check ArgoCD application status
   - Verify git push succeeded

3. **ML job not created**
   - Check ml-config-watcher logs
   - Verify ConfigMap changed
   - Check RBAC permissions

4. **Service unavailable**
   - Check pod status
   - View pod logs
   - Verify service selector

## Next Steps

1. **Read the quick start guide:**
   ```bash
   cat scripts/QUICK_START.md
   ```

2. **Set up your environment:**
   ```bash
   pip install requests matplotlib
   ```

3. **Start testing:**
   ```bash
   ./scripts/run_tests.sh
   ```

4. **Analyze and visualize:**
   ```bash
   python3 scripts/analyze_results.py test*.json -o report.txt
   python3 scripts/visualize_results.py test*.json --comparison comparison.png
   ```

5. **Write your report:**
   ```bash
   cd scripts
   nano report_template.tex
   pdflatex report_template.tex
   ```

## Files Overview

```
scripts/
├── README.md              # Complete documentation
├── QUICK_START.md         # Step-by-step guide
├── test_procedures.md     # Detailed procedures
├── test_cicd.py          # Monitoring script ⭐
├── analyze_results.py     # Analysis script ⭐
├── visualize_results.py   # Visualization script
├── run_tests.sh          # Interactive helper ⭐
└── report_template.tex    # LaTeX report template ⭐

# Generated during testing:
test1_replicas.json        # Test 1 results
test2_code.json           # Test 2 results
test3_dataset.json        # Test 3 results
comparison_report.txt     # Comparison summary
comparison.png            # Comparison chart
*.png                     # Various graphs
report_template.pdf       # Final PDF report
```

## Resources

- **Documentation:** All in `scripts/` directory
- **Examples:** Check the QUICK_START.md for complete walkthrough
- **Help:** See troubleshooting sections in README.md

Good luck with your testing! 🚀
