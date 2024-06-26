from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group as DjangoGroup

from apps.core.models import *


class Group(DjangoGroup):
    class Meta:
        verbose_name = "group"
        verbose_name_plural = "groups"
        proxy = True


class GroupAdmin(BaseGroupAdmin):
    pass


class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "company",
        "email_verified",
        "is_staff",

    )
    list_display_links = (
        "email",
    )
    list_editable = (
        "email_verified",
    )
    list_filter = (
        "email",
        "company",
        "is_staff",
    )
    list_per_page = 20
    fieldsets = (
        (
            "Login Credentials",
            {
                "fields": (
                    "email",
                    "password",
                    "avatar",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "google_provider",
                    "is_staff",
                    "email_verified",
                    "company",
                    "groups",
                    "user_permissions"
                )
            },
        ),
        (
            "Important Dates",
            {
                "fields": (
                    "created",
                    "updated",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            "Personal Information",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                ),
            },
        ),
    )
    readonly_fields = ("created", "updated",)
    search_fields = ("email",)
    ordering = ("email",)


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            'Profile Information', {
                'fields': [
                    "user",
                    "full_name",
                    'date_of_birth',
                    'address',
                    'occupation',
                ],
            }
        ),
    ]
    list_display = (
        'full_name',
        "occupation",
        'date_of_birth',
        'created',
        'updated',
    )
    list_display_links = (
        "full_name",
        "occupation",
        "date_of_birth",
    )
    list_per_page = 20
    search_fields = (
        "full_name",
        "occupation",
    )


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            'Profile Information', {
                'fields': [
                    "user",
                    'name',
                    'country',
                    'address',
                ],
            }
        ),
    ]
    list_display_links = (
        "name",
        'country',
    )
    list_display = (
        "name",
        'country',
        'created',
        'updated',
    )
    list_filter = (
        'country',
    )
    list_per_page = 20
    search_fields = (
        "name",
        "country",
        'address',
    )
    ordering = (
        'name',
        'country',
    )


admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.unregister(DjangoGroup)
