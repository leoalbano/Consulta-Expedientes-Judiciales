
import os
import zipfile
from flask import Flask, send_file

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <html>
    <head>
        <title>Descargar Aplicación</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .container { max-width: 800px; margin: 0 auto; }
            .btn { display: inline-block; background: #0066cc; color: white; padding: 10px 20px; 
                   text-decoration: none; border-radius: 5px; font-weight: bold; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Consulta de Expedientes Judiciales</h1>
            <p>Haz clic en el botón para descargar la aplicación como archivo ZIP:</p>
            <a href="/download" class="btn">Descargar ZIP</a>
        </div>
    </body>
    </html>
    '''

@app.route('/download')
def download_zip():
    # Nombre del archivo ZIP temporal
    zip_filename = 'consulta_expedientes.zip'
    
    # Eliminar el ZIP si ya existe
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
    
    # Crear un nuevo archivo ZIP
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Archivos a incluir en el ZIP
        important_files = [
            'app.py', 'main.py', 'soap_client.py', 'run_windows.py',
            'requirements.txt', 'README.md', 'instrucciones_windows.txt'
        ]
        
        # Carpetas a incluir
        important_folders = ['templates', 'static']
        
        # Agregar archivos individuales
        for file in important_files:
            if os.path.exists(file):
                zipf.write(file)
                print(f"Agregado: {file}")
            else:
                print(f"Archivo no encontrado: {file}")
        
        # Agregar carpetas completas
        for folder in important_folders:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path)
                        print(f"Agregado: {file_path}")
            else:
                print(f"Carpeta no encontrada: {folder}")
    
    # Verificar que el archivo se haya creado correctamente
    if os.path.exists(zip_filename) and os.path.getsize(zip_filename) > 0:
        print(f"ZIP creado correctamente: {zip_filename} ({os.path.getsize(zip_filename)} bytes)")
        # Devolver el archivo para su descarga
        return send_file(zip_filename, as_attachment=True, download_name='consulta_expedientes.zip')
    else:
        return "Error al crear el archivo ZIP", 500

if __name__ == '__main__':
    print("Iniciando servidor de descarga en http://0.0.0.0:8080")
    print("Visita esta URL en tu navegador para descargar la aplicación")
    app.run(host='0.0.0.0', port=8080, debug=True)
