from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def ejecutar_pregunta(client, engine, pregunta):
    prompt = [
        {"role": "system", "content": "Eres un experto en bases de datos. Devuelve solo SQL válido para responder preguntas del usuario."},
        {"role": "user", "content": pregunta}
    ]
    respuesta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=prompt
    )
    sql = respuesta.choices[0].message.content.strip()
    logger.info(f"SQL generado: {sql}")

    try:
        with engine.connect() as conn:
            resultado = conn.execute(text(sql))
            columnas = resultado.keys()
            filas = resultado.fetchall()
            datos = [dict(zip(columnas, fila)) for fila in filas]
            return {"sql": sql, "resultados": datos}
    except Exception as e:
        logger.error(f"Error al ejecutar SQL: {e}")
        return {"sql": sql, "error": str(e)}
