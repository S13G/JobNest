from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.models import EmployeeProfile, CompanyProfile
from utilities.caching import clear_user_cache


@receiver(post_save, sender=EmployeeProfile)
def clear_employee_profile_cache(sender, instance, **kwargs):
    """
    Clear cache when an employee profile is created or updated
    :param instance:
    :param sender:
    :param kwargs:
    :return:
    """

    current_user = kwargs.get("current_user", instance.user.id)

    clear_user_cache(user_id=current_user, pattern_string="employee_profile")


@receiver(post_save, sender=CompanyProfile)
def clear_employee_profile_cache(sender, instance, **kwargs):
    """
    Clear cache when an company profile is created or updated
    :param instance:
    :param sender:
    :param kwargs:
    :return:
    """

    current_user = kwargs.get("current_user", instance.user.id)

    clear_user_cache(user_id=current_user, pattern_string="company_profile")
