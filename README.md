# Blockchain-Technology-Final-Project
Blockchain Technology Final Project by Rayed Jawad &amp; Shamia Shanaha 

# Blockchain Loan Ledger

📄 [Read the full paper (PDF)](Design_and_Implementation_of_a_Blockchain_Based_Loan_Ledger_with_Proof_of_Work_and_Digital_Signatures.pdf)

Many people find blockchain hard to understand because the concepts are difficult to picture without a hands-on example. This is a simplified blockchain system that records loan transactions, built as a teaching tool to make those concepts visible and testable. The loan transactions are simulated, but the cryptography and hashing are real.

## What it does

Each loan is saved as a JSON file in the `blockchain/` folder. The project shows three core blockchain ideas in action:

- **SHA-256 hashing** — Catches any change to old blocks.
- **Proof of Work** — Each new block must be mined by finding a number that makes its hash start with a set number of leading zeros.
- **Digital signatures (ECDSA, SECP256k1)** — Lets a borrower prove a transaction is really theirs.

A Flask web app lets you add transactions, generate keys, browse the chain, and check that nothing has been tampered with.

## Install and run

```bash
pip install -r requirements.txt
python main.py
```

## Pages

- `/` — Add a new loan (borrower, lender, amount, and optional private key to sign it).
- `/keys` — Generate a new keypair. **Save the private key. It's only shown once.**
- `/chain` — Wiew every block and whether its signature is valid, invalid, or unsigned. 
- `/checking` — Verify the whole chain.

1. The genesis block gets made for you on the first run, so you don't have to set it up.
2. Every new block holds the hash of the previous block's file, and that's what ties the chain together.
3. To mine a block, you keep trying different nonces until the hash comes out with enough leading zeros.
4. If you paste in a private key, your loan details (borrower, lender, amount, timestamp) get signed with it. The block then keeps the signature and your public key, so later on, anyone can tell the loan actually came from you and that nothing was edited after the fact.
5. The integrity checker goes back through and re-checks every link, every proof of work, and every signature.

## To run tests
```bash
python -m unittest test_blockchain.py
```
