from django.contrib import admin
from .models import Chart, Note, ICD10Code, CodeAssignment

# Register your models here.


@admin.register(Chart)
class ChartAdmin(admin.ModelAdmin):
    """Admin interface for Chart model."""
    list_display = ('case_id', 'visit_info', 'id')
    search_fields = ('case_id',)
    ordering = ('-id',)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """Admin interface for Note model."""
    list_display = ('note_id', 'title', 'chart', 'id')
    search_fields = ('note_id', 'title', 'content')
    list_filter = ('title',)
    ordering = ('-id',)


@admin.register(ICD10Code)
class ICD10CodeAdmin(admin.ModelAdmin):
    """Admin interface for ICD10Code model."""
    list_display = ('icd_code', 'short_description', 'id')
    search_fields = ('icd_code', 'short_description', 'long_description')
    ordering = ('icd_code',)


@admin.register(CodeAssignment)
class CodeAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for CodeAssignment model."""
    list_display = ('note', 'icd_code', 'similarity_score', 'created_at')
    search_fields = ('note__note_id', 'icd_code__icd_code')
    list_filter = ('created_at',)
    ordering = ('-similarity_score',)
