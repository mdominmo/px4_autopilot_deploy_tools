#!/bin/bash
# Configura una IP estatica de forma PERMANENTE (persiste tras reiniciar)
# creando/actualizando un perfil de conexion en NetworkManager.
# A diferencia de set_eth_ip(s).sh, NO hace falta volver a ejecutarlo
# cada vez que arranca el equipo: NetworkManager aplica el perfil solo.

IFACE="${1:-enP8p1s0}"
IP="${2:-10.10.10.11}"
PREFIX="${3:-24}"
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

ADDRESSES="${IP}/${PREFIX}"

if nmcli -t -f NAME connection show | grep -qx "$CON_NAME"; then
    echo "Actualizando perfil existente '$CON_NAME'..."
    nmcli connection modify "$CON_NAME" \
        connection.interface-name "$IFACE" \
        ipv4.method manual \
        ipv4.addresses "$ADDRESSES" \
        connection.autoconnect yes \
        connection.autoconnect-priority 10
else
    echo "Creando perfil '$CON_NAME'..."
    nmcli connection add \
        type ethernet \
        con-name "$CON_NAME" \
        ifname "$IFACE" \
        ipv4.method manual \
        ipv4.addresses "$ADDRESSES" \
        connection.autoconnect yes \
        connection.autoconnect-priority 10
fi

echo "Aplicando configuracion..."
if nmcli connection up "$CON_NAME" &>/dev/null; then
    echo "Interfaz $IFACE activa con IP $ADDRESSES"
else
    echo "Perfil guardado, pero no se pudo activar ahora (revisa el cable/enlace)."
    echo "Se aplicara solo en cuanto la interfaz este disponible."
fi

echo ""
echo "Configuracion PERMANENTE guardada en NetworkManager (perfil '$CON_NAME')."
echo "Se aplicara sola en cada arranque, sin volver a ejecutar este script."
echo ""
ip addr show "$IFACE"
