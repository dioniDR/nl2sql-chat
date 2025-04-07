from sqlalchemy import create_engine, text
from .config import DB_URL, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
import mysql.connector
from mysql.connector import Error
import time
import logging

logger = logging.getLogger(__name__)

def lanzar_mysqlconnector():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        if connection.is_connected():
            logger.info("Lanzamiento con mysql.connector exitoso.")
    except Error as e:
        logger.error(f"No se pudo lanzar con mysql.connector: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            logger.info("Conexión mysql.connector cerrada.")

def intentar_sqlalchemy():
    try:
        engine = create_engine(DB_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Conexión SQLAlchemy exitosa.")
        return engine
    except Exception as e:
        logger.error(f"Error en SQLAlchemy: {e}")
        return None
