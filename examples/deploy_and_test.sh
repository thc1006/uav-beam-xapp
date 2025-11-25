#!/bin/bash
#
# UAV Beam xApp Deployment and Testing Script
#
# This script automates the deployment of UAV Beam xApp to O-RAN SC Near-RT RIC
# and performs comprehensive validation tests.
#
# Usage:
#   ./deploy_and_test.sh [OPTIONS]
#
# Options:
#   --namespace <ns>     Kubernetes namespace (default: ricxapp)
#   --release-name <name> Helm release name (default: uav-beam-xapp)
#   --skip-build         Skip Docker image build
#   --skip-deploy        Skip Helm deployment
#   --test-only          Only run tests (skip build and deploy)
#

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
NAMESPACE="ricxapp"
RELEASE_NAME="uav-beam-xapp"
CHART_PATH="./helm/uav-beam-xapp"
IMAGE_REPO="ghcr.io/thc1006/uav-beam-xapp"
IMAGE_TAG="0.1.0"
SKIP_BUILD=false
SKIP_DEPLOY=false
TEST_ONLY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --release-name)
            RELEASE_NAME="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-deploy)
            SKIP_DEPLOY=true
            shift
            ;;
        --test-only)
            TEST_ONLY=true
            SKIP_BUILD=true
            SKIP_DEPLOY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "================================================================"
    echo "$1"
    echo "================================================================"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    local missing_tools=()

    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi

    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi

    if ! command -v helm &> /dev/null; then
        missing_tools+=("helm")
    fi

    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi

    log_success "All prerequisites satisfied"

    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    log_success "Kubernetes cluster accessible"

    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE does not exist. Creating..."
        kubectl create namespace "$NAMESPACE"
        log_success "Namespace created"
    fi
}

# Build Docker image
build_image() {
    if [ "$SKIP_BUILD" = true ]; then
        log_info "Skipping Docker image build"
        return
    fi

    print_header "Building Docker Image"

    log_info "Building $IMAGE_REPO:$IMAGE_TAG"

    if docker build -t "$IMAGE_REPO:$IMAGE_TAG" .; then
        log_success "Docker image built successfully"
    else
        log_error "Docker build failed"
        exit 1
    fi

    # Optionally push to registry
    read -p "Push image to registry? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Pushing image to registry..."
        docker push "$IMAGE_REPO:$IMAGE_TAG"
        log_success "Image pushed successfully"
    fi
}

# Deploy with Helm
deploy_xapp() {
    if [ "$SKIP_DEPLOY" = true ]; then
        log_info "Skipping Helm deployment"
        return
    fi

    print_header "Deploying xApp with Helm"

    log_info "Installing/Upgrading Helm release: $RELEASE_NAME"

    if helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" \
        --namespace "$NAMESPACE" \
        --set image.repository="$IMAGE_REPO" \
        --set image.tag="$IMAGE_TAG" \
        --wait \
        --timeout 5m; then
        log_success "Helm deployment successful"
    else
        log_error "Helm deployment failed"
        exit 1
    fi
}

# Wait for pod to be ready
wait_for_pod() {
    print_header "Waiting for xApp Pod"

    log_info "Waiting for pod to be ready (timeout: 5 minutes)..."

    if kubectl wait --for=condition=ready pod \
        -l "app.kubernetes.io/name=uav-beam-xapp" \
        -n "$NAMESPACE" \
        --timeout=5m; then
        log_success "Pod is ready"
    else
        log_error "Pod failed to become ready"
        kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=uav-beam-xapp"
        exit 1
    fi
}

