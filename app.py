# Python 3.9.13

from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', variableTitel='Tristan')

@app.route('/process_text', methods=['POST'])
def process_text():
    user_text = request.form['user_text']  
    processed_text = f'You entered: "{user_text}"'  # Example response

    return render_template('index.html', response=processed_text)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)