#!/bin/bash
#
# Convierte este PC en gateway de Internet para la red del router donde
# está la Jetson, usando como salida la conexión WiFi al hotspot del móvil.
#
# Topología:
#
#   Móvil (hotspot WiFi) --- wlan0 [PC] eth0 --- Router (sin Internet) --- WiFi --- Jetson
#
# La comunicación Jetson <-> PC a través del router (misma subred) no se ve
# afectada: solo se redirige el tráfico hacia fuera de esa subred.
#
# Ejecutar con: sudo bash compartir_internet.sh [LAN_IFACE] [WAN_IFACE]
#
set -euo pipefail

# --- CONFIGURACIÓN: ajusta estos nombres a los de tu equipo ---
# Interfaz conectada al router donde está la Jetson (suele ser eth0/enp...)
LAN_IFACE="${1:-eno1}"
# Interfaz conectada al hotspot del móvil (suele ser wlan0/wlp...)
WAN_IFACE="${2:-wlo1}"

echo "== Interfaces detectadas =="
ip -br addr show
echo

echo "== Comprobando que $WAN_IFACE es la salida hacia Internet =="
RUTA=$(ip route get 8.8.8.8 2>/dev/null | head -1 || true)
echo "$RUTA"
if [[ "$RUTA" != *"$WAN_IFACE"* ]]; then
  echo
  echo "AVISO: la ruta hacia 8.8.8.8 no usa $WAN_IFACE."
  echo "Revisa 'ip route' y ajusta las métricas (o LAN_IFACE/WAN_IFACE arriba)"
  echo "para que el tráfico a Internet salga por $WAN_IFACE."
  echo
fi

# --- 1) Habilitar reenvío de paquetes IPv4 (y dejarlo persistente) ---
sysctl -w net.ipv4.ip_forward=1
sed -i '/^net\.ipv4\.ip_forward/d' /etc/sysctl.conf
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

# --- 2) NAT: enmascarar el tráfico que sale hacia el móvil ---
iptables -t nat -C POSTROUTING -o "$WAN_IFACE" -j MASQUERADE 2>/dev/null \
  || iptables -t nat -A POSTROUTING -o "$WAN_IFACE" -j MASQUERADE

# --- 3) Permitir el reenvío entre la red de la Jetson e Internet ---
iptables -C FORWARD -i "$LAN_IFACE" -o "$WAN_IFACE" -j ACCEPT 2>/dev/null \
  || iptables -A FORWARD -i "$LAN_IFACE" -o "$WAN_IFACE" -j ACCEPT
iptables -C FORWARD -i "$WAN_IFACE" -o "$LAN_IFACE" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null \
  || iptables -A FORWARD -i "$WAN_IFACE" -o "$LAN_IFACE" -m state --state RELATED,ESTABLISHED -j ACCEPT

# --- 4) Aviso si ufw está activo (su política puede bloquear el FORWARD) ---
if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
  echo
  echo "AVISO: ufw está activo. Si la Jetson no consigue salir a Internet,"
  echo "edita /etc/default/ufw, pon DEFAULT_FORWARD_POLICY=\"ACCEPT\""
  echo "y ejecuta 'sudo ufw reload'."
fi

# --- 5) Persistir las reglas de iptables si está disponible ---
if command -v netfilter-persistent >/dev/null; then
  netfilter-persistent save
else
  echo
  echo "Para que las reglas de NAT sobrevivan a un reinicio:"
  echo "  sudo apt install iptables-persistent"
  echo "  sudo netfilter-persistent save"
fi

echo
echo "== Listo =="
IP_LAN=$(ip -4 -br addr show "$LAN_IFACE" | awk '{print $3}' | cut -d/ -f1)
echo "IP de este PC en la red del router ($LAN_IFACE): $IP_LAN"
echo "Usa esta IP como PC_IP en jetson/configurar_gateway.sh"
