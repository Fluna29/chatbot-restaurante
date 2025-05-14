# Bot de Reservas WhatsApp 🍝

Este proyecto es un bot desarrollado en Flask que permite gestionar reservas y pedidos para llevar a través de WhatsApp utilizando Twilio.

## 🚀 Despliegue en Render

Sigue estos pasos para desplegar tu bot en [Render.com](https://render.com):

### 1. Requisitos

- Cuenta gratuita en [Render](https://render.com)
- Cuenta en [Twilio](https://www.twilio.com/) con acceso a Sandbox de WhatsApp
- Repositorio en GitHub (donde subirás este código)

### 2. Estructura del proyecto

Asegúrate de tener los siguientes archivos en tu repositorio:

```
app.py                    # Tu bot Flask completo
requirements.txt          # Dependencias (Flask, Twilio)
Procfile                  # Instrucción para arrancar Flask
runtime.txt               # Versión de Python (opcional)
pedidos_guardados.json    # (opcional) Datos iniciales
id_counter.json           # (opcional) Contador de ID inicial
```

### 3. Variables de entorno (Environment Variables)

En tu servicio de Render, configura las siguientes variables:

| Clave               | Valor                   |
|--------------------|--------------------------|
| `TWILIO_SID`        | Tu SID de cuenta Twilio |
| `TWILIO_AUTH_TOKEN` | Tu token de autenticación Twilio |

### 4. Despliegue

1. Ve a [https://dashboard.render.com](https://dashboard.render.com)
2. Crea un nuevo **Web Service**
3. Conecta tu repositorio de GitHub
4. Render instalará todo automáticamente
5. Tu app estará disponible en una URL como:

```
https://mi-bot-whatsapp.onrender.com
```

Configura esa URL como webhook en tu sandbox de Twilio.

---

## 📦 Endpoints disponibles

- `POST /bot` → endpoint para WhatsApp (Twilio)
- `GET /api/pedidos` → obtener pedidos
- `POST /api/pedidos` → crear nuevo pedido
- `PUT /api/pedidos/<id>` → actualizar pedido
- `DELETE /api/pedidos/<id>` → eliminar pedido

---

