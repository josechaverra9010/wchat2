"""
Modelos para almacenar conversaciones, mensajes y datos de la empresa
"""
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    """Conversación con un usuario de WhatsApp"""
    phone_number = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Conversación'
        verbose_name_plural = 'Conversaciones'
    
    def __str__(self):
        return f"{self.name or self.phone_number}"
    
    def get_recent_messages(self, limit=10):
        """Obtener mensajes recientes para contexto"""
        return self.messages.order_by('-created_at')[:limit]


class Message(models.Model):
    """Mensaje individual en una conversación"""
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('image', 'Imagen'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Documento'),
        ('location', 'Ubicación'),
        ('sticker', 'Sticker'),
        ('unknown', 'Desconocido'),
    ]
    
    DIRECTION_CHOICES = [
        ('incoming', 'Entrante'),
        ('outgoing', 'Saliente'),
    ]
    
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    message_id = models.CharField(max_length=100, unique=True, db_index=True)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    content = models.TextField()
    media_url = models.URLField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Metadata adicional
    status = models.CharField(max_length=20, blank=True, default='sent')
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
    
    def __str__(self):
        return f"{self.conversation.phone_number} - {self.message_type} - {self.direction}"


class BotContext(models.Model):
    """Contexto persistente para cada conversación"""
    conversation = models.OneToOneField(
        Conversation,
        on_delete=models.CASCADE,
        related_name='context'
    )
    context_data = models.JSONField(default=dict)
    last_intent = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Contexto de Bot'
        verbose_name_plural = 'Contextos de Bot'
    
    def __str__(self):
        return f"Context for {self.conversation.phone_number}"


# --- MODELOS DE LA BASE DE DATOS EBANO COMPANY ---

class Cliente(models.Model):
    """Cliente de Ébano Company"""
    nombre = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'clientes'
        managed = False
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Producto disponible en el catálogo"""
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    categoria = models.CharField(max_length=100, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'productos'
        managed = False
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
    
    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    """Pedido realizado por un cliente"""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=50)
    direccion_envio = models.TextField(blank=True)
    notas = models.TextField(blank=True)
    
    class Meta:
        db_table = 'pedidos'
        managed = False
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
    
    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.nombre}"


class DetallePedido(models.Model):
    """Detalle de productos en un pedido"""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'detalle_pedidos'
        managed = False
        verbose_name = 'Detalle de Pedido'
        verbose_name_plural = 'Detalles de Pedidos'
    
    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"
