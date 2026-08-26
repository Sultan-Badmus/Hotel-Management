from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from hotel_management.models import AccomodationBuilding, City
from django.core.cache import cache


@receiver([post_save, post_delete], sender=City)
def invalidate_city_cache(sender, instance, **kwargs):
    """Invalidate city list/detail caches when a city is created, updated or deleted"""

    cache.delete_pattern("*city_list*")


@receiver([post_save, post_delete], sender=AccomodationBuilding)
def invalidate_building_cache(sender, instance, **kwargs):
    """Invalidate building list/detail caches when a building is created, updated or deleted"""

    cache.delete_pattern("*building_list*")
