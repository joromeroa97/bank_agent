import os
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Configura tus variables de entorno o reemplaza aquí directamente
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")  # e.g. "faq-index"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializa Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Lista de preguntas frecuentes y respuestas
faqs = [
    {
        "id": "faq-1",
        "pregunta": "¿Cómo puedo abrir una cuenta bancaria?",
        "respuesta": "Para abrir una cuenta bancaria, acércate a una sucursal con tu cédula y un comprobante de domicilio."
    },
    {
        "id": "faq-2",
        "pregunta": "¿Cuáles son los requisitos para solicitar una tarjeta de crédito?",
        "respuesta": "Debes ser mayor de edad, tener ingresos comprobables y presentar tu cédula."
    },
    # Agrega más FAQs aquí
]

# Insertar embeddings en Pinecone
for faq in faqs:
    embedding_response = openai_client.embeddings.create(
        input=faq["pregunta"],
        model="text-embedding-ada-002"
    )
    vector = embedding_response.data[0].embedding
    index.upsert(
        vectors=[
            {
                "id": faq["id"],
                "values": vector,
                "metadata": {
                    "pregunta": faq["pregunta"],
                    "respuesta": faq["respuesta"]
                }
            }
        ]
    )

print("FAQs insertadas en Pinecone.")