from django.contrib import admin
from .models import CustomUser, LawyerProfile


admin.site.register(CustomUser)
admin.site.register(LawyerProfile)

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    UploadedDocument, GeneratedDocument, ChatSession, 
    ChatMessage, DocumentTemplate, DocumentDownloadLog
)

@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'user', 'file_type', 'file_size_kb', 'upload_date', 'is_processed', 'processing_status']
    list_filter = ['file_type', 'is_processed', 'upload_date']
    search_fields = ['original_filename', 'user__email', 'user__full_name']
    readonly_fields = ['upload_date', 'file_size', 'session_key']
    
    def file_size_kb(self, obj):
        return f"{obj.file_size / 1024:.1f} KB"
    file_size_kb.short_description = 'File Size'
    
    def processing_status(self, obj):
        if obj.is_processed:
            return format_html('<span style="color: green;">✓ Processed</span>')
        elif obj.processing_error:
            return format_html('<span style="color: red;">✗ Error</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pending</span>')
    processing_status.short_description = 'Status'

@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ['document_type', 'user', 'created_at', 'download_count', 'last_downloaded', 'is_active']
    list_filter = ['document_type', 'created_at', 'is_active']
    search_fields = ['user__email', 'user__full_name', 'document_id']
    readonly_fields = ['document_id', 'created_at', 'downloaded_at', 'download_count', 'formatted_answers']
    
    def last_downloaded(self, obj):
        if obj.downloaded_at:
            return obj.downloaded_at.strftime('%Y-%m-%d %H:%M')
        return 'Never'
    last_downloaded.short_description = 'Last Downloaded'
    
    def formatted_answers(self, obj):
        try:
            answers = json.loads(obj.answers_json)
            formatted = []
            for key, value in answers.items():
                formatted.append(f"<strong>{key.replace('_', ' ').title()}:</strong> {value}")
            return mark_safe('<br>'.join(formatted))
        except:
            return "Invalid JSON"
    formatted_answers.short_description = 'User Answers'

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    readonly_fields = ['message_type', 'content', 'timestamp']
    extra = 0
    can_delete = False

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_identifier', 'mode', 'message_count', 'created_at', 'last_activity', 'has_document']
    list_filter = ['mode', 'created_at', 'last_activity']
    search_fields = ['user__email', 'session_key']
    readonly_fields = ['session_key', 'created_at', 'last_activity']
    inlines = [ChatMessageInline]
    
    def session_identifier(self, obj):
        if obj.user:
            return f"{obj.user.email} ({obj.session_key[:8]}...)"
        return f"Anonymous ({obj.session_key[:8]}...)"
    session_identifier.short_description = 'Session'
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
    
    def has_document(self, obj):
        return "Yes" if obj.uploaded_document else "No"
    has_document.short_description = 'Has Document'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session_info', 'message_type', 'content_preview', 'timestamp']
    list_filter = ['message_type', 'timestamp']
    search_fields = ['content', 'session__user__email']
    readonly_fields = ['session', 'timestamp']
    
    def session_info(self, obj):
        user_info = obj.session.user.email if obj.session.user else f"Anonymous ({obj.session.session_key[:8]}...)"
        return user_info
    session_info.short_description = 'Session'
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'document_type', 'created_by', 'created_at', 'is_active']
    list_filter = ['document_type', 'is_active', 'created_at']
    search_fields = ['name', 'document_type']
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(DocumentDownloadLog)
class DocumentDownloadLogAdmin(admin.ModelAdmin):
    list_display = ['document_info', 'user', 'downloaded_at', 'ip_address']
    list_filter = ['downloaded_at', 'document__document_type']
    search_fields = ['user__email', 'document__document_id', 'ip_address']
    readonly_fields = ['document', 'user', 'downloaded_at', 'ip_address', 'user_agent']
    
    def document_info(self, obj):
        return f"{obj.document.get_document_type_display()} ({obj.document.document_id[:8]}...)"
    document_info.short_description = 'Document'
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing

# # Custom admin views for analytics
# class ChatbotAnalyticsAdmin(admin.ModelAdmin):
#     """Custom admin view for chatbot analytics"""
    
#     def changelist_view(self, request, extra_context=None):
#         # Add analytics data to context
#         from django.db.models import Count, Avg
#         from django.utils import timezone
#         from datetime import timedelta
        
#         # Calculate analytics
#         total_sessions = ChatSession.objects.count()
#         total_messages = ChatMessage.objects.count()
#         total_documents_uploaded = UploadedDocument.objects.count()
#         total_documents_generated = GeneratedDocument.objects.count()
        
#         # Recent activity (last 7 days)
#         week_ago = timezone.now() - timedelta(days=7)
#         recent_sessions = ChatSession.objects.filter(created_at__gte=week_ago).count()
#         recent_uploads = UploadedDocument.objects.filter(upload_date__gte=week_ago).count()
#         recent_generations = GeneratedDocument.objects.filter(created_at__gte=week_ago).count()
        
#         # Document type distribution
#         doc_types = GeneratedDocument.objects.values('document_type').annotate(
#             count=Count('document_type')
#         ).order_by('-count')
        
#         # Mode usage statistics
#         mode_usage = ChatSession.objects.values('mode').annotate(
#             count=Count('mode')
#         ).order_by('-count')
        
#         extra_context = extra_context or {}
#         extra_context.update({
#             'total_sessions': total_sessions,
#             'total_messages': total_messages,
#             'total_documents_uploaded': total_documents_uploaded,
#             'total_documents_generated': total_documents_generated,
#             'recent_sessions': recent_sessions,
#             'recent_uploads': recent_uploads,
#             'recent_generations': recent_generations,
#             'doc_types': doc_types,
#             'mode_usage': mode_usage,
#         })
        
#         return super().changelist_view(request, extra_context=extra_context)

# # Register a dummy model for analytics dashboard
# class ChatbotAnalytics:
#     class Meta:
#         verbose_name = "Chatbot Analytics"
#         verbose_name_plural = "Chatbot Analytics"
        
#     def __str__(self):
#         return "Analytics Dashboard"

# admin.site.register([ChatbotAnalytics], ChatbotAnalyticsAdmin)