import hashlib
import traceback
from enum import Enum
from typing import Dict, Callable, Union

import oqs
from Crypto.Hash import SHA256, SHA512, SHA3_256, SHA3_512
from Crypto.PublicKey import RSA, ECC
from Crypto.PublicKey.ECC import EccKey
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Signature import pkcs1_15, eddsa

import mtsssigner.logger as logger
from mtsssigner.blocks.Block import Block

SCHEME_NOT_SUPPORTED = ("Signature algorithms must be 'PKCS#1 v1.5' or 'Ed25519' or 'Dilithium2' or 'Dilithium3' or"
                        "'Dilithium5' or 'Falcon-512' or 'Falcon-1024'")

RFC_ED25519 = "rfc8032"
DILITHIUM_START = "Dilithium"
FALCON_START = "Falcon"

D_BYTES_LENGTH = 2
D_BYTES_ORDER = 'big'

DIRECTORY_BLOCKS = "blocks_data"


class Blake2bHash:
    oid = '1.3.6.1.4.1.1722.12.2.1.16'
    algorithm = hashlib.blake2b

    content: bytes

    def __init__(self, content: bytes):
        self.content = content

    def digest(self):
        return self.algorithm(self.content).digest()


class Blake2sHash:
    oid = '1.3.6.1.4.1.1722.12.2.2.8'
    algorithm = hashlib.blake2s

    content: bytes

    def __init__(self, content: bytes):
        self.content = content

    def digest(self):
        return self.algorithm(self.content).digest()


class ALGORITHM(str, Enum):
    RSA = "rsa"
    ED25519 = "ed25519"
    DILITHIUM2 = "Dilithium2"
    DILITHIUM3 = "Dilithium3"
    DILITHIUM5 = "Dilithium5"
    FALCON512 = "Falcon-padded-512"
    FALCON1024 = "Falcon-padded-1024"


class HASH(str, Enum):
    SHA256 = "SHA256"
    SHA512 = "SHA512"
    SHA3_256 = "SHA3-256"
    SHA3_512 = "SHA3-512"
    BLAKE2S = "BLAKE2S"
    BLAKE2B = "BLAKE2B"


