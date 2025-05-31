# Minokamo Secure Protocol (MSP)

Minokamo Secure Protocol (MSP) is a minimal, educational TCP-based protocol with CRC validation, structured binary packet format, and optional AES encryption support.

## Files

- `msp.py` - Basic MSP implementation
- `msp-secure.py` - Enhanced version with AES encryption support

## Features

- ✅ Custom binary packet structure:
  - SYNC (2 bytes)
  - LENGTH (2 bytes)
  - VERSION (1 byte)
  - TYPE (1 byte)
  - PAYLOAD (n bytes)
  - CRC (1 byte)
- ✅ Works over TCP sockets
- ✅ AES encryption support (msp-secure.py)
- ✅ Ctrl+C safe shutdown with timeout
- ✅ Multi-threaded server
- ✅ Easy to understand and extend
- ✅ Ideal for educational use or protocol experimentation

## Requirements

- Python 3.8+
- For secure version: `pip install cryptography`

## Usage

### Basic Version (msp.py)

#### Start server:
```bash
python msp.py --mode server --host 127.0.0.1 --port 9009 
```

#### Send message (client):
```bash
python msp.py --mode client --host 127.0.0.1 --port 9009 --message "Hello MSP"
```

### Secure Version (msp-secure.py)

#### Start encrypted server:
```bash
# With custom password
python msp-secure.py --mode server --password mypassword

# With demonstration password
python msp-secure.py --mode server --secure
```

#### Send encrypted message:
```bash
# With custom password
python msp-secure.py --mode client --message "Hello Secure MSP!" --password mypassword

# With demonstration password
python msp-secure.py --mode client --message "Hello Secure MSP!" --secure
```

#### Plain text mode (no encryption):
```bash
python msp-secure.py --mode server
python msp-secure.py --mode client --message "Hello MSP!"
```

## Security Features

The secure version (`msp-secure.py`) includes:
- 🔐 AES-256-CBC encryption
- 🔑 Password-based key derivation (SHA-256)
- 🎲 Random IV generation for each message
- 📦 PKCS7 padding
- 🔄 Backward compatibility with plain text mode

## Planned Features

- 🖥️ GUI tool (Tkinter)
- 📡 COM port & physical serial support
- 📁 File transfer protocol

## Protocol Diagram

![MSP Flow](msp-diagram-en.svg)

## Protocol Detailed Flow 

![MSP Flow](msp-flow-diagram-en.svg)

## References & Tutorials

- 🇺🇸 **English**: https://betelgeuse.work/python-original-protocol/
- 🇯🇵 **Japanese**: https://minokamo.tokyo/2025/05/19/9009/
- 🇮🇳 **Hindi**: https://minokamo.in/original-protocol/
- 📺 **YouTube Videos**:
- 🇺🇸 **English**: https://youtu.be/6eFuAKiCImQ
- 🇯🇵 **Japanese**: https://youtu.be/Yg8pPqAhvU0

## 📄 LICENSE

MIT License

Copyright (c) 2025 Mamu Minokamo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.