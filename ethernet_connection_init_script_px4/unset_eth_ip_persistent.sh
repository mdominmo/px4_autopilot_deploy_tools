#!/bin/bash
# Revierte lo hecho por set_eth_ip_persistent.sh:
# - elimina el perfil "static-<interfaz>" de NetworkManager
# - limpia IPs manuales que pudieran quedar en la interfaz
# - deja la interfaz en modo automatico/DHCP (configuracion por defecto)

IFACE="${1:-enP8p1s0}"
CON_NAME="static-${IFACE}"

if ! ip link show "$IFACE" &>/dev/null; then
    echo "Error: interfaz '$IFACE' no encontrada"
    echo "Interfaces disponibles:"
    ip -br link show | awk '{print "  " $1}'
    exit 1
fi

if ! command -v nmcli &>/dev/null; then
    echo "nmcli no encontrado. Instala con: sudo apt install network-manager"
    exit 1
fi

if nmcli -t -f NAME connection show | grep -qx "$CON_NAME"; then
    echo "Eliminando perfil persistente '$CON_NAME'..."
    nmcli connection delete "$CON_NAME"
else
    echo "No existe el perfil '$CON_NAME', nada que eliminar."
fi

echo "Limpiando IPs manuales en $IFACE..."
sudo ip addr flush dev "$IFACE" 2>/dev/null || ip addr flush dev "$IFACE" 2>/dev/null || \
    echo "(No se pudieron limpiar IPs manuales, ejecuta con sudo si quedan restos)"

echo "Reconectando $IFACE con configuracion por defecto..."
nmcli device connect "$IFACE" &>/dev/null || \
    echo "(No se pudo reconectar ahora, NetworkManager lo hara solo cuando haya enlace)"

echo ""
echo "Interfaz $IFACE devuelta a su configuracion por defecto."
ip addr show "$IFACE"
