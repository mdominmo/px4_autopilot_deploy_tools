#!/bin/bash

JETSON_USER="grvc"
JETSON_IP="${1:-10.100.100.30}"
JETSON_HOST="${JETSON_USER}@${JETSON_IP}"

PX4_LOCAL="/home/manuel/repositories/own/px4_autopilot_deploy_tools/"
PX4_REMOTE="/home/grvc/repositories/px4_autopilot_deploy_tools/"

ORIGAMI_LOCAL="/home/manuel/repositories/work/origami-swarming/"
ORIGAMI_REMOTE="/home/grvc/repositories/origami-swarming/"

RSYNC_OPTS="-avz --delete --exclude='.git/' --exclude='__pycache__/' --exclude='*.pyc'"

read -s -p "Contraseña SSH para ${JETSON_HOST}: " SSH_PASS
echo ""

echo "=== Sincronizando px4_autopilot_deploy_tools ==="
sshpass -p "$SSH_PASS" rsync $RSYNC_OPTS "$PX4_LOCAL" "${JETSON_HOST}:${PX4_REMOTE}"
if [ $? -ne 0 ]; then
    echo "[ERROR] Fallo al sincronizar px4_autopilot_deploy_tools"
    exit 1
fi

echo ""
echo "=== Sincronizando origami-swarming ==="
if [ ! -d "$ORIGAMI_LOCAL" ]; then
    echo "[AVISO] El directorio local $ORIGAMI_LOCAL no existe, saltando..."
else
    sshpass -p "$SSH_PASS" rsync $RSYNC_OPTS "$ORIGAMI_LOCAL" "${JETSON_HOST}:${ORIGAMI_REMOTE}"
    if [ $? -ne 0 ]; then
        echo "[ERROR] Fallo al sincronizar origami-swarming"
        exit 1
    fi
fi

echo ""
echo "Sincronización completada."
