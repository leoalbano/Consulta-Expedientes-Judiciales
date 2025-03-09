
from app import app

if __name__ == "__main__":
    print("Iniciando aplicación en http://localhost:5000")
    print("Presiona Ctrl+C para detener la aplicación")
    app.run(host="localhost", port=5000, debug=True)
