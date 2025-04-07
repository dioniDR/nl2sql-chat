from fastapi import FastAPI
from app.schema import PreguntaRequest
from app.database import intentar_sqlalchemy, lanzar_mysqlconnector
from app.openai_client import preparar_modelo
from app.logic import ejecutar_pregunta
from fastapi.middleware.cors import CORSMiddleware
import time
import logging

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

@app.post("/preguntar")
def preguntar(req: PreguntaRequest):
    return ejecutar_pregunta(client, engine, req.pregunta)
