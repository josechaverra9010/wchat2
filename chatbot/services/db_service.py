"""
Servicio para consultar la base de datos de Ébano Company - VERSIÓN CORREGIDA
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
            logger.info(f"🔍 Buscando cliente - Teléfono: {telefono}, Email: {email}, Nombre: {nombre}")
            
            if telefono:
                # Limpiar el número de teléfono (quitar espacios, guiones, etc.)
                telefono_limpio = ''.join(filter(str.isdigit, telefono))
                cliente = Cliente.objects.filter(telefono__icontains=telefono_limpio).first()
                if cliente:
                    logger.info(f"✅ Cliente encontrado por teléfono: {cliente.nombre}")
                    return cliente
                    
            if email:
                cliente = Cliente.objects.filter(email__iexact=email).first()
                if cliente:
                    logger.info(f"✅ Cliente encontrado por email: {cliente.nombre}")
                    return cliente
                    
            if nombre:
                cliente = Cliente.objects.filter(nombre__icontains=nombre).first()
                if cliente:
                    logger.info(f"✅ Cliente encontrado por nombre: {cliente.nombre}")
                    return cliente
            
            logger.info("ℹ️ No se encontró cliente")
        except Exception as e:
            logger.error(f"❌ Error buscando cliente: {e}", exc_info=True)
        
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
            logger.info(f"📦 Listando productos - Categoría: {categoria}, Disponibles: {disponibles}, Limit: {limit}")
            
            query = Producto.objects.filter(activo=True)
            
            if categoria:
                query = query.filter(categoria__icontains=categoria)
            
            if disponibles:
                query = query.filter(stock__gt=0)
            
            productos = list(query.order_by('-fecha_creacion')[:limit])
            logger.info(f"✅ Productos encontrados: {len(productos)}")
            
            return productos
        except Exception as e:
            logger.error(f"❌ Error listando productos: {e}", exc_info=True)
            return []
    
    @staticmethod
    def buscar_producto(nombre):
        """
        Buscar productos por nombre
        
        Returns:
            QuerySet de productos
        """
        try:
            logger.info(f"🔍 Buscando producto por nombre: {nombre}")
            
            productos = Producto.objects.filter(
                Q(nombre__icontains=nombre) | Q(descripcion__icontains=nombre),
                activo=True
            )
            
            logger.info(f"✅ Productos encontrados: {productos.count()}")
            return productos
        except Exception as e:
            logger.error(f"❌ Error buscando producto: {e}", exc_info=True)
            return Producto.objects.none()
    
    @staticmethod
    def obtener_producto_por_id(producto_id):
        """
        Obtener producto específico por ID
        
        Returns:
            Producto object o None
        """
        try:
            logger.info(f"🔍 Obteniendo producto ID: {producto_id}")
            producto = Producto.objects.get(id=producto_id, activo=True)
            logger.info(f"✅ Producto encontrado: {producto.nombre}")
            return producto
        except Producto.DoesNotExist:
            logger.info(f"ℹ️ Producto ID {producto_id} no existe")
            return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo producto: {e}", exc_info=True)
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
            hay_stock = producto.stock >= cantidad
            logger.info(f"📊 Stock verificado - Producto {producto_id}: {producto.stock} (necesita {cantidad}) = {hay_stock}")
            return hay_stock
        except Exception as e:
            logger.error(f"❌ Error verificando stock: {e}", exc_info=True)
            return False
    
    @staticmethod
    def obtener_pedidos_cliente(cliente_id, limit=5):
        """
        Obtener pedidos de un cliente
        
        Returns:
            QuerySet de pedidos
        """
        try:
            logger.info(f"📋 Obteniendo pedidos del cliente ID: {cliente_id}")
            pedidos = list(Pedido.objects.filter(
                cliente_id=cliente_id
            ).order_by('-fecha_pedido')[:limit])
            logger.info(f"✅ Pedidos encontrados: {len(pedidos)}")
            return pedidos
        except Exception as e:
            logger.error(f"❌ Error obteniendo pedidos: {e}", exc_info=True)
            return []
    
    @staticmethod
    def obtener_detalle_pedido(pedido_id):
        """
        Obtener detalles completos de un pedido
        
        Returns:
            Dict con información del pedido
        """
        try:
            logger.info(f"📋 Obteniendo detalle del pedido ID: {pedido_id}")
            pedido = Pedido.objects.select_related('cliente').get(id=pedido_id)
            detalles = DetallePedido.objects.filter(pedido=pedido).select_related('producto')
            
            logger.info(f"✅ Detalle encontrado - {detalles.count()} items")
            
            return {
                'pedido': pedido,
                'detalles': list(detalles),
                'total_items': detalles.count()
            }
        except Pedido.DoesNotExist:
            logger.info(f"ℹ️ Pedido ID {pedido_id} no existe")
            return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo detalle pedido: {e}", exc_info=True)
            return None
    
    @staticmethod
    def obtener_categorias():
        """
        Obtener lista de categorías únicas
        
        Returns:
            List de categorías
        """
        try:
            logger.info("🏷️ Obteniendo categorías")
            categorias = Producto.objects.filter(
                activo=True
            ).values_list('categoria', flat=True).distinct()
            categorias_lista = [c for c in categorias if c]
            logger.info(f"✅ Categorías encontradas: {categorias_lista}")
            return categorias_lista
        except Exception as e:
            logger.error(f"❌ Error obteniendo categorías: {e}", exc_info=True)
            return []
    
    @staticmethod
    def buscar_productos_por_precio(precio_min=None, precio_max=None, limit=10):
        """
        Buscar productos por rango de precio
        
        Returns:
            QuerySet de productos
        """
        try:
            logger.info(f"💰 Buscando productos por precio - Min: {precio_min}, Max: {precio_max}")
            
            query = Producto.objects.filter(activo=True, stock__gt=0)
            
            if precio_min is not None:
                query = query.filter(precio__gte=precio_min)
            
            if precio_max is not None:
                query = query.filter(precio__lte=precio_max)
            
            productos = list(query.order_by('precio')[:limit])
            logger.info(f"✅ Productos en rango de precio: {len(productos)}")
            
            return productos
        except Exception as e:
            logger.error(f"❌ Error buscando por precio: {e}", exc_info=True)
            return []
    
    @staticmethod
    def productos_mas_vendidos(limit=5):
        """
        Obtener productos más vendidos
        
        Returns:
            Lista de productos con cantidad vendida
        """
        try:
            logger.info(f"⭐ Obteniendo productos más vendidos (limit: {limit})")
            
            productos = DetallePedido.objects.values(
                'producto__id', 'producto__nombre', 'producto__precio'
            ).annotate(
                total_vendido=Sum('cantidad')
            ).order_by('-total_vendido')[:limit]
            
            productos_lista = list(productos)
            logger.info(f"✅ Productos populares encontrados: {len(productos_lista)}")
            
            return productos_lista
        except Exception as e:
            logger.error(f"❌ Error obteniendo productos más vendidos: {e}", exc_info=True)
            return []
    
    @staticmethod
    def estadisticas_cliente(cliente_id):
        """
        Obtener estadísticas de un cliente
        
        Returns:
            Dict con estadísticas
        """
        try:
            logger.info(f"📊 Obteniendo estadísticas del cliente ID: {cliente_id}")
            
            pedidos = Pedido.objects.filter(cliente_id=cliente_id)
            total_gastado = pedidos.aggregate(Sum('total'))['total__sum'] or 0
            
            stats = {
                'total_pedidos': pedidos.count(),
                'total_gastado': total_gastado,
                'ultimo_pedido': pedidos.order_by('-fecha_pedido').first()
            }
            
            logger.info(f"✅ Estadísticas: {stats['total_pedidos']} pedidos, ${stats['total_gastado']}")
            
            return stats
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}", exc_info=True)
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
            logger.info(f"🔧 Ejecutando consulta SQL personalizada")
            with connection.cursor() as cursor:
                cursor.execute(query, params or [])
                columns = [col[0] for col in cursor.description]
                resultados = [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]
                logger.info(f"✅ Consulta ejecutada: {len(resultados)} resultados")
                return resultados
        except Exception as e:
            logger.error(f"❌ Error en consulta raw: {e}", exc_info=True)
            return []
