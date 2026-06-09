#!/bin/bash
IFACE="${1:-enP8p1s0}"
SUBNET="${2:-10.10.10.0/24}"

if ! command -v nmap &>/dev/null; then
    echo "nmap no encontrado. Instala con: sudo apt install nmap"
    exit 1
fi

if ! ip link show "$IFACE" &>/dev/null; then
    echo "Error: interfaz '$IFACE' no encontrada"
    echo "Interfaces disponibles:"
    ip -br link show | awk '{print "  " $1}'
    exit 1
fi

SRC_IP=$(ip -4 addr show "$IFACE" | awk '/inet / {split($2,a,"/"); print a[1]; exit}')
if [ -z "$SRC_IP" ]; then
    echo "Error: '$IFACE' no tiene IP configurada."
    echo "Configura primero con: sudo ./set_eth_ip.sh $IFACE"
    exit 1
fi
echo "IP local: $SRC_IP"

echo "Escaneando $SUBNET en interfaz $IFACE ..."
sudo nmap -sn -e "$IFACE" -S "$SRC_IP" "$SUBNET"

echo ""
echo "Tabla ARP (hosts que respondieron recientemente):"
ip neigh show dev "$IFACE"
