# Python 3.9.13
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
    
@app.route('/')
def index():
    return render_template('index.html', variableTitel='Tristan')

@app.route('/find_songs', methods=['POST'])
def post_endpoint():
    data = request.json
    response = {"message": "Data received successfully", "received_data": data}
    print(response)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)