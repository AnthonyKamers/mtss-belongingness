import sys
from getpass import getpass

import oqs
from Crypto.PublicKey import RSA, ECC


# Generates PKCS#1 RSA private/public key pair and writes them
# to {key_path}_priv.pem and {key_path}_pub.pem respectively
def __gen_rsa_keypair(modulus: int, key_path: str):
    key = RSA.generate(modulus)
    private_key_password = getpass(
        "Enter desired private key password (press Enter for no password):"
    )
    if private_key_password == "":
        private_key = key.export_key(pkcs=1)
    else:
        private_key = key.export_key(passphrase=private_key_password, pkcs=1)
    with open(key_path + "_priv.pem", "wb") as priv_key_file:
        priv_key_file.write(private_key)

    public_key = key.publickey().export_key()
    with open(key_path + "_pub.pem", "wb") as pub_key_file:
        pub_key_file.write(public_key)


# Generates PKCS#8 Ed25519 private/public key pair and writes them
# to {key_path}_priv.pem and {key_path}_pub.pem respectively
def __gen_ed22519_keypair(key_path: str):
    key = ECC.generate(curve="ed25519")
    private_key_password = getpass(
        "Enter desired private key password (press Enter for no password):"
    )
    if private_key_password == "":
        private_key = key.export_key(format="PEM", use_pkcs8=True)
    else:
        private_key = key.export_key(
            format="PEM",
            use_pkcs8=True,
            passphrase=private_key_password,
            protection="PBKDF2WithHMAC-SHA1AndAES128-CBC"
        )
    with open(key_path + "_priv.pem", "w") as priv_key_file:
        priv_key_file.write(private_key)

    public_key = key.public_key().export_key(format="PEM")
    with open(key_path + "_pub.pem", "w") as pub_key_file:
        pub_key_file.write(public_key)


def __gen_dilithium_keypair(key_path: str, version: str = "2"):
    __gen_generic_oqs_signature(key_path, "Dilithium", version)


def __gen_falcon_keypair(key_path: str, version: str):
    __gen_generic_oqs_signature(key_path, f"Falcon-{version}", version)


def __gen_generic_oqs_signature(key_path: str, algorithm_oqs: str, version: str):
    with oqs.Signature(algorithm_oqs) as key_pair_generator:
        public_key = key_pair_generator.generate_keypair()
        private_key = key_pair_generator.export_secret_key()

        with open(f'{key_path}_{version}_priv.key', "wb") as priv_key_file:
            priv_key_file.write(private_key)

        with open(f'{key_path}_{version}_pub.key', "wb") as pub_key_file:
            pub_key_file.write(public_key)


# python key_generator.py rsa {key name} {modulus}
# python key_generator.py ed25519 {key name}
# python key_generator.py Dilithium2 {key name}
# python key_generator.py Falcon {key name}
if __name__ == '__main__':
    algorithm = sys.argv[1].lower()
    key_name = sys.argv[2]
    if algorithm == "rsa":
        key_modulus = int(sys.argv[3])
        __gen_rsa_keypair(key_modulus, key_name)
    elif algorithm == "ed25519":
        __gen_ed22519_keypair(key_name)
    elif algorithm.startswith("dilithium"):
        __gen_dilithium_keypair(key_name, algorithm[-1])
    elif algorithm.startswith("falcon"):
        version = algorithm.split("-")[1]
        algorithm = f'falcon-padded-{version}'
        __gen_falcon_keypair(key_name, version)
    else:
        print("Unspported opperation (must be 'rsa', 'ed25519' or Dilithium2)")
