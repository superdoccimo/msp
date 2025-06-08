import socket
import struct
import threading
import argparse

SYNC = b'\xAA\x55'
VERSION = 1
TYPE_DATA = 0x10
TYPE_ACK = 0x11

def build_packet(packet_type, payload):
    payload_bytes = payload.encode('utf-8')
    header = struct.pack('!2sHBB', SYNC, len(payload_bytes) + 7, VERSION, packet_type)
    crc = sum(payload_bytes) % 256
    return header + payload_bytes + struct.pack('B', crc)

def parse_packet(data):
    if data[:2] != SYNC:
        return None, 'Invalid SYNC'
    if len(data) < 7:
        return None, 'Packet too short'
    total_length = struct.unpack('!H', data[2:4])[0]
    if len(data) != total_length:
        return None, 'Invalid length'
    version, packet_type = data[4], data[5]
    payload = data[6:-1]
    crc = data[-1]
    if sum(payload) % 256 != crc:
        return None, 'CRC mismatch'
    return {
        'version': version,
        'type': packet_type,
        'payload': payload.decode('utf-8')
    }, None

class MSPServer:
    def __init__(self, host='0.0.0.0', port=9009):
        self.host = host
        self.port = port

    def handle_client(self, conn, addr):
        print(f"[+] Connected by {addr}")
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                pkt, err = parse_packet(data)
                if err:
                    print(f"[!] Error: {err}")
                    continue
                print(f"[>] Received: {pkt}")
                if pkt['type'] == TYPE_DATA:
                    ack = build_packet(TYPE_ACK, 'OK')
                    conn.sendall(ack)
            except Exception as e:
                print(f"[!] Exception: {e}")
                break
        conn.close()
        print(f"[-] Disconnected {addr}")

    def start(self):
        print(f"[*] Starting MSP Server on {self.host}:{self.port}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.host, self.port))
                s.listen()
                s.settimeout(1.0)  # Allow KeyboardInterrupt to be caught during accept
                print(f"[*] Listening for connections... (Ctrl+C to stop)")
                while True:
                    try:
                        conn, addr = s.accept()
                        threading.Thread(target=self.handle_client, args=(conn, addr)).start()
                    except socket.timeout:
                        continue
        except KeyboardInterrupt:
            print("\n[!] Server manually stopped.")
        except Exception as e:
            print(f"[!] Server failed to start: {e}")

class MSPClient:
    def __init__(self, host='127.0.0.1', port=9009):
        self.host = host
        self.port = port

    def send_data(self, message):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                pkt = build_packet(TYPE_DATA, message)
                s.sendall(pkt)
                print(f"[DEBUG] Sent packet: {message}")
                response = s.recv(1024)
                pkt, err = parse_packet(response)
                if err:
                    print(f"[!] Error in response: {err}")
                else:
                    print(f"[<] ACK Received: {pkt}")
        except Exception as e:
            print(f"[!] Connection failed: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['server', 'client'], required=True)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=9009)
    parser.add_argument('--message', help='Message to send (client mode only)')
    args = parser.parse_args()

    print(f"[DEBUG] Running in {args.mode} mode")

    if args.mode == 'server':
        server = MSPServer(args.host, args.port)
        server.start()
    else:
        client = MSPClient(args.host, args.port)
        if args.message:
            client.send_data(args.message)
        else:
            print("[!] Message required in client mode")
