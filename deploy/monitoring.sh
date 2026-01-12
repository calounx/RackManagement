#!/bin/bash
# HomeRack Monitoring Stack Management Script
# Manages Prometheus and Grafana monitoring services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
}

# Start monitoring stack
start_monitoring() {
    log "Starting monitoring stack..."

    # Check if homerack-network exists
    if ! docker network ls | grep -q homerack-network; then
        warning "homerack-network not found, creating it..."
        docker network create homerack-network
    fi

    # Start monitoring services
    docker-compose -f docker-compose.monitoring.yml up -d

    log "Waiting for services to be ready..."
    sleep 10

    # Check service health
    check_services

    echo ""
    info "Monitoring stack started successfully!"
    echo ""
    show_urls
}

# Stop monitoring stack
stop_monitoring() {
    log "Stopping monitoring stack..."
    docker-compose -f docker-compose.monitoring.yml down
    log "Monitoring stack stopped"
}

# Restart monitoring stack
restart_monitoring() {
    log "Restarting monitoring stack..."
    docker-compose -f docker-compose.monitoring.yml restart
    log "Monitoring stack restarted"
    show_urls
}

# Check service status
check_services() {
    echo ""
    info "Service Status:"
    echo "----------------------------------------"

    services=("prometheus" "grafana" "node-exporter" "cadvisor")

    for service in "${services[@]}"; do
        container_name="homerack-${service}"
        if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
            echo -e "${GREEN}✓${NC} ${service} is running"
        else
            echo -e "${RED}✗${NC} ${service} is not running"
        fi
    done
    echo "----------------------------------------"
}

# Show monitoring URLs
show_urls() {
    HOSTNAME=$(hostname)

    echo ""
    info "Monitoring URLs:"
    echo "----------------------------------------"
    echo -e "${BLUE}Prometheus:${NC}    http://${HOSTNAME}:9090"
    echo -e "${BLUE}Grafana:${NC}       http://${HOSTNAME}:3000"
    echo -e "                   (default: admin/admin)"
    echo -e "${BLUE}Node Exporter:${NC} http://${HOSTNAME}:9100/metrics"
    echo -e "${BLUE}cAdvisor:${NC}      http://${HOSTNAME}:8081"
    echo "----------------------------------------"
    echo ""
}

# View logs
view_logs() {
    service=$1

    if [ -z "$service" ]; then
        docker-compose -f docker-compose.monitoring.yml logs -f
    else
        docker-compose -f docker-compose.monitoring.yml logs -f "$service"
    fi
}

# Show resource usage
show_resources() {
    echo ""
    info "Container Resource Usage:"
    echo "----------------------------------------"

    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
        $(docker ps --filter "name=homerack-" --format "{{.Names}}")

    echo "----------------------------------------"
}

# Backup monitoring data
backup_monitoring() {
    log "Backing up monitoring data..."

    BACKUP_DIR="${BACKUP_DIR:-/var/backups/homerack/monitoring}"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    mkdir -p "$BACKUP_DIR"

    # Backup Prometheus data
    docker run --rm \
        -v homerack-monitoring_prometheus-data:/data \
        -v "${BACKUP_DIR}:/backup" \
        alpine \
        tar czf "/backup/prometheus_${TIMESTAMP}.tar.gz" -C /data .

    # Backup Grafana data
    docker run --rm \
        -v homerack-monitoring_grafana-data:/data \
        -v "${BACKUP_DIR}:/backup" \
        alpine \
        tar czf "/backup/grafana_${TIMESTAMP}.tar.gz" -C /data .

    log "Monitoring data backed up to: ${BACKUP_DIR}"
}

# Display help
show_help() {
    echo ""
    echo "HomeRack Monitoring Stack Management"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start monitoring stack (Prometheus + Grafana)"
    echo "  stop        - Stop monitoring stack"
    echo "  restart     - Restart monitoring stack"
    echo "  status      - Check service status"
    echo "  urls        - Show monitoring service URLs"
    echo "  logs [svc]  - View logs (optionally for specific service)"
    echo "  resources   - Show container resource usage"
    echo "  backup      - Backup monitoring data"
    echo "  help        - Show this help message"
    echo ""
    echo "Services: prometheus, grafana, node-exporter, cadvisor"
    echo ""
    echo "Examples:"
    echo "  $0 start                  # Start all monitoring services"
    echo "  $0 logs grafana          # View Grafana logs"
    echo "  $0 status                # Check service status"
    echo ""
}

# Main script logic
main() {
    check_docker

    case "${1:-help}" in
        start)
            start_monitoring
            ;;
        stop)
            stop_monitoring
            ;;
        restart)
            restart_monitoring
            ;;
        status)
            check_services
            ;;
        urls)
            show_urls
            ;;
        logs)
            view_logs "$2"
            ;;
        resources)
            show_resources
            ;;
        backup)
            backup_monitoring
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
