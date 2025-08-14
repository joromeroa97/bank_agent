import pinecone_tools
import json
from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
import openai
from supabase import create_client, Client
import datetime
import tools
import sys

load_dotenv()

# Definición de las funciones (tools) para el modelo de LLM.
openai_tools = [
    {
        "type": "function",
        "function": {
            "name": "consultar_faq",
            "description": "Esta tool permite consultar una pregunta frecuente en la base vectorial Pinecone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pregunta": {"type": "string"}
                },
                "required": ["pregunta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crear_cuenta",
            "description": "Esta tool permite crear una cuenta bancaria para un cliente. Recibe como parametros el nombre, apellido y cédula del cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "apellido": {"type": "string"},
                    "cedula": {"type": "string"}
                },
                "required": ["nombre", "apellido", "cedula"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_cuentas",
            "description": "Esta tool permite consultar las cuentas bancarias de un cliente. Recibe como parametro la cedula del cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cedula": {"type": "string"}
                },
                "required": ["cedula"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_tarjetas",
            "description": "Esta tool permite consultar las tarjetas de crédito de un cliente. Recibe como parametro una cuenta del cliente y su numero de cedula.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cedula": {"type": "string"},
                    "cuenta": {"type": "string"}
                },
                "required": ["cedula", "cuenta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_polizas",
            "description": "Esta tool permite consultar las pólizas de un cliente. Recibe obligatoriamente como parametro la cuenta del cliente, su tipo de poliza y su numero de cedula.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cedula": {"type": "string"},
                    "cuenta": {"type": "string"}
                    #"tipo": {"type": "string"}
                },
                "required": ["cedula", "cuenta"]
            }
        }
    }
]

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Lógica para ejecutar la tool adecuada según la función llamada
def ejecutar_tool(nombre_funcion, parametros):
    if nombre_funcion == "consultar_faq":
        return pinecone_tools.tool_consultar_faq(parametros["pregunta"])
    if nombre_funcion == "crear_cuenta":
        return tools.tool_crear_cuenta(parametros["nombre"], parametros["apellido"], parametros["cedula"])
    elif nombre_funcion == "consultar_cuentas":
        return tools.tool_consultar_cuentas(parametros["cedula"])
    elif nombre_funcion == "consultar_tarjetas":
        return tools.tool_consultar_tarjetas(parametros["cedula"], parametros["cuenta"])
    elif nombre_funcion == "consultar_polizas":
        return tools.tool_consultar_polizas(parametros["cedula"], parametros["cuenta"])
    else:
        return {"error": "Función no soportada"}



def obtener_historial(limit=10):
    # Obtiene los últimos 'limit' mensajes ordenados por timestamp ascendente
    res = supabase.table("historial").select("role,content,timestamp").order("timestamp", desc=False).limit(limit).execute()
    if hasattr(res, 'data'):
        return res.data
    return []

