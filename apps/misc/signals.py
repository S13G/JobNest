from django.conf import settings
from django.core.cache import caches, cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.misc.models import Tip, FAQ


@receiver(post_save, sender=Tip)
@receiver(post_delete, sender=Tip)
def clear_cache(sender, **kwargs):
    """
    Clear cache when a tip is created or deleted
    :param sender:
    :param kwargs:
    :return:
    """
    caches["retrieve_all_tips"].clear()


@receiver(post_save, sender=FAQ)
@receiver(post_delete, sender=FAQ)
def clear_cache(sender, **kwargs):
    """
    Clear cache when a FAQ is created or deleted
    :param sender:
    :param kwargs:
    :return:
    """
    print("clearing cache")
    cache_keys = cache._cache.get_client(1).keys(
        f"*{settings.CACHES['default']['KEY_PREFIX']}*"
    )
    print(cache_keys)
    # key = caches['default'].make_key('retrieve_faqs')
    # print(key)
    cache.delete_many(cache_keys)
