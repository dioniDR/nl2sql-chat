import logging
import time
import json
from functools import wraps
from fastapi import Request

logger = logging.getLogger(__name__)

def log_api_request(func):
    """
    Decorador que intercepta y registra toda la información de una solicitud
    a la API antes de procesarla.
    """
    @wraps(func)
    async def wrapper(req: Request, *args, **kwargs):
        # Registrar tiempo de inicio
        start_time = time.time()
        
        # Obtener la ruta de la solicitud
        path = req.url.path
        
        # Obtener los datos de la solicitud
        try:
            # Clonar el cuerpo de la solicitud
            body_bytes = await req.body()
            # Restaurar el cuerpo para que la función original pueda leerlo
            req._body = body_bytes
            
            # Intentar decodificar como JSON
            try:
                body = json.loads(body_bytes.decode())
            except json.JSONDecodeError:
                body = body_bytes.decode()
                
            # Registrar los detalles de la solicitud
            logger.info(f"API Request: {path}")
            logger.info(f"Request Body: {json.dumps(body, ensure_ascii=False)}")
            
            # Capturar información del contexto de base de datos
            db_context = {
                "current_db": kwargs.get("metadata_manager", {}).schema_info.get("current_db", "unknown"),
                "tables_count": len(kwargs.get("metadata_manager", {}).schema_info.get("tables", {})),
                "has_schema_changed": kwargs.get("metadata_manager", {}).has_schema_changed()
            }
            logger.info(f"DB Context: {json.dumps(db_context, ensure_ascii=False)}")
            
        except Exception as e:
            logger.error(f"Error al interceptar solicitud: {e}")
        
        # Ejecutar la función original
        response = await func(*args, **kwargs)
        
        # Registrar tiempo de finalización y duración
        end_time = time.time()
        duration = end_time - start_time
        
        # Registrar respuesta y duración
        try:
            logger.info(f"API Response: {json.dumps(response, ensure_ascii=False)}")
        except:
            logger.info("No se pudo serializar la respuesta para el log")
            
        logger.info(f"Request Duration: {duration:.2f}s")
        
        return response
    
    return wrapper