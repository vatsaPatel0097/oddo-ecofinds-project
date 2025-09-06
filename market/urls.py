from django.urls import path
from . import views

app_name = 'market'

urlpatterns = [
    path('',views.product_list, name='product_list'),
    path('product/list/', views.product_list, name='product_list'),            # homepage / feed
    path('about/', views.about, name='about'),
        
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("product/add/", views.product_create, name="product_create"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("product/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("product/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/", views.update_cart, name="update_cart"),
    path("cart/remove/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.previous_purchases, name="previous_purchases"),
    path("dashboard/", views.user_dashboard, name="user_dashboard"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),

]
