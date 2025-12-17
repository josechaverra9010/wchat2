"""
Servicio para consultar la base de datos de Ébano Company
"""
import logging
from django.db import connection
from django.db.models import Q, Count, Sum
from ..models import Cliente, Producto, Pedido, DetallePedido

logger = logging.getLogger('chatbot')


class DatabaseService:
    """Servicio para operaciones de base de datos"""
    
    @staticmethod
    def buscar_cliente(telefono=None, email=None, nombre=None):
        """
        Buscar cliente por teléfono, email o nombre
        
        Returns:
            Cliente object o None
        """
        try:
            if telefono:
                return Cliente.objects.filter(telefono__icontains=telefono).first()
            if email:
                return Cliente.objects.filter(email__iexact=email).first()
            if nombre:
                return Cliente.objects.filter(nombre__icontains=nombre).first()
        except Exception as e:
            logger.error(f"Error buscando cliente: {e}")
        return None
    
    @staticmethod
    def listar_productos(categoria=None, disponibles=True, limit=10):
        """
        Listar productos con filtros opcionales
        
        Args:
            categoria: Filtrar por categoría
            disponibles: Solo productos con stock > 0
            limit: Número máximo de resultados
        
        Returns:
            QuerySet de productos
        """
        try:
            query = Producto.objects.filter(activo=True)
            
            if categoria:
                query = query.filter(categoria__icontains=categoria)
            
            if disponibles:
                query = query.filter(stock__gt=0)
            
            return query.order_by('-fecha_creacion')[:limit]
        except Exception as e:
            logger.error(f"Error listando productos: {e}")
            return []
    
    @staticmethod
    def buscar_producto(nombre):
        """
        Buscar productos por nombre
        
        Returns:
            QuerySet de productos
        """
        try:
            return Producto.objects.filter(
                Q(nombre__icontains=nombre) | Q(descripcion__icontains=nombre),
                activo=True
            )
        except Exception as e:
            logger.error(f"Error buscando producto: {e}")
            return []
    
    @staticmethod
    def obtener_producto_por_id(producto_id):
        """
        Obtener producto específico por ID
        
        Returns:
            Producto object o None
        """
        try:
            return Producto.objects.get(id=producto_id, activo=True)
        except Producto.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo producto: {e}")
            return None
    
    @staticmethod
    def verificar_stock(producto_id, cantidad=1):
        """
        Verificar si hay stock suficiente
        
        Returns:
            bool
        """
        try:
            producto = Producto.objects.get(id=producto_id)
            return producto.stock >= cantidad
        except Exception as e:
            logger.error(f"Error verificando stock: {e}")
            return False
    
    @staticmethod
    def obtener_pedidos_cliente(cliente_id, limit=5):
        """
        Obtener pedidos de un cliente
        
        Returns:
            QuerySet de pedidos
        """
        try:
            return Pedido.objects.filter(
                cliente_id=cliente_id
            ).order_by('-fecha_pedido')[:limit]
        except Exception as e:
            logger.error(f"Error obteniendo pedidos: {e}")
            return []
    
    @staticmethod
    def obtener_detalle_pedido(pedido_id):
        """
        Obtener detalles completos de un pedido
        
        Returns:
            Dict con información del pedido
        """
        try:
            pedido = Pedido.objects.select_related('cliente').get(id=pedido_id)
            detalles = DetallePedido.objects.filter(pedido=pedido).select_related('producto')
            
            return {
                'pedido': pedido,
                'detalles': detalles,
                'total_items': detalles.count()
            }
        except Pedido.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo detalle pedido: {e}")
            return None
    
    @staticmethod
    def obtener_categorias():
        """
        Obtener lista de categorías únicas
        
        Returns:
            List de categorías
        """
        try:
            categorias = Producto.objects.filter(
                activo=True
            ).values_list('categoria', flat=True).distinct()
            return [c for c in categorias if c]
        except Exception as e:
            logger.error(f"Error obteniendo categorías: {e}")
            return []
    
    @staticmethod
    def buscar_productos_por_precio(precio_min=None, precio_max=None, limit=10):
        """
        Buscar productos por rango de precio
        
        Returns:
            QuerySet de productos
        """
        try:
            query = Producto.objects.filter(activo=True, stock__gt=0)
            
            if precio_min is not None:
                query = query.filter(precio__gte=precio_min)
            
            if precio_max is not None:
                query = query.filter(precio__lte=precio_max)
            
            return query.order_by('precio')[:limit]
        except Exception as e:
            logger.error(f"Error buscando por precio: {e}")
            return []
    
    @staticmethod
    def productos_mas_vendidos(limit=5):
        """
        Obtener productos más vendidos
        
        Returns:
            QuerySet de productos con cantidad vendida
        """
        try:
            productos = DetallePedido.objects.values(
                'producto__id', 'producto__nombre', 'producto__precio'
            ).annotate(
                total_vendido=Sum('cantidad')
            ).order_by('-total_vendido')[:limit]
            
            return list(productos)
        except Exception as e:
            logger.error(f"Error obteniendo productos más vendidos: {e}")
            return []
    
    @staticmethod
    def estadisticas_cliente(cliente_id):
        """
        Obtener estadísticas de un cliente
        
        Returns:
            Dict con estadísticas
        """
        try:
            pedidos = Pedido.objects.filter(cliente_id=cliente_id)
            
            return {
                'total_pedidos': pedidos.count(),
                'total_gastado': pedidos.aggregate(Sum('total'))['total__sum'] or 0,
                'ultimo_pedido': pedidos.order_by('-fecha_pedido').first()
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return None
    
    @staticmethod
    def ejecutar_consulta_raw(query, params=None):
        """
        Ejecutar consulta SQL personalizada (usar con precaución)
        
        Args:
            query: String SQL
            params: Parámetros de la consulta
        
        Returns:
            Lista de resultados
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params or [])
                columns = [col[0] for col in cursor.description]
                return [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Error en consulta raw: {e}")
            return []
