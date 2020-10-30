from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView,DetailView,View
from .forms import *
from django.contrib import messages
from django.utils import timezone
from .models import *
import random
import string
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_ref_code():
    return '' .join(random.choices(string.ascii_lowercase + string.digits, k=20))


class home(ListView):
    model = Item
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        et = super(home, self).get_context_data(**kwargs)
        et['new_item_qs'] = Item.objects.filter().order_by('-created_on')[:3]
        return et


class Product(DetailView):
    model = Item
    template_name = 'core/product_details.html'


class OderSummary(LoginRequiredMixin,View):
    def get(self,*args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user,ordered=False)
            return render(self.request, 'core/order_summary.html',{'object': order})
        except ObjectDoesNotExist:
            messages.error(self.request,'You do not have thr active order')
            return redirect('/')


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class Checkout(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})

            return render(self.request, "core/checkout-page.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()

                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")


class PaymentView(View):
    def get(self, *args,**kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order':order,
                'DISPLAY_COUPON_FORM': False
            }
            return render(self.request,'core/payment.html', context)
        else:
            messages.warning(self.request, "You haven't added a billing address")
            return redirect('core:checkout')

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            token = form.cleaned_data.get('stripeToken')
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
                    customer = stripe.Customer.retrieve(
                        userprofile.stripe_customer_id)
                    customer.sources.create(source=token)

                else:
                    customer = stripe.Customer.create(
                        email=self.request.user.email,
                    )
                    customer.sources.create(source=token)
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()

            amount = int(order.get_total() * 100)

            try:

                if use_default or save:
                    # charge the customer because we cannot charge the token more than once
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        customer=userprofile.stripe_customer_id
                    )
                else:
                    # charge once off on the token
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        source=token
                    )

                # create the payment
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # assign the payment to the order

                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.payment = payment
                order.ref_code = create_ref_code()
                order.save()

                messages.success(self.request, "Your order was successful!")
                return redirect("/")

            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get('error', {})
                messages.warning(self.request, f"{err.get('message')}")
                return redirect("/")

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.warning(self.request, "Rate limit error")
                return redirect("/")

            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                print(e)
                messages.warning(self.request, "Invalid parameters")
                return redirect("/")

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.warning(self.request, "Not authenticated")
                return redirect("/")

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.warning(self.request, "Network error")
                return redirect("/")

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.warning(
                    self.request, "Something went wrong. You were not charged. Please try again.")
                return redirect("/")

            except Exception as e:
                # send an email to ourselves
                messages.warning(
                    self.request, "A serious error occurred. We have been notifed.")
                return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")




@login_required
def add_to_cart(request,slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user = request.user,
        ordered = False)

    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the oder or cart
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, 'this item quantity was updated ')
        else:
            messages.info(request,'this item was added to your cart ')
            order.items.add(order_item)
            return redirect('core:product', slug=slug)
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user = request.user, ordered_date = ordered_date)
        order.items.add(order_item)
        messages.info(request, 'this item was added to your cart ')
    return redirect('core:product', slug=slug)


@login_required
def remove_to_cart(request, slug):
    # let get an item from thr item list
    item = get_object_or_404(Item, slug=slug)
    # let check if the user has the oder in that is not ordered yet
    order_qs = Order.objects.filter(user= request.user, ordered=-False)
    # if that the user has the order in the order list
    if order_qs.exists():
        # then grab the that order
        order = order_qs[0]
        # and check the specific oder item regarding to slug item in the request
        if order.items.filter(item__slug = item.slug).exists():
            """
             after that now we need to grab that oder from the oder_item by filtering using
             user in request and ordered not, and the item itself
            """
            order_item = OrderItem.objects.filter(
                item= item,
                user=request.user,
                ordered=False
            )[0]
            """
            then finally we remove that oder from cart completely
            """
            order.items.remove(order_item)
            messages.info(request, 'this item was removed from your cart ')
        else:
            # a message to the user that there is no that kind of query set
            messages.info(request, 'this item was was not in your cart ')
            return redirect('core:product',slug=slug)
    else:
        messages.info(request, "You don't have an active order")
        return redirect('core:product', slug=slug)
    return redirect('core:product', slug=slug)


def get_coupon(request,code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request,'Coupon does not exist ')
        return redirect('core:checkout')


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")


class RequestRefund(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
          }
        return render(self.request,'core/request_refund.html',context)

    def post(self,*args, **kwargs ):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code= form.cleaned_data .get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # edit the order
            try:
                order = Order.objects.get(ref_code= ref_code)
                order.refund_requested = True
                order.save()

                refund = Refund()
                refund.order= order
                refund.reason= message
                refund.email = email
                refund.save()
                messages.info(self.request, 'your request was received')
                return redirect('core:request-refund')
            except ObjectDoesNotExist:
                messages.info(self.request, "This order does'nt exist")
                return redirect('core:request-refund')

            # grab all the refund we have in the list of order




