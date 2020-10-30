
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.shortcuts import reverse
from django_countries.fields import CountryField
from django.utils import timezone

CATEGORY_CHOICES = (
    ('s', 'Shirt'),
    ('SW', 'Sport ware'),
    ('o', 'Out wear'),
    ('LP', 'Laptop',),
    ('CM', 'Camera',),
    ('DV', 'Accessories',),
    ('SM', 'Smart pohone',),
    ('HP', 'Headphone',),
    ('TB', 'Tablet',),

)

LABEL_CHOICES =(
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger'),

)

PAYMENT_CHOICES = (
    ('P', 'PayPal'),
    ('S', 'Stripe'),
)
ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


def userprofile_receiver(sender, instance, created,*args,**kwargs):
    if created:
        userprofile = UserProfile.objects.create(user = instance)


post_save.connect(userprofile_receiver,sender= settings.AUTH_USER_MODEL)


class Item(models.Model):
    image = models.FileField(upload_to='product_images',blank=True, null=True)
    title = models.CharField(max_length=200)
    price = models.FloatField()
    discount_price = models.FloatField(blank= True, null=True)
    category = models.CharField( choices=CATEGORY_CHOICES, max_length=2, null=True)
    label = models.CharField( choices=LABEL_CHOICES, max_length=2, null=True)
    description = models.TextField( blank= True, null=True)
    slug = models.SlugField(max_length=200, null=True)
    updated_on = models.DateTimeField(auto_now=True, null =True)
    created_on = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name_plural = 'Items'
        ordering=['-created_on']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:product', kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse('core:add-to-cart', kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse('core:remove-to-cart', kwargs={
            'slug': self.slug
        })


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE,null = True)
    ordered = models.BooleanField(default=False, null=True)
    quantity = models.IntegerField( default=1, null = True,)

    class Meta:
        verbose_name_plural = 'Ordered items'

    def __str__(self):
        return f'{self.quantity } of {self.item.title}'

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_discount_total_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_discount_total_item_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_discount_total_item_price()
        return self.get_total_item_price()


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,null = True)
    ref_code = models.CharField(max_length=20, blank=True, null=True)
    items = models.ManyToManyField(OrderItem)
    ordered_date = models.DateTimeField(null = True)
    ordered = models.BooleanField(default=False, null = True)
    billing_address = models.ForeignKey('Address', related_name='billing_address',
                                        on_delete=models.SET_NULL, blank=True, null=True)
    shipping_address = models.ForeignKey('Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)


    '''
    1. Item added to cart
    2. Adding a billing address
    (Failed checkout)
    3. Payment
    (Pre-processing, processing, packaging etc.)
    4. Being delivered
    5. Received
    6. Refunds
    '''

    class Meta:
        verbose_name_plural = 'Order'

    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length =100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False, null=True)
    zip = models.CharField(max_length=200)
    address_type = models.CharField( max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "addresses"

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.FloatField()
    timestamp = models.DateTimeField( auto_now_add=True)

    class Meta:
        verbose_name_plural = "Payments"

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code


class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"


















