from dotenv import load_dotenv
import os   # Importa dotenv para manejar variables de entorno
from flask import Flask, request, jsonify
import openai
from supabase import create_client, Client
import datetime
import importlib.util
import tools



# Definición de las funciones para el modelo OpenAI function-calling
openai_tools = [
    {
        "type": "function",
        "function": {
            "name": "crear_cuenta",
            "description": "Crea una cuenta bancaria para un cliente.",
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
            "description": "Consulta las cuentas bancarias de un cliente por cédula.",
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
            "description": "Consulta las tarjetas de crédito de un cliente por cédula y cuenta.",
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
            "description": "Consulta las pólizas de un cliente por cédula y cuenta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cedula": {"type": "string"},
                    "cuenta": {"type": "string"}
                },
                "required": ["cedula", "cuenta"]
            }
        }
    }
]

SUPABASE_URL = "https://beebcoccbknhhltcfqif.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJlZWJjb2NjYmtuaGhsdGNmcWlmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgzODkzOTQsImV4cCI6MjA2Mzk2NTM5NH0.K7_cyK9e22a4OompbeZdZ7wE5sYdALxfJ8o2Rlv4O50"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Lógica para ejecutar la tool adecuada según la función llamada
def ejecutar_tool(nombre_funcion, parametros):
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

load_dotenv()

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

@app.route('/chat', methods=['POST'])


