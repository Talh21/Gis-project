from flask import Flask
from routes import main  # Import the Blueprint directly from routes.py

app = Flask(__name__)

# Register the Blueprint
app.register_blueprint(main)  # Use the Blueprint object

# Optional: Set a URL prefix for the Blueprint
# app.register_blueprint(main, url_prefix='/main')

if __name__ == "__main__":
    app.run(debug=True)
