import os
import json
import gspread
from flask import Flask, request, redirect, url_for
from google.oauth2.service_account import Credentials
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gestão de Consumo</title>
    </head>
    <body>
        <h1>Gestão de Consumo</h1>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True)
