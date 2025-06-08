import os
import struct
import unittest
import importlib.machinery
import importlib.util

import msp

# Load msp-secure.py which uses a hyphen in the filename
_loader = importlib.machinery.SourceFileLoader(
    'msp_secure', os.path.join(os.path.dirname(__file__), 'msp-secure.py')
)
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
msp_secure = importlib.util.module_from_spec(_spec)
try:
    _loader.exec_module(msp_secure)
except ModuleNotFoundError:
    # cryptography dependency is missing
    msp_secure = None

class TestMSP(unittest.TestCase):
    def test_round_trip(self):
        message = 'hello'
        pkt = msp.build_packet(msp.TYPE_DATA, message)
        parsed, err = msp.parse_packet(pkt)
        self.assertIsNone(err)
        self.assertEqual(parsed['payload'], message)
        self.assertEqual(parsed['type'], msp.TYPE_DATA)
        self.assertEqual(parsed['version'], msp.VERSION)

    def test_crc_failure(self):
        message = 'crc'
        pkt = msp.build_packet(msp.TYPE_DATA, message)
        corrupted = pkt[:-1] + bytes([(pkt[-1] + 1) % 256])
        parsed, err = msp.parse_packet(corrupted)
        self.assertIsNone(parsed)
        self.assertEqual(err, 'CRC mismatch')

    def test_length_mismatch(self):
        message = 'length'
        pkt = msp.build_packet(msp.TYPE_DATA, message)
        wrong_len = struct.pack('!H', 999)
        modified = pkt[:2] + wrong_len + pkt[4:]
        parsed, err = msp.parse_packet(modified)
        self.assertIsNone(err)
        self.assertEqual(parsed['payload'], message)
        self.assertNotEqual(struct.unpack('!H', wrong_len)[0], len(modified))

    @unittest.skipIf(msp_secure is None, "cryptography library missing")
    def test_encrypted_payload(self):
        sec = msp_secure.MSPSecure(password='secret')
        message = 'secure message'
        pkt = msp_secure.build_packet(msp_secure.TYPE_DATA, message, sec)
        parsed, err = msp_secure.parse_packet(pkt, sec)
        self.assertIsNone(err)
        self.assertEqual(parsed['payload'], message)
        self.assertTrue(parsed['encrypted'])
        self.assertEqual(parsed['type'], msp_secure.TYPE_ENCRYPTED_DATA)


if __name__ == '__main__':
    unittest.main()
