from fastapi import FastAPI, Request
from pydantic import BaseModel
from app.schema import PreguntaRequest
from app.database import intentar_sqlalchemy, lanzar_mysqlconnector
from app.openai_client import preparar_modelo
from app.logic import ejecutar_pregunta
from fastapi.middleware.cors import CORSMiddleware
import time
import logging
from sqlalchemy.sql import text
from app.metadata import DBMetadataManager, MetadataRefresher
from app.middleware import log_api_request  # Importar nuestro decorador
import json

# Configurar logs
logging.basicConfig(filename="logs/app.log", level=logging.INFO)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = preparar_modelo()
engine = intentar_sqlalchemy()
if not engine:
    lanzar_mysqlconnector()
    time.sleep(2)
    engine = intentar_sqlalchemy()

# Inicializar el gestor de metadatos
metadata_manager = DBMetadataManager(engine)
metadata_refresher = MetadataRefresher(metadata_manager, interval=900)  # 15 minutos en segundos
metadata_refresher.start()

class SQLRequest(BaseModel):
    sql: str

@app.post("/preguntar")
async def preguntar(req: PreguntaRequest):
    # Verificar si han cambiado las tablas o bases de datos
    if metadata_manager.has_schema_changed():
        metadata_manager.refresh_metadata()
        logging.info("Esquema actualizado antes de procesar la consulta")
    
    # Para interceptar lo que se envía a la API, añade logging aquí
    logging.info(f"Pregunta recibida: {req.pregunta}")
    logging.info(f"Base de datos actual: {metadata_manager.schema_info.get('current_db', 'unknown')}")
    logging.info(f"Tablas disponibles: {list(metadata_manager.schema_info.get('tables', {}).keys())}")
    
    # Añadir contexto de base de datos a la pregunta
    current_db = metadata_manager.schema_info.get('current_db', 'unknown')
    contexto_pregunta = f"Base de datos actual: {current_db}. Mi pregunta es: {req.pregunta}"
    
    # Ejecutar la consulta
    start_time = time.time()
    result = ejecutar_pregunta(client, engine, contexto_pregunta, metadata_manager)
    end_time = time.time()
    
    # Registrar el tiempo y resultado
    logging.info(f"Tiempo de procesamiento: {end_time - start_time:.2f}s")
    logging.info(f"SQL generado: {result.get('sql', 'No se generó SQL')}")
    
    return result

@app.post("/preguntar-sql")
def preguntar_sql(data: SQLRequest):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(data.sql))
            columnas = result.keys()
            filas = result.fetchall()
            datos = [dict(zip(columnas, fila)) for fila in filas]
            return {"resultados": datos}
    except Exception as e:
        return {"error": str(e)}

@app.post("/refrescar-esquema")
def refrescar_esquema():
    try:
        metadata_manager.refresh_metadata()
        return {"message": "Esquema refrescado exitosamente"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/esquema")
def obtener_esquema():
    try:
        return {"esquema": metadata_manager.get_metadata()}
    except Exception as e:
        return {"error": str(e)}

@app.post("/cambiar-intervalo-actualizacion")
def cambiar_intervalo_actualizacion(intervalo: int):
    try:
        metadata_refresher.update_interval(intervalo)
        return {"message": f"Intervalo de actualización cambiado a {intervalo} minutos"}
    except Exception as e:
        return {"error": str(e)}
