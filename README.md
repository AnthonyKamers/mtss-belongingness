# Modification-tolerant signature scheme (MTSS)

The proposal of this application is to make a practical implementation of a `d-modification-tolerant signature scheme` (
_Modification Tolerant Signature Schemes: Location and
Correction_), where it is possible to locate modifications made in the signed document up to a certain point. For this, the file is divided into blocks, and up to `d` blocks can be modified according to the structure generated for the signature. The DOI of the original article is [10.1007/978-3-030-35423-7_2](https://doi.org/10.1007/978-3-030-35423-7_2).

This project was already used as basis for a paper that was accepted for SBSeg 2024, with the DOI [10.5753/sbseg.2024.241677](https://doi.org/10.5753/sbseg.2024.241677). The paper was made using LaTeX and the contents used can be found in [this repository](https://github.com/AnthonyKamers/paper-mtss-signer). This repository contains the python code and experiments performed for the paper; the exact version used for the paper is available at tag [`v1.0`](https://github.com/AnthonyKamers/mtss-signer/releases/tag/v1.0).

However, new modifications were performed in the code after tag `v1.0`, and new features were added. We implemented more signature schemes, consider a much larger variety of documents and corresponding block division, we developped a new construction to guarantee the support for documents with an arbitrary number of blocks (which was not possible), improved the MTSS signature operations, and we provide a practical implementation of the MTSS partial data integrity problem (implementing the protocol proposed in the SBSeg 2024 paper); moreover, we improved the performance and organization of the code. New performance experiments were conducted using the `performance/` folder, and the results are available in the same folder (under the `output/` folder).

# Using

Submodules required: liboqs, liboqs-python

Dependencies: Python 3.10, pycryptodome, galois, pytest, sympy, liboqs-python, cython, typer

Our implementation uses the library `typer` to provide a better CLI experience. The `main.py` file is responsible for the MTSS operations; the `belongingness_protocol.py` file is responsible for the partial data integrity protocol. Both files can be executed using the CLI, and for more instructions, you can use the `--help` flag.

We remark on a specific flag used on the operations: `--concatenate-strings`. If this flag is passed, we consider the MTSS operations to be performed on the concatenation of the blocks of the document, like proposed in:
Luo, D. (2024). Modification-Tolerant Signature Schemes
using Combinatorial Group Testing: Theory, Algorithms,
and Implementation. Master’s thesis, University of Ottawa.
If this flag is not provided, the algorithms will be performed as described in the original MTSS work (which is more inneficient).

### MTSS operations

```bash
python3 main.py --help
```

We provide the MTSS operations for: signing, verifying and locating (the `verify` command, and correcting (the `verify-correct` command). The documents formats supported are: .txt, .csv (with comma division and break line division), .json, .xml, .pdf, .png, .bmp, .pgm. The supported signature schemes are: RSA-2048, RSA-4096, ED25519, Dilithium2, Dilithium3, Dilithium5, Facon-padded-512, Falcon-padded-1024. The supported hash functions are: SHA-256, SHA-512, SHA3-256, SHA3-512, BLAKE2s, BLAKE2b. Multiple parameters can be defined in order to check the performance of the MTSS operations, or to test other configurations.

### Partial data integrity protocol

```bash
python belongingness_protocol.py --help
```

We separate the partial data integrity protocol in three parts: client_1, server_1, client_2. This was important to check the overall performance of the protocol, and to check the correctness of the protocol. The protocol is based on the SBSeg 2024 paper, and it is implemented in the `belongingness_protocol.py` file. The protocol is executed using the CLI, and for more instructions, you can use the `--help` flag.