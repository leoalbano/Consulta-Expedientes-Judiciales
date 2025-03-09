
# Consulta de Expedientes Judiciales - Aplicación para Windows

Esta aplicación te permite consultar expedientes judiciales del Poder Judicial de Uruguay mediante el servicio SOAP oficial.

## Instrucciones para descargar y ejecutar en Windows

### Método 1: Descargar como ZIP desde Replit

1. Haz clic en el botón de "..." (tres puntos) en la parte superior del explorador de archivos
2. Selecciona "Download as ZIP"
3. Descomprime el archivo ZIP en tu computadora
4. Sigue las instrucciones de instalación y ejecución que se detallan abajo

### Método 2: Clonar desde Replit (requiere Git)

1. Abre una terminal o línea de comandos
2. Ejecuta: `git clone https://replit.com/@usuario/nombre-del-repl.git` (reemplaza con la URL de tu Repl)
3. Navega a la carpeta del proyecto: `cd nombre-del-repl`
4. Sigue las instrucciones de instalación y ejecución que se detallan abajo

## Instalación y ejecución

1. Asegúrate de tener Python 3.11 o superior instalado
   - Puedes descargarlo desde: https://www.python.org/downloads/
   - Durante la instalación, marca la opción "Add Python to PATH"

2. Abre una ventana de línea de comandos (CMD) o PowerShell
   - Navega hasta la carpeta donde descomprimiste o clonaste el proyecto
   - Por ejemplo: `cd C:\Users\TuUsuario\Downloads\consulta-expedientes`

3. Instala las dependencias necesarias:
   ```
   pip install -r requirements.txt
   ```

4. Ejecuta la aplicación:
   ```
   python run_windows.py
   ```

5. Abre tu navegador y visita: http://localhost:5000

## Notas importantes

- La aplicación se conecta al servicio SOAP del Poder Judicial de Uruguay
- Asegúrate de tener conexión a internet para que funcione correctamente
- Si encuentras errores, verifica que todas las dependencias estén instaladas correctamente

## Archivos principales

- `run_windows.py`: Archivo para ejecutar la aplicación en Windows
- `app.py`: Contiene la lógica principal de la aplicación
- `soap_client.py`: Cliente SOAP para comunicarse con el servicio del Poder Judicial
- `templates/`: Carpeta con las plantillas HTML de la interfaz

## Soporte

Si tienes problemas para ejecutar la aplicación, revisa las instrucciones en `instrucciones_windows.txt`
