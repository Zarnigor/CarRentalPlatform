from django.urls import path, include


urlpatterns = [
    path('', include('apps.accounts.urls')),
    path('geo/', include('apps.geo.urls')),
    path('fleet/', include('apps.fleet.urls')),
    path('bookings/', include('apps.booking.urls')),
    path('rentals/', include('apps.rental.urls')),
    path('damages/', include('apps.damage.urls')),
    path('ops/', include('apps.ops.urls')),
]

# API versiya control kerak
# hamma applardagi url pathlar shu yerda reg qilinadi (bo'ldi)

# ModelViewSet: list, create,
# GenericAPIView