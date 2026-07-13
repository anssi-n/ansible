#!/usr/bin/env bash

set -euo pipefail

# Default values
LOAD_BALANCER=${LOAD_BALANCER:-0}
ETCD_NODES=${ETCD_NODES:-0}
CONTROL_PLANE_NODES=${CONTROL_PLANE_NODES:-0}
WORKER_NODES=${WORKER_NODES:-0}

# Starting IPs
LB_IP="192.168.59.20"
ETCD_IP_BASE="192.168.59."
CONTROL_IP_BASE="192.168.59."
WORKER_IP_BASE="192.168.59."

OUTPUT_FILE="${1:-inventory.ini}"

cat > "$OUTPUT_FILE" << EOF
# Auto-generated Ansible Inventory - $(date)
# LOAD_BALANCER=$LOAD_BALANCER ETCD_NODES=$ETCD_NODES CONTROL_PLANE_NODES=$CONTROL_PLANE_NODES WORKER_NODES=$WORKER_NODES

EOF

# ====================== LOAD BALANCER ======================
if [ "$LOAD_BALANCER" -eq 1 ]; then
    cat >> "$OUTPUT_FILE" << EOF
[lb_node]
lb ansible_host=$LB_IP

EOF
else
    cat >> "$OUTPUT_FILE" << EOF
[lb_node]

EOF
fi

# ====================== ETCD NODES ======================
cat >> "$OUTPUT_FILE" << EOF
[etcd_nodes]
EOF
if [ "$ETCD_NODES" -gt 0 ]; then
    for i in $(seq 1 "$ETCD_NODES"); do
        ip=$((10 + i - 1))
        echo "etcd-${i} ansible_host=${ETCD_IP_BASE}${ip}" >> "$OUTPUT_FILE"
    done
fi
echo "" >> "$OUTPUT_FILE"

# ====================== CONTROL PLANE NODES ======================
cat >> "$OUTPUT_FILE" << EOF
[control_plane_nodes]
EOF
if [ "$CONTROL_PLANE_NODES" -gt 0 ]; then
    for i in $(seq 1 "$CONTROL_PLANE_NODES"); do
        ip=$((30 + i - 1))
        echo "control-plane-${i} ansible_host=${CONTROL_IP_BASE}${ip}" >> "$OUTPUT_FILE"
    done
fi
echo "" >> "$OUTPUT_FILE"

# ====================== WORKER NODES ======================
cat >> "$OUTPUT_FILE" << EOF
[worker_nodes]
EOF
if [ "$WORKER_NODES" -gt 0 ]; then
    for i in $(seq 1 "$WORKER_NODES"); do
        ip=$((50 + i - 1))
        echo "worker-${i} ansible_host=${WORKER_IP_BASE}${ip}" >> "$OUTPUT_FILE"
    done
fi
echo "" >> "$OUTPUT_FILE"

# ====================== CHILDREN GROUPS ======================
cat >> "$OUTPUT_FILE" << EOF
[k8s_cluster:children]
control_plane_nodes
worker_nodes
etcd_nodes
EOF

echo "   Inventory successfully generated: $OUTPUT_FILE"
echo "   Load Balancer : $LOAD_BALANCER"
echo "   Etcd nodes    : $ETCD_NODES"
echo "   Control nodes : $CONTROL_PLANE_NODES"
echo "   Worker nodes  : $WORKER_NODES"
