from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()


PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")  # e.g. "gcp-starter"
PINECONE_INDEX = os.getenv("PINECONE_INDEX")  # e.g. "faq-index"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializa Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

from openai import OpenAI
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def tool_consultar_faq(pregunta):
    # Obtener embedding de la pregunta
    embedding_response = openai_client.embeddings.create(
        input=pregunta,
        model="text-embedding-ada-002"
    )
    vector = embedding_response.data[0].embedding
    # Buscar en Pinecone
    query_response = index.query(vector=vector, top_k=1, include_metadata=True)
    if query_response.matches:
        return query_response.matches[0].metadata.get("respuesta", "No se encontró respuesta.")
    return "No se encontró respuesta."
