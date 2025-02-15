import os
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from flask import Flask, request, jsonify, render_template
from PIL import Image
import requests

app = Flask(__name__)

# Dictionary mapping diseases to recommended pesticides
pesticide_recommendations = {
    'Bacterial Blight': 'Copper-based fungicides, Streptomycin',
    'Red Rot': 'Fungicides containing Mancozeb or Copper',
    'Blight': 'Fungicides containing Chlorothalonil',
    'Common_Rust': 'Fungicides containing Azoxystrobin or Propiconazole',
    'Gray_Leaf_Spot,Healthy': 'Fungicides containing Azoxystrobin or Propiconazole',
    'Bacterial blight': 'Copper-based fungicides, Streptomycin',
    'curl_virus': 'Insecticides such as Imidacloprid or Pyrethroids',
    'fussarium_wilt': 'Soil fumigants, Fungicides containing Thiophanate-methyl',
    'Blast': 'Fungicides containing Tricyclazole or Propiconazole',
    'Brownspot': 'Fungicides containing Azoxystrobin or Propiconazole',
    'Tungro': 'Insecticides such as Neonicotinoids or Pyrethroids',
    'septoria': 'Fungicides containing Azoxystrobin or Propiconazole',
    'strip_rust': 'Fungicides containing Azoxystrobin or Propiconazole'
}


def recommend_pesticide(predicted_class):
    if predicted_class == 'Healthy':
        return 'No need for any pesticide, plant is healthy'
    return pesticide_recommendations.get(predicted_class, "No recommendation available")


# Load H5 models
models = {
    'sugarcane': tf.keras.models.load_model("models/sugercane_model.h5", custom_objects={"KerasLayer": hub.KerasLayer}),
    'maize': tf.keras.models.load_model("models/maize_model.h5", custom_objects={"KerasLayer": hub.KerasLayer}),
    'cotton': tf.keras.models.load_model("models/cotton_model.h5", custom_objects={"KerasLayer": hub.KerasLayer}),
    'rice': tf.keras.models.load_model("models/rice.h5", custom_objects={"KerasLayer": hub.KerasLayer}),
    'wheat': tf.keras.models.load_model("models/wheat_model.h5", custom_objects={"KerasLayer": hub.KerasLayer}),
}

class_names = {
    'sugarcane': ['Bacterial Blight', 'Healthy', 'Red Rot'],
    'maize': ['Blight', 'Common_Rust', 'Gray_Leaf_Spot,Healthy'],
    'cotton': ['Bacterial blight', 'curl_virus', 'fussarium_wilt', 'Healthy'],
    'rice': ['Bacterial_blight', 'Blast', 'Brownspot', 'Tungro'],
    'wheat': ['Healthy', 'septoria', 'strip_rust'],
}


def preprocess_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image = image.resize((224, 224))
    img_array = np.array(image).astype("float32") / 255.0
    return np.expand_dims(img_array, axis=0)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/classify', methods=['POST'])
def classify_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    plant_type = request.form.get('plant_type')
    if plant_type not in models:
        return jsonify({'error': 'Invalid plant type'}), 400

    image = preprocess_image(file)
    predictions = models[plant_type].predict(image)
    predicted_index = np.argmax(predictions)
    predicted_class = class_names[plant_type][predicted_index]
    recommended_pesticide = recommend_pesticide(predicted_class)

    return jsonify({
        'predicted_class': predicted_class,
        'recommended_pesticide': recommended_pesticide
    })



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
