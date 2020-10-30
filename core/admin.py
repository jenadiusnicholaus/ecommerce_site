from django.contrib import admin
from .models import *


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Update orders to refund granted'


class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'label', 'category', 'slug')
    list_filter = ("title",)
    search_fields = ['title', 'category']
    prepopulated_fields = {'slug': ('title',)}


# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['user',
#                     'ordered',
#                     'being_delivered',
#                     'received',
#                     'refund_requested',
#                     'refund_granted',
#                     'shipping_address',
#                     'billing_address',
#                     'payment',
#                     'ref_code',
#                     'coupon']
#     list_display_links = [
#         'user',
#         'shipping_address',
#         'billing_address',
#         'payment',
#         'coupon'
#     ]
#     list_filter = ['ordered',
#                    'being_delivered',
#                    'received',
#                    'refund_requested',
#                    'refund_granted']
#     search_fields = [
#         'user__username',
#         'ref_code'
#     ]
#     actions = [make_refund_accepted]


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'ordered', ]


class paymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'stripe_charge_id', 'amount', 'timestamp']


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'address_type',
        'default'
    ]
    list_filter = ['default', 'address_type', 'country']
    search_fields = ['user', 'street_address', 'apartment_address', 'zip']


admin.site.register(Item, ItemAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Order, )
admin.site.register(Address, AddressAdmin)
admin.site.register(Payment, paymentAdmin)
admin.site.register(Coupon)
admin.site.register(UserProfile)

