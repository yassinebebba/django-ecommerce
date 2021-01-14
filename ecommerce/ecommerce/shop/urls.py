from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from .views import (
    home_view, CustomLoginView, register_view, ProductDetailView, basket_view, CheckoutView
)

app_name = 'shop'

urlpatterns = [
    path('', home_view, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register_view, name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('product/<int:pk>', ProductDetailView.as_view(), name='product_detail'),
    path('basket/', basket_view, name='basket'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),

]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
