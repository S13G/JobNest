from django.contrib import admin

from apps.misc.models import Tip


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
