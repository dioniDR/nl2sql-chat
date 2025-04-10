import threading
import time
import logging

logger = logging.getLogger(__name__)

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