# app.py
import os
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from flask import Flask, request, jsonify, render_template
from PIL import Image
import requests
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.serving import run_simple
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

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

def get_plant_info(disease, plant_type="Unknown"):
    prompt = f"""
    Disease Name: {disease}
    Plant Type: {plant_type}
    Explain this disease in a very simple way for a farmer. Include:
    - Symptoms
    - Causes
    - Severity
    - How It Spreads
    - Treatment & Prevention
    """
    try:
        API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-1B-Instruct/v1/chat/completions"
        headers = {"Authorization": "Bearer os.getenv('HUGGINGFACE_API_TOKEN')"}
        print(os.getenv('HUGGINGFACE_API_TOKEN'))
        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ]
        }
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        detailed_info = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"detailed_info": detailed_info}
    except requests.exceptions.HTTPError as http_err:
        print("HTTP error occurred:", http_err)
        print("Response Content:", response.content)
    except Exception as e:
        print("Other error occurred:", str(e))
    return {"detailed_info": ""}

def get_web_pesticide_info(disease, plant_type="Unknown"):
    query = f"site:agrowon.esakal.com {disease} in {plant_type}"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": os.getenv("GOOGLE_API_KEY"),
        "cx": os.getenv("GOOGLE_CX"),
        "q": query,
        "num": 3
    }
    print(os.getenv("GOOGLE_API_KEY"))
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            item = data["items"][0]
            return {
                "title": item.get("title", "No title available"),
                "link": item.get("link", "#"),
                "snippet": item.get("snippet", "No snippet available"),
                "summary": item.get("snippet", "No snippet available")
            }
    except requests.exceptions.HTTPError as http_err:
        print("Error retrieving web pesticide info:", http_err)
        print("Response Content:", response.content)
    except Exception as e:
        print("Other error occurred:", str(e))
    return None

def get_more_web_info(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": os.getenv("GOOGLE_API_KEY"),
        "cx": os.getenv("GOOGLE_CX"),
        "q": query,
        "num": 3
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = []
        if "items" in data:
            for item in data["items"]:
                results.append({
                    "title": item.get("title", "No title available"),
                    "link": item.get("link", "#"),
                    "snippet": item.get("snippet", "No snippet available")
                })
        return results
    except requests.exceptions.HTTPError as http_err:
        print("Error retrieving additional articles:", http_err)
        print("Response Content:", response.content)
    except Exception as e:
        print("Other error occurred:", str(e))
    return []

def get_commercial_product_info(recommendation):
    indiamart_query = f"site:indiamart.com pesticide '{recommendation}'"
    krishi_query = f"site:krishisevakendra.in/products pesticide '{recommendation}'"
    indiamart_results = get_more_web_info(indiamart_query)
    krishi_results = get_more_web_info(krishi_query)
    return indiamart_results + krishi_results

@app.route('/')
def home():
    print(f"Rendering home page.")
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify_image():
    if 'file' not in request.files:
        print("No file uploaded.")
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    plant_type = request.form.get('plant_type')
    
    # Check if the provided plant type exists
    if plant_type not in models:
        print(f"Invalid plant type: {plant_type}")
        return jsonify({'error': 'Invalid plant type'}), 400
    image = preprocess_image(file)
    predictions = models[plant_type].predict(image)
    
    # Print the predictions for debugging
    predicted_classes = np.argmax(predictions, axis=1)
    print(f"Predicted classes: {predicted_classes}")
    
    predicted_index = np.argmax(predictions)
    predicted_class = class_names[plant_type][predicted_index]
    recommended_pesticide = recommend_pesticide(predicted_class)
    # Print the recommended pesticide for debugging
    print(f"Recommended pesticide for {predicted_class}: {recommended_pesticide}")
    
    # Get detailed plant info
    detailed_info = get_plant_info(predicted_class, plant_type)
    
    # Get web pesticide info
    web_pesticide_info = get_web_pesticide_info(predicted_class, plant_type)
    
    # Get commercial product info
    commercial_product_info = get_commercial_product_info(recommended_pesticide)
    
    return jsonify({
        'predicted_class': predicted_class,
        'recommended_pesticide': recommended_pesticide,
        'detailed_info': detailed_info['detailed_info'],
        'web_pesticide_info': web_pesticide_info,
        'commercial_product_info': commercial_product_info
    })

@app.route('/get_plant_info', methods=['POST'])
def get_plant_info_route():
    data = request.json
    disease = data.get('disease')
    plant_type = data.get('plant_type', 'Unknown')
    detailed_info = get_plant_info(disease, plant_type)
    return jsonify(detailed_info)

class CustomHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            if event.src_path.endswith(".py") and not event.src_path.startswith("C:\\Users\\Admin\\AppData\\Local\\"):
                print(f"Detected change in {event.src_path}, reloading...")
                os._exit(0)

if __name__ == '__main__':
    event_handler = CustomHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.getcwd(), recursive=True)
    observer.start()
    try:
        run_simple('0.0.0.0', 5000, app, use_reloader=False, use_debugger=True)
    finally:
        observer.stop()
        observer.join()
#latest works