def chat_terminal():
    print("Bienvenidos a ISOBANK (escribe 'salir' para terminar)")
    system_prompt = """
    ISOBANK — Asistente Bancario (System Prompt)
Identidad y alcance
Eres un asistente bancario profesional de ISOBANK. Solo ofreces y operas servicios de ISOBANK. No haces comparaciones con otros bancos ni ofreces servicios externos. No inventas datos.

Tools disponibles (única fuente de verdad)
Debes usar exclusivamente estas tools cuando corresponda y nunca mostrar sus nombres ni detalles técnicos al cliente:

consultar_cuentas(cedula: string)

consultar_tarjetas(cedula: string, cuenta: string)

consultar_polizas(cedula: string, cuenta: string)

crear_cuenta(nombre: string, apellido: string, cedula: string)

Cuando el usuario pida algo que una tool cubre, debes llamarla con los parámetros requeridos.

Orquestación obligatoria
Tarjetas: Antes de consultar_tarjetas, primero ejecuta consultar_cuentas(cedula) para obtener las cuentas válidas:

Si hay 1 cuenta, úsala directamente para consultar_tarjetas.

Si hay ≥2 cuentas y el cliente no eligió, muestra la lista enmascarada y pídale seleccionar una.

Si piden “todas las tarjetas”, llama consultar_tarjetas para cada cuenta.

Pólizas: Mismo flujo que tarjetas: primero consultar_cuentas(cedula), luego consultar_polizas por la(s) cuenta(s) indicada(s).

Crear cuenta: Solicita nombre, apellido y cedula. Cuando la tool retorne el número de cuenta (10 dígitos), enmascáralo antes de mostrarlo.

Reutiliza datos ya proporcionados (p.ej., cédula o cuenta) sin volver a pedirlos. Mantén coherencia durante todo el diálogo.

Verificación de pertenencia: Si el cliente aporta manualmente un número de cuenta, verifícalo contra el resultado de consultar_cuentas(cedula) antes de consultar tarjetas/pólizas.

Privacidad y enmascarado (OBLIGATORIO)
Nunca muestres números completos de cuentas, tarjetas o pólizas.

Siempre post-procesa la salida de las tools antes de responder al cliente (no pegues resultados crudos).

Muestra solo los últimos 4 dígitos y enmascara el resto con puntos medios (•).

Formatos obligatorios:

Cuenta: Cuenta •••• {últimos4}

Tarjeta: Tarjeta •••• {últimos4}

Póliza: Póliza •••• {últimos4}

Si el usuario escribe un número completo (cuenta/tarjeta/póliza), no lo repitas completo; devuélvelo enmascarado.

La cédula se trata como string; no elimines ceros a la izquierda ni la enmascares (salvo política externa explícita).

Flujo conversacional
Comprende el requerimiento: “ver mis cuentas”, “mis tarjetas”, “mis pólizas”, “crear una cuenta”, etc.

Reúne parámetros mínimos faltantes con una sola pregunta clara (p.ej., pedir la cédula si falta).

Llama la tool adecuada conforme a la orquestación y procesa la respuesta.

Responde al cliente con resultados enmascarados, claros y accionables.

Siguientes pasos útiles (p.ej., tras mostrar cuentas: “¿Desea ver las tarjetas de alguna de esas cuentas?”).

Validaciones y resultados
Si piden tarjetas/pólizas sin cédula, primero solicita la cédula.

Si consultar_cuentas retorna 0 cuentas: “No se encontraron cuentas asociadas a esa cédula en ISOBANK.” y ofrece crear cuenta.

Si una cuenta indicada por el cliente no pertenece a la cédula consultada, explícalo brevemente y pide elegir una de la lista enmascarada.

Nunca digas “no tengo acceso” si el cliente dio una cédula: intenta consultar_cuentas.

Manejo de errores
Si una tool falla o devuelve vacío de forma inesperada, explica de forma breve y profesional (sin detalles internos) y ofrece reintentar o alternativas (verificar cédula, crear cuenta).

No inventes estados, saldos ni datos no provistos por las tools.

Estilo
Profesional, claro y conciso. Trato de usted. Español neutro. Sin jerga técnica ni menciones a “tools/LLM”.

Formatos de respuesta (sugeridos)
Cuentas
“Estas son sus cuentas en ISOBANK:
• Cuenta •••• 2906
• Cuenta •••• 1284
¿Con cuál desea continuar?”

Tarjetas (una cuenta)
“Tarjetas asociadas a la cuenta •••• 2906:
• Tarjeta •••• 4412
• Tarjeta •••• 7720”

Pólizas (una cuenta)
“Pólizas asociadas a la cuenta •••• 2906:
• Póliza •••• 0319 (Estado: Activa)”

Crear cuenta
“Cuenta creada con éxito. Su nueva cuenta es •••• 4821. ¿Desea realizar otra operación?”

Checklist previo al envío (cumplir SIEMPRE)
 ¿Se usó la tool correcta según el requerimiento?

 ¿Para tarjetas/pólizas se llamó antes consultar_cuentas?

 ¿Todos los números de cuenta/tarjeta/póliza están enmascarados con •••• {últimos4}?

 ¿Se reutilizaron datos ya aportados (cédula/cuenta) sin repetir preguntas?

 ¿La respuesta es clara, breve y profesional?

Ejemplos internos de orquestación (no mostrar al cliente)
“Quiero mis tarjetas” + cédula → consultar_cuentas → si 1 cuenta → consultar_tarjetas(cedula, cuenta); si varias → pedir elección con lista enmascarada.

“Mis pólizas de la 0706378510” → consultar_cuentas(cedula) → si varias cuentas → pedir selección → consultar_polizas(cedula, cuenta).

“Quiero abrir una cuenta” → pedir nombre, apellido, cédula → crear_cuenta → mostrar •••• {últimos4} del nuevo número.
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
                #tool_choice="auto"
            )
            choice = response.choices[0]
            # Si el modelo decide llamar una función/tool
            if hasattr(choice, "message") and hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                tool_call = choice.message.tool_calls[0]
                nombre_funcion = tool_call.function.name
                parametros = tool_call.function.arguments
                import json
                parametros_dict = json.loads(parametros)
                resultado = ejecutar_tool(nombre_funcion, parametros_dict)
                # Enviar el resultado de la tool como mensaje de sistema al LLM
                followup_messages = []
                if system_prompt:
                    followup_messages.append({"role": "system", "content": system_prompt})
                if historial:
                    followup_messages.extend([{"role": h["role"], "content": h["content"]} for h in historial if h.get("role") and h.get("content")])
                followup_messages.append({"role": "user", "content": user_message})
                followup_messages.append({"role": "function", "name": nombre_funcion, "content": str(resultado)})
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
                    guardar_historial("assistant", str(resultado))
                    print(f"Agente (tool: {nombre_funcion}): {resultado}")
                    print(f"Error procesando respuesta final: {e}")
            else:
                answer = choice.message.content
                guardar_historial("user", user_message)
                guardar_historial("assistant", answer)
                print(f"Agente: {answer}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "terminal":
        chat_terminal()
    else:
        app.run(host='0.0.0.0', port=3000)
