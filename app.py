import os
import json
import gspread
from flask import Flask, request, redirect, url_for
from google.oauth2.service_account import Credentials
from datetime import datetime

from flask import Flask

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Gestão de Consumo</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: Arial; text-align: center; }
        #map { height: 500px; width: 90%; margin: 20px auto; }
    </style>
</head>
<body>
    <h1>Gestão de Consumo</h1>
    <div id="map"></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const map = L.map('map').setView([38.7223, -9.1393], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        L.marker([38.7223, -9.1393]).addTo(map).bindPopup("Lisboa");
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML

if __name__ == '__main__':
    app.run(debug=True)
