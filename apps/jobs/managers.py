from django.db import models


class JobManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('type', 'recruiter')

    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None

    def get_active_jobs(self):
        return self.get_queryset().filter(active=True).order_by('-created')


class AppliedJobManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('job', 'user')

    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class SavedJobManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('job', 'user')

    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None
