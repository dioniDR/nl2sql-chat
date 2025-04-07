from openai import OpenAI
from .config import OPENAI_API_KEY

def preparar_modelo():
    return OpenAI(api_key=OPENAI_API_KEY)
