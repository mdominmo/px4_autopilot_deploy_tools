#!/bin/bash
#
# CASO: Jetson conectada DIRECTAMENTE POR CABLE al PC (misma subred,
# sin router de por medio).
#
# Revierte los cambios hechos por configurar_gateway_cable_directo.sh:
# quita el gateway y el DNS manual del perfil de conexion estatico de la
# interfaz ethernet, dejando a la Jetson sin salida a Internet por ahi
# (solo conectividad directa con el PC en su subred).
#
# Ejecutar en la Jetson, con sudo:
#   sudo bash restaurar_gateway_cable_directo.sh [IFACE]
#
set -euo pipefail

IFACE="${1:-enP8p1s0}"
CON_NAME="static-${IFACE}"

if ! nmcli -t -f NAME connection show | grep -qx "$CON_NAME"; then
  echo "No se encontro el perfil '$CON_NAME'."
  exit 1
fi

nmcli connection modify "$CON_NAME" \
    ipv4.gateway "" \
    ipv4.ignore-auto-dns no \
    ipv4.dns ""

nmcli connection up "$CON_NAME"

echo
echo "== Rutas actuales =="
ip route
