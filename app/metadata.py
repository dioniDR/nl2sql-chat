from sqlalchemy import inspect, text
import logging
import json
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)

class DBMetadataManager:
    def __init__(self, engine):
        self.engine = engine
        self.schema_info = {}
        self.last_check_time = datetime.now()
        self.last_fingerprint = None
        self.refresh_metadata()
    
    def refresh_metadata(self):
        """Actualiza la información del esquema de la base de datos"""
        try:
            self.schema_info = {
                'databases': self._get_databases(),
                'current_db': self._get_current_db(),
                'tables': {},
                'relationships': []
            }
            
            # Obtener información de tablas en la base de datos actual
            for table_name in self._get_tables():
                self.schema_info['tables'][table_name] = self._get_table_info(table_name)
                
            # Intenta identificar relaciones
            self._identify_relationships()
            
            # Actualizar huella digital
            self.last_fingerprint = self.get_schema_fingerprint()
            self.last_check_time = datetime.now()
            
            logger.info("Metadata de base de datos actualizada correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar metadata: {e}")
            return False
    
    def _get_databases(self):
        """Obtener todas las bases de datos disponibles"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SHOW DATABASES"))
            return [row[0] for row in result]
    
    def _get_current_db(self):
        """Obtener la base de datos actual"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT DATABASE()"))
            return result.scalar()
    
    def _get_tables(self):
        """Obtener todas las tablas en la base de datos actual"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            return [row[0] for row in result]
    
    def _get_table_info(self, table_name):
        """Obtener información detallada de una tabla"""
        with self.engine.connect() as conn:
            # Obtener estructura de columnas
            columns_result = conn.execute(text(f"DESCRIBE `{table_name}`"))
            columns = [{
                'name': row[0],
                'type': row[1],
                'nullable': row[2] == 'YES',
                'key': row[3],
                'default': row[4],
                'extra': row[5]
            } for row in columns_result]
            
            # Obtener una muestra de datos
            try:
                sample_result = conn.execute(text(f"SELECT * FROM `{table_name}` LIMIT 3"))
                sample_data = [dict(row) for row in sample_result]
            except Exception as e:
                logger.warning(f"No se pudo obtener muestra de datos para {table_name}: {e}")
                sample_data = []
            
            # Obtener conteo de registros (aproximado para tablas grandes)
            try:
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
                record_count = count_result.scalar()
            except Exception as e:
                logger.warning(f"No se pudo obtener conteo para {table_name}: {e}")
                record_count = None
            
            return {
                'columns': columns,
                'record_count': record_count,
                'sample_data': sample_data
            }
    
    def _identify_relationships(self):
        """Intenta identificar relaciones entre tablas basándose en nombres de columnas"""
        relationships = []
        
        # Buscar columnas que parezcan foreign keys (terminan en _id)
        for table_name, table_info in self.schema_info['tables'].items():
            for column in table_info['columns']:
                if column['name'].endswith('_id') and column['name'] != 'id':
                    # Extraer el nombre de la tabla referenciada
                    referenced_table = column['name'][:-3]
                    # Verificar si existe en plural
                    if referenced_table + 's' in self.schema_info['tables']:
                        relationships.append({
                            'table': table_name,
                            'column': column['name'],
                            'referenced_table': referenced_table + 's',
                            'referenced_column': 'id'
                        })
        
        self.schema_info['relationships'] = relationships
    
    def get_schema_description(self):
        """Genera una descripción textual del esquema para usar en prompts"""
        description = f"Base de datos actual: {self.schema_info['current_db']}\n"
        description += "Bases de datos disponibles: " + ", ".join(self.schema_info['databases']) + "\n\n"
        
        description += "Tablas disponibles:\n"
        for table_name, table_info in self.schema_info['tables'].items():
            count_info = f" (~{table_info['record_count']} registros)" if table_info['record_count'] is not None else ""
            description += f"- Tabla: {table_name}{count_info}\n"
            description += "  Columnas:\n"
            for column in table_info['columns']:
                key_info = " (PK)" if column['key'] == 'PRI' else ""
                description += f"    - {column['name']}: {column['type']}{key_info}\n"
        
        if self.schema_info['relationships']:
            description += "\nRelaciones detectadas:\n"
            for rel in self.schema_info['relationships']:
                description += f"- {rel['table']}.{rel['column']} -> {rel['referenced_table']}.{rel['referenced_column']}\n"
        
        return description
    
    def get_schema_fingerprint(self):
        """Genera una huella digital del esquema actual"""
        fingerprint = {}
        
        # Obtener lista de bases de datos
        fingerprint['databases'] = self._get_databases()
        
        # Para la base de datos actual, obtener lista de tablas
        current_db = self._get_current_db()
        fingerprint[current_db] = {}
        
        # Para cada tabla, obtener una huella de su estructura
        for table in self._get_tables():
            try:
                with self.engine.connect() as conn:
                    # Intentar usar CHECKSUM TABLE si está disponible
                    try:
                        result = conn.execute(text(f"CHECKSUM TABLE `{table}`"))
                        checksum = result.scalar()
                        fingerprint[current_db][table] = checksum
                    except:
                        # Alternativa: usar la estructura de la tabla como huella
                        result = conn.execute(text(f"SHOW CREATE TABLE `{table}`"))
                        create_stmt = result.fetchone()[1]
                        fingerprint[current_db][table] = hash(create_stmt)
            except Exception as e:
                logger.warning(f"No se pudo obtener huella para tabla {table}: {e}")
                fingerprint[current_db][table] = None
        
        return fingerprint
    
    def has_schema_changed(self):
        """Comprueba si el esquema ha cambiado comparando huellas digitales"""
        # Si no tenemos huella previa, asumimos que no hay cambios
        if self.last_fingerprint is None:
            return False
            
        try:
            current_fingerprint = self.get_schema_fingerprint()
            
            # Verificar cambios en bases de datos
            if set(current_fingerprint['databases']) != set(self.last_fingerprint['databases']):
                logger.info("Detectado cambio en las bases de datos")
                return True
            
            # Verificar cambios en tablas de la base de datos actual
            current_db = self._get_current_db()
            
            # Si la base de datos actual cambió, consideramos que hay cambios
            if current_db not in self.last_fingerprint:
                logger.info(f"La base de datos actual {current_db} es nueva")
                return True
            
            # Verificar si hay tablas nuevas o eliminadas
            if set(current_fingerprint[current_db].keys()) != set(self.last_fingerprint[current_db].keys()):
                logger.info("Detectado cambio en las tablas")
                return True
            
            # Verificar si alguna tabla cambió su estructura
            for table, checksum in current_fingerprint[current_db].items():
                if checksum != self.last_fingerprint[current_db].get(table):
                    logger.info(f"Detectado cambio en la estructura de la tabla {table}")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error al verificar cambios en el esquema: {e}")
            # Ante la duda, consideramos que no hay cambios para no sobrecargar
            return False


class MetadataRefresher:
    def __init__(self, db_metadata, interval=900):  # 15 minutos por defecto
        self.db_metadata = db_metadata
        self.interval = interval
        self.thread = None
        self.running = False
        self.last_refresh = time.time()
    
    def start(self):
        """Inicia el proceso de actualización periódica en segundo plano"""
        if self.running:
            logger.warning("El refrescador ya está en ejecución")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._refresh_loop)
        self.thread.daemon = True  # El hilo terminará cuando termine el programa principal
        self.thread.start()
        logger.info(f"Iniciado refrescamiento automático de metadatos cada {self.interval} segundos")
    
    def stop(self):
        """Detiene el proceso de actualización periódica"""
        if not self.running:
            logger.warning("El refrescador no está en ejecución")
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            logger.info("Refrescador detenido correctamente")
    
    def _refresh_loop(self):
        """Bucle principal que ejecuta la actualización periódica"""
        while self.running:
            # Esperar hasta el próximo intervalo
            time.sleep(min(10, self.interval))  # Comprobamos cada 10 segundos como máximo
            
            # Verificar si ha pasado el intervalo completo
            current_time = time.time()
            if current_time - self.last_refresh >= self.interval:
                try:
                    logger.info("Iniciando actualización periódica de metadatos")
                    # Verificar cambios antes de actualizar completamente
                    if self.db_metadata.has_schema_changed():
                        self.db_metadata.refresh_metadata()
                        logger.info("Metadatos actualizados por detección de cambios")
                    else:
                        logger.info("No se detectaron cambios en el esquema, omitiendo actualización completa")
                    
                    self.last_refresh = current_time
                except Exception as e:
                    logger.error(f"Error en actualización periódica de metadatos: {e}")
    
    def force_refresh(self):
        """Fuerza una actualización inmediata de los metadatos"""
        try:
            result = self.db_metadata.refresh_metadata()
            self.last_refresh = time.time()
            return result
        except Exception as e:
            logger.error(f"Error al forzar actualización de metadatos: {e}")
            return False
    
    def set_interval(self, seconds):
        """Cambia el intervalo de actualización"""
        if seconds < 60:
            logger.warning(f"Intervalo demasiado corto ({seconds}s), estableciendo mínimo de 60s")
            seconds = 60
        
        self.interval = seconds
        logger.info(f"Intervalo de actualización cambiado a {seconds} segundos")
        return True