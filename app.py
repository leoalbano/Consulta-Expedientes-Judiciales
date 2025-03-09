import os
import logging
import concurrent.futures
import io
from flask import Flask, render_template, request, flash, redirect, url_for, make_response
from soap_client import ConsultaExpedientes
import re
from xhtml2pdf import pisa

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Patrón para validar IUE
IUE_PATTERN = r'^\d{1,3}\s*-\s*\d+\s*/\s*\d{4}$'

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/consultar', methods=['POST'])
def consultar():
    iue = request.form.get('iue', '').strip()

    if not iue:
        flash('Debe ingresar un IUE', 'error')
        return redirect(url_for('index'))

    if not re.match(IUE_PATTERN, iue):
        flash('Formato de IUE inválido. Debe ser: Sede - NroRegistro / Año', 'error')
        return redirect(url_for('index'))

    try:
        cliente = ConsultaExpedientes()
        resultado = cliente.consultar_expediente(iue)
        return render_template('results.html', resultado=resultado, iue=iue)

    except ConnectionError as e:
        logger.error(f"Error de conexión: {str(e)}")
        flash('Error de conexión con el servicio. Por favor intente más tarde.', 'error')
        return redirect(url_for('index'))

    except ValueError as ve:
        logger.error(f"Error de formato: {str(ve)}")
        flash(str(ve), 'error')
        return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        flash(str(e), 'error')
        return redirect(url_for('index'))

@app.route('/consulta-lote', methods=['GET'])
def consulta_lote():
    return render_template('batch_search.html')

@app.route('/consultar-lote', methods=['POST'])
def consultar_lote():
    sede = request.form.get('sede', '').strip()
    desde = int(request.form.get('desde', 1))
    hasta = int(request.form.get('hasta', 30))
    anio = request.form.get('anio', '2024').strip()

    if hasta < desde:
        flash('El número final debe ser mayor o igual al inicial', 'error')
        return redirect(url_for('consulta_lote'))

    if hasta - desde > 50:
        flash('Por favor, consulte máximo 50 expedientes a la vez', 'error')
        return redirect(url_for('consulta_lote'))

    resultados = []
    cliente = ConsultaExpedientes()

    # Procesar las consultas en paralelo para mejorar rendimiento
    def consultar_iue(nro):
        iue = f"{sede}-{nro}/{anio}"
        try:
            return cliente.consultar_expediente(iue)
        except Exception as e:
            logger.error(f"Error consultando {iue}: {str(e)}")
            return {
                'expediente': iue,
                'origen': 'Error en la consulta',
                'caratula': str(e)
            }

    # Usar ThreadPoolExecutor para paralelizar las consultas
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Crear un futures para cada número en el rango
        futures = {executor.submit(consultar_iue, nro): nro for nro in range(desde, hasta + 1)}
        
        # Procesar los resultados a medida que se completan
        for future in concurrent.futures.as_completed(futures):
            try:
                resultado = future.result()
                if resultado:
                    resultados.append(resultado)
            except Exception as e:
                nro = futures[future]
                iue = f"{sede}-{nro}/{anio}"
                logger.error(f"Excepción en consulta de {iue}: {str(e)}")
                resultados.append({
                    'expediente': iue,
                    'origen': 'Error',
                    'caratula': f"Error: {str(e)}"
                })

    # Ordenar resultados por número de expediente
    resultados.sort(key=lambda x: int(re.search(r'-\s*(\d+)\s*/', x['expediente']).group(1)))
    
    return render_template('batch_results.html', 
                          resultados=resultados, 
                          sede=sede, 
                          desde=desde, 
                          hasta=hasta, 
                          anio=anio)

@app.route('/descargar-pdf/<tipo>/<parametros>')
def descargar_pdf(tipo, parametros):
    try:
        if tipo == 'individual':
            iue = parametros
            cliente = ConsultaExpedientes()
            resultado = cliente.consultar_expediente(iue)
            html = render_template('pdf_template.html', resultado=resultado, iue=iue, tipo="individual")
        elif tipo == 'lote':
            sede, desde, hasta, anio = parametros.split('-')
            desde = int(desde)
            hasta = int(hasta)
            resultados = []
            cliente = ConsultaExpedientes()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(cliente.consultar_expediente, f"{sede}-{nro}/{anio}"): nro for nro in range(desde, hasta + 1)}
                for future in concurrent.futures.as_completed(futures):
                    try:
                        resultado = future.result()
                        if resultado:
                            resultados.append(resultado)
                    except Exception as e:
                        nro = futures[future]
                        iue = f"{sede}-{nro}/{anio}"
                        resultados.append({
                            'expediente': iue,
                            'origen': 'Error',
                            'caratula': f"Error: {str(e)}"
                        })
            
            resultados.sort(key=lambda x: int(re.search(r'-\s*(\d+)\s*/', x['expediente']).group(1)))
            html = render_template('pdf_template.html', resultados=resultados, sede=sede, desde=desde, hasta=hasta, anio=anio, tipo="lote")
        else:
            return "Tipo de descarga no válido", 400
        
        # Crear PDF desde HTML
        result = io.BytesIO()
        pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            response = make_response(result.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            if tipo == 'individual':
                response.headers['Content-Disposition'] = f'attachment; filename=expediente_{iue.replace("/", "-").replace(" ", "")}.pdf'
            else:
                response.headers['Content-Disposition'] = f'attachment; filename=expedientes_{sede}_{desde}_a_{hasta}_{anio}.pdf'
            return response
        
        return "Error al generar PDF", 500
    
    except Exception as e:
        logger.error(f"Error al generar PDF: {str(e)}")
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)