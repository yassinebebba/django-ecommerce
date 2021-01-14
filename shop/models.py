from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete


class Category(models.Model):
    class Meta:
        verbose_name_plural = 'categories'

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    thumbnail = models.ImageField(upload_to='thumbnails')
    description = models.TextField()
    price = models.FloatField(default=0.00)

    def __str__(self):
        return self.title

    def pre_delete_handler(self):
        product_in_basket_qs = BasketProduct.objects.filter(product=self)
        for product in product_in_basket_qs:
            product.delete()



class Basket(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


def post_save_basket_create(sender, instance, created, *args, **kwargs):
    if created:
        Basket.objects.get_or_create(user=instance)

    user_basket, created = Basket.objects.get_or_create(user=instance)

    user_basket.save()


post_save.connect(post_save_basket_create, sender=User)


def product_pre_delete_handler(sender, instance, **kwargs):
    if isinstance(instance, Product):
        instance.pre_delete_handler()


pre_delete.connect(product_pre_delete_handler, sender=Product)


class BasketProduct(models.Model):
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, null=True, blank=True)
    quantity = models.IntegerField()

    def __str__(self):
        return f'{self.basket.user.username} --> {self.product.title}'
