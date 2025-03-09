
from flask import Flask

# Importar la app de app.py en lugar de crear una nueva
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