class SigScheme:
    sig_algorithm: str
    signature_length_bytes: int
    hash_function: str
    digest_size: int
    digest_size_bytes: int
    hash: Dict[str, Callable]
    get_pub_key: Dict[str, Callable]
    get_priv_key: Dict[str, Callable]

    def __init__(self, algorithm: str, hash_function: str = HASH.SHA512):
        self.get_priv_key = {
            ALGORITHM.RSA: get_rsa_private_key_from_file,
            ALGORITHM.ED25519: get_ed25519_private_key_from_file,
            ALGORITHM.DILITHIUM2: get_raw_key,
            ALGORITHM.DILITHIUM3: get_raw_key,
            ALGORITHM.DILITHIUM5: get_raw_key,
            ALGORITHM.FALCON512: get_raw_key,
            ALGORITHM.FALCON1024: get_raw_key
        }
        self.get_pub_key = {
            ALGORITHM.RSA: RSA.import_key,
            ALGORITHM.ED25519: ECC.import_key,
        }
        self.hash = {
            HASH.SHA256: SHA256.new,
            HASH.SHA512: SHA512.new,
            HASH.SHA3_256: SHA3_256.new,
            HASH.SHA3_512: SHA3_512.new,
            HASH.BLAKE2B: Blake2bHash,
            HASH.BLAKE2S: Blake2sHash,
        }

        self.sig_algorithm = algorithm
        self.hash_function = hash_function

        # get hash function size
        if self.hash_function == HASH.BLAKE2B:
            self.digest_size = 512
        elif self.hash_function == HASH.BLAKE2S:
            self.digest_size = 256
        else:
            self.digest_size = int(hash_function[-3:])

        # set signature and digest size in bytes
        self.signature_length_bytes = 0
        self.digest_size_bytes = int(self.digest_size / 8)

    def get_digest(self, content: Union[str, bytes, Block]) -> bytes:
        if isinstance(content, str) or isinstance(content, Block):
            content = str(content).encode()
        return self.hash[self.hash_function](content).digest()

    def sign(self, private_key: Union[RsaKey, EccKey, bytes], content: Union[bytes, bytearray]) -> bytes:
        hash_now = self.hash[self.hash_function](content)
        if self.sig_algorithm == ALGORITHM.RSA:
            return pkcs1_15.new(private_key).sign(hash_now)
        elif self.sig_algorithm == ALGORITHM.ED25519:
            return eddsa.new(private_key, RFC_ED25519).sign(hash_now)
        elif self.sig_algorithm.startswith(DILITHIUM_START) or self.sig_algorithm.startswith(FALCON_START):
            with oqs.Signature(self.sig_algorithm, private_key) as signer:
                return signer.sign(hash_now.digest())

    def verify(self, public_key: Union[RsaKey, EccKey, bytes], content: Union[bytearray, bytes], signature: bytes) -> bool:
        hash_now = self.hash[self.hash_function](content)
        try:
            if self.sig_algorithm == ALGORITHM.RSA:
                pkcs1_15.new(public_key).verify(hash_now, signature)
                return True
            elif self.sig_algorithm == ALGORITHM.ED25519:
                eddsa.new(public_key, RFC_ED25519).verify(hash_now, signature)
            elif self.sig_algorithm.startswith(DILITHIUM_START) or self.sig_algorithm.startswith(FALCON_START):
                with oqs.Signature(self.sig_algorithm) as verifier:
                    return verifier.verify(hash_now.digest(), signature, public_key)
        except (TypeError, ValueError, SystemError):
            logger.log_error(traceback.print_exc)
            return False

    def get_private_key(self, key_path: str) -> Union[RsaKey, EccKey, bytes]:
        private_key = self.get_priv_key[self.sig_algorithm](key_path)
        self.set_signature_length_bytes(private_key)
        return private_key

    def get_public_key(self, key_path: str) -> Union[RsaKey, EccKey]:
        if self.sig_algorithm.startswith(DILITHIUM_START) or self.sig_algorithm.startswith(FALCON_START):
            public_key = get_raw_key(key_path)
        else:
            public_key = self.get_pub_key[self.sig_algorithm](get_raw_key(key_path))

        self.set_signature_length_bytes(public_key)
        return public_key

    def set_signature_length_bytes(self, key: Union[RsaKey, EccKey, bytes]) -> None:
        if self.sig_algorithm == ALGORITHM.RSA:
            self.signature_length_bytes = int(key.n.bit_length() / 8)
        elif self.sig_algorithm == ALGORITHM.ED25519:
            self.signature_length_bytes = 64

        # https://openquantumsafe.org/liboqs/algorithms/sig/dilithium.html
        elif self.sig_algorithm == ALGORITHM.DILITHIUM2:
            self.signature_length_bytes = 2420
        elif self.sig_algorithm == ALGORITHM.DILITHIUM3:
            self.signature_length_bytes = 3293
        elif self.sig_algorithm == ALGORITHM.DILITHIUM5:
            self.signature_length_bytes = 4595

        # https://openquantumsafe.org/liboqs/algorithms/sig/falcon.html for padded
        elif self.sig_algorithm == ALGORITHM.FALCON512:
            self.signature_length_bytes = 666
        elif self.sig_algorithm == ALGORITHM.FALCON1024:
            self.signature_length_bytes = 1280


def get_rsa_private_key_from_file(private_key_path: str) -> RsaKey:
    return RSA.import_key(get_raw_key(private_key_path), None)


def get_ed25519_private_key_from_file(private_key_path: str) -> EccKey:
    return ECC.import_key(get_raw_key(private_key_path), None)


# Retrieves a private key from bytes in a file
def get_raw_key(private_key_path: str) -> bytes:
    with open(private_key_path, "rb") as key_file:
        return key_file.read()
