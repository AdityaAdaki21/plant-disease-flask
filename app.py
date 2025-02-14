# app.py
from flask import Flask, render_template, request, jsonify
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from PIL import Image
import os
import io
import base64
from googletrans import Translator # type: ignore
import requests

app = Flask(__name__)

# Force legacy Keras
os.environ["TF_USE_LEGACY_KERAS"] = "1"

# Load models (similar to the Streamlit version)
def load_model(model_path):
    return tf.keras.models.load_model(
        model_path,
        custom_objects={"KerasLayer": hub.KerasLayer},
        compile=False
    )

# Initialize models
models = {
    'sugarcane': load_model("models/sugercane_model.h5"),
    'maize': load_model("models/maize_model.h5"),
    'cotton': load_model("models/cotton_model.h5"),
    'rice': load_model("models/rice.h5"),
    'wheat': load_model("models/wheat_model.h5"),
}

# Class names (same as original)
class_names = {
    'sugarcane': ['Bacterial Blight', 'Healthy', 'Red Rot'],
    'maize': ['Blight', 'Common_Rust', 'Gray_Leaf_Spot,Healthy'],
    'cotton': ['Bacterial blight', 'curl_virus', 'fussarium_wilt', 'Healthy'],
    'rice': ['Bacterial_blight', 'Blast', 'Brownspot', 'Tungro'],
    'wheat': ['Healthy', 'septoria', 'strip_rust'],
}

# Pesticide recommendations (same as original)
pesticide_recommendations = {
    'Bacterial Blight': 'Copper-based fungicides, Streptomycin',
    'Red Rot': 'Fungicides containing Mancozeb or Copper',
    'Blight': 'Fungicides containing Chlorothalonil',
    'Common_Rust': 'Fungicides containing Azoxystrobin or Propiconazole',
    'Gray_Leaf_Spot,Healthy': 'Fungicides containing Azoxystrobin or Propiconazole',
    'Bacterial blight': 'Copper-based fungicides, Streptomycin',
    'curl_virus': 'Insecticides such as Imidacloprid or Pyrethroids',
    'fussarium_wilt': 'Soil fumigants, Fungicides containing Thiophanate-methyl',
    'Bacterial_blight': 'Copper-based fungicides, Streptomycin',
    'Blast': 'Fungicides containing Tricyclazole or Propiconazole',
    'Brownspot': 'Fungicides containing Azoxystrobin or Propiconazole',
    'Tungro': 'Insecticides such as Neonicotinoids or Pyrethroids',
    'septoria': 'Fungicides containing Azoxystrobin or Propiconazole',
    'strip_rust': 'Fungicides containing Azoxystrobin or Propiconazole'
}

def preprocess_image(image_file):
    image = Image.open(io.BytesIO(image_file.read())).convert("RGB")
    image = image.resize((224, 224))
    img_array = np.array(image).astype("float32") / 255.0
    return np.expand_dims(img_array, axis=0)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    image_file = request.files['image']
    plant_type = request.form.get('plant_type', 'sugarcane')
    
    try:
        input_image = preprocess_image(image_file)
        predictions = models[plant_type].predict(input_image)
        predicted_index = np.argmax(predictions)
        predicted_class = class_names[plant_type][predicted_index]
        pesticide = pesticide_recommendations.get(predicted_class, "No recommendation available")
        
        # Get additional information
        plant_info = get_plant_info(predicted_class, plant_type)
        commercial_products = get_commercial_product_info(pesticide)
        additional_articles = get_more_web_info(f"{predicted_class} in {plant_type}")
        
        return jsonify({
            'predicted_class': predicted_class,
            'pesticide': pesticide,
            'plant_info': plant_info,
            'commercial_products': commercial_products,
            'additional_articles': additional_articles
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)