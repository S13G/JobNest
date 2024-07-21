from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.jobs.models import Job, AppliedJob, SavedJob, JobType
from utilities.cache_clear import clear_cache


@receiver(post_save, sender=Job)
@receiver(post_delete, sender=Job)
def clear_job_cache(sender, **kwargs):
    """
        Clear cache when a job is created, deleted or updated
        :param sender:
        :param kwargs:
        :return:
    """
    clear_cache(cache_key_prefixes=["retrieve_jobs", "retrieve_job", "retrieve_vacancies"])


@receiver(post_save, sender=AppliedJob)
@receiver(post_delete, sender=AppliedJob)
def clear_applied_job_cache(sender, **kwargs):
    """
        Clear cache when a tip is created or deleted
        :param sender:
        :param kwargs:
        :return:
    """
    clear_cache(cache_key_prefixes=["retrieve_applied_jobs", "retrieve_applied_job", "retrieve_vacancies"])


@receiver(post_save, sender=SavedJob)
@receiver(post_delete, sender=SavedJob)
def clear_saved_job_cache(sender, **kwargs):
    """
        Clear cache when a tip is created or deleted
        :param sender:
        :param kwargs:
        :return:
    """
    clear_cache(cache_key_prefixes=["retrieve_saved_jobs"])


@receiver(post_save, sender=JobType)
@receiver(post_delete, sender=JobType)
def clear_job_type_cache(sender, **kwargs):
    """
        Clear cache when a job type is created or deleted
        :param sender:
        :param kwargs:
        :return:
    """
    clear_cache(cache_key_prefixes=["retrieve_job_types"])
