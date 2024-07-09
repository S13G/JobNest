from django.db import models


class BaseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('job', 'user')

    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class JobManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('type', 'recruiter')

    def get_active_jobs(self):
        return self.get_queryset().filter(active=True).order_by('-created')

    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class AppliedJobManager(BaseManager):
    pass  # Inherits from BaseManager with default behavior


class SavedJobManager(BaseManager):
    pass  # Inherits from BaseManager with default behavior
