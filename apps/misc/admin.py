from django.contrib import admin

from apps.misc.models import Tip, FAQType, FAQ


# Register your models here.

@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Tips information", {
                "fields": (
                    "title",
                    "description",
                    "author",
                    "author_image",
                    "position",
                )
            }
        ),
    )
    list_display = (
        'title',
        'author',
        'position',
    )
    search_fields = (
        'title',
        'description',
        'author',
        'position',
    )
    list_filter = (
        'title',
        'description',
        'author',
        'position',
    )
    list_per_page = 20


@admin.register(FAQType)
class FAQTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
    search_fields = (
        'name',
    )
    list_filter = (
        'name',
    )
    list_per_page = 20


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            'FAQ information', {
                'fields': [
                    'question',
                    'type',
                    'answer',
                ],
            }
        ),
    ]
    list_display = (
        'question',
        'type',
    )
    search_fields = (
        'question',
        'type',
    )
    list_filter = (
        'type',
    )
    list_per_page = 20
