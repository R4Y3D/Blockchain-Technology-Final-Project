import os
import json
import hashlib
import time
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError

BLOCKCHAIN_DIR = "blockchain/"
DIFFICULTY = 4
os.makedirs(BLOCKCHAIN_DIR, exist_ok=True)


# --- Hashing & Mining ---

def get_hash(filename):
    with open(BLOCKCHAIN_DIR + filename, 'rb') as f:
        content = f.read()
    return hashlib.sha256(content).hexdigest()


def mine(data: dict, difficulty: int = DIFFICULTY) -> tuple[int, str]:
    nonce = 0
    prefix = '0' * difficulty
    payload = json.dumps(data, sort_keys=True)
    while True:
        candidate = payload + str(nonce)
        hash_result = hashlib.sha256(candidate.encode()).hexdigest()
        if hash_result.startswith(prefix):
            return nonce, hash_result
        nonce += 1


# --- Digital Signatures ---
#
# How this works in three steps:
#
#   1. generate_keypair()
#      Creates a private key and a matching public key using the SECP256k1
#      elliptic curve (the same curve Bitcoin uses). The private key is secret: 
#      only the borrower keeps it. The public key is stored in the block so
#      anyone can verify the signature later.
#
#   2. sign_transaction(private_key_pem, tx_data)
#      Takes the borrower's private key and the transaction dict, serializes the
#      dict to a deterministic JSON string (sort_keys=True so key order never
#      changes), then produces a signature. Only someone who holds the exact same
#      private key could produce this same signature for this same data.
#
#   3. verify_signature(public_key_pem, tx_data, signature_hex)
#      Anyone, including the integrity checker, can take the public key, the
#      same transaction dict, and the signature and confirm they match.
#      If the transaction data was changed even one character, verification fails.

def generate_keypair() -> tuple[str, str]:
    signing_key = SigningKey.generate(curve=SECP256k1)
    verifying_key = signing_key.get_verifying_key()
    private_pem = signing_key.to_pem().decode()
    public_pem = verifying_key.to_pem().decode()
    return private_pem, public_pem


def extract_public_key(private_key_pem: str) -> str:
    try:
        sk = SigningKey.from_pem(private_key_pem.strip())
        return sk.get_verifying_key().to_pem().decode()
    except Exception as e:
        raise ValueError("Invalid private key") from e


def sign_transaction(private_key_pem: str, tx_data: dict) -> str:
    signing_key = SigningKey.from_pem(private_key_pem)
    message = json.dumps(tx_data, sort_keys=True).encode()
    signature = signing_key.sign(message, hashfunc=hashlib.sha256)
    return signature.hex()


def verify_signature(public_key_pem: str, tx_data: dict, signature_hex: str) -> bool:
    try:
        verifying_key = VerifyingKey.from_pem(public_key_pem)
        message = json.dumps(tx_data, sort_keys=True).encode()
        verifying_key.verify(bytes.fromhex(signature_hex), message, hashfunc=hashlib.sha256)
        return True
    except (BadSignatureError, Exception):
        return False


# --- Chain Management ---

def create_genesis_block():
    genesis_path = BLOCKCHAIN_DIR + "1"
    if os.path.exists(genesis_path):
        return
    genesis = {
        "borrower": "Genesis",
        "lender": "Genesis",
        "amount": 0,
        "timestamp": 0,
        "prev_block": {"hash": "", "filename": ""},
        "proof_of_work": {"nonce": 0, "hash": ""}
    }
    with open(genesis_path, 'w') as f:
        json.dump(genesis, f, indent=4, ensure_ascii=False)
        f.write('\n')


def get_chain():
    files = sorted([f for f in os.listdir(BLOCKCHAIN_DIR) if f.isdigit()], key=lambda x: int(x))
    chain = []
    for file in files:
        with open(BLOCKCHAIN_DIR + file) as f:
            block = json.load(f)
        block['block_number'] = int(file)
        chain.append(block)
    return chain


def check_integrity():
    files = sorted([f for f in os.listdir(BLOCKCHAIN_DIR) if f.isdigit()], key=lambda x: int(x))
    results = []

    for file in files:
        with open(BLOCKCHAIN_DIR + file) as f:
            block = json.load(f)
        prev_filename = block.get('prev_block').get('filename')

        if prev_filename == "":
            print(f'Block {file}: Ok')
            results.append({'block': file, 'result': 'Ok'})
            continue

        errors = []

        # Check 1: has the previous block's file been tampered with?
        prev_hash = block.get('prev_block').get('hash')
        actual_hash = get_hash(prev_filename)
        if prev_hash != actual_hash:
            errors.append("Previous block was changed")

        # Check 2: is the proof-of-work still valid?
        stored_nonce = block.get('proof_of_work', {}).get('nonce')
        stored_pow_hash = block.get('proof_of_work', {}).get('hash')
        block_without_pow = {k: v for k, v in block.items() if k != 'proof_of_work'}
        payload = json.dumps(block_without_pow, sort_keys=True) + str(stored_nonce)
        recomputed = hashlib.sha256(payload.encode()).hexdigest()
        pow_ok = recomputed == stored_pow_hash and recomputed.startswith('0' * DIFFICULTY)
        if not pow_ok:
            errors.append("Proof of work is invalid")

        # Check 3: if the block has a digital signature, verify it.
        # Blocks without a signature (older blocks) are skipped: not penalized.
        public_key_pem = block.get('public_key')
        sig_hex = block.get('signature')
        if public_key_pem and sig_hex:
            tx_fields = {k: block[k] for k in ('borrower', 'lender', 'amount', 'timestamp') if k in block}
            if not verify_signature(public_key_pem, tx_fields, sig_hex):
                errors.append("Signature is invalid")

        res = 'Ok' if not errors else '; '.join(errors)
        print(f'Block {file}: {res}')
        results.append({'block': file, 'result': res})

    return results


def write_block(borrower, lender, amount, private_key_pem=None):
    if not borrower or not lender:
        raise ValueError("Borrower and lender are required")

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("Amount must be a positive number")

    create_genesis_block()

    numeric_files = [f for f in os.listdir(BLOCKCHAIN_DIR) if f.isdigit()]
    blocks_count = len(numeric_files)
    prev_block = str(blocks_count)

    # The transaction fields are what the borrower signs.
    # We capture the timestamp here so the signature commits to an exact moment.
    tx_fields = {
        "borrower": borrower,
        "lender": lender,
        "amount": amount,
        "timestamp": time.time(),
    }

    # If the borrower provided their private key, sign the transaction.
    # The public key and signature are stored in the block alongside the data.
    if private_key_pem:
        public_key_pem = SigningKey.from_pem(private_key_pem).get_verifying_key().to_pem().decode()
        tx_fields["public_key"] = public_key_pem
        tx_fields["signature"] = sign_transaction(private_key_pem, {
            "borrower": borrower,
            "lender": lender,
            "amount": amount,
            "timestamp": tx_fields["timestamp"],
        })

    data = {
        **tx_fields,
        "prev_block": {
            "hash": get_hash(prev_block),
            "filename": prev_block
        }
    }

    nonce, pow_hash = mine(data)
    block = {**data, "proof_of_work": {"nonce": nonce, "hash": pow_hash}}

    with open(BLOCKCHAIN_DIR + str(blocks_count + 1), 'w') as f:
        json.dump(block, f, indent=4, ensure_ascii=False)
        f.write('\n')

    print(f"Block {blocks_count + 1} mined: nonce={nonce}, hash={pow_hash}")


if __name__ == '__main__':
    check_integrity()
