from djoser.serializers import UserCreatePasswordRetypeSerializer, UserSerializer as BaseUserSerializer
from rest_framework import serializers
from .models import (
    AccomodationBuilding,
    City,
    Room,
    Reservation,
    Order,
    Product,
    OrderItem,
)


class UserCreateSerializer(UserCreatePasswordRetypeSerializer):
    """Registration serializer: adds first_name/last_name to Djoser's default fields.

    Activation gating (is_active=False until confirmed) and locking new users
    out of is_staff/is_superuser are both handled by Djoser itself, driven by
    SEND_ACTIVATION_EMAIL and User.objects.create_user() respectively.
    """

    class Meta(UserCreatePasswordRetypeSerializer.Meta):
        fields = UserCreatePasswordRetypeSerializer.Meta.fields + (
            "first_name",
            "last_name",
        )


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ("first_name", "last_name")


class AccomodationBuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccomodationBuilding
        fields = "__all__"

    def validate(self, attrs):
        instance = self.instance or AccomodationBuilding()
        for field, value in attrs.items():
            setattr(instance, field, value)
        instance.full_clean()
        return attrs


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = "__all__"

    def validate(self, attrs):
        instance = self.instance or City()
        for field, value in attrs.items():
            setattr(instance, field, value)
        instance.full_clean()
        return attrs


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"

    def validate(self, attrs):
        instance = self.instance or Room()
        for field, value in attrs.items():
            setattr(instance, field, value)
        instance.full_clean()
        return attrs


class ReservationSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Reservation
        fields = "__all__"

    def validate(self, attrs):
        status = attrs.get("status")
        check_in_date = attrs.get("check_in_date")
        check_out_date = attrs.get("check_out_date")

        if status == Reservation.StatusChoices.CHECKED_IN and not check_in_date:
            raise serializers.ValidationError(
                {"check_in_date": "This field is required when status is Checked In."}
            )

        if status == Reservation.StatusChoices.CHECKED_OUT and not check_out_date:
            raise serializers.ValidationError(
                {"check_out_date": "This field is required when status is Checked Out."}
            )

        instance = self.instance or Reservation()
        for field, value in attrs.items():
            setattr(instance, field, value)
        instance.full_clean()
        return attrs


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            # 'id',
            "name",
            "description",
            "price",
            "stock",
        )

    def validate_price(self, value):
        """Check that price is greater than zero"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


class OrderItemSerializers(serializers.ModelSerializer):
    # product = ProductSerializer() - to return all fields in the model
    product_name = serializers.CharField(source="product.name")
    product_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="product.price"
    )

    class Meta:
        model = OrderItem
        fields = ("product_name", "product_price", "quantity", "item_subtotal")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializers(many=True, read_only=True)
    total_price = serializers.SerializerMethodField(method_name="total")

    def total(self, obj):  # we can also use get_total_price here
        # we are using items here because items has been set as a related field in the Model
        order_items = obj.items.all()
        return sum(order_item.item_subtotal for order_item in order_items)

    class Meta:
        model = Order
        fields = (
            "order_id",
            "reservation",
            "created_at",
            "status",
            "items",
            "total_price",
        )


class ProductInfoSerializers(serializers.Serializer):
    products = ProductSerializer(many=True)
    count = serializers.IntegerField()
    max_price = serializers.FloatField()
