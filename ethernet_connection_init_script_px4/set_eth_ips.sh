#!/bin/bash
IFACE="${1:-enP8p1s0}"
IP1="${2:-10.10.10.11}"
IP2="${3:-10.100.100.30}"

if ! ip link show "$IFACE" &>/dev/null; then
    echo "Error: interfaz '$IFACE' no encontrada"
    echo "Interfaces disponibles:"
    ip -br link show | awk '{print "  " $1}'
    exit 1
fi

sudo ip addr flush dev "$IFACE"
sudo ip addr add "$IP1/24" dev "$IFACE"
sudo ip addr add "$IP2/24" dev "$IFACE"
sudo ip link set "$IFACE" up

echo "Interfaz $IFACE configurada con IPs $IP1/24 y $IP2/24"
ip addr show "$IFACE"
