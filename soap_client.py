import logging
from zeep import Client
from zeep.exceptions import TransportError, Fault
import re

logger = logging.getLogger(__name__)

class ConsultaExpedientes:
    def __init__(self):
        # URL del servicio SOAP del Poder Judicial
        self.wsdl = 'http://www.expedientes.poderjudicial.gub.uy/wsConsultaIUE.php?wsdl'
        try:
            self.client = Client(wsdl=self.wsdl)
            logger.debug(f"Cliente SOAP inicializado correctamente con WSDL: {self.wsdl}")
        except TransportError as e:
            logger.error(f"Error al inicializar el cliente SOAP: {str(e)}")
            raise ConnectionError("No se pudo conectar al servicio del Poder Judicial. Por favor, intente más tarde.")

    def _limpiar_iue(self, iue):
        """
        Limpia el IUE de espacios adicionales manteniendo el formato correcto
        """
        try:
            partes = re.split(r'\s*[-/]\s*', iue)
            if len(partes) != 3:
                raise ValueError("Error al procesar el formato del IUE")
            return f"{partes[0].strip()}-{partes[1].strip()}/{partes[2].strip()}"
        except Exception as e:
            logger.error(f"Error al limpiar IUE '{iue}': {str(e)}")
            raise ValueError("Error al procesar el formato del IUE")

    def consultar_expediente(self, iue):
        """
        Consulta un expediente por su IUE
        Args:
            iue (str): Identificador Único de Expediente
        Returns:
            dict: Información del expediente
        """
        try:
            iue_limpio = self._limpiar_iue(iue)
            logger.debug(f"Consultando expediente con IUE: {iue_limpio}")

            try:
                # Realizar la consulta según la documentación
                response = self.client.service.consultaIUE(iue=iue_limpio)

                # Log detallado de la respuesta para debuggear
                logger.debug(f"Tipo de respuesta: {type(response)}")
                logger.debug(f"Respuesta completa: {response}")

                if response is None:
                    logger.warning(f"No se encontraron datos para el IUE: {iue_limpio}")
                    return {
                        'expediente': iue_limpio,
                        'origen': 'No disponible',
                        'caratula': 'No se encontró información para el expediente consultado',
                        'primer_movimiento': 'No disponible'
                    }

                # Extraer movimientos directamente de la respuesta principal si están disponibles
                primer_movimiento = "No disponible"
                movimientos_urls = []

                try:
                    # Verificar si tenemos movimientos en la respuesta principal
                    if hasattr(response, 'movimientos') and response.movimientos:
                        # Ordenar movimientos por fecha (el más antiguo primero)
                        movimientos = response.movimientos
                        if isinstance(movimientos, list):
                            # Convertir a lista si no lo es ya
                            movimientos_lista = list(movimientos)
                            
                            # Buscar primero movimientos con enlaces
                            movimientos_con_enlaces = []
                            for mov in movimientos_lista:
                                tiene_enlaces = False
                                for attr_name in dir(mov):
                                    if attr_name.startswith('__'):
                                        continue
                                    try:
                                        attr_value = getattr(mov, attr_name)
                                        if isinstance(attr_value, str) and ('http://' in attr_value or 'https://' in attr_value):
                                            tiene_enlaces = True
                                            url_desc = f"{mov.fecha if hasattr(mov, 'fecha') else 'Fecha desconocida'}: {attr_value}"
                                            movimientos_urls.append(url_desc)
                                    except:
                                        continue
                                if tiene_enlaces:
                                    movimientos_con_enlaces.append(mov)
                            
                            # Si hay movimientos con enlaces, usar el más antiguo como primer movimiento
                            if movimientos_con_enlaces:
                                try:
                                    # Ordenar por fecha (ascendente)
                                    movimientos_con_enlaces.sort(key=lambda x: x.fecha if hasattr(x, 'fecha') else '')
                                    primer_mov = movimientos_con_enlaces[0]
                                    fecha = primer_mov.fecha if hasattr(primer_mov, 'fecha') else "Sin fecha"
                                    tipo = primer_mov.tipo if hasattr(primer_mov, 'tipo') else "Sin tipo"
                                    decreto = primer_mov.decreto if hasattr(primer_mov, 'decreto') and primer_mov.decreto else ""
                                    decreto_txt = f" - Decreto: {decreto}" if decreto else ""
                                    primer_movimiento = f"{fecha}: {tipo}{decreto_txt} (Con enlace)"
                                except Exception as sort_err:
                                    logger.error(f"Error al ordenar movimientos con enlaces: {str(sort_err)}")
                                    primer_mov = movimientos_con_enlaces[0]
                                    fecha = primer_mov.fecha if hasattr(primer_mov, 'fecha') else "Sin fecha"
                                    tipo = primer_mov.tipo if hasattr(primer_mov, 'tipo') else "Sin tipo"
                                    primer_movimiento = f"{fecha}: {tipo} (Con enlace)"
                            else:
                                # Si no hay movimientos con enlaces, usar el comportamiento anterior
                                try:
                                    # Ordenar por fecha
                                    movimientos_lista.sort(key=lambda x: x.fecha if hasattr(x, 'fecha') else '')
                                    primer_mov = movimientos_lista[0]
                                    fecha = primer_mov.fecha if hasattr(primer_mov, 'fecha') else "Sin fecha"
                                    tipo = primer_mov.tipo if hasattr(primer_mov, 'tipo') else "Sin tipo"
                                    decreto = primer_mov.decreto if hasattr(primer_mov, 'decreto') and primer_mov.decreto else ""
                                    decreto_txt = f" - Decreto: {decreto}" if decreto else ""
                                    primer_movimiento = f"{fecha}: {tipo}{decreto_txt}"
                                except Exception as sort_err:
                                    logger.error(f"Error al ordenar movimientos: {str(sort_err)}")
                                    primer_mov = movimientos_lista[0]
                                    fecha = primer_mov.fecha if hasattr(primer_mov, 'fecha') else "Sin fecha"
                                    tipo = primer_mov.tipo if hasattr(primer_mov, 'tipo') else "Sin tipo"
                                    primer_movimiento = f"{fecha}: {tipo}"
                        else:
                            # Si solo hay un movimiento
                            tiene_enlaces = False
                            for attr_name in dir(movimientos):
                                if attr_name.startswith('__'):
                                    continue
                                try:
                                    attr_value = getattr(movimientos, attr_name)
                                    if isinstance(attr_value, str) and ('http://' in attr_value or 'https://' in attr_value):
                                        tiene_enlaces = True
                                        url_desc = f"{movimientos.fecha if hasattr(movimientos, 'fecha') else 'Fecha desconocida'}: {attr_value}"
                                        movimientos_urls.append(url_desc)
                                except:
                                    continue
                            
                            fecha = movimientos.fecha if hasattr(movimientos, 'fecha') else "Sin fecha"
                            tipo = movimientos.tipo if hasattr(movimientos, 'tipo') else "Sin tipo"
                            decreto = movimientos.decreto if hasattr(movimientos, 'decreto') and movimientos.decreto else ""
                            decreto_txt = f" - Decreto: {decreto}" if decreto else ""
                            enlace_txt = " (Con enlace)" if tiene_enlaces else ""
                            primer_movimiento = f"{fecha}: {tipo}{decreto_txt}{enlace_txt}"

                    # Buscar URLs en otros atributos de la respuesta
                    for attr_name in dir(response):
                        if attr_name.startswith('__'):
                            continue
                        try:
                            attr_value = getattr(response, attr_name)
                            if isinstance(attr_value, str):
                                # Buscar URLs en el texto
                                import re
                                urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', attr_value)
                                for url in urls:
                                    movimientos_urls.append(f"{attr_name}: {url}")
                        except:
                            continue

                except Exception as e:
                    logger.error(f"Error al procesar movimientos para IUE '{iue_limpio}': {str(e)}")
                    primer_movimiento = "Error al procesar movimientos"

                # Procesamiento de la respuesta y agregar enlaces a movimientos
                movimientos_procesados = []
                if hasattr(response, 'movimientos') and response.movimientos:
                    for mov in response.movimientos:
                        mov_dict = {
                            'fecha': mov.fecha if hasattr(mov, 'fecha') else '',
                            'tipo': mov.tipo if hasattr(mov, 'tipo') else '',
                            'decreto': mov.decreto if hasattr(mov, 'decreto') else '',
                            'vencimiento': mov.vencimiento if hasattr(mov, 'vencimiento') else '',
                            'sede': mov.sede if hasattr(mov, 'sede') else '',
                            'enlaces': []
                        }
                        
                        # Buscar enlaces en los atributos del movimiento
                        for attr_name in dir(mov):
                            if attr_name.startswith('__'):
                                continue
                            try:
                                attr_value = getattr(mov, attr_name)
                                if isinstance(attr_value, str) and ('http://' in attr_value or 'https://' in attr_value):
                                    mov_dict['enlaces'].append({
                                        'tipo': attr_name,
                                        'url': attr_value
                                    })
                                    # Si es un decreto, también agregar como enlace_decreto
                                    if attr_name.lower() in ['decreto', 'resolucion', 'sentencia'] or 'decreto' in attr_name.lower():
                                        mov_dict['enlace_decreto'] = attr_value
                            except:
                                continue
                        
                        movimientos_procesados.append(mov_dict)

                return {
                    'expediente': iue_limpio,
                    'origen': response.origen if hasattr(response, 'origen') else 'No disponible',
                    'caratula': response.caratula if hasattr(response, 'caratula') else 'No disponible',
                    'primer_movimiento': primer_movimiento,
                    'urls_movimientos': movimientos_urls,
                    'movimientos': movimientos_procesados if movimientos_procesados else response.movimientos if hasattr(response, 'movimientos') else []
                }

            except Exception as e:
                logger.error(f"Error al llamar al servicio SOAP: {str(e)}")
                raise

        except Fault as e:
            logger.error(f"Error SOAP al consultar IUE '{iue}': {str(e)}")
            raise Exception(f"Error en la consulta: {str(e)}")
        except ValueError as ve:
            logger.error(f"Error de formato en IUE '{iue}': {str(ve)}")
            raise ValueError(str(ve))
        except Exception as e:
            logger.error(f"Error inesperado al consultar IUE '{iue}': {str(e)}")
            raise Exception("Error al procesar la consulta. Por favor, intente más tarde.")