# Run validation tests
run_tests() {
    print_header "Running Validation Tests"

    local pod_name
    pod_name=$(kubectl get pod -n "$NAMESPACE" \
        -l "app.kubernetes.io/name=uav-beam-xapp" \
        -o jsonpath='{.items[0].metadata.name}')

    if [ -z "$pod_name" ]; then
        log_error "Cannot find xApp pod"
        exit 1
    fi

    log_info "Testing pod: $pod_name"

    # Test 1: Check pod status
    log_info "Test 1: Checking pod status..."
    if kubectl get pod "$pod_name" -n "$NAMESPACE" | grep -q "Running"; then
        log_success "Pod is running"
    else
        log_error "Pod is not running"
        kubectl describe pod "$pod_name" -n "$NAMESPACE"
        return 1
    fi

    # Test 2: Check container logs for errors
    log_info "Test 2: Checking container logs..."
    if kubectl logs "$pod_name" -n "$NAMESPACE" --tail=50 | grep -qi "error\|fatal"; then
        log_warning "Found errors in logs:"
        kubectl logs "$pod_name" -n "$NAMESPACE" --tail=50 | grep -i "error\|fatal"
    else
        log_success "No errors in recent logs"
    fi

    # Test 3: Check RMR initialization
    log_info "Test 3: Checking RMR initialization..."
    if kubectl logs "$pod_name" -n "$NAMESPACE" | grep -q "RMR initialization complete"; then
        log_success "RMR initialized successfully"
    else
        log_warning "RMR initialization message not found"
    fi

    # Test 4: Health check
    log_info "Test 4: Testing health endpoint..."
    if kubectl exec "$pod_name" -n "$NAMESPACE" -- curl -f http://localhost:8080/health > /dev/null 2>&1; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
    fi

    # Test 5: Check ConfigMap
    log_info "Test 5: Checking ConfigMap..."
    if kubectl get configmap "${RELEASE_NAME}-config" -n "$NAMESPACE" > /dev/null 2>&1; then
        log_success "ConfigMap exists"
    else
        log_error "ConfigMap not found"
    fi

    # Test 6: Check Services
    log_info "Test 6: Checking Services..."
    local svc_count
    svc_count=$(kubectl get svc -n "$NAMESPACE" -l "app.kubernetes.io/name=uav-beam-xapp" --no-headers | wc -l)
    if [ "$svc_count" -ge 2 ]; then
        log_success "Found $svc_count services (HTTP + RMR)"
    else
        log_error "Expected 2 services, found $svc_count"
    fi

    # Test 7: Check RMR ports
    log_info "Test 7: Checking RMR ports..."
    if kubectl exec "$pod_name" -n "$NAMESPACE" -- netstat -an | grep -q "4560\|4561"; then
        log_success "RMR ports are listening"
    else
        log_warning "RMR ports may not be listening (netstat check failed)"
    fi

    # Test 8: Check SDL connection (if enabled)
    log_info "Test 8: Checking SDL connection..."
    if kubectl logs "$pod_name" -n "$NAMESPACE" | grep -q "SDL.*connected\|Redis.*connected"; then
        log_success "SDL connection established"
    else
        log_warning "SDL connection status unclear"
    fi
}

# Display xApp information
display_info() {
    print_header "xApp Deployment Information"

    local pod_name
    pod_name=$(kubectl get pod -n "$NAMESPACE" \
        -l "app.kubernetes.io/name=uav-beam-xapp" \
        -o jsonpath='{.items[0].metadata.name}')

    echo "Namespace:     $NAMESPACE"
    echo "Release Name:  $RELEASE_NAME"
    echo "Pod Name:      $pod_name"
    echo ""

    log_info "Services:"
    kubectl get svc -n "$NAMESPACE" -l "app.kubernetes.io/name=uav-beam-xapp"

    echo ""
    log_info "Pods:"
    kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=uav-beam-xapp"

    echo ""
    log_info "Recent logs (last 20 lines):"
    kubectl logs "$pod_name" -n "$NAMESPACE" --tail=20
}

# Cleanup function
cleanup() {
    read -p "Uninstall xApp? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Uninstalling xApp..."
        helm uninstall "$RELEASE_NAME" -n "$NAMESPACE"
        log_success "xApp uninstalled"
    fi
}

# Main execution
main() {
    print_header "UAV Beam xApp Deployment and Testing"

    echo "Configuration:"
    echo "  Namespace:     $NAMESPACE"
    echo "  Release:       $RELEASE_NAME"
    echo "  Image:         $IMAGE_REPO:$IMAGE_TAG"
    echo "  Skip Build:    $SKIP_BUILD"
    echo "  Skip Deploy:   $SKIP_DEPLOY"
    echo "  Test Only:     $TEST_ONLY"
    echo ""

    check_prerequisites
    build_image
    deploy_xapp

    if [ "$SKIP_DEPLOY" = false ]; then
        wait_for_pod
    fi

    run_tests
    display_info

    echo ""
    log_success "All tasks completed!"

    # Offer cleanup
    echo ""
    cleanup
}

# Run main function
main
