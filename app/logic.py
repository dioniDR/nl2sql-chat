from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def es_sql_valido(sql):
    palabras_clave = ["SELECT", "SHOW", "DESCRIBE", "WITH"]
    return any(sql.strip().upper().startswith(p) for p in palabras_clave)

def ejecutar_pregunta(client, engine, pregunta, db_metadata):
    # Obtener descripción del esquema
    schema_description = db_metadata.get_schema_description()

    prompt = [
        {"role": "system", "content": f"Eres un experto en SQL. Tu única tarea es convertir preguntas en lenguaje natural en sentencias SQL válidas de MySQL. No debes explicar, solo generar SQL directamente. Aquí está la descripción del esquema de la base de datos:\n{schema_description}"},
        {"role": "user", "content": pregunta}
    ]
    respuesta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=prompt
    )
    sql = respuesta.choices[0].message.content.strip()

    # Limpiar si viene con triple backticks ```sql
    if sql.startswith("```"):
        sql = sql.strip("```").replace("sql", "").strip()
    
    logger.info(f"SQL generado: {sql}")

    # Validar si el SQL es válido
    if not es_sql_valido(sql):
        logger.error("El modelo no devolvió una consulta SQL válida.")
        return {"error": "El modelo no devolvió una consulta SQL válida."}

    try:
        with engine.connect() as conn:
            resultado = conn.execute(text(sql))

            # Detectar si es una operación DDL
            if sql.strip().upper().startswith(("CREATE", "ALTER", "DROP")):
                logger.info("Operación DDL detectada, refrescando metadatos.")
                db_metadata.refresh()

            # Procesar resultados si no es DDL
            if resultado.returns_rows:
                columnas = resultado.keys()
                filas = resultado.fetchall()
                datos = [dict(zip(columnas, fila)) for fila in filas]
                return {"sql": sql, "resultados": datos}
            else:
                return {"sql": sql, "resultados": "Operación ejecutada exitosamente."}
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error al ejecutar SQL: {error_message}")

        # Mejorar manejo de errores para tablas inexistentes
        if "doesn't exist" in error_message or "no such table" in error_message:
            return {"sql": sql, "error": "La consulta hace referencia a una tabla inexistente."}
        return {"sql": sql, "error": error_message}
