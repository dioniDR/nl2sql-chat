from app.logic import ejecutar_pregunta
from app.openai_client import preparar_modelo
from app.database import intentar_sqlalchemy

def test_consulta_simple():
    engine = intentar_sqlalchemy()
    client = preparar_modelo()
    resultado = ejecutar_pregunta(client, engine, "¿Cuántas bases de datos hay?")
    assert "sql" in resultado
