from django.contrib import admin
from .models import (
    AccomodationBuilding,
    City,
    Room,
    Reservation,
    User,
    Product,
    Order,
    OrderItem,
)
from django.contrib.auth.admin import UserAdmin

# Register your models here.
admin.site.site_header = "Hotel Management Admin"
admin.site.site_title = "Hotel Management Admin Portal"
admin.site.register(AccomodationBuilding)
admin.site.register(City)
admin.site.register(Room)
admin.site.register(Reservation)
admin.site.register(User, UserAdmin)
admin.site.register(Product)
admin.site.register(Order)
