
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from datetime import datetime
import os
import json

app = Flask(__name__)

ARCHIVO_PEDIDOS = "pedidos_guardados.json"
ARCHIVO_CONTADOR = "id_counter.json"

if os.path.exists(ARCHIVO_PEDIDOS):
    with open(ARCHIVO_PEDIDOS, "r", encoding="utf-8") as f:
        pedidos_guardados = json.load(f)
else:
    pedidos_guardados = []

if os.path.exists(ARCHIVO_CONTADOR):
    with open(ARCHIVO_CONTADOR, "r", encoding="utf-8") as f:
        contador = json.load(f)["ultimo_id"]
else:
    contador = 0

def guardar_en_archivo():
    with open(ARCHIVO_PEDIDOS, "w", encoding="utf-8") as f:
        json.dump(pedidos_guardados, f, indent=2, ensure_ascii=False)
    with open(ARCHIVO_CONTADOR, "w", encoding="utf-8") as f:
        json.dump({"ultimo_id": contador}, f)

def generar_id_numerico():
    global contador
    contador += 1
    return contador

def enviar_mensaje_whatsapp(telefono, mensaje):
    try:
        account_sid = os.environ.get("TWILIO_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            from_="whatsapp:+14155238886",
            to=f"whatsapp:{telefono}",
            body=mensaje
        )
        print("Mensaje enviado:", msg.sid)
    except Exception as e:
        print("Error al enviar mensaje:", e)

@app.route("/api/pedidos", methods=["GET"])
def obtener_pedidos():
    print("Contenido actual:", pedidos_guardados)
    return jsonify(pedidos_guardados)


@app.route("/api/pedidos/<int:id_pedido>", methods=["PUT"])
def actualizar_pedido(id_pedido):
    datos = request.get_json()
    for pedido in pedidos_guardados:
        if pedido.get("id") == id_pedido:
            pedido.update(datos)
            pedido["timestamp"] = datetime.now().isoformat()
            guardar_en_archivo()
            # Enviar mensaje si se actualizó el estado
            if "estado" in datos and "telefono" in pedido:
                estado = datos["estado"]
                mensaje = {
                    "pendiente": "🕒 Tu pedido ha sido recibido.",
                    "en_preparacion": "👨‍🍳 Tu pedido está en preparación.",
                    "preparado": "✅ Tu pedido ya está listo para recoger.",
                    "entregado": "🚚 Tu pedido ha sido entregado. ¡Gracias!"
                }.get(estado, None)
                if mensaje:
                    enviar_mensaje_whatsapp(pedido["telefono"], mensaje)
            return jsonify({"mensaje": "Pedido actualizado", "pedido": pedido})
    return jsonify({"error": "Pedido no encontrado"}), 404

@app.route("/api/pedidos/<int:id_pedido>", methods=["DELETE"])
def eliminar_pedido(id_pedido):
    global pedidos_guardados
    pedido = next((p for p in pedidos_guardados if p.get("id") == id_pedido), None)
    if pedido:
        telefono = pedido.get("telefono")
        tipo = pedido.get("tipo")
        mensaje = "🛑 Tu reserva ha sido cancelada." if tipo == "reserva" else "🛑 Tu pedido ha sido cancelado."
        if telefono:
            enviar_mensaje_whatsapp(telefono, mensaje)
    pedidos_guardados = [p for p in pedidos_guardados if p.get("id") != id_pedido]
    guardar_en_archivo()
    return jsonify({"mensaje": "Pedido eliminado"}), 200

@app.route("/api/pedidos", methods=["POST"])
def crear_pedido():
    data = request.get_json()
    data["timestamp"] = datetime.now().isoformat()
    data["id"] = generar_id_numerico()
    pedidos_guardados.append(data)
    guardar_en_archivo()
    return jsonify({"mensaje": "Pedido creado", "pedido": data}), 201

estado_usuario = {}

PLATOS = {
    "1": "Spaghetti alla Carbonara",
    "2": "Pasta al Pomodoro",
    "3": "Fettuccine Alfredo",
    "4": "Penne al Pesto con Pollo",
    "5": "Pizza Margherita",
    "6": "Pizza Prosciutto e Funghi",
    "7": "Lasagna Tradicional",
    "8": "Risotto ai Frutti di Mare",
    "9": "Ensalada Caprese",
    "10": "Saltimbocca alla Romana"
}

LISTADO_PRODUCTOS = "\n".join([f"{n}. {nombre}" for n, nombre in PLATOS.items()])

