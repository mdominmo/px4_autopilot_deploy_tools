#!/bin/bash
#
# CASO: Jetson conectada DIRECTAMENTE POR CABLE al PC (misma subred,
# sin router de por medio), p.ej. PC en 10.100.100.50/24 y Jetson en
# 10.100.100.30/24.
#
# Hace que la Jetson salga a Internet a traves del PC: anade el PC como
# gateway por defecto y configura DNS publicos en el perfil de conexion
# estatico de la interfaz ethernet (el creado por set_eth_ip_persistent.sh).
#
# Requiere que el PC ya tenga el reenvio/NAT activo, ejecutando ANTES:
#   sudo bash pc/compartir_internet.sh <iface_jetson> <iface_internet>
#
# Ejecutar en la Jetson, con sudo:
#   sudo bash configurar_gateway_cable_directo.sh [PC_IP] [IFACE]
#
set -euo pipefail

# IP del PC en la interfaz conectada por cable a la Jetson
PC_IP="${1:-10.100.100.50}"
# Interfaz ethernet de la Jetson conectada al PC
IFACE="${2:-enP8p1s0}"
CON_NAME="static-${IFACE}"

if ! nmcli -t -f NAME connection show | grep -qx "$CON_NAME"; then
  echo "No se encontro el perfil '$CON_NAME'."
  echo "Configura primero la IP estatica con:"
  echo "  sudo bash set_eth_ip_persistent.sh $IFACE <IP> <PREFIX>"
  exit 1
fi

nmcli connection modify "$CON_NAME" \
    ipv4.gateway "$PC_IP" \
    ipv4.ignore-auto-dns yes \
    ipv4.dns "8.8.8.8 1.1.1.1"

nmcli connection up "$CON_NAME"

echo
echo "== Rutas actuales =="
ip route
echo
echo "Prueba con: ping -c 3 8.8.8.8"
