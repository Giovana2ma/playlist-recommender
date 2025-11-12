#!/bin/bash
# Automated CI/CD Testing Script
# This script helps run all three test scenarios sequentially

set -e

# Configuration
NAMESPACE="giovanamachado"
SERVICE_NAME="playlist-recommender-svc"
PORT=50013
SERVICE_URL="http://localhost:${PORT}/api/recommend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check kubectl
    if command -v kubectl &> /dev/null; then
        print_success "kubectl is installed"
    else
        print_error "kubectl is not installed"
        exit 1
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        print_success "Python3 is installed"
    else
        print_error "Python3 is not installed"
        exit 1
    fi
    
    # Check requests library
    if python3 -c "import requests" &> /dev/null; then
        print_success "Python requests library is installed"
    else
        print_error "Python requests library is not installed"
        print_warning "Install with: pip install requests"
        exit 1
    fi
    
    # Check cluster connection
    if kubectl cluster-info &> /dev/null; then
        print_success "Connected to Kubernetes cluster"
    else
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check namespace
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        print_success "Namespace $NAMESPACE exists"
    else
        print_error "Namespace $NAMESPACE does not exist"
        exit 1
    fi
}

# Setup port forwarding
setup_port_forward() {
    print_header "Setting Up Port Forwarding"
    
    # Kill existing port-forward if any
    pkill -f "port-forward.*${SERVICE_NAME}" || true
    sleep 2
    
    # Start new port-forward in background
    kubectl port-forward "svc/${SERVICE_NAME}" "${PORT}:${PORT}" -n "$NAMESPACE" &> /tmp/port-forward.log &
    PORT_FORWARD_PID=$!
    
    # Wait for port-forward to be ready
    sleep 5
    
    # Test connection
    if curl -s -X POST "$SERVICE_URL" -H "Content-Type: application/json" \
        -d '{"songs":["test"]}' &> /dev/null; then
        print_success "Port forwarding established (PID: $PORT_FORWARD_PID)"
        echo "$PORT_FORWARD_PID" > /tmp/port-forward.pid
    else
        print_error "Port forwarding failed"
        exit 1
    fi
}

# Run Test 1: Replica Scaling
run_test1() {
    print_header "Test 1: Kubernetes Deployment Changes (Replica Scaling)"
    
    print_warning "This test will modify the replica count in your deployment."
    print_warning "Make sure you have committed all changes before proceeding."
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."
    
    # Get current replica count
    CURRENT_REPLICAS=$(kubectl get deployment playlist-recommender -n "$NAMESPACE" \
        -o jsonpath='{.spec.replicas}')
    print_success "Current replicas: $CURRENT_REPLICAS"
    
    # Calculate new replica count
    if [ "$CURRENT_REPLICAS" -eq 2 ]; then
        NEW_REPLICAS=3
    else
        NEW_REPLICAS=2
    fi
    
    echo ""
    print_warning "Will change replicas from $CURRENT_REPLICAS to $NEW_REPLICAS"
    echo ""
    print_warning "Action required:"
    echo "1. In another terminal, start the monitoring script:"
    echo "   python3 scripts/test_cicd.py $SERVICE_URL -d 15 -o test1_replicas.json"
    echo ""
    echo "2. Then edit k8s/base/deployment.yaml and change replicas to $NEW_REPLICAS"
    echo "3. Commit and push the changes"
    echo ""
    read -p "Press Enter when monitoring is started and you're ready to make changes..."
    
    print_success "Test 1 setup complete. Make your changes now."
    print_warning "When the test is complete, analyze results with:"
    echo "   python3 scripts/analyze_results.py test1_replicas.json"
}

# Run Test 2: Code Update
run_test2() {
    print_header "Test 2: Code Updates (Container Image Version)"
    
    print_warning "This test will update the container image version."
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."
    
    # Get current image
    CURRENT_IMAGE=$(kubectl get deployment playlist-recommender -n "$NAMESPACE" \
        -o jsonpath='{.spec.template.spec.containers[0].image}')
    print_success "Current image: $CURRENT_IMAGE"
    
    echo ""
    print_warning "Action required:"
    echo "1. In another terminal, start the monitoring script:"
    echo "   python3 scripts/test_cicd.py $SERVICE_URL -d 20 -o test2_code.json"
    echo ""
    echo "2. Build and push new Docker image:"
    echo "   cd api"
    echo "   docker build -t docker.io/giovana2ma/playlists-frontend:0.2 ."
    echo "   docker push docker.io/giovana2ma/playlists-frontend:0.2"
    echo ""
    echo "3. Update k8s/base/deployment.yaml with new image tag"
    echo "4. Update k8s/base/configmap.yaml API_VERSION"
    echo "5. Commit and push the changes"
    echo ""
    read -p "Press Enter when monitoring is started and you're ready to make changes..."
    
    print_success "Test 2 setup complete. Make your changes now."
    print_warning "When the test is complete, analyze results with:"
    echo "   python3 scripts/analyze_results.py test2_code.json"
}

