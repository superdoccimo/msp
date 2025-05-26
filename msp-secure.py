import socket
import struct
import threading
import argparse
import hashlib
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

# MSP Protocol Constants
SYNC = b'\xAA\x55'
VERSION = 2  # Updated for secure version
TYPE_DATA = 0x10
TYPE_ACK = 0x11
TYPE_ENCRYPTED_DATA = 0x20  # New type for encrypted data

class MSPSecure:
    def __init__(self, password=None):
        """
        Initialize MSP Secure with optional password for encryption
        """
        self.password = password
        self.key = None
        if password:
            # Derive AES key from password using SHA-256
            self.key = hashlib.sha256(password.encode()).digest()
    
    def _pad_data(self, data):
        """Add PKCS7 padding to data"""
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data)
        padded_data += padder.finalize()
        return padded_data
    
    def _unpad_data(self, data):
        """Remove PKCS7 padding from data"""
        unpadder = padding.PKCS7(128).unpadder()
        unpadded_data = unpadder.update(data)
        unpadded_data += unpadder.finalize()
        return unpadded_data
    
    def encrypt_payload(self, payload):
        """Encrypt payload using AES-CBC"""
        if not self.key:
            return payload.encode('utf-8'), False
        
        # Generate random IV
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Pad and encrypt
        padded_payload = self._pad_data(payload.encode('utf-8'))
        encrypted_data = encryptor.update(padded_payload) + encryptor.finalize()
        
        # Return IV + encrypted data
        return iv + encrypted_data, True
    
    def decrypt_payload(self, encrypted_data):
        """Decrypt payload using AES-CBC"""
        if not self.key:
            return encrypted_data.decode('utf-8')
        
        # Extract IV and encrypted data
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        # Decrypt and unpad
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        payload = self._unpad_data(padded_data)
        
        return payload.decode('utf-8')

def build_packet(packet_type, payload, msp_secure=None):
    """Build MSP packet with optional encryption"""
    if msp_secure and msp_secure.key and packet_type == TYPE_DATA:
        # Encrypt the payload
        encrypted_payload, is_encrypted = msp_secure.encrypt_payload(payload)
        if is_encrypted:
            packet_type = TYPE_ENCRYPTED_DATA
        payload_bytes = encrypted_payload
    else:
        payload_bytes = payload.encode('utf-8')
    
    header = struct.pack('!2sHBB', SYNC, len(payload_bytes) + 7, VERSION, packet_type)
    crc = sum(payload_bytes) % 256
    return header + payload_bytes + struct.pack('B', crc)

def parse_packet(data, msp_secure=None):
    """Parse MSP packet with optional decryption"""
    if data[:2] != SYNC:
        return None, 'Invalid SYNC'
    
    total_length = struct.unpack('!H', data[2:4])[0]
    version, packet_type = data[4], data[5]
    payload_bytes = data[6:-1]
    crc = data[-1]
    
    if sum(payload_bytes) % 256 != crc:
        return None, 'CRC mismatch'
    
    # Decrypt if necessary
    if packet_type == TYPE_ENCRYPTED_DATA and msp_secure and msp_secure.key:
        try:
            payload = msp_secure.decrypt_payload(payload_bytes)
        except Exception as e:
            return None, f'Decryption failed: {e}'
    else:
        payload = payload_bytes.decode('utf-8')
    
    return {
        'version': version,
        'type': packet_type,
        'payload': payload,
        'encrypted': packet_type == TYPE_ENCRYPTED_DATA
    }, None

class MSPSecureServer:
    def __init__(self, host='0.0.0.0', port=9009, password=None):
        self.host = host
        self.port = port
        self.msp_secure = MSPSecure(password)
        self.encryption_status = "🔐 AES Encrypted" if password else "🔓 Plain Text"

    def handle_client(self, conn, addr):
        print(f"[+] Connected by {addr} - {self.encryption_status}")
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                
                pkt, err = parse_packet(data, self.msp_secure)
                if err:
                    print(f"[!] Error: {err}")
                    continue
                
                encryption_indicator = "🔐" if pkt.get('encrypted') else "🔓"
                print(f"[>] Received {encryption_indicator}: {pkt}")
                
                if pkt['type'] in [TYPE_DATA, TYPE_ENCRYPTED_DATA]:
                    ack = build_packet(TYPE_ACK, 'OK', self.msp_secure)
                    conn.sendall(ack)
                    
            except Exception as e:
                print(f"[!] Exception: {e}")
                break
        conn.close()
        print(f"[-] Disconnected {addr}")

    def start(self):
        print(f"[*] Starting MSP Secure Server on {self.host}:{self.port}")
        print(f"[*] Security Mode: {self.encryption_status}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.host, self.port))
                s.listen()
                s.settimeout(1.0)
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

class MSPSecureClient:
    def __init__(self, host='127.0.0.1', port=9009, password=None):
        self.host = host
        self.port = port
        self.msp_secure = MSPSecure(password)
        self.encryption_status = "🔐 AES Encrypted" if password else "🔓 Plain Text"

    def send_data(self, message):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                print(f"[*] Connecting with {self.encryption_status} mode")
                s.connect((self.host, self.port))
                
                pkt = build_packet(TYPE_DATA, message, self.msp_secure)
                s.sendall(pkt)
                
                encryption_indicator = "🔐" if self.msp_secure.key else "🔓"
                print(f"[DEBUG] Sent packet {encryption_indicator}: {message}")
                
                response = s.recv(1024)
                pkt, err = parse_packet(response, self.msp_secure)
                if err:
                    print(f"[!] Error in response: {err}")
                else:
                    print(f"[<] ACK Received: {pkt}")
        except Exception as e:
            print(f"[!] Connection failed: {e}")

def main():
    parser = argparse.ArgumentParser(description='MSP Secure Protocol - Enhanced with AES encryption')
    parser.add_argument('--mode', choices=['server', 'client'], required=True, help='Run as server or client')
    parser.add_argument('--host', default='127.0.0.1', help='Host address')
    parser.add_argument('--port', type=int, default=9009, help='Port number')
    parser.add_argument('--message', help='Message to send (client mode only)')
    parser.add_argument('--password', help='Password for AES encryption (optional)')
    parser.add_argument('--secure', action='store_true', help='Use default password for demonstration')
    
    args = parser.parse_args()
    
    # Use default password if --secure flag is used
    password = args.password
    if args.secure and not password:
        password = "MinokamoSecure2024"
        print("[*] Using default demonstration password")
    
    print(f"[DEBUG] Running in {args.mode} mode")
    print(f"[DEBUG] Encryption: {'Enabled' if password else 'Disabled'}")

    if args.mode == 'server':
        server = MSPSecureServer(args.host, args.port, password)
        server.start()
    else:
        if args.message:
            client = MSPSecureClient(args.host, args.port, password)
            client.send_data(args.message)
        else:
            print("[!] Message required in client mode")
            print("Example usage:")
            print(f"  python {__file__} --mode client --message 'Hello MSP!' --password mypassword")
            print(f"  python {__file__} --mode client --message 'Hello MSP!' --secure")

if __name__ == '__main__':
    main()