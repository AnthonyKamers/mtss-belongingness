import subprocess
import traceback
from getpass import getpass
from typing import Dict, Callable, Union, List

import oqs
from Crypto.Hash import SHA256, SHA512, SHA3_256, SHA3_512
from Crypto.PublicKey import RSA, ECC
from Crypto.PublicKey.ECC import EccKey
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Signature import pkcs1_15, eddsa
import hashlib

import mtsssigner.logger as logger

SCHEME_NOT_SUPPORTED = ("Signature algorithms must be 'PKCS#1 v1.5' or 'Ed25519' or 'Dilitium2' or 'Dilitium3' or "
                        "'Dilitium5'")


class Blake2bHash:
    oid = '1.3.6.1.4.1.1722.12.2.1.16'
    algorithm = hashlib.blake2b

    content: bytes

    def __init__(self, content: bytes):
        self.content = content

    def digest(self):
        return self.algorithm(self.content).digest()


class SigScheme:
    sig_algorithm: str
    signature_length_bytes: int
    hash_function: str
    digest_size: int
    digest_size_bytes: int
    hash: Dict[str, Callable]
    get_pub_key: Dict[str, Callable]
    get_priv_key: Dict[str, Callable]

    def __init__(self, algorithm: str, hash_function: str = "SHA512"):
        self.get_priv_key = {
            "PKCS#1 v1.5": get_rsa_private_key_from_file,
            "Ed25519": get_ed25519_private_key_from_file,
            "Dilithium2": get_dilithium_private_key_from_file,
            "Dilithium3": get_dilithium_private_key_from_file,
            "Dilithium5": get_dilithium_private_key_from_file,
        }
        self.get_pub_key = {
            "PKCS#1 v1.5": RSA.import_key,
            "Ed25519": ECC.import_key,
        }
        self.hash = {
            "SHA256": SHA256.new,
            "SHA512": SHA512.new,
            "SHA3-256": SHA3_256.new,
            "SHA3-512": SHA3_512.new,
            "BLAKE2B": Blake2bHash,
        }
        if algorithm not in self.get_priv_key.keys():
            raise ValueError(SCHEME_NOT_SUPPORTED)
        if hash_function not in self.hash.keys():
            raise ValueError("Hashing algorithms must be 'SHA256', 'SHA512', 'SHA3-256' or 'SHA3-512'")
        self.sig_algorithm = algorithm
        self.hash_function = hash_function

        if self.hash_function == "BLAKE2B":
            self.digest_size = 512
        else:
            self.digest_size = int(hash_function[-3:])
        self.signature_length_bytes = 0
        self.digest_size_bytes = int(self.digest_size / 8)

    def get_digest(self, content: Union[str, bytes]) -> bytes:
        if isinstance(content, str):
            content = content.encode()
        return self.hash[self.hash_function](content).digest()

    def sign(self, private_key: Union[RsaKey, EccKey, bytes], content: Union[bytes, bytearray]) -> bytes:
        hash_now = self.hash[self.hash_function](content)
        if self.sig_algorithm == "PKCS#1 v1.5":
            return pkcs1_15.new(private_key).sign(hash_now)
        elif self.sig_algorithm == "Ed25519":
            return eddsa.new(private_key, 'rfc8032').sign(hash_now)
        elif self.sig_algorithm.startswith("Dilithium"):
            with oqs.Signature(self.sig_algorithm, private_key) as signer:
                return signer.sign(bytes(content))
        else:
            raise ValueError(SCHEME_NOT_SUPPORTED)

    def verify(self, public_key: Union[RsaKey, EccKey, bytes], content: Union[bytearray, bytes], signature: bytes) -> bool:
        hash_now = self.hash[self.hash_function](content)
        if self.sig_algorithm == "PKCS#1 v1.5":
            try:
                pkcs1_15.new(public_key).verify(hash_now, signature)
                return True
            except ValueError:
                logger.log_error(traceback.print_exc)
                return False
        elif self.sig_algorithm == "Ed25519":
            try:
                eddsa.new(public_key, 'rfc8032').verify(hash_now, signature)
                return True
            except ValueError:
                logger.log_error(traceback.print_exc)
                return False
        elif self.sig_algorithm.startswith("Dilithium"):
            try:
                with oqs.Signature(self.sig_algorithm) as verifier:
                    return verifier.verify(content, signature, public_key)
            except (TypeError, ValueError, SystemError):
                logger.log_error(traceback.print_exc)
                return False
        else:
            raise ValueError(SCHEME_NOT_SUPPORTED)

    def get_private_key(self, key_path: str) -> Union[RsaKey, EccKey, bytes]:
        private_key = self.get_priv_key[self.sig_algorithm](key_path)
        self.set_signature_length_bytes(private_key)
        return private_key

    def get_public_key(self, key_path: str) -> Union[RsaKey, EccKey]:
        if self.sig_algorithm.startswith("Dilithium"):
            with open(key_path, "rb") as key_file:
                public_key = key_file.read()
        else:
            with open(key_path, "r", encoding="utf=8") as key_file:
                public_key_str: str = key_file.read()
            public_key = self.get_pub_key[self.sig_algorithm](public_key_str)

        self.set_signature_length_bytes(public_key)
        return public_key

    def set_signature_length_bytes(self, key: Union[RsaKey, EccKey, bytes]) -> None:
        if self.sig_algorithm == "PKCS#1 v1.5":
            self.signature_length_bytes = int(key.n.bit_length() / 8)
        elif self.sig_algorithm == "Ed25519":
            self.signature_length_bytes = 64

        # https://openquantumsafe.org/liboqs/algorithms/sig/dilithium.html
        elif self.sig_algorithm == "Dilithium2":
            self.signature_length_bytes = 2420
        elif self.sig_algorithm == "Dilithium3":
            self.signature_length_bytes = 4000
        elif self.sig_algorithm == "Dilithium5":
            self.signature_length_bytes = 4864


