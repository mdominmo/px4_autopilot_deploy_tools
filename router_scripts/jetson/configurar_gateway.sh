#!/bin/bash
#
# Hace que la Jetson saque su tráfico a Internet a través del PC,
# en lugar de a través del router (que no tiene salida a Internet).
#
# Solo cambia la ruta por defecto (0.0.0.0/0) y el DNS; la comunicación
# con el PC dentro de la subred del router sigue igual.
#
# Ejecutar DESPUÉS de pc/compartir_internet.sh, con sudo:
#   sudo bash configurar_gateway.sh [PC_IP] [IFACE]
#
set -euo pipefail

# --- CONFIGURACIÓN ---
# IP del PC en la red del router (la que imprime compartir_internet.sh)
PC_IP="${1:-192.168.1.50}"
# Interfaz WiFi de la Jetson
IFACE="${2:-wlP1p1s0}"

CONEXION=$(nmcli -t -f NAME,DEVICE connection show --active | grep ":${IFACE}$" | cut -d: -f1)
if [[ -z "$CONEXION" ]]; then
  echo "No se encontró una conexión activa en $IFACE."
  echo "Revisa con: nmcli connection show --active"
  exit 1
fi
echo "Conexión activa: $CONEXION"

# Añade una ruta por defecto hacia el PC con prioridad sobre la del router
nmcli connection modify "$CONEXION" +ipv4.routes "0.0.0.0/0 $PC_IP 50"

# El router no puede resolver hacia Internet: usar DNS públicos
nmcli connection modify "$CONEXION" ipv4.ignore-auto-dns yes
nmcli connection modify "$CONEXION" ipv4.dns "8.8.8.8 1.1.1.1"

nmcli connection up "$CONEXION"

echo
echo "== Rutas actuales =="
ip route
echo
echo "Prueba con: ping -c 3 8.8.8.8"
