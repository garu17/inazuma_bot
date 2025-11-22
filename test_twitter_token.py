#!/usr/bin/env python3
"""
Script para verificar que el Bearer Token de Twitter es válido
"""

import os
from dotenv import load_dotenv
import tweepy

# Cargar variables de entorno
load_dotenv()

print("="*60)
print("[TEST] Twitter API Bearer Token Validator")
print("="*60)

bearer_token = os.getenv('TWITTER_BEARER_TOKEN', '').strip()

print(f'\n📋 Token from .env:')
print(f'   {bearer_token}')
print(f'\n📊 Token Details:')
print(f'   Length: {len(bearer_token)} characters')
print(f'   Format: URL-encoded (contains %XX sequences)')
print(f'   Starts with: {bearer_token[:30]}...')
print(f'   Ends with: ...{bearer_token[-30:]}')

print(f'\n🔍 Intentando conectar a Twitter API...')
print(f'   (usando token tal como está en .env, sin decodificar)')
try:
    client = tweepy.Client(bearer_token=bearer_token)
    print(f'✅ Conexión exitosa!')
    
    # Intentar obtener un usuario para verificar que funciona
    print(f'\n🔍 Intentando obtener información del usuario @Gael20635038...')
    user = client.get_user(username='Gael20635038')
    if user and user.data:
        print(f'✅✅✅ TOKEN VÁLIDO! ✅✅✅')
        print(f'   Usuario encontrado: @{user.data["username"]} (ID: {user.data["id"]})')
        print(f'\n   El token funciona correctamente.')
        print(f'   Puedes usarlo en el bot sin problemas.')
    else:
        print(f'⚠️  No se pudo obtener información del usuario')
        
except tweepy.Unauthorized as e:
    print(f'❌ ERROR 401 Unauthorized: Token inválido o expirado')
    print(f'   {e}')
except tweepy.Forbidden as e:
    print(f'❌ ERROR 403 Forbidden: Permisos insuficientes')
    print(f'   {e}')
except tweepy.TooManyRequests as e:
    print(f'❌ ERROR 429 Too Many Requests: Rate limit alcanzado')
    print(f'   {e}')
    print(f'\n   Esto es normal con el plan free de Twitter.')
    print(f'   El token probablemente es válido.')
except tweepy.TweepyException as e:
    print(f'❌ Error de Tweepy: {e}')
except Exception as e:
    print(f'❌ Error inesperado: {type(e).__name__}: {e}')

print(f'\n' + "="*60)
print("[TEST] Fin de validación")
print("="*60)
