#!/bin/bash
IFACE="${1:-enP8p1s0}"
IP="${2:-10.10.10.11}"

if ! ip link show "$IFACE" &>/dev/null; then
    echo "Error: interfaz '$IFACE' no encontrada"
    echo "Interfaces disponibles:"
    ip -br link show | awk '{print "  " $1}'
    exit 1
fi

sudo ip addr flush dev "$IFACE"
sudo ip addr add "$IP/24" dev "$IFACE"
sudo ip link set "$IFACE" up

echo "Interfaz $IFACE configurada con IP $IP/24"
ip addr show "$IFACE"
