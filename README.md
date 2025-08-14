ISOBANK Bank Agent — README

Agente conversacional bancario para ISOBANK con orquestación de tools, RAG (Pinecone) para FAQs, persistencia de historial en Supabase y máscara de datos sensibles.

🚀 Resumen

Este proyecto implementa un asistente bancario virtual que:

Atiende consultas de cuentas, tarjetas y pólizas mediante function calling (OpenAI).

Consulta FAQs con RAG usando Pinecone.

Persiste el historial de conversación en Supabase.

Aplica reglas estrictas de validación de cédula (10 dígitos) y enmascarado de números sensibles (cuentas/tarjetas: * + últimos 4).

🧰 Tools disponibles

consultar_cuentas(cedula: string)

consultar_tarjetas(cedula: string, cuenta: string)

consultar_polizas(cedula: string, cuenta: string)

crear_cuenta(nombre: string, apellido: string, cedula: string)

consultar_faq(pregunta: string) → RAG en Pinecone

El orquestador enruta las tool calls en ejecutar_tool(nombre_funcion, parametros).

🔒 Reglas de seguridad y privacidad

Validación de cédula: exactamente 10 dígitos numéricos.

Enmascarado obligatorio:

Cuentas (10 dígitos): ******7890

Tarjetas (16 dígitos): ************1111

Nunca repetir números completos, aunque el cliente los pegue en el chat.

No inventar datos: si una tool no retorna información, se responde con transparencia.

Recomendado (no incluido por defecto): gating de autenticación/autorización antes de ejecutar tools.

📦 Requisitos

Python 3.10+

Dependencias (sugerido en requirements.txt):

openai, flask, python-dotenv, supabase, pydantic (opcional), pinecone-client (según tu wrapper), requests

⚙️ Configuración

# Crea un archivo .env en la raíz:

OPENAI_API_KEY=sk-...
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOi...
Si tu módulo pinecone_tools lo requiere:
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...   # o PINECONE_INDEX=...


Supabase
Tabla historial (mínimo):

role (text) — ‘user’ | ‘assistant’ | ‘system’ | ‘tool’

content (text)

timestamp (text ISO-8601)

Active RLS según tu estrategia. Evita guardar PII en claro.

▶️ Ejecución
# Modo Terminal (desarrollo)
python app.py terminal


Verás: Bienvenidos a ISOBANK (escribe 'salir' para terminar).

Modo API HTTP (servidor Flask)

# Importante: Levantar el archivo api.py.

python api.py
levanta en http://0.0.0.0:3000

🧠 System Prompt (resumen de comportamiento)

Español neutro, trato de usted, profesional y conciso.

Tarjetas/Pólizas: primero consultar cuentas; si hay varias, solicitar elección; si hay una, proceder directo.

Validar cédula (^\d{10}$) antes de llamar tools.

Enmascarar siempre cuentas/tarjetas con * + últimos 4.

FAQs via Pinecone (RAG).

No mencionar nombres de tools ni detalles técnicos.

🧾 Formatos de respuesta (obligatorios)

Cuentas bancarias:

Número de cuenta: ******7890

Número de cuenta: ******4321

Tarjetas de crédito:

Número: ************1111, Tipo: Visa, Límite: $5,000

Número: ************0004, Tipo: MasterCard, Límite: $10,000

Pólizas:

Número: POL123456, Tipo: Vida, Vigencia: 2025-12-31
(Si tu backend exige enmascarar el número de póliza, aplica el mismo criterio con * y últimos 4.)

🧪 Pruebas rápidas (manual)

Cuentas (con cédula válida): debe listar enmascarado.

Tarjetas: con múltiples cuentas, debe pedir elegir; si hay una, va directo.

Pólizas: mismo patrón que tarjetas.

FAQs: responde desde Pinecone sin exponer PII.

👤 Autor / Contacto

Ing. Jandry Romero
LinkedIn: https://www.linkedin.com/in/jandry-romero-arcentales-5b9836224/