# Run Test 3: Dataset Update
run_test3() {
    print_header "Test 3: Training Dataset Update"
    
    print_warning "This test will update the ML training dataset."
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."
    
    # Get current dataset
    CURRENT_DATASET=$(kubectl get configmap playlist-config -n "$NAMESPACE" \
        -o jsonpath='{.data.DATASET_NAME}')
    print_success "Current dataset: $CURRENT_DATASET"
    
    # Determine new dataset
    if [ "$CURRENT_DATASET" = "ds1" ]; then
        NEW_DATASET="ds2"
    else
        NEW_DATASET="ds1"
    fi
    
    echo ""
    print_warning "Will change dataset from $CURRENT_DATASET to $NEW_DATASET"
    echo ""
    print_warning "Action required:"
    echo "1. In another terminal, start the monitoring script:"
    echo "   python3 scripts/test_cicd.py $SERVICE_URL -d 30 -o test3_dataset.json"
    echo ""
    echo "2. Edit k8s/base/configmap.yaml:"
    echo "   DATASET_URL: /home/datasets/spotify/2023_spotify_${NEW_DATASET}.csv"
    echo "   DATASET_NAME: $NEW_DATASET"
    echo "   MODEL_FILENAME: rules_${NEW_DATASET}.pkl"
    echo ""
    echo "3. Commit and push the changes"
    echo ""
    echo "4. Monitor ML job creation:"
    echo "   kubectl get jobs -n $NAMESPACE -w"
    echo ""
    read -p "Press Enter when monitoring is started and you're ready to make changes..."
    
    print_success "Test 3 setup complete. Make your changes now."
    print_warning "When the test is complete, analyze results with:"
    echo "   python3 scripts/analyze_results.py test3_dataset.json"
}

# Generate report
generate_report() {
    print_header "Generating Report"
    
    # Check if all test files exist
    if [ ! -f "test1_replicas.json" ]; then
        print_warning "test1_replicas.json not found - Test 1 may not be complete"
    fi
    
    if [ ! -f "test2_code.json" ]; then
        print_warning "test2_code.json not found - Test 2 may not be complete"
    fi
    
    if [ ! -f "test3_dataset.json" ]; then
        print_warning "test3_dataset.json not found - Test 3 may not be complete"
    fi
    
    # Analyze all results
    if [ -f "test1_replicas.json" ] && [ -f "test2_code.json" ] && [ -f "test3_dataset.json" ]; then
        print_success "All test results found. Generating comparison report..."
        python3 scripts/analyze_results.py test1_replicas.json test2_code.json test3_dataset.json \
            -o comparison_report.txt
        print_success "Report saved to comparison_report.txt"
    else
        print_warning "Some test results missing. Run all tests first."
    fi
    
    # Compile LaTeX report if pdflatex is available
    if command -v pdflatex &> /dev/null; then
        echo ""
        read -p "Do you want to compile the LaTeX report? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_success "Compiling LaTeX report..."
            cd scripts
            pdflatex report_template.tex
            pdflatex report_template.tex  # Run twice for TOC
            print_success "PDF report generated: scripts/report_template.pdf"
            cd ..
        fi
    else
        print_warning "pdflatex not found. Install TeX Live to compile PDF report."
        print_warning "You can compile manually with: cd scripts && pdflatex report_template.tex"
    fi
}

# Cleanup
cleanup() {
    print_header "Cleanup"
    
    # Kill port-forward
    if [ -f /tmp/port-forward.pid ]; then
        PID=$(cat /tmp/port-forward.pid)
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            print_success "Stopped port forwarding (PID: $PID)"
        fi
        rm /tmp/port-forward.pid
    fi
}

# Main menu
main_menu() {
    while true; do
        print_header "CI/CD Testing Menu"
        echo "1. Check prerequisites"
        echo "2. Setup port forwarding"
        echo "3. Run Test 1 (Replica Scaling)"
        echo "4. Run Test 2 (Code Update)"
        echo "5. Run Test 3 (Dataset Update)"
        echo "6. Generate comparison report"
        echo "7. Run all tests sequentially"
        echo "8. Cleanup and exit"
        echo ""
        read -p "Select option (1-8): " choice
        
        case $choice in
            1) check_prerequisites ;;
            2) setup_port_forward ;;
            3) run_test1 ;;
            4) run_test2 ;;
            5) run_test3 ;;
            6) generate_report ;;
            7)
                check_prerequisites
                setup_port_forward
                run_test1
                echo ""
                read -p "Test 1 complete. Press Enter to continue to Test 2..."
                run_test2
                echo ""
                read -p "Test 2 complete. Press Enter to continue to Test 3..."
                run_test3
                echo ""
                read -p "All tests complete. Press Enter to generate report..."
                generate_report
                ;;
            8)
                cleanup
                print_success "Goodbye!"
                exit 0
                ;;
            *) print_error "Invalid option" ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Handle Ctrl+C
trap cleanup EXIT

# Run main menu
main_menu
