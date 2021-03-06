from binascii import hexlify
from hashlib import sha256  # Python standard lib SHA2 is already in C

# from fastecdsa import _ecdsa
from .curve import P256
from .util import RFC6979


class EcdsaError(Exception):
    def __init__(self, msg):
        self.msg = msg


def sign(msg, d, curve=P256, hashfunc=sha256):
    """Sign a message using the elliptic curve digital signature algorithm.

    The elliptic curve signature algorithm works as follows:

    1. Take a hash of the message to be signed: :math:`e = hash(msg)`.
    2. Truncate :math:`e` down to :math:`q` bits, where :math:`q` is the order of the curve:
       :math:`z = e_{0-q}`.
    3. Pick a nonce :math:`k` using the process descrived in RFC6979.

    Args:
        |  msg (str): A message to be signed.
        |  d (long): An ECDSA private key.
        |  curve (fastecdsa.curve.Curve): The curve to be used to sign the message.
        |  hashfunc (_hashlib.HASH): The hash function used to compress the message.
    """
    # generate a deterministic nonce per RFC6979
    rfc6979 = RFC6979(msg, d, curve.q, hashfunc)
    k = rfc6979.gen_nonce()

    hashed = hashfunc(msg.encode()).hexdigest()
    r, s = _ecdsa.sign(hashed, str(d), str(k), curve.name)
    return (int(r), int(s))


def verify(sig, msg, Q, curve=P256, hashfunc=sha256):
    r, s = sig

    # validate Q, r, s
    if not curve.is_point_on_curve(Q):
        raise EcdsaError('Invalid public key, point is not on curve {}'.format(curve.name))
    elif r > curve.q or r < 1:
        raise EcdsaError('Invalid Signature: r is not a positive integer smaller than the curve order')
    elif s > curve.q or s < 1:
        raise EcdsaError('Invalid Signature: s is not a positive integer smaller than the curve order')

    qx, qy = Q
    hashed = hashfunc(msg.encode()).hexdigest()
    return _ecdsa.verify(str(r), str(s), hashed, str(qx), str(qy), curve.name)
