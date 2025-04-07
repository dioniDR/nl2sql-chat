from pydantic import BaseModel

class PreguntaRequest(BaseModel):
    pregunta: str
