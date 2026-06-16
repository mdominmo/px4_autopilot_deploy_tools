from pymavlink import mavutil
import pymavlink.mavutil as mavutil_module

original_add_message = mavutil_module.add_message
def patched_add_message(messages, mtype, msg):
    try:
        original_add_message(messages, mtype, msg)
    except TypeError:
        messages[mtype] = msg
mavutil_module.add_message = patched_add_message

mav = mavutil.mavlink_connection('/dev/ttyACM0', baud=2000000)
try:
    mav.wait_heartbeat(timeout=10)
except Exception:
    pass

print("Esperando posición GPS...")
msg = mav.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=15)
if msg is None:
    print("Error: no se recibió posición GPS.")
    exit(1)

lat = msg.lat / 1e7
lon = msg.lon / 1e7
alt = msg.alt / 1e3  # mm -> m

print(f"Posición actual: lat={lat:.7f}, lon={lon:.7f}, alt={alt:.2f}m")

mav.mav.command_long_send(
    mav.target_system, mav.target_component,
    mavutil.mavlink.MAV_CMD_DO_SET_HOME,
    0,
    0,        # param1: 0 = usar lat/lon/alt especificados (1 = posición actual del FC)
    0, 0, 0,  # param2-4: unused
    lat, lon, alt
)

ack = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
if ack and ack.command == mavutil.mavlink.MAV_CMD_DO_SET_HOME:
    if ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
        print("Home seteado correctamente.")
    else:
        print(f"Comando rechazado, result={ack.result}")
else:
    print("No se recibió ACK (el home puede haberse seteado igual).")
