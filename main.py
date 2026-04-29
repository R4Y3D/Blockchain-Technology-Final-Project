import datetime
from flask import Flask, render_template, request, redirect, url_for
from block import write_block, check_integrity, get_chain

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        borrower = request.form.get('borrower')
        lender = request.form.get('lender')
        amount = request.form.get('amount')
        try:
            write_block(borrower=borrower, lender=lender, amount=amount)
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
        ts = block.get('timestamp')
        if ts:
            block['timestamp_str'] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        else:
            block['timestamp_str'] = 'N/A'
    return render_template('chain.html', blocks=blocks)

if __name__ == '__main__':
    app.run(debug=True)
