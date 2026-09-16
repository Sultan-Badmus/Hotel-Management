from django.db import models, transaction
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    """Custom user model. Add fields here if needed later."""

    pass


class AccomodationBuilding(models.Model):
    building_name = models.CharField(max_length=100)
    city = models.ForeignKey("City", on_delete=models.CASCADE)
    building_location = models.CharField(max_length=100)
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )

    def __str__(self):
        return self.building_name

    def save(self, *args, **kwargs):
        # Ensure that the latitude and longitude are within valid ranges
        if not (-90 <= self.latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90 degrees.")
        if not (-180 <= self.longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180 degrees.")
        super().save(*args, **kwargs)

    def clean(self):
        # Ensure that there is no same building name in the same city
        qs = AccomodationBuilding.objects.filter(
            building_name=self.building_name,
            city=self.city,
        ).exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError(
                f"A building with the name '{self.building_name}' already exists in {self.city.city_name}."
            )


class City(models.Model):
    city_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.city_name

    def clean(self):
        # Ensure that there is no same city name in the same country
        qs = City.objects.filter(
            city_name=self.city_name,
            country=self.country,
        ).exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError(
                f"A city with the name '{self.city_name}' already exists in {self.country}."
            )


class Room(models.Model):
    room_number = models.CharField(max_length=10)
    building = models.ForeignKey(AccomodationBuilding, on_delete=models.CASCADE)
    capacity = models.PositiveIntegerField()
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    space_taken = models.PositiveIntegerField(default=0)
    space_left = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Room {self.room_number}-{self.building.building_name}"

    def save(self, *args, **kwargs):
        self.space_left = self.capacity - self.space_taken
        super().save(*args, **kwargs)


class Reservation(models.Model):
    class StatusChoices(models.TextChoices):
        RESERVED = "RS", "Reserved"
        CHECKED_IN = "CI", "Checked In"
        CHECKED_OUT = "CO", "Checked Out"
        CANCELLED = "CA", "Cancelled"

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    is_employee = models.BooleanField(default=False)
    check_in_date = models.DateTimeField(null=True, blank=True)
    check_out_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=2,
        choices=StatusChoices.choices,
        default=StatusChoices.RESERVED,
    )

    def __str__(self):
        return f"Reservation for {self.guest_name} in Room {self.room.room_number}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        needs_room_lock = is_new or self.status in (
            self.StatusChoices.CHECKED_OUT,
            self.StatusChoices.CANCELLED,
        )

        with transaction.atomic():
            if needs_room_lock:
                # Lock the room row so concurrent reservations against it can't
                # both read the same stale space_taken and both succeed.
                room = Room.objects.select_related("building").select_for_update().get(
                    pk=self.room_id
                )
                self.room = room

            if is_new:
                if room.space_left <= 0:
                    raise ValidationError(
                        f"Room {room.room_number} in {room.building.building_name} is fully booked."
                    )
                room.space_taken += 1
                room.save()

            if self.status == self.StatusChoices.CHECKED_IN:
                self.check_in_date = timezone.now()

            elif self.status == self.StatusChoices.CHECKED_OUT:
                self.check_out_date = timezone.now()
                room.space_taken -= 1
                room.save()

            elif self.status == self.StatusChoices.CANCELLED:
                room.space_taken -= 1
                room.save()

            super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    @property
    def in_stock(self):
        """check if stock is available"""
        return self.stock > 0

    def __str__(self):
        return self.name


class Order(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "pending"
        CONFIRMED = "confirmed"
        CANCELLED = "cancelled"

    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,
        blank=True,
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    guest_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10, choices=StatusChoices.choices, default=StatusChoices.PENDING
    )
    products = models.ManyToManyField(
        Product, through="OrderItem", related_name="orders"
    )

    def save(self, *args, **kwargs):
        if self.user:
            self.guest_name = self.user.username
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_id} by {self.guest_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    @property
    def item_subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.order_id}"