# Retrieves a private key from password-protected PEM file using OpenSSL
def get_rsa_private_key_from_file(private_key_path: str) -> RsaKey:
    try:
        with open(private_key_path, "r", encoding="utf=8") as key_file:
            private_key_lines: List[str] = key_file.readlines()
            private_key_str: str = "\n".join(private_key_lines)
        if private_key_lines[1] == "Proc-Type: 4,ENCRYPTED\n":
            private_key_password = getpass("Enter private key password:")
        else:
            private_key_password = None
    except OSError or ValueError:
        logger.log_error(traceback.print_exc)
        private_key_password = getpass("Enter private key password:")
        open_pk_command = f"openssl rsa -in {private_key_path} -passin pass:{private_key_password}"
        process = subprocess.run(open_pk_command.split(), stdout=subprocess.PIPE, check=True)
        openssl_stdout = str(process.stdout)[2:-3]
        private_key_str = get_correct_private_key_str_from_openssl_stdout(openssl_stdout)
    return RSA.import_key(private_key_str, private_key_password)


# Retrieves a private key from password-protected PEM file using OpenSSL
def get_ed25519_private_key_from_file(private_key_path: str) -> EccKey:
    with open(private_key_path, "r", encoding="utf=8") as key_file:
        private_key_lines: List[str] = key_file.readlines()
        private_key_str: str = "\n".join(private_key_lines)
    if private_key_lines[0] == "-----BEGIN ENCRYPTED PRIVATE KEY-----":
        private_key_password = getpass("Enter private key password:")
    else:
        private_key_password = None
    return ECC.import_key(private_key_str, private_key_password)


# Retrieves a private key from bytes in a file
def get_dilithium_private_key_from_file(private_key_path: str) -> bytes:
    with open(private_key_path, "rb") as key_file:
        return key_file.read()


# Returns the correctly formatted string for creating
# a private key object from the OpenSSL process output
def get_correct_private_key_str_from_openssl_stdout(openssl_stdout: str) -> str:
    lines_key = openssl_stdout.split("\\n")
    private_key_str = lines_key[0] + "\n"
    for line in range(len(lines_key) - 2):
        private_key_str += lines_key[line + 1]
    private_key_str += "\n" + lines_key[-1]
    return private_key_str
