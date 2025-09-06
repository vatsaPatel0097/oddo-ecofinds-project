from django.db import models
from django.utils.text import slugify
from django.utils import timezone
class UserAccount(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # store hashed password ideally
    created_at = models.DateTimeField(auto_now_add=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return self.username



CATEGORIES = [
    ("electronics", "Electronics"),
    ("books", "Books"),
    ("clothing", "Clothing"),
    ("furniture", "Furniture"),
    ("home", "Home"),
    ("toys", "Toys"),
    ("other", "Other"),
]

CONDITIONS = [
    ("new", "New"),
    ("like_new", "Like New"),
    ("used_good", "Used - Good"),
    ("used_fair", "Used - Fair"),
    ("for_parts", "For parts / not working"),
]

class Product(models.Model):
    owner = models.ForeignKey("market.UserAccount", on_delete=models.CASCADE, related_name="products")
    title = models.CharField(max_length=250, db_index=True)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORIES, default="other")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    condition = models.CharField(max_length=30, choices=CONDITIONS, default="used_good")
    year_of_manufacture = models.PositiveIntegerField(null=True, blank=True)
    brand = models.CharField(max_length=150, blank=True)
    model = models.CharField(max_length=150, blank=True)

    # dimensions in cm (optional)
    length_cm = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    width_cm  = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)

    weight_kg = models.DecimalField(max_digits=7, decimal_places=3, null=True, blank=True)
    material = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=80, blank=True)

    original_packaging = models.BooleanField(default=False)
    manual_included = models.BooleanField(default=False)
    working_condition_description = models.TextField(blank=True)

    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:220]
            slug = base
            num = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base}-{num}"
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def primary_image_url(self):
        first = self.images.first()
        if first and first.image:
            return first.image.url
        return "/static/img/placeholder.png"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/%Y/%m/%d/")
    alt = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Image for {self.product.title}"

class CartItem(models.Model):
    user = models.ForeignKey("market.UserAccount", on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey("market.Product", on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.title} x {self.qty} ({self.user.username})"

    @property
    def subtotal(self):
        try:
            return self.product.price * self.qty
        except Exception:
            return 0


class Order(models.Model):
    user = models.ForeignKey("market.UserAccount", on_delete=models.CASCADE, related_name="orders")
    ordered = models.BooleanField(default=False)  # False -> active (shouldn't happen), True -> completed
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Order #{self.id} for {self.user.username}"

    @property
    def total_amount(self):
        items = self.items.all()
        total = sum((it.price_snapshot or 0) * it.qty for it in items)
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_id = models.PositiveIntegerField()
    title = models.CharField(max_length=255, blank=True)
    qty = models.PositiveIntegerField(default=1)
    price_snapshot = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.title} x {self.qty} (order {self.order_id})"