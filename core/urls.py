from  django.urls import path
from .views import \
    home,\
    Checkout,\
    Product,\
    add_to_cart,\
    remove_to_cart,\
    OderSummary,\
    PaymentView,\
    AddCouponView, RequestRefund


app_name = 'core'
urlpatterns = [
    path('', home.as_view(), name='item-list' ),
    path('checkout/',Checkout.as_view(), name='checkout' ),
    path('payment/<payment_option>/',PaymentView.as_view(), name='payment' ),
    path('order-summary/',OderSummary.as_view(), name='order-summary'),
    path('product/<slug>/',  Product.as_view(), name='product'),
    path('add-to-cart/<slug>/',add_to_cart, name='add-to-cart'),
    path('add-coupon/',AddCouponView, name='add-coupon'),
    path('remove-to-cart/<slug>/',remove_to_cart, name='remove-to-cart'),
    path('request-refund/',RequestRefund.as_view(), name='request-refund'),
]