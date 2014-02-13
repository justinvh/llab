import hashlib
import random
import struct

from Crypto.Cipher import AES

from llab.web import settings

mode = AES.MODE_CBC

def encrypt(text, password):
    key = hashlib.sha256(settings.SECRET_KEY + password).digest()
    iv = ''.join(chr(random.randint(0, 0xFF)) for i in range(16))
    encryptor = AES.new(key, mode, iv)
    content_size = len(text)
    pad_size = content_size % 16 if content_size > 16 else 16 - content_size
    data = struct.pack('<Q', content_size) + iv
    return data + encryptor.encrypt(text + (' ' * pad_size))


def decrypt(cipher, password):
    key = hashlib.sha256(settings.SECRET_KEY + password).digest()
    q = struct.calcsize('Q')
    size = struct.unpack('<Q', cipher[:q])[0]
    iv = cipher[q:q + 16]
    decryptor = AES.new(key, mode, iv)
    return decryptor.decrypt(cipher[q + 16:])[:size]
