import hashlib
import json
import os
import tempfile

import block as blockchain_module


def test_mine():
    data = {"borrower": "Alice", "lender": "Bob", "amount": 500.0}
    nonce, pow_hash = blockchain_module.mine(data, difficulty=4)

    assert isinstance(nonce, int) and nonce >= 0
    assert pow_hash.startswith("0000")

    # Verify the hash is reproducible from the same data + nonce
    payload = json.dumps(data, sort_keys=True) + str(nonce)
    recomputed = hashlib.sha256(payload.encode()).hexdigest()
    assert recomputed == pow_hash


def test_signature():
    private_pem, public_pem = blockchain_module.generate_keypair()

    tx = {"borrower": "Alice", "lender": "Bob", "amount": 100.0, "timestamp": 1000000.0}
    sig = blockchain_module.sign_transaction(private_pem, tx)

    # Correct data verifies
    assert blockchain_module.verify_signature(public_pem, tx, sig) is True

    # Tampered data fails
    tampered = {**tx, "amount": 999.0}
    assert blockchain_module.verify_signature(public_pem, tampered, sig) is False


def test_integrity():
    original_dir = blockchain_module.BLOCKCHAIN_DIR
    with tempfile.TemporaryDirectory() as tmpdir:
        blockchain_module.BLOCKCHAIN_DIR = tmpdir + "/"
        try:
            # Write genesis + one valid block
            blockchain_module.write_block("Alice", "Bob", 200.0)

            results = blockchain_module.check_integrity()
            assert all(r["result"] == "Ok" for r in results), results

            # Tamper with block 2 (the non-genesis block) directly on disk
            block2_path = os.path.join(tmpdir, "2")
            with open(block2_path) as f:
                data = json.load(f)
            data["amount"] = 99999.0
            with open(block2_path, "w") as f:
                json.dump(data, f)

            results = blockchain_module.check_integrity()
            # Block 2 references block 1's hash; block 1's content is unchanged
            # so prev-hash check on block 2 will still pass — but PoW will fail
            # because the stored hash no longer matches the recomputed one.
            tampered = [r for r in results if r["result"] != "Ok"]
            assert len(tampered) > 0, "Expected at least one tampered block to be detected"
        finally:
            blockchain_module.BLOCKCHAIN_DIR = original_dir
