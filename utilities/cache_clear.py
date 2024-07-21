from django.conf import settings
from django.core.cache import cache


def clear_cache(cache_key_prefix: str) -> None:
    # Create the pattern to match keys containing 'retrieve_faqs'
    pattern = f"*{settings.CACHES['default']['KEY_PREFIX']}*{cache_key_prefix}*"

    # Fetch keys matching the pattern
    cache_keys = cache._cache.get_client(1).keys(pattern)

    # Delete the matched keys
    if cache_keys:
        cache._cache.get_client(1).delete(*cache_keys)

    return None
