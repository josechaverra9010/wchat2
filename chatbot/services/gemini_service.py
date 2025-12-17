"""
Servicio para interactuar con Google Gemini AI - VERSIÓN CORREGIDA
"""
import logging
import re
import google.generativeai as genai
from django.conf import settings
from .db_service import DatabaseService

logger = logging.getLogger('chatbot')


class GeminiService:
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.db_service = DatabaseService()
        
        if not self.api_key:
            logger.warning("API de Gemini sin configurar")
            return
        
        # Configurar Gemini
        genai.configure(api_key=self.api_key)
        
        # Configuración del modelo
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1500,
        }
        
        # Configuración de seguridad
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]
        
        # Inicializar modelo
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
    
    def _extraer_informacion_db(self, message):
        """
        Extraer información relevante de la base de datos según el mensaje
        
        Returns:
            String con contexto de la base de datos
        """
        context = ""
        message_lower = message.lower()
        
        logger.info("="*60)
        logger.info("🔍 EXTRAYENDO INFORMACIÓN DE LA BASE DE DATOS")
        logger.info(f"📝 Mensaje: {message}")
        logger.info("="*60)
        
        try:
            # 1. SIEMPRE mostrar algunos productos (para cualquier consulta)
            logger.info("📦 Consultando productos disponibles...")
            productos_general = self.db_service.listar_productos(limit=10)
            if productos_general:
                context += "\n\n📦 **CATÁLOGO DE PRODUCTOS DISPONIBLES:**\n"
                for p in productos_general:
                    context += f"• ID: {p.id} | {p.nombre} - ${p.precio:,.0f} COP | Stock: {p.stock} | Categoría: {p.categoria or 'Sin categoría'}\n"
                logger.info(f"✅ Se encontraron {len(productos_general)} productos")
            else:
                logger.warning("⚠️ No se encontraron productos en la base de datos")
            
            # 2. Búsqueda específica por nombre de producto
            palabras_clave = [palabra for palabra in message_lower.split() if len(palabra) > 3]
            logger.info(f"🔑 Palabras clave para búsqueda: {palabras_clave}")
            
            for palabra in palabras_clave:
                productos_busqueda = self.db_service.buscar_producto(palabra)
                if productos_busqueda.exists():
                    context += f"\n\n🔍 **BÚSQUEDA: '{palabra.upper()}':**\n"
                    for p in productos_busqueda[:5]:
                        context += f"• {p.nombre} - ${p.precio:,.0f} COP (Stock: {p.stock})\n"
                        if p.descripcion:
                            context += f"  Descripción: {p.descripcion[:150]}...\n"
                    logger.info(f"✅ Búsqueda '{palabra}': {productos_busqueda.count()} resultados")
                    break
            
            # 3. Categorías disponibles
            if any(word in message_lower for word in ['categoría', 'categorias', 'tipo', 'tipos', 'qué tienen']):
                logger.info("🏷️ Consultando categorías...")
                categorias = self.db_service.obtener_categorias()
                if categorias:
                    context += "\n\n🏷️ **CATEGORÍAS DISPONIBLES:**\n"
                    context += ", ".join(categorias) + "\n"
                    logger.info(f"✅ Categorías encontradas: {categorias}")
            
            # 4. Productos más vendidos / populares
            if any(word in message_lower for word in ['popular', 'vendido', 'recomendación', 'recomienda', 'mejor']):
                logger.info("⭐ Consultando productos populares...")
                populares = self.db_service.productos_mas_vendidos(limit=5)
                if populares:
                    context += "\n\n⭐ **PRODUCTOS MÁS POPULARES:**\n"
                    for p in populares:
                        context += f"• {p['producto__nombre']} - ${p['producto__precio']:,.0f} COP ({p['total_vendido']} vendidos)\n"
                    logger.info(f"✅ Productos populares: {len(populares)} encontrados")
            
            # 5. Búsqueda por rango de precio
            numeros = re.findall(r'\d+', message)
            if numeros and any(word in message_lower for word in ['precio', 'cuesta', 'vale', 'cuánto', 'cuanto']):
                logger.info(f"💰 Búsqueda por precio: {numeros}")
                precio_ref = int(numeros[0])
                # Si el número es muy pequeño, asumimos miles
                if precio_ref < 1000:
                    precio_ref *= 1000
                
                productos_precio = self.db_service.buscar_productos_por_precio(
                    precio_min=precio_ref * 0.5,
                    precio_max=precio_ref * 1.5,
                    limit=5
                )
                if productos_precio:
                    context += f"\n\n💰 **PRODUCTOS CERCA DE ${precio_ref:,.0f} COP:**\n"
                    for p in productos_precio:
                        context += f"• {p.nombre} - ${p.precio:,.0f} COP (Stock: {p.stock})\n"
                    logger.info(f"✅ Productos por precio: {len(productos_precio)} encontrados")
            
            # 6. Stock específico
            if any(word in message_lower for word in ['stock', 'disponible', 'hay', 'tienen']):
                logger.info("📊 Mostrando información de stock...")
                # Ya incluido en el catálogo general
            
            logger.info("="*60)
            logger.info(f"📊 CONTEXTO GENERADO ({len(context)} caracteres)")
            logger.info("="*60)
        
        except Exception as e:
            logger.error(f"❌ Error extrayendo información DB: {e}", exc_info=True)
        
        return context
    
    def get_response(self, message, context=None, phone_number=None):
        """
        Generar respuesta usando Gemini con contexto de base de datos
        
        Args:
            message: Mensaje del usuario
            context: Contexto de conversación previo
            phone_number: Número de teléfono del usuario
        
        Returns:
            Respuesta generada por Gemini
        """
        if not self.api_key:
            return "Lo siento, el servicio de IA no está configurado correctamente."
        
        try:
            logger.info("="*80)
            logger.info("🤖 GENERANDO RESPUESTA CON GEMINI")
            logger.info(f"📱 Teléfono: {phone_number}")
            logger.info(f"💬 Mensaje: {message}")
            logger.info("="*80)
            
            # Extraer información de la base de datos
            db_context = self._extraer_informacion_db(message)
            
            # Información del cliente si se proporciona teléfono
            cliente_info = ""
            if phone_number:
                logger.info(f"👤 Buscando cliente con teléfono: {phone_number}")
                cliente = self.db_service.buscar_cliente(telefono=phone_number)
                if cliente:
                    stats = self.db_service.estadisticas_cliente(cliente.id)
                    cliente_info = f"\n\n👤 **INFORMACIÓN DEL CLIENTE:**\n"
                    cliente_info += f"• Nombre: {cliente.nombre}\n"
                    cliente_info += f"• Email: {cliente.email}\n"
                    if stats:
                        cliente_info += f"• Total pedidos: {stats['total_pedidos']}\n"
                        cliente_info += f"• Total gastado: ${stats['total_gastado']:,.0f} COP\n"
                    logger.info(f"✅ Cliente encontrado: {cliente.nombre}")
                else:
                    logger.info("ℹ️ Cliente no encontrado en la base de datos")
            
            # Construir prompt con contexto MEJORADO
            system_prompt = """Eres **Parchabot**, el asistente virtual de **Ébano Company** en Quibdó, Chocó, Colombia.

Tu misión es ayudar a los clientes con información sobre productos, precios, stock, pedidos y cualquier consulta relacionada con la empresa.

**REGLAS IMPORTANTES:**
1. **USA SIEMPRE LA INFORMACIÓN DE LA BASE DE DATOS** que se te proporciona abajo
2. **NUNCA INVENTES** información sobre productos, precios o stock
3. Si la información no está en la base de datos, dilo claramente
4. Responde en español colombiano, como si fueras de Quibdó
5. Sé amigable, usa emojis 😊 pero profesional
6. Mantén respuestas CORTAS (máximo 3 párrafos)
7. Cuando menciones precios, usa formato: $50.000 COP
8. Si te preguntan por productos específicos, busca en el catálogo proporcionado

**INFORMACIÓN DISPONIBLE DE LA BASE DE DATOS:**
{db_context}

{cliente_info}

**CONTEXTO DE LA CONVERSACIÓN:**
{context}

**MENSAJE ACTUAL DEL USUARIO:**
{message}

**INSTRUCCIONES ESPECÍFICAS:**
- Si pregunta por productos: menciona nombres, precios y stock del catálogo
- Si pregunta por disponibilidad: revisa el stock en la información proporcionada
- Si pregunta por categorías: usa las categorías de la base de datos
- Si pregunta por precios: usa los precios exactos de la base de datos
- Si pregunta por recomendaciones: sugiere productos del catálogo

**TU RESPUESTA (corta y directa usando la información de arriba):**"""
            
            prompt = system_prompt.format(
                db_context=db_context if db_context else "⚠️ No hay productos en la base de datos",
                cliente_info=cliente_info,
                context=context if context else "Esta es la primera interacción",
                message=message
            )
            
            logger.info(f"📤 Enviando prompt a Gemini ({len(prompt)} caracteres)")
            
            # Generar respuesta
            response = self.model.generate_content(prompt)
            
            if response.text:
                logger.info(f"✅ Respuesta generada: {response.text[:100]}...")
                logger.info("="*80)
                return response.text.strip()
            else:
                logger.warning("⚠️ Gemini no generó respuesta de texto")
                return "Lo siento, no pude generar una respuesta en este momento."
        
        except Exception as e:
            logger.error(f"❌ Error generando respuesta con Gemini: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error al procesar tu mensaje. Por favor intenta de nuevo."
    
    def get_response_with_history(self, messages_history, phone_number=None):
        """
        Generar respuesta usando historial completo
        
        Args:
            messages_history: Lista de diccionarios con 'role' y 'content'
            phone_number: Número de teléfono del usuario
        
        Returns:
            Respuesta generada por Gemini
        """
        if not self.api_key:
            return "Lo siento, el servicio de IA no está configurado correctamente."
        
        try:
            # Obtener último mensaje para contexto DB
            last_message = messages_history[-1]['content'] if messages_history else ""
            db_context = self._extraer_informacion_db(last_message)
            
            # Iniciar chat
            chat = self.model.start_chat(history=[])
            
            # Agregar contexto de base de datos al primer mensaje
            if db_context and messages_history:
                first_msg = f"{db_context}\n\n{messages_history[0]['content']}"
                messages_history[0]['content'] = first_msg
            
            # Procesar historial
            for msg in messages_history[:-1]:
                if msg['role'] == 'user':
                    chat.send_message(msg['content'])
            
            # Enviar último mensaje
            response = chat.send_message(last_message)
            
            if response.text:
                return response.text.strip()
            else:
                return "Lo siento, no pude generar una respuesta."
        
        except Exception as e:
            logger.error(f"Error con historial de Gemini: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error al procesar tu mensaje."
    
    def analyze_sentiment(self, text):
        """Analizar sentimiento de un texto"""
        if not self.api_key:
            return {'sentiment': 'neutral', 'score': 0.5}
        
        try:
            prompt = f"""Analiza el sentimiento del siguiente texto y responde SOLO con una palabra:
'positivo', 'negativo' o 'neutral'

Texto: {text}

Sentimiento:"""
            
            response = self.model.generate_content(prompt)
            sentiment_text = response.text.strip().lower()
            
            sentiment_map = {
                'positivo': 'positive',
                'negativo': 'negative',
                'neutral': 'neutral'
            }
            
            sentiment = sentiment_map.get(sentiment_text, 'neutral')
            
            return {'sentiment': sentiment, 'score': 0.5}
        
        except Exception as e:
            logger.error(f"Error analizando sentimiento: {e}")
            return {'sentiment': 'neutral', 'score': 0.5}
