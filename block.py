import os
import json
import hashlib
import time 

BLOCKCHAIN_DIR = "blockchain/"
DIFFICULTY = 4 # the number of leading zeros required in the hash
os.makedirs(BLOCKCHAIN_DIR, exist_ok=True)


def get_hash(prev_block):
    with open(BLOCKCHAIN_DIR + prev_block, 'rb') as f:
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

def check_integrity():
    #files = sorted(os.listdir(BLOCKCHAIN_DIR), key=lambda x: int(x))
    files = sorted([f for f in os.listdir(BLOCKCHAIN_DIR) if f.isdigit()], key=lambda x: int(x))
    results = []

    #for file in files[1:]:
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
        
        block_without_pow = {}
        for key, value in block.items():
            if key != 'proof_of_work':
                block_without_pow[key] = value
        
        payload = json.dumps(block_without_pow, sort_keys=True) + str(stored_nonce)
        recomputed = hashlib.sha256(payload.encode()).hexdigest()
        pow_ok = recomputed == stored_pow_hash and recomputed.startswith('0' * DIFFICULTY)
        
        errors = []
        if not prev_ok:
            errors.append("Previous block was changed")
        if not pow_ok:
            errors.append("Proof of work is invalid")
        
        if len(errors) == 0:
                res = 'Ok'
        else:
            res = '; '.join(errors)
        
        #if prev_hash and pow_ok:
            #res = 'Ok'
       # elif not prev_ok:
            #res = 'was changed' 
        #else: 
           # res = 'Proof of work is invalid'

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


    #blocks_count = len(os.listdir(BLOCKCHAIN_DIR))
    all_files = os.listdir(BLOCKCHAIN_DIR)
    numeric_files = []
    for file in all_files:
        if file.isdigit():
            numeric_files.append(file)
    blocks_count = len(numeric_files)
    prev_block = str(blocks_count)

    data = {
        "borrower": borrower,
        "lender": lender,
        "amount": amount,
        "prev_block": {
            "hash": get_hash(prev_block),
            "filename": prev_block
        }
    }
    
    nonce, pow_hash = mine(data)
    block = {}
    for key, value in data.items():
        block[key] = value
    block['proof_of_work'] = {"nonce": nonce, "hash": pow_hash}

    current_block = BLOCKCHAIN_DIR + str(blocks_count+ 1 )#len(os.listdir(BLOCKCHAIN_DIR)) + 1)

    with open(current_block, 'w') as f:
        json.dump(block, f, indent=4, ensure_ascii=False)
        f.write('\n')
    
    print(f"Block {blocks_count + 1} mined: nonce={nonce}, hash={pow_hash}")

def main():
   # write_block(borrower = 'andrew', lender = 'kate', amount = 100 )
   check_integrity()

if __name__ == '__main__':
    main()