from pymavlink import mavutil
import pymavlink.mavutil as mavutil_module
import time
import struct
import argparse

original_add_message = mavutil_module.add_message
def patched_add_message(messages, mtype, msg):
    try:
        original_add_message(messages, mtype, msg)
    except TypeError:
        messages[mtype] = msg
mavutil_module.add_message = patched_add_message

parser = argparse.ArgumentParser(description='Escribe extras.txt con configuracion de red y agente UXRCE')
parser.add_argument('--px4-ip',     default='10.10.10.10', help='IP del Pixhawk en eth0 (default: 10.10.10.10)')
parser.add_argument('--agent-ip',   default='10.10.10.11', help='IP del agente UXRCE en el PC (default: 10.10.10.11)')
parser.add_argument('--agent-port', default=8888, type=int, help='Puerto del agente UXRCE (default: 8888)')
parser.add_argument('--drone-name', default='px4_1', help='Nombre del dron para el namespace UXRCE (default: px4_1)')
parser.add_argument('--mask',       default='255.255.255.0')
parser.add_argument('--device',     default='/dev/ttyACM0')
parser.add_argument('--baud',       default=2000000, type=int)
parser.add_argument('-n', '--name', default='px4_1', help='Namespace del dron para UXRCE DDS (default: px4_1)')
args = parser.parse_args()

OP_RemoveFile       = 8
OP_CreateFile       = 6
OP_TerminateSession = 1
OP_WriteFile        = 7
OP_Ack              = 128
OP_Nack             = 129

def mavftp_send(mav, opcode, session, offset, data=b'', seq=1):
    header = struct.pack('<HBBBBBBI', seq, session, opcode, len(data), 0, 0, 0, offset)
    payload = bytearray(251)
    payload[0:12] = header
    payload[12:12+len(data)] = data
    mav.mav.file_transfer_protocol_send(0, mav.target_system, mav.target_component, bytes(payload))

def wait_ack(mav, timeout=3):
    t = time.time()
    while time.time() - t < timeout:
        msg = mav.recv_match(type='FILE_TRANSFER_PROTOCOL', blocking=True, timeout=1)
        if msg:
            return bytearray(msg.payload)
    return None

def shell(mav, cmd):
    cmd = cmd + '\n'
    mav.mav.serial_control_send(
        mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL,
        mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE |
        mavutil.mavlink.SERIAL_CONTROL_FLAG_RESPOND,
        0, 0, len(cmd),
        [ord(c) for c in cmd.ljust(70, '\0')][:70]
    )
    time.sleep(0.5)
    out = ''
    while True:
        msg = mav.recv_match(type='SERIAL_CONTROL', blocking=True, timeout=1)
        if not msg:
            break
        out += bytes(msg.data[:msg.count]).decode('utf-8', errors='replace')
    print(out)

mav = mavutil.mavlink_connection(args.device, baud=args.baud)
try:
    mav.wait_heartbeat(timeout=10)
except:
    pass
print("Conectado")

content = (
    f"set +e\n"
    f"ifconfig eth0 {args.px4_ip} netmask {args.mask}\n"
    f"sleep 10\n"
    f"uxrce_dds_client stop\n"
    f"sleep 10\n"
<<<<<<< HEAD
    f"uxrce_dds_client start -t udp -h {args.agent_ip} -p {args.agent_port} -n {args.drone_name}\n"
=======
    f"uxrce_dds_client start -t udp -h {args.agent_ip} -p {args.agent_port} -n {args.name}\n"
>>>>>>> b5776e0139e3e5eadc60d827041058b06ecfb651
    f"set -e\n"
).encode()
path = b'/fs/microsd/etc/extras.txt\x00'

print(f"\nContenido a escribir:\n{content.decode()}")

mavftp_send(mav, OP_RemoveFile, 0, 0, path, seq=1)
ack = wait_ack(mav)
print(f"RemoveFile: opcode={ack[3] if ack else 'timeout'}")

mavftp_send(mav, OP_CreateFile, 0, 0, path, seq=2)
ack = wait_ack(mav)
if not ack or ack[3] == OP_Nack:
    print(f"ERROR CreateFile: {ack[12] if ack else 'timeout'}")
    exit(1)
session = ack[2]
print(f"CreateFile: opcode={ack[3]} session={session}")

mavftp_send(mav, OP_WriteFile, session, 0, content, seq=3)
ack = wait_ack(mav)
if not ack or ack[3] == OP_Nack:
    print(f"ERROR WriteFile: {ack[12] if ack else 'timeout'}")
    exit(1)
print(f"WriteFile: opcode={ack[3]} size={ack[4]}")

mavftp_send(mav, OP_TerminateSession, session, 0, seq=4)
print("Sesion cerrada")

time.sleep(0.5)
shell(mav, 'cat /fs/microsd/etc/extras.txt')
