from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for

from block import write_block, check_integrity

app = Flask(__name__)

@app.route('/', methods = ['POST', 'GET'])
def index():
    if request.method == 'POST':
        borrower = request.form.get('borrower')
        lender = request.form.get('lender')
        amount = request.form.get('amount')
        #write_block(borrower=borrower, lender=lender, amount=amount)
        try: 
            write_block(borrower = borrower, lender = lender, amount = amount)
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

if __name__ == '__main__':
    app.run(debug=True)