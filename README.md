# Bot de Discord - Base

Estructura basica para arrancar un bot de Discord con Python y discord.py.

## Estructura
```
discord-bot-basico/
├── bot.py              # Archivo principal, arranca el bot
├── cogs/
│   └── ejemplo.py       # Ejemplo de cog (modulo de comandos)
├── requirements.txt     # Dependencias
├── .env.example         # Plantilla para tu token
└── .gitignore
```

## Pasos para correrlo

1. Crea un bot en https://discord.com/developers/applications, copia el token
   y activa los "Privileged Gateway Intents" (Message Content, Server Members).

2. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

3. Renombra `.env.example` a `.env` y pega tu token ahi:
   ```
   DISCORD_TOKEN=tu_token_real
   ```

4. Invita el bot a tu servidor con este link (reemplaza CLIENT_ID):
   ```
   https://discord.com/api/oauth2/authorize?client_id=CLIENT_ID&permissions=8&scope=bot%20applications.commands
   ```

5. Corre el bot:
   ```
   python bot.py
   ```

## Como agregar mas comandos

Crea un nuevo archivo en `cogs/`, siguiendo el patron de `ejemplo.py`, y se carga
automaticamente al iniciar el bot.
# OmniverseMC-Staff-Updates
