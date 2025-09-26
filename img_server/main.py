from flask import Flask, send_from_directory, request, jsonify
import os

app = Flask(__name__)
IMAGE_FOLDER = 'images'
os.makedirs(IMAGE_FOLDER, exist_ok=True)



@app.route('/img/<img_uuid>')
def get_image(img_uuid : str):
    return send_from_directory(IMAGE_FOLDER, img_uuid)

@app.route('/img')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)