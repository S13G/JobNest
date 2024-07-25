from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.misc.models import Tip, FAQ
from utilities.caching import clear_cache


@receiver(post_save, sender=Tip)
@receiver(post_delete, sender=Tip)
def clear_tips_cache(sender, **kwargs):
    """
    Clear cache when a tip is created or deleted
    :param sender:
    :param kwargs:
    :return:
    """
    clear_cache(cache_key_prefixes=["retrieve_tips", "retrieve_tip"])


@receiver(post_save, sender=FAQ)
@receiver(post_delete, sender=FAQ)
def clear_faqs_cache(sender, **kwargs):
    """
    Clear cache when a FAQ is created or deleted
    :param sender:
    :param kwargs:
    :return:
    """
    clear_cache(cache_key_prefixes=["retrieve_faqs"])
