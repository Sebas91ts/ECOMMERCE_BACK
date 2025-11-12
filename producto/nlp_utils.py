# producto/nlp_utils.py

import json
from decouple import config
import google.generativeai as genai

PROMPT_ECOMMERCE = """Eres un analizador de lenguaje natural para un ecommerce de electrodomésticos.
Analiza la solicitud del usuario y extrae información estructurada.

SOLO responde con un objeto JSON válido con estos campos:
- producto_nombre: string (ej: "refrigerador", "lavadora")
- marca: string (ej: "samsung", "lg") 
- cantidad: number (default: 1)
- accion: string ("agregar_carrito" o "buscar")
- caracteristicas: array de strings
- categoria: string o null
- precio_maximo: number o null

Texto a analizar: "{texto_usuario}"

SOLO EL JSON, nada más."""

def clean_gemini_response(text):
    """Limpia la respuesta de Gemini"""
    if text.startswith("```json"):
        return text.lstrip("```json").rstrip("```").strip()
    elif text.startswith("```"):
        return text.lstrip("```").rstrip("```").strip()
    return text.strip()

def parse_ecommerce_query(texto_usuario: str) -> dict:
    api_key = config('API_GEMINI', default='')
    
    if not api_key:
        print("⚠️ API_GEMINI no configurada")
        return {"accion": "buscar", "error": "API no configurada"}
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = PROMPT_ECOMMERCE.format(texto_usuario=texto_usuario)
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        print(f"🔍 Gemini raw response: '{raw_text}'")
        
        # Limpiar respuesta
        cleaned_text = clean_gemini_response(raw_text)
        
        # Parsear JSON
        parsed_data = json.loads(cleaned_text)
        print(f"✅ JSON parseado correctamente: {parsed_data}")
        
        return parsed_data

    except json.JSONDecodeError as e:
        print(f"❌ Error parseando JSON: {e}")
        return {"accion": "buscar", "error": "Error parseando respuesta"}
    except Exception as e:
        print(f"❌ Error en Gemini: {type(e).__name__}: {e}")
        return {"accion": "buscar", "error": "Error de conexión"}