import hashlib
import random
import struct
import base64

from itertools import izip

from Crypto.Cipher import AES

from llab.web import settings

mode = AES.MODE_CBC


def encrypt(text, password):
    key = hashlib.sha256(settings.SECRET_KEY + password).digest()
    iv = ''.join(chr(random.randint(0, 0xFF)) for i in range(16))
    encryptor = AES.new(key, mode, iv)
    content_size = len(text)
    pad_size = 0
    if content_size % 16 > 0:
        pad_size = 16 - (content_size % 16)
    data = struct.pack('<Q', content_size) + iv
    message = data + encryptor.encrypt(text + (' ' * pad_size))
    digest = hashlib.sha1(password).hexdigest()
    sha1 = ':'.join('{}{}'.format(*a) for a in izip(digest[::2], digest[1::2]))
    return base64.b64encode(message), sha1


def decrypt(cipher, password):
    key = hashlib.sha256(settings.SECRET_KEY + password).digest()
    cipher = base64.b64decode(cipher)
    q = struct.calcsize('Q')
    size = struct.unpack('<Q', cipher[:q])[0]
    iv = cipher[q:q + 16]
    decryptor = AES.new(key, mode, iv)
    return decryptor.decrypt(cipher[q + 16:])[:size]
