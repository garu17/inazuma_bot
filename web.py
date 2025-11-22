"""
Flask web server para Inazuma Bot
Proporciona una interfaz web y mantiene el bot activo en Render
"""

from flask import Flask, render_template_string
from datetime import datetime
import os

app = Flask(__name__)

# HTML para la página principal
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inazuma Bot - Twitter Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }
        
        h1 {
            color: #667eea;
            margin-bottom: 10px;
            text-align: center;
            font-size: 2.5em;
        }
        
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        
        .status {
            background: #f0f7ff;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            font-size: 1.05em;
        }
        
        .status-label {
            font-weight: 600;
            color: #333;
        }
        
        .status-value {
            color: #667eea;
            font-weight: 500;
        }
        
        .status-ok {
            color: #10b981;
        }
        
        .info-section {
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .info-section h2 {
            color: #333;
            font-size: 1.3em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .info-section p {
            color: #666;
            line-height: 1.6;
            margin: 8px 0;
        }
        
        .features {
            list-style: none;
            margin: 15px 0;
        }
        
        .features li {
            padding: 8px 0;
            color: #555;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .features li:before {
            content: "✓";
            color: #10b981;
            font-weight: bold;
            font-size: 1.2em;
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #999;
            font-size: 0.9em;
        }
        
        .emoji {
            font-size: 1.3em;
        }
        
        .twitter-link {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 24px;
            background: #1da1f2;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            transition: background 0.3s;
        }
        
        .twitter-link:hover {
            background: #1a91da;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1><span class="emoji">⚡</span> Inazuma Bot</h1>
        <p class="subtitle">Monitor de Tweets en Discord</p>
        
        <div class="status">
            <div class="status-item">
                <span class="status-label">Estado del Bot:</span>
                <span class="status-value status-ok">✓ Activo</span>
            </div>
            <div class="status-item">
                <span class="status-label">Servidor de Web:</span>
                <span class="status-value status-ok">✓ En línea</span>
            </div>
            <div class="status-item">
                <span class="status-label">Última actualización:</span>
                <span class="status-value">{{ timestamp }}</span>
            </div>
        </div>
        
        <div class="info-section">
            <h2><span class="emoji">🔍</span> Funcionalidades</h2>
            <ul class="features">
                <li>Monitorea tweets de cuentas configuradas</li>
                <li>Publica automáticamente en Discord</li>
                <li>Filtra tweets con #spoilersie</li>
                <li>Enlaces directos a los tweets</li>
                <li>Optimizado para plan free de Twitter API</li>
            </ul>
        </div>
        
        <div class="info-section">
            <h2><span class="emoji">📊</span> Configuración</h2>
            <p><strong>Usuario monitorizado:</strong> {{ username }}</p>
            <p><strong>Intervalo de verificación:</strong> {{ check_interval }} segundos</p>
            <p><strong>Canal de Discord:</strong> #{{ discord_channel }}</p>
        </div>
        
        <div class="info-section">
            <h2><span class="emoji">ℹ️</span> Sobre el Bot</h2>
            <p>
                Inazuma Bot es un monitor de Twitter automático que sincroniza los tweets 
                de cuentas seleccionadas directamente en tu servidor de Discord.
            </p>
            <p style="margin-top: 15px;">
                El bot se ejecuta continuamente revisando nuevos tweets cada {{ check_interval_minutes }} minutos 
                y los publica automáticamente en el canal configurado.
            </p>
        </div>
        
        <div style="text-align: center; margin-top: 25px;">
            <a href="https://twitter.com/{{ username }}" class="twitter-link" target="_blank">
                📱 Ver en Twitter
            </a>
        </div>
        
        <div class="footer">
            <p>Inazuma Bot • Última verificación: {{ timestamp }}</p>
            <p>Desarrollado con Discord.py y Tweepy</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Página principal del bot"""
    from dotenv import load_dotenv
    load_dotenv()
    
    username = os.getenv('TWITTER_USERNAMES_TO_MONITOR', 'Gael20635038').split(',')[0].strip()
    check_interval = os.getenv('TWITTER_CHECK_INTERVAL', '3600')
    discord_channel = os.getenv('DISCORD_CHANNEL_ID', '1440438758024544439')
    
    try:
        check_interval_int = int(check_interval)
        check_interval_minutes = check_interval_int // 60
    except:
        check_interval_int = 3600
        check_interval_minutes = 60
    
    return render_template_string(
        HTML_TEMPLATE,
        timestamp=datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        username=username,
        check_interval=check_interval_int,
        check_interval_minutes=check_interval_minutes,
        discord_channel='noticias'
    )

@app.route('/health')
def health():
    """Endpoint para verificar que el bot está vivo (útil para Render)"""
    return {
        'status': 'ok',
        'bot': 'running',
        'timestamp': datetime.now().isoformat()
    }, 200

if __name__ == '__main__':
    # En producción (Render), usar gunicorn
    # En desarrollo local, usar Flask
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
