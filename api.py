from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# Simulación de base de datos en memoria
clientes = {}
cuentas = {}
tarjetas = {}
polizas = {}

# 1. Crear cuenta bancaria
@app.route('/crear_cuenta', methods=['POST'])
def crear_cuenta():
    data = request.get_json()
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    cedula = data.get('cedula')
    if not (nombre and apellido and cedula):
        return jsonify({'error': 'Faltan datos requeridos'}), 400
    # Generar número de cuenta de 10 dígitos único
    while True:
        numero_cuenta = str(random.randint(10**9, 10**10-1))
        if numero_cuenta not in cuentas:
            break
    cuentas[numero_cuenta] = cedula
    if cedula not in clientes:
        clientes[cedula] = {'nombre': nombre, 'apellido': apellido, 'cuentas': []}
    clientes[cedula]['cuentas'].append(numero_cuenta)
    return jsonify({'mensaje': 'Cuenta creada exitosamente', 'numero_cuenta': numero_cuenta})

# 2. Consultar cuentas por cédula
@app.route('/consultar_cuentas', methods=['POST'])
def consultar_cuentas():
    data = request.get_json()
    cedula = data.get('cedula')
    if not cedula:
        return jsonify({'error': 'Falta el número de cédula'}), 400
    cuentas_cliente = clientes.get(cedula, {}).get('cuentas', [])
    return jsonify({'cuentas': cuentas_cliente})

# 3. Consultar tarjetas de crédito
@app.route('/consultar_tarjetas', methods=['POST'])
def consultar_tarjetas():
    data = request.get_json()
    cedula = data.get('cedula')
    cuenta = data.get('cuenta')
    if not (cedula and cuenta and len(cuenta) == 10):
        return jsonify({'error': 'Datos inválidos'}), 400
    tarjetas_cliente = tarjetas.get((cedula, cuenta), [
        {'numero': '4111111111111111', 'tipo': 'Visa', 'limite': '$5,000'}
    ])
    return jsonify({'tarjetas': tarjetas_cliente})

# 4. Consultar pólizas
@app.route('/consultar_polizas', methods=['POST'])
def consultar_polizas():
    data = request.get_json()
    cedula = data.get('cedula')
    cuenta = data.get('cuenta')
    if not (cedula and cuenta and len(cuenta) == 10):
        return jsonify({'error': 'Datos inválidos'}), 400
    polizas_cliente = polizas.get((cedula, cuenta), [
        {'numero': 'POL123456', 'tipo': 'Vida', 'vigencia': '2025-12-31'}
    ])
    return jsonify({'polizas': polizas_cliente})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002)
