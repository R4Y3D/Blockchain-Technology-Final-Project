import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from block import write_block, check_integrity, get_chain, generate_keypair, verify_signature, extract_public_key

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        borrower = request.form.get('borrower')
        lender = request.form.get('lender')
        amount = request.form.get('amount')
        # Private key is optional: if the user pastes it, the block is signed.
        # If left blank, the block is saved without a signature (still valid on chain).
        private_key_pem = request.form.get('private_key') or None
        try:
            write_block(borrower=borrower, lender=lender, amount=amount,
                        private_key_pem=private_key_pem)
        except ValueError as e:
            return str(e), 400
        except Exception as e:
            return f"Failed to write block: {str(e)}", 500
        return redirect(url_for('index'))
    return render_template('index.html', checking_results=[])

@app.route('/checking')
def check():
    results = check_integrity()
    return render_template('index.html', checking_results=results)

@app.route('/chain')
def chain():
    blocks = get_chain()
    for block in blocks:
        # Format the Unix timestamp into a readable string
        ts = block.get('timestamp')
        block['timestamp_str'] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') if ts else 'N/A'

        # Determine signature status for display in the explorer
        public_key_pem = block.get('public_key')
        sig_hex = block.get('signature')
        if block.get('block_number') == 1:
            block['sig_status'] = 'genesis'
        elif public_key_pem and sig_hex:
            tx_fields = {k: block[k] for k in ('borrower', 'lender', 'amount', 'timestamp') if k in block}
            block['sig_status'] = 'valid' if verify_signature(public_key_pem, tx_fields, sig_hex) else 'invalid'
        else:
            block['sig_status'] = 'unsigned'

    return render_template('chain.html', blocks=blocks)

@app.route('/validate-key', methods=['POST'])
def validate_key():
    pem = request.form.get('private_key', '').strip()
    if not pem:
        return jsonify({'public_key': None, 'status': 'empty'})
    try:
        public_pem = extract_public_key(pem)
        return jsonify({'public_key': public_pem, 'status': 'valid'})
    except ValueError:
        return jsonify({'public_key': None, 'status': 'invalid'})

@app.route('/keys')
def keys():
    # Generate a fresh key pair every time this page is loaded.
    # The private key is shown once, the user must save it themselves.
    private_pem, public_pem = generate_keypair()
    return render_template('keys.html', private_key=private_pem, public_key=public_pem)

if __name__ == '__main__':
    app.run(debug=True)
