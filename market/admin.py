from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(UserAccount)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "category", "price", "quantity", "is_available", "created_at")
    list_filter = ("category", "is_available", "condition")
    search_fields = ("title", "description", "brand", "model")
    inlines = [ProductImageInline]
    prepopulated_fields = {"slug": ("title",)}

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "image", "created_at")

admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)