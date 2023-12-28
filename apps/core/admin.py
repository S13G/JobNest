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
        "first_name",
        "last_name",
        "phone_number",
        "coins_available",
        "email",
        "email_changed",
        "email_verified",
        "is_staff",
        "is_active",

    )
    list_display_links = (
        "first_name",
        "last_name",
        "phone_number",
        "email",
    )
    list_filter = (
        "first_name",
        "last_name",
        "email",
        "is_staff",
        "is_active",
    )
    list_per_page = 20
    fieldsets = (
        (
            "Login Credentials",
            {
                "fields": (
                    "email",
                    "password"
                )
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                    "avatar",
                    "coins_available",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "email_verified",
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
                    "first_name",
                    "last_name",
                    "phone_number",
                    "email",
                    "coins_available",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    readonly_fields = ("created", "updated",)
    search_fields = ("email", "first_name", "last_name", "phone_number",)
    ordering = ("email", "first_name", "last_name",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            'Profile Information', {
                'fields': [
                    "user",
                ],
            }
        ),
    ]
    list_display = (
        'full_name',
        "phone_number",
        'created',
        'updated',
    )
    list_per_page = 20
    search_fields = (
        "full_name",
        "phone_number",
    )

    @admin.display(description='Phone number')
    def phone_number(self, obj):
        return obj.user.phone_number


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            'Profile Information', {
                'fields': [
                    "user",
                    'date_of_birth',
                    'occupation',
                    'address',
                ],
            }
        ),
    ]
    list_display = (
        "full_name",
        "phone_number",
        "phone_number",
        'date_of_birth',
        'occupation',
        'created',
        'updated',
    )
    list_filter = (
        'date_of_birth',
        'occupation',
    )
    list_per_page = 20
    search_fields = (
        "full_name",
        "phone_number",
        'occupation',
        'address',
        'date_of_birth',
    )
    ordering = (
        'date_of_birth',
        'occupation',
    )

    @admin.display(description='Phone number')
    def phone_number(self, obj):
        return obj.user.phone_number


admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.unregister(DjangoGroup)
