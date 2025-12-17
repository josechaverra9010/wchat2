"""
Servicio para interactuar con Google Gemini AI - INTEGRADO CON BASE DE DATOS
"""
import logging
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
            "max_output_tokens": 1024,
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
            model_name="gemini-2.5-flash",
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
        
        try:
            # Buscar productos
            if any(word in message_lower for word in ['producto', 'productos', 'catálogo', 'precio', 'stock', 'disponible']):
                productos = self.db_service.listar_productos(limit=5)
                if productos:
                    context += "\n\n📦 **PRODUCTOS DISPONIBLES:**\n"
                    for p in productos:
                        context += f"• {p.nombre} - ${p.precio:,.0f} (Stock: {p.stock}) - {p.categoria}\n"
            
            # Buscar por nombre de producto específico
            palabras = message_lower.split()
            for palabra in palabras:
                if len(palabra) > 3:  # Evitar palabras muy cortas
                    productos_busqueda = self.db_service.buscar_producto(palabra)
                    if productos_busqueda and not context.__contains__("PRODUCTOS DISPONIBLES"):
                        context += "\n\n🔍 **PRODUCTOS ENCONTRADOS:**\n"
                        for p in productos_busqueda[:3]:
                            context += f"• {p.nombre} - ${p.precio:,.0f} (Stock: {p.stock})\n"
                            if p.descripcion:
                                context += f"  {p.descripcion[:100]}...\n"
                        break
            
            # Buscar categorías
            if 'categoría' in message_lower or 'categorias' in message_lower:
                categorias = self.db_service.obtener_categorias()
                if categorias:
                    context += "\n\n🏷️ **CATEGORÍAS DISPONIBLES:**\n"
                    context += ", ".join(categorias)
            
            # Productos más vendidos
            if 'popular' in message_lower or 'vendido' in message_lower or 'recomendación' in message_lower:
                populares = self.db_service.productos_mas_vendidos(limit=3)
                if populares:
                    context += "\n\n⭐ **PRODUCTOS MÁS POPULARES:**\n"
                    for p in populares:
                        context += f"• {p['producto__nombre']} - ${p['producto__precio']:,.0f} ({p['total_vendido']} vendidos)\n"
            
            # Búsqueda por rango de precio
            if 'precio' in message_lower and any(char.isdigit() for char in message):
                # Extraer números del mensaje
                import re
                numeros = re.findall(r'\d+', message)
                if numeros:
                    precio_ref = int(numeros[0])
                    productos_precio = self.db_service.buscar_productos_por_precio(
                        precio_min=precio_ref * 0.8,
                        precio_max=precio_ref * 1.2,
                        limit=3
                    )
                    if productos_precio:
                        context += f"\n\n💰 **PRODUCTOS CERCA DE ${precio_ref:,.0f}:**\n"
                        for p in productos_precio:
                            context += f"• {p.nombre} - ${p.precio:,.0f}\n"
        
        except Exception as e:
            logger.error(f"Error extrayendo información DB: {e}")
        
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
            # Extraer información de la base de datos
            db_context = self._extraer_informacion_db(message)
            
            # Información del cliente si se proporciona teléfono
            cliente_info = ""
            if phone_number:
                cliente = self.db_service.buscar_cliente(telefono=phone_number)
                if cliente:
                    stats = self.db_service.estadisticas_cliente(cliente.id)
                    cliente_info = f"\n\n👤 **INFORMACIÓN DEL CLIENTE:**\n"
                    cliente_info += f"Nombre: {cliente.nombre}\n"
                    cliente_info += f"Email: {cliente.email}\n"
                    if stats:
                        cliente_info += f"Total pedidos: {stats['total_pedidos']}\n"
                        cliente_info += f"Total gastado: ${stats['total_gastado']:,.0f}\n"
            
            # Construir prompt con contexto
            system_prompt = """Eres un asistente virtual de Ébano Company, especializado en ayudar a los clientes con información sobre productos, pedidos y servicios.

Tu nombre es Parchabot y estás aquí para brindar la mejor atención al cliente.

Características:
- Eres educado, profesional y conciso
- Respondes en español con lenguaje nativo de Quibdó, Chocó
- Usas la información de la base de datos para dar respuestas precisas
- Si no encuentras información específica, lo admites honestamente
- Evitas respuestas muy largas (máximo 2-3 párrafos)
- Usas emojis para ser más amigable
- Cuando muestres precios, usa formato colombiano: $50.000

INFORMACIÓN DE LA EMPRESA:
Ébano Company es una empresa dedicada a ofrecer productos de calidad a nuestros clientes.

{cliente_info}

{db_context}

Contexto de la conversación anterior:
{context}

Usuario dice: {message}

INSTRUCCIONES:
- Si te preguntan por productos, usa la información de la base de datos
- Si mencionan precios o stock, verifica los datos actuales
- Si preguntan por pedidos, ofrece consultar su historial
- Sé específico con los datos (nombres, precios, stock)
- Si la información no está disponible, ofrece alternativas

Responde de forma natural y útil:"""
            
            prompt = system_prompt.format(
                cliente_info=cliente_info,
                db_context=db_context,
                context=context if context else "No hay conversación previa",
                message=message
            )
            
            # Generar respuesta
            response = self.model.generate_content(prompt)
            
            if response.text:
                logger.info(f"Respuesta de Gemini generada con contexto DB")
                return response.text.strip()
            else:
                logger.warning("Gemini no generó respuesta de texto")
                return "Lo siento, no pude generar una respuesta en este momento."
        
        except Exception as e:
            logger.error(f"Error generando respuesta con Gemini: {str(e)}", exc_info=True)
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
