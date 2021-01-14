from django.contrib import admin
from .models import Product, Category, Basket, BasketProduct

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Basket)
admin.site.register(BasketProduct)

