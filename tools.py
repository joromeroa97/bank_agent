import requests

# Tool 1: Crear cuenta bancaria

def tool_crear_cuenta(nombre, apellido, cedula):
    url = "http://localhost:3002/crear_cuenta"
    payload = {"nombre": nombre, "apellido": apellido, "cedula": cedula}
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {"error": "Lo sentimos, no pudimos procesar tu solicitud. Inténtalo más tarde."}

# Tool 2: Consultar cuentas bancarias

def tool_consultar_cuentas(cedula):
    url = "http://localhost:3002/consultar_cuentas"
    payload = {"cedula": cedula}
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {"error": "Lo sentimos, no pudimos procesar tu solicitud. Inténtalo más tarde."}

# Tool 3: Consultar tarjetas de crédito

def tool_consultar_tarjetas(cedula, cuenta):
    url = "http://localhost:3002/consultar_tarjetas"
    payload = {"cedula": cedula, "cuenta": cuenta}
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {"error": "Lo sentimos, no pudimos procesar tu solicitud. Inténtalo más tarde."}

# Tool 4: Consultar pólizas

def tool_consultar_polizas(cedula, cuenta):
    url = "http://localhost:3002/consultar_polizas"
    payload = {"cedula": cedula, "cuenta": cuenta}
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {"error": "Lo sentimos, no pudimos procesar tu solicitud. Inténtalo más tarde."}
