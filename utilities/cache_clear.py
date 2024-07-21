from django.conf import settings
from django.core.cache import cache


def clear_cache(cache_key_prefixes: list) -> None:
    """
        Clear cache keys matching any of the given patterns.

        :param cache_key_prefixes: Variable number of cache key prefixes to match.
        :return: None
        """
    # Fetch the Redis client
    redis_client = cache._cache.get_client(1)

    # Iterate over each pattern and delete matching keys
    for prefix in cache_key_prefixes:
        pattern = f"*{settings.CACHES['default']['KEY_PREFIX']}*{prefix}*"
        cache_keys = redis_client.keys(pattern)

        if cache_keys:
            redis_client.delete(*cache_keys)

    return None
