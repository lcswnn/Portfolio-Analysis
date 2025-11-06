#main Flask app for Web app
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Portfolio Analysis App!"
  
app.run(debug=True)