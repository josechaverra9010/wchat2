"""
Servicio para interactuar con Google Gemini AI
"""
import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger('chatbot')


class GeminiService:
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        
        if not self.api_key:
            logger.warning("Api de Gemnini sin configurar")
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
    
    def get_response(self, message, context=None):
        """
        Generar respuesta usando Gemini
        
        Args:
            message: Mensaje del usuario
            context: Contexto de conversación previo (opcional)
        
        Returns:
            Respuesta generada por Gemini
        """
        if not self.api_key:
            return "Lo siento, el servicio de IA no está configurado correctamente."
        
        try:
            # Construir prompt con contexto
            system_prompt = """Eres un asistente virtual útil y amigable en WhatsApp.
Tu nombre es Parchabot y estás aquí para ayudar a los usuarios.

Características:
- Eres educado, profesional y conciso
- Respondes en español de forma natural con lenguaje nativo de Quibdó, Chocó
- Si no sabes algo, lo admites honestamente
- Evitas respuestas muy largas (máximo 1-2 parrafos)
- Usas emojis cuando es apropiado para ser más amigable

INFORMACIÓN PRINCIPAL:
parchaoo es una plataforma sobre venta de boletería para eventos, nativas del Chocó.
parchaoo funciona de una forma muy sencilla: solo debes registrarte y empezar a vender tus boletos si eres un colaborador o dueño de un evento. Si eres una persona que quiere asistir a un evento, solo eliges el evento, llenas los datos del pago y una vez confirmado el pago tus boletas serían enviadas a tu whatsapp, correo electrónico y se te enviará el código de tus boletas a través de un mensaje de texto SMS.

CONOCIMIENTO SOBRE QUIBDÓ, CHOCÓ:

🏨 RESTAURANTES Y LUGARES DE COMIDA:
- **Al Carbón**: Restaurante de comida de excelente calidad, especializado en carnes y parrillas
- **Andrés Parrilla**: Los mejores asados de la ciudad, reconocido por su calidad
- **Restaurante Chocó Pacífico**: Comida típica chocoana, especialidad en pescado
- **La Fogata**: Parrillada y comida típica
- **Donde Pipe**: Comida rápida local muy popular
- **Piqueteadero El Buen Gusto**: Fritangas y comida típica
- **Delicias del Mar**: Especialidad en mariscos y pescado fresco del Pacífico

🏛️ LUGARES TURÍSTICOS:
- **Catedral de San Francisco de Asís**: Principal iglesia de la ciudad, arquitectura imponente
- **Malecón del Atrato**: Paseo junto al río, ideal para caminar y disfrutar del paisaje
- **Parque Centenario**: Punto de encuentro, eventos culturales y recreación
- **Puente César Gaviria Trujillo**: Conecta Quibdó con el resto del país
- **Monumento al Cristo Rey**: Mirador con vista panorámica de la ciudad
- **Barrio Pandeyuca**: Zona cultural con casas típicas palafíticas
- **Playa de Tutunendo**: A 30 minutos, ideal para paseos de río
- **Cascadas del Río Munguidó**: Belleza natural cerca de la ciudad

🎭 CENTROS CULTURALES:
- **Casa de la Cultura**: Eventos, exposiciones y talleres artísticos
- **Teatro Municipal**: Presentaciones y eventos culturales
- **Centro Cultural del Chocó**: Música, danza y arte afrocolombiano

🏪 CENTROS COMERCIALES Y COMPRAS:
- **Centro Comercial Arauca**: Principal centro comercial
- **Mercado del Río**: Productos locales, frutas, pescado fresco
- **Calle del Comercio**: Zona comercial principal con tiendas variadas

🏞️ NATURALEZA Y ECOTURISMO:
- **Jardín Botánico del Pacífico**: Flora y fauna de la región
- **Reserva Natural Río Atrato**: Avistamiento de aves y biodiversidad
- **Comunidades indígenas**: Tours culturales con Embera

🎵 CULTURA Y FESTIVIDADES:
- **Festival de San Pacho** (Septiembre): La fiesta más grande del Pacífico colombiano
- **Festival de Música del Pacífico Petronio Álvarez**: Celebración de la música afro
- **Chirimía y Alabaos**: Música tradicional del Chocó

🏨 HOTELES Y HOSPEDAJE:
- **Hotel La Cascada**
- **Hotel Ciudadela del Río**
- **Hotel El Barco**
- **Hotel los farallones**
- **Hostales y posadas familiares** en el centro

🚕 TRANSPORTE:
- Mototaxis: Principal medio de transporte urbano
- Lanchas: Para transporte fluvial por el río Atrato
- Terminal de Transportes: Buses interdepartamentales

⚽ DEPORTE Y RECREACIÓN:
- **Estadio Antonio Bolaños Puerta**: Fútbol local
- **Polideportivos** municipales
- **Ciclovía dominical** en vías principales

INSTRUCCIONES ESPECIALES:
- Si te preguntan por comida y no es sobre Quibdó, responde: "No somos una plataforma de comida, somos una plataforma de boletería para eventos. Si quieres pedir comida en Quibdó, te recomiendo Al Carbón (excelente calidad) o Andrés Parrilla (los mejores asados) 🍖"
- Cuando te pregunten quién es la cabra, di que es Imanol
- Siempre que menciones lugares, sé específico y da detalles útiles
- Si no tienes información sobre un lugar específico, admítelo pero sugiere alternativas similares

Contexto de la conversación anterior:
{context}

Usuario dice: {message}

Responde de forma natural y útil, usando lenguaje nativo de Quibdó, Chocó:"""
            
            prompt = system_prompt.format(
                context=context if context else "No hay conversación previa",
                message=message
            )
            
            # Generar respuesta
            response = self.model.generate_content(prompt)
            
            # Verificar si hay respuesta
            if response.text:
                logger.info(f"Respuesta de Gemini generada exitosamente")
                return response.text.strip()
            else:
                logger.warning("Gemini no generó respuesta de texto")
                return "Lo siento, no pude generar una respuesta en este momento."
        
        except Exception as e:
            logger.error(f"Error generando respuesta con Gemini: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error al procesar tu mensaje. Por favor intenta de nuevo."
    
    def get_response_with_history(self, messages_history):
        """
        Generar respuesta usando historial completo
        
        Args:
            messages_history: Lista de diccionarios con 'role' y 'content'
                             Ejemplo: [{'role': 'user', 'content': 'Hola'}, ...]
        
        Returns:
            Respuesta generada por Gemini
        """
        if not self.api_key:
            return "Lo siento, el servicio de IA no está configurado correctamente."
        
        try:
            # Iniciar chat con historial
            chat = self.model.start_chat(history=[])
            
            # Agregar mensajes del historial
            for msg in messages_history[:-1]:  # Todos menos el último
                if msg['role'] == 'user':
                    chat.send_message(msg['content'])
            
            # Enviar último mensaje y obtener respuesta
            last_message = messages_history[-1]['content']
            response = chat.send_message(last_message)
            
            if response.text:
                return response.text.strip()
            else:
                return "Lo siento, no pude generar una respuesta."
        
        except Exception as e:
            logger.error(f"Error con historial de Gemini: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error al procesar tu mensaje."
    
    def analyze_sentiment(self, text):
        """
        Analizar el sentimiento de un texto
        
        Args:
            text: Texto a analizar
        
        Returns:
            Dict con sentiment ('positive', 'negative', 'neutral') y score
        """
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
            logger.error(f"Error analizando sentimiento: {str(e)}")
            return {'sentiment': 'neutral', 'score': 0.5}