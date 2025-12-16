"""
Configuración del panel de administración de Django
"""
from django.contrib import admin
from .models import Conversation, Message, BotContext


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'name', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['phone_number', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('messages')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'direction', 'message_type', 'content_preview', 'timestamp']
    list_filter = ['direction', 'message_type', 'status', 'timestamp']
    search_fields = ['conversation__phone_number', 'content']
    readonly_fields = ['message_id', 'timestamp', 'created_at']
    date_hierarchy = 'timestamp'
    
    def content_preview(self, obj):
        """Mostrar vista previa del contenido"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenido'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('conversation')


@admin.register(BotContext)
class BotContextAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'last_intent', 'updated_at']
    search_fields = ['conversation__phone_number', 'last_intent']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('conversation')
