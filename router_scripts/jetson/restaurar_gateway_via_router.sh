#!/bin/bash
#
# CASO: Jetson conectada por WiFi a un router (sin salida a Internet),
# en la misma red que el PC.
#
# Revierte los cambios hechos por configurar_gateway_via_router.sh:
# elimina la ruta por defecto hacia el PC y vuelve al DNS automático del router.
#
# Ejecutar con: sudo bash restaurar_gateway_via_router.sh [PC_IP] [IFACE]
#
set -euo pipefail

# Deben coincidir con los usados en configurar_gateway_via_router.sh
PC_IP="${1:-192.168.1.50}"
IFACE="${2:-wlP1p1s0}"

CONEXION=$(nmcli -t -f NAME,DEVICE connection show --active | grep ":${IFACE}$" | cut -d: -f1)
if [[ -z "$CONEXION" ]]; then
  echo "No se encontró una conexión activa en $IFACE."
  echo "Revisa con: nmcli connection show --active"
  exit 1
fi
echo "Conexión activa: $CONEXION"

nmcli connection modify "$CONEXION" -ipv4.routes "0.0.0.0/0 $PC_IP 50"
nmcli connection modify "$CONEXION" ipv4.ignore-auto-dns no
nmcli connection modify "$CONEXION" -ipv4.dns "8.8.8.8 1.1.1.1"

nmcli connection up "$CONEXION"

echo
echo "== Rutas actuales =="
ip route
