from django.contrib import admin

from apps.jobs.models import JobType, JobRequirement, Job, AppliedJob


# Register your models here.

@admin.register(JobType)
class JobTypeAdmin(admin.ModelAdmin):
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


class JobRequirementInline(admin.TabularInline):
    model = JobRequirement
    extra = 4


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    readonly_fields = (
        "created",
        "updated",
    )
    list_select_related = (
        'recruiter',
    )
    inlines = [JobRequirementInline]
    fieldsets = [
        (
            'Job information', {
                'fields': [
                    'recruiter',
                    'title',
                    'salary',
                    'type',
                    'location',
                    'active',
                ],
            }
        ),
    ]
    list_display = (
        'title',
        'recruiter_name',
        'location',
        'type',
        'active',
    )
    search_fields = (
        'title',
        'recruiter',
        'location',
        'type',
        'active',
        'is_saved',
    )
    list_filter = (
        'title',
        'recruiter',
        'location',
        'type',
        'active',
    )
    list_per_page = 20

    @admin.display(description="Job recruiter")
    def recruiter_name(self, obj):
        return obj.recruiter.company_profile.name


@admin.register(AppliedJob)
class AppliedJobAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            'Applied Jobs information', {
                'fields': [
                    'job',
                    'user',
                    'cv',
                    'review',
                    'status',
                    'interview_date',
                ],
            }
        ),
        (
            'Important dates', {
                'fields': [
                    'created',
                    'updated',
                ],
            }
        ),
    ]
    readonly_fields = (
        "created",
        "updated",
    )
    list_display = (
        'job',
        'user',
        'status',
    )
    search_fields = (
        'job',
        'user',
        'review',
        'status',
    )
    list_filter = (
        'job',
        'user',
        'status',
    )
    list_per_page = 20
