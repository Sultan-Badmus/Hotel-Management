from django.db.models import Max
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    AccomodationBuilding,
    City,
    Room,
    Reservation,
    Order,
    OrderItem,
    Product,
)
from .permissions import IsAdminOrReadOnly
from .serializers import (
    AccomodationBuildingSerializer,
    CitySerializer,
    RoomSerializer,
    ReservationSerializer,
    OrderSerializer,
    OrderItemSerializers,
    ProductSerializer,
    ProductInfoSerializers,
)
from .filters import CityFilter


# ---- City: ViewSet ----

CITY_CACHE_TTL = 60 * 15  # matches the "*city_list*" pattern cleared in signals.py
CITY_CACHE_KEY_PREFIX = "city_list"


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.order_by("id")
    serializer_class = CitySerializer
    filterset_class = CityFilter
    search_fields = ["city_name", "country"]
    ordering_fields = ["city_name", "country", "id"]
    ordering = ["id"]
    permission_classes = [IsAdminOrReadOnly]

    @method_decorator(cache_page(CITY_CACHE_TTL, key_prefix=CITY_CACHE_KEY_PREFIX))
    @method_decorator(vary_on_headers("Authorization"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(CITY_CACHE_TTL, key_prefix=CITY_CACHE_KEY_PREFIX))
    @method_decorator(vary_on_headers("Authorization"))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


# ---- AccomodationBuilding: ViewSet ----

BUILDING_CACHE_TTL = 60 * 15  # matches "*building_list*" cleared in signals.py
BUILDING_CACHE_KEY_PREFIX = "building_list"


class AccomodationBuildingViewSet(viewsets.ModelViewSet):
    queryset = AccomodationBuilding.objects.select_related("city").order_by("id")
    serializer_class = AccomodationBuildingSerializer
    filterset_fields = ["city", "building_name"]
    search_fields = ["building_name", "building_location"]
    ordering_fields = ["building_name", "id"]
    ordering = ["id"]
    permission_classes = [IsAdminOrReadOnly]

    @method_decorator(
        cache_page(BUILDING_CACHE_TTL, key_prefix=BUILDING_CACHE_KEY_PREFIX)
    )
    @method_decorator(vary_on_headers("Authorization"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(
        cache_page(BUILDING_CACHE_TTL, key_prefix=BUILDING_CACHE_KEY_PREFIX)
    )
    @method_decorator(vary_on_headers("Authorization"))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


# ---- Room, Reservation, Product: ViewSets (full CRUD) ----


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related("building").order_by("id")
    serializer_class = RoomSerializer
    filterset_fields = ["building", "capacity"]
    search_fields = ["room_number"]
    ordering_fields = ["room_number", "capacity", "price_per_night", "space_left", "id"]
    ordering = ["id"]
    permission_classes = [IsAdminOrReadOnly]


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.select_related("room").all()
    filter_backends = [DjangoFilterBackend]
    serializer_class = ReservationSerializer
    filterset_fields = ["status", "room", "is_employee"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.order_by("id")
    serializer_class = ProductSerializer
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price", "stock", "id"]
    ordering = ["id"]
    permission_classes = [IsAdminOrReadOnly]


class ProductInfoAPIView(APIView):
    """Aggregate info: full product list, count and max price."""

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductInfoSerializers(
            {
                "products": products,
                "count": products.count(),
                "max_price": products.aggregate(max_price=Max("price"))["max_price"]
                or 0,
            }
        )
        return Response(serializer.data)


# ---- Order & OrderItem: read-only ViewSets ----
# OrderSerializer/OrderItemSerializers are display-oriented (nested, computed
# fields) rather than write-oriented, so these are exposed read-only. Orders
# and their items are created/mutated through the Reservation flow.


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.select_related("reservation").prefetch_related(
        "items__product"
    )
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "reservation"]


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OrderItem.objects.select_related("order", "product")
    serializer_class = OrderItemSerializers
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["order", "product"]