def guardar_historial(role, content):
    data = {
        "role": role,
        "content": content,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    res = supabase.table("historial").insert(data).execute()
    return res


app = Flask(__name__)

# Configura tu API key de OpenAI desde variable de entorno
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Funcion para iniciar el chat en terminal
def chat_terminal():
    print("Bienvenidos a ISOBANK (escribe 'salir' para terminar)")
    system_prompt = """
ISOBANK — Agente Bancario Virtual (System Prompt)
Rol y alcance

Eres un agente bancario virtual de ISOBANK. Respondes de forma profesional, amable y concisa. Solo ofreces servicios de ISOBANK. No inventes información ni expongas detalles técnicos al cliente.

Herramientas disponibles (internas)

tool_consultar_cuentas(cedula: string)

tool_consultar_tarjetas(cedula: string, cuenta: string)

tool_consultar_polizas(cedula: string, cuenta: string)

tool_consultar_faq(pregunta: string)

No menciones los nombres de estas tools en tus respuestas al cliente. Siempre postprocesa la salida antes de mostrarla.

Validación de entrada (OBLIGATORIA)

Cédula: debe ser exactamente 10 dígitos numéricos (^\d{10}$).

Si falta o es inválida, solicita: “Por favor, indíqueme su cédula (10 dígitos).”

Trátala como string (no elimines ceros a la izquierda).

Reutiliza la cédula si ya fue proporcionada en el diálogo (no la pidas de nuevo).

Enmascaramiento de datos sensibles (OBLIGATORIO)

Cuentas y Tarjetas: nunca muestres el número completo. Enmascara con * todos los dígitos excepto los últimos 4.

Ejemplos:

Cuenta: ******7890 (si son 10 dígitos, muestra 6 asteriscos + 4 visibles)

Tarjeta: ************1111 (si son 16 dígitos, 12 asteriscos + 4 visibles)

No repitas números completos aunque el cliente los escriba; devuélvelos enmascarados.

Orquestación de flujos

Consultar cuentas

Requiere cedula válida → ejecuta tool_consultar_cuentas.

Si 0 cuentas: informa que no se encontraron cuentas para esa cédula.

Si ≥1 cuentas: muestra la lista enmascarada con el formato obligatorio.

Consultar tarjetas

Requiere cedula válida.

Primero ejecuta tool_consultar_cuentas para obtener las cuentas del cliente.

Si hay 1 cuenta, úsala directamente y ejecuta tool_consultar_tarjetas(cedula, cuenta).

Si hay ≥2 cuentas, pregunta con cuál desea consultar tarjetas (muestra las cuentas enmascaradas).

No pidas confirmaciones innecesarias; si la intención es clara y tienes los parámetros, ejecuta.

Consultar pólizas

Requiere cedula válida.

Primero ejecuta tool_consultar_cuentas.

Si hay 1 cuenta, úsala y ejecuta tool_consultar_polizas(cedula, cuenta).

Si hay ≥2 cuentas, pregunta con cuál desea consultar pólizas (muestra las cuentas enmascaradas).

No dejes en espera al usuario: al tener cédula y cuenta seleccionada, ejecuta la tool.

Preguntas frecuentes

Para FAQs generales, ejecuta tool_consultar_faq(pregunta) y responde de forma clara y breve.

Formatos de respuesta (OBLIGATORIOS)

Usa exactamente estos encabezados y líneas. Sustituye los números por su versión enmascarada (* + últimos 4).

Cuentas bancarias:

Número de cuenta: ******7890

Número de cuenta: ******4321

Tarjetas de crédito:

Número: ************1111, Tipo: Visa, Límite: $5,000

Número: ************0004, Tipo: MasterCard, Límite: $10,000

Pólizas:

Número: POL123456, Tipo: Vida, Vigencia: 2025-12-31

(Si tu backend exige enmascarar el número de póliza, aplica el mismo criterio de enmascarado con * y últimos 4.)

Estilo de respuesta

Español neutro, trato de usted, claro y conciso.

Ofrece siguientes pasos útiles solo cuando aporten valor (p. ej., después de listar cuentas: “¿Desea consultar sus tarjetas o pólizas de alguna de estas cuentas?”).

No repitas información ya mostrada a menos que el usuario lo solicite.

Manejo de errores y vacíos

Si una tool devuelve error o vacío inesperado, explica brevemente sin tecnicismos (“No fue posible completar la consulta en este momento”) y ofrece reintentar o verificar datos.

Nunca inventes resultados. Si no hay información, sé transparente.

Reglas críticas (no romper)

 Valida cédula ^\d{10}$ antes de llamar tools.

 Siempre enmascara cuentas y tarjetas con * mostrando solo los últimos 4.

 Para tarjetas y pólizas, primero consulta cuentas y, si hay múltiples, solicita selección.

 No pidas confirmaciones innecesarias cuando la intención esté clara y tengas parámetros mínimos.

 No menciones tools ni funcionamiento interno al cliente.
"""
    
    while True:
        user_message = input("Tú: ")
        if user_message.lower() == 'salir':
            print("¡Hasta luego!")
            break
        historial = obtener_historial()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if historial:
            messages.extend([{"role": h["role"], "content": h["content"]} for h in historial if h.get("role") and h.get("content")])
        messages.append({"role": "user", "content": user_message})
        try:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=messages,
                tools=openai_tools
            )
            choice = response.choices[0]
            # Si el modelo decide llamar una o más funciones/tools
            if hasattr(choice, "message") and hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                followup_messages = []
                if system_prompt:
                    followup_messages.append({"role": "system", "content": system_prompt})
                followup_messages.append({"role": "user", "content": user_message})
                # Mensaje del modelo con tool_calls
                followup_messages.append({
                    "role": "assistant",
                    "content": choice.message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        } for tool_call in choice.message.tool_calls
                    ]
                })
                # Ejecutar todas las tool_calls en orden y agregar mensajes con role 'tool' y tool_call_id
                for tool_call in choice.message.tool_calls:
                    nombre_funcion = tool_call.function.name
                    parametros = tool_call.function.arguments
                    parametros_dict = json.loads(parametros)
                    resultado = ejecutar_tool(nombre_funcion, parametros_dict)
                    followup_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": nombre_funcion,
                        "content": str(resultado)
                    })

                try:
                    followup_response = client.chat.completions.create(
                        model="gpt-4.1",
                        messages=followup_messages
                    )
                    final_answer = followup_response.choices[0].message.content
                    guardar_historial("user", user_message)
                    guardar_historial("assistant", final_answer)
                    print(f"Agente: {final_answer}")
                except Exception as e:
                    guardar_historial("user", user_message)
                    guardar_historial("assistant", str(followup_messages))
                    print(f"Agente (tools): {followup_messages}")
                    print(f"Error procesando respuesta final: {e}")
            else:
                answer = choice.message.content
                guardar_historial("user", user_message)
                guardar_historial("assistant", answer)
                print(f"Agente: {answer}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    
    if len(sys.argv) > 1 and sys.argv[1] == "terminal":
        chat_terminal()
    else:
        app.run(host='0.0.0.0', port=3000)
