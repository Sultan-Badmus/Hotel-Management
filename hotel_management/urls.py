from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("cities", views.CityViewSet, basename="city")
router.register("buildings", views.AccomodationBuildingViewSet, basename="building")
router.register("rooms", views.RoomViewSet, basename="room")
router.register("reservations", views.ReservationViewSet, basename="reservation")
router.register("products", views.ProductViewSet, basename="product")
router.register("orders", views.OrderViewSet, basename="order")
router.register("order-items", views.OrderItemViewSet, basename="orderitem")


urlpatterns = [
    path("products/info/", views.ProductInfoAPIView.as_view()),
    path("auth/", include("djoser.urls")),
    path("", include(router.urls)),
]
