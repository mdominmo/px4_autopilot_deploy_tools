#!/bin/bash
#
# Revierte los cambios hechos por compartir_internet.sh:
# quita las reglas de NAT/forwarding y desactiva ip_forward.
#
# Ejecutar con: sudo bash deshacer_compartir_internet.sh [LAN_IFACE] [WAN_IFACE]
#
set -euo pipefail

# Deben coincidir con los usados en compartir_internet.sh
LAN_IFACE="${1:-eth0}"
WAN_IFACE="${2:-wlan0}"

iptables -t nat -D POSTROUTING -o "$WAN_IFACE" -j MASQUERADE 2>/dev/null || true
iptables -D FORWARD -i "$LAN_IFACE" -o "$WAN_IFACE" -j ACCEPT 2>/dev/null || true
iptables -D FORWARD -i "$WAN_IFACE" -o "$LAN_IFACE" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true

sysctl -w net.ipv4.ip_forward=0
sed -i '/^net\.ipv4\.ip_forward/d' /etc/sysctl.conf

if command -v netfilter-persistent >/dev/null; then
  netfilter-persistent save
fi

echo "Reglas de NAT/forwarding eliminadas y ip_forward desactivado."
