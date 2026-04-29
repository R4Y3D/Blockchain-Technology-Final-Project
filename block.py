import os
import json
import hashlib
import time

BLOCKCHAIN_DIR = "blockchain/"
DIFFICULTY = 4
os.makedirs(BLOCKCHAIN_DIR, exist_ok=True)


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

        prev_hash = block.get('prev_block').get('hash')
        stored_nonce = block.get('proof_of_work', {}).get('nonce')
        stored_pow_hash = block.get('proof_of_work', {}).get('hash')

        actual_hash = get_hash(prev_filename)
        prev_ok = prev_hash == actual_hash

        block_without_pow = {k: v for k, v in block.items() if k != 'proof_of_work'}
        payload = json.dumps(block_without_pow, sort_keys=True) + str(stored_nonce)
        recomputed = hashlib.sha256(payload.encode()).hexdigest()
        pow_ok = recomputed == stored_pow_hash and recomputed.startswith('0' * DIFFICULTY)

        errors = []
        if not prev_ok:
            errors.append("Previous block was changed")
        if not pow_ok:
            errors.append("Proof of work is invalid")

        res = 'Ok' if not errors else '; '.join(errors)
        print(f'Block {file}: {res}')
        results.append({'block': file, 'result': res})

    return results


def write_block(borrower, lender, amount):
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

    data = {
        "borrower": borrower,
        "lender": lender,
        "amount": amount,
        "timestamp": time.time(),
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