@app.route('/bot', methods=['POST'])
def bot():
    from_numero = request.form.get("From", "").replace("whatsapp:", "")
    mensaje = request.form.get("Body", "").strip().lower()
    respuesta = MessagingResponse()
    msg = respuesta.message()

    if from_numero not in estado_usuario:
        estado_usuario[from_numero] = {"fase": "esperando_tipo"}

    usuario = estado_usuario[from_numero]

    if "menu" in mensaje or "menú" in mensaje:
        msg.body("🇮🇹 Menú del Día – escribe *pedido* o *reserva* para comenzar:\n\n" + LISTADO_PRODUCTOS)
        return str(respuesta)

    if usuario["fase"] == "esperando_tipo":
        if "reserva" in mensaje:
            usuario["tipo"] = "reserva"
        elif "llevar" in mensaje or "pedido" in mensaje:
            usuario["tipo"] = "pedido_para_llevar"
        else:
            msg.body("¿Deseas hacer una *reserva* o un *pedido para llevar*?")
            return str(respuesta)
        usuario["fase"] = "esperando_nombre"
        msg.body("✏️ Por favor, escribe *solo tu nombre completo*, sin frases adicionales.")

    elif usuario["fase"] == "esperando_nombre":
        usuario["nombre"] = mensaje.title()
        if usuario["tipo"] == "reserva":
            usuario["fase"] = "esperando_personas"
            msg.body("👥 ¿Para cuántas personas es la reserva?")
        else:
            usuario["fase"] = "esperando_hora"
            msg.body("🕒 ¿A qué hora deseas recoger tu pedido? (Ej: 14:00)")

    elif usuario["fase"] == "esperando_personas":
        try:
            usuario["personas"] = int(mensaje)
            usuario["fase"] = "esperando_fecha"
            msg.body("📅 ¿Para qué fecha deseas reservar? (Ej: 2025-05-14)")
        except ValueError:
            msg.body("❌ Por favor, escribe solo el número de personas. (Ej: 3)")

    elif usuario["fase"] == "esperando_fecha":
        usuario["fecha"] = mensaje
        usuario["fase"] = "esperando_hora"
        msg.body("🕒 ¿A qué hora deseas reservar mesa? (Ej: 14:00)")

    elif usuario["fase"] == "esperando_hora":
        usuario["hora"] = mensaje
        if usuario["tipo"] == "reserva":
            payload = {
                "id": generar_id_numerico(),
                "telefono": from_numero,
                "tipo": usuario["tipo"],
                "nombre": usuario["nombre"],
                "fecha": usuario["fecha"],
                "personas": usuario["personas"],
                "hora": usuario["hora"],
                "productos": [],
                "timestamp": datetime.now().isoformat()
            }
            pedidos_guardados.append(payload)
            guardar_en_archivo()
            msg.body(
                f"✅ ¡Reserva confirmada!\n\n"
                f"📌 Nombre: {usuario['nombre']}\n"
                f"📅 Fecha: {usuario['fecha']}\n"
                f"👥 Personas: {usuario['personas']}\n"
                f"🕒 Hora: {usuario['hora']}"
            )
            del estado_usuario[from_numero]
        else:
            usuario["fase"] = "esperando_productos"
            msg.body(
                "📝 Escribe los *números* de los productos que deseas, separados por comas.\n"
                "Ej: 1, 2, 2, 5\n\n" + LISTADO_PRODUCTOS
            )

    elif usuario["fase"] == "esperando_productos":
        from collections import Counter
        numeros = [n.strip() for n in mensaje.split(",")]
        cantidades = Counter(numeros)
        productos = []
        for num, cant in cantidades.items():
            nombre = PLATOS.get(num)
            if nombre:
                productos.append(f"{nombre} (x{cant})")
        usuario["productos"] = productos

        payload = {
            "id": generar_id_numerico(),
            "telefono": from_numero,
            "tipo": usuario["tipo"],
            "nombre": usuario["nombre"],
            "hora": usuario["hora"],
            "productos": usuario["productos"],
            "timestamp": datetime.now().isoformat(),
            "estado": "pendiente"
        }
        pedidos_guardados.append(payload)
        guardar_en_archivo()
        msg.body(
            f"✅ ¡Pedido para llevar confirmado!\n\n"
            f"📌 Nombre: {usuario['nombre']}\n"
            f"🕒 Hora de recogida: {usuario['hora']}\n"
            f"🍽️ Productos:\n- " + "\n- ".join(usuario["productos"])
        )
        del estado_usuario[from_numero]

    else:
        msg.body("👋 ¡Hola! ¿Deseas hacer una *reserva* o un *pedido para llevar*?")

    return str(respuesta)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

