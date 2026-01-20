from django import template
import os

register = template.Library()

@register.filter
def file_type_class(filename):
    """Return CSS class based on file type"""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    if ext == 'pdf':
        return 'pdf'
    elif ext in ['doc', 'docx']:
        return 'doc'
    elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg']:
        return 'image'
    elif ext in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']:
        return 'video'
    elif ext in ['mp3', 'wav', 'ogg', 'aac']:
        return 'audio'
    elif ext in ['zip', 'rar', '7z', 'tar', 'gz']:
        return 'archive'
    else:
        return 'default'

@register.filter
def file_icon(filename):
    """Return Font Awesome icon class based on file type"""
    file_type = file_type_class(filename)
    
    icons = {
        'pdf': 'fa-file-pdf',
        'doc': 'fa-file-word',
        'image': 'fa-file-image',
        'video': 'fa-file-video',
        'audio': 'fa-file-audio',
        'archive': 'fa-file-archive',
        'default': 'fa-file'
    }
    
    return icons.get(file_type, 'fa-file')

@register.filter
def filename_only(filepath):
    """Extract filename from file path"""
    return os.path.basename(filepath)