# Python 3.9.13
from flask import Flask, jsonify, render_template, request
from tensorflow import keras

app = Flask(__name__)

# we need to then get the features of the song and pass it to the model
# https://chatgpt.com/c/2b5593b3-1616-471b-b4a6-c2cc2db7bd29
def load_model():
    model = keras.models.load_model('spotify_model_1.h5')
    return model

def predict_popularity(metadata):
    model = load_model()
    prediction = model.predict(metadata)
    return prediction
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/find_songs', methods=['POST'])
def post_endpoint():
    data = request.json
    response = {"message": "Data received successfully", "received_data": data}
    print(response)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)