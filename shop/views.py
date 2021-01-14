from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.messages.views import messages
from django.views import View

from .models import Product
from datetime import datetime
from django.contrib.auth.views import LoginView
from django.views.generic import DetailView
from django.views.generic.edit import FormMixin
from django.contrib.messages.views import SuccessMessageMixin

from .forms import UserCreationForm, AddToBasketForm

from django.conf import settings

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


def home_view(request):
    product_qs = Product.objects.all()
    context = {
        'products': product_qs
    }

    return render(request, 'shop/home.html', context=context)


class CustomLoginView(SuccessMessageMixin, LoginView):
    template_name = 'shop/login.html'

    def get_success_message(self, cleaned_data):
        date = datetime.now().hour
        if 5 <= date <= 11:
            return f'Good morning, {self.request.user.username}.'
        elif 12 <= date <= 17:
            return f'Good afternoon, {self.request.user.username}.'
        else:
            return f'Good evening, {self.request.user.username}.'

    def get_success_url(self):
        return reverse('shop:home')


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your Account has been created successfully.')
            return redirect('shop:login')
    form = UserCreationForm()
    context = {
        'form': form
    }
    return render(request, 'shop/register.html', context=context)


class ProductDetailView(FormMixin, DetailView):
    template_name = 'shop/product_detail.html'
    model = Product

    form_class = AddToBasketForm

    def get_success_url(self):
        return reverse('shop:basket')

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        product = self.object
        quantity = form.cleaned_data['quantity']
        if quantity <= 0:
            messages.warning(self.request, 'Please make sure you put a positive number in quantity.')
            return self.form_invalid(form)
        user = self.request.user
        product_in_basket = user.basket.basketproduct_set.filter(product=product).first()
        if product_in_basket is not None:
            product_in_basket.quantity += quantity
            product_in_basket.save()
        else:
            user.basket.basketproduct_set.create(basket=user.basket, product=product, quantity=quantity)
        return super().form_valid(form)


def basket_view(request):
    if request.method == 'POST':
        item = request.POST.get('item', '')
        if item:
            obj = get_object_or_404(request.user.basket.basketproduct_set, pk=item)
            obj.delete()
            return redirect('shop:basket')

    user_basket_qs = request.user.basket.basketproduct_set.all()
    total = 0
    for product in user_basket_qs:
        total += product.product.price * product.quantity

    context = {
        'user_basket_products': user_basket_qs,
        'total': total
    }
    return render(request, 'shop/basket.html', context=context)



class CheckoutView(View):
    def get(self, *args, **kwargs):
        context = {
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLISHABLE_KEY
        }
        return render(self.request, 'shop/checkout.html', context=context)

    def post(self, *args, **kwargs):
        token = self.request.POST.get('stripeToken')
        user_basket_qs = self.request.user.basket.basketproduct_set.all()
        total = 0
        for product in user_basket_qs:
            total += product.product.price * product.quantity

        try:
            stripe.Charge.create(
                amount= int(total * 100),  # pence
                currency='gbp',
                source=token,
                description=f'Charge for {self.request.user.username}'
            )
            for product in user_basket_qs:
                product.delete()

            messages.success(self.request, 'Thank you for your purchase.')

            return redirect('shop:home')
        except stripe.error.CardError as e:
            messages.warning(self.request, f"{e.error.message}")

        except stripe.error.RateLimitError as e:
            messages.warning(self.request, "Rate limit error")

        except stripe.error.InvalidRequestError as e:
            messages.warning(self.request, "Invalid parameters")

        except stripe.error.AuthenticationError as e:
            messages.warning(self.request, "Not authenticated")

        except stripe.error.APIConnectionError as e:
            messages.warning(self.request, "Network error")

        except stripe.error.StripeError as e:
            messages.warning(self.request, "Something went wrong, you were not charged please try again")

        except Exception as e:
            messages.warning(self.request, "Serious error occurred, we have been notified")
