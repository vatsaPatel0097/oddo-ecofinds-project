from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib import messages
from .models import *
from django.db.models import Q
import hashlib
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib import messages
from .utils import login_required_custom
from django.db import transaction , IntegrityError

def home(request):
    return render(request, "market/home.html")

def about(request):
    return render(request, "market/about.html")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("market:register")

        if UserAccount.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("market:register")

        if UserAccount.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("market:register")

        hashed_pw = hash_password(password1)
        user = UserAccount.objects.create(username=username, email=email, password=hashed_pw)

        # store user id in session
        request.session["user_id"] = user.id
        request.session["username"] = user.username

        return redirect("market:login")

    return render(request, "market/register.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        hashed_pw = hash_password(password)

        try:
            user = UserAccount.objects.get(email=email, password=hashed_pw)
            # set session
            request.session["user_id"] = user.id
            request.session["username"] = user.username
            return redirect("market:user_dashboard")
        except UserAccount.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return redirect("market:login")

    return render(request, "market/login.html")


def logout_view(request):
    request.session.flush()  # clear session
    return redirect("market:login")

@login_required_custom
def profile_view(request):
    user_id = request.session.get("user_id")
    username = request.session.get("username")
    return render(request, "market/profile.html", {"username": username})


def product_list(request):
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("category", "").strip()

    qs = Product.objects.filter(is_available=True)
    if cat:
        qs = qs.filter(category=cat)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "q": q,
        "category": cat,
        "categories": CATEGORIES,
    }
    return render(request, "market/product_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    context = {"product": product}
    return render(request, "market/product_detail.html", context)


@login_required_custom
def product_create(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        category = request.POST.get("category", "other")
        price = request.POST.get("price", "0")
        quantity = request.POST.get("quantity", "1")
        condition = request.POST.get("condition", "used_good")
        year_of_manufacture = request.POST.get("year_of_manufacture") or None
        brand = request.POST.get("brand", "").strip()
        model = request.POST.get("model", "").strip()

        length_cm = request.POST.get("length_cm") or None
        width_cm = request.POST.get("width_cm") or None
        height_cm = request.POST.get("height_cm") or None
        weight_kg = request.POST.get("weight_kg") or None
        material = request.POST.get("material", "").strip()
        color = request.POST.get("color", "").strip()
        original_packaging = True if request.POST.get("original_packaging") == "on" else False
        manual_included = True if request.POST.get("manual_included") == "on" else False
        working_condition_description = request.POST.get("working_condition_description", "").strip()

        # validation
        errors = []
        if not title or len(title) < 3:
            errors.append("Enter a valid title (min 3 characters).")
        try:
            price_val = float(price)
            if price_val < 0:
                errors.append("Price must be non-negative.")
        except:
            errors.append("Enter a valid price.")
        try:
            qty_val = int(quantity)
            if qty_val < 0:
                errors.append("Quantity must be >= 0.")
        except:
            errors.append("Enter a valid quantity.")

        if errors:
            return render(request, "market/product_create.html", {"errors": errors, "categories": CATEGORIES, "conditions": CONDITIONS})

        owner = UserAccount.objects.get(id=request.session["user_id"])

        prod = Product.objects.create(
            owner=owner,
            title=title,
            description=description,
            category=category,
            price=price_val,
            quantity=qty_val,
            condition=condition,
            year_of_manufacture=year_of_manufacture,
            brand=brand,
            model=model,
            length_cm=length_cm or None,
            width_cm=width_cm or None,
            height_cm=height_cm or None,
            weight_kg=weight_kg or None,
            material=material,
            color=color,
            original_packaging=original_packaging,
            manual_included=manual_included,
            working_condition_description=working_condition_description,
        )

        # handle multiple images
        images = request.FILES.getlist("images")
        for img in images:
            ProductImage.objects.create(product=prod, image=img)

        return redirect("market:product_detail", slug=prod.slug)

    return render(request, "market/product_create.html", {"categories": CATEGORIES, "conditions": CONDITIONS})


@login_required_custom
def product_edit(request, pk):
    prod = get_object_or_404(Product, pk=pk)
    if prod.owner.id != request.session.get("user_id"):
        messages.error(request, "You are not allowed to edit this product.")
        return redirect("market:product_detail", slug=prod.slug)

    if request.method == "POST":
        # similar handling as create, update fields
        prod.title = request.POST.get("title", prod.title)
        prod.description = request.POST.get("description", prod.description)
        prod.category = request.POST.get("category", prod.category)
        try:
            prod.price = float(request.POST.get("price", prod.price))
        except:
            pass
        try:
            prod.quantity = int(request.POST.get("quantity", prod.quantity))
        except:
            pass
        prod.condition = request.POST.get("condition", prod.condition)
        prod.brand = request.POST.get("brand", prod.brand)
        prod.model = request.POST.get("model", prod.model)
        prod.length_cm = request.POST.get("length_cm") or None
        prod.width_cm = request.POST.get("width_cm") or None
        prod.height_cm = request.POST.get("height_cm") or None
        prod.weight_kg = request.POST.get("weight_kg") or None
        prod.material = request.POST.get("material", prod.material)
        prod.color = request.POST.get("color", prod.color)
        prod.original_packaging = True if request.POST.get("original_packaging") == "on" else False
        prod.manual_included = True if request.POST.get("manual_included") == "on" else False
        prod.working_condition_description = request.POST.get("working_condition_description", prod.working_condition_description)
        prod.save()

        # new images:
        images = request.FILES.getlist("images")
        for img in images:
            ProductImage.objects.create(product=prod, image=img)

        messages.success(request, "Product updated.")
        return redirect("market:product_detail", slug=prod.slug)

    return render(request, "market/product_edit.html", {"product": prod, "categories": CATEGORIES, "conditions": CONDITIONS})


@login_required_custom
def product_delete(request, pk):
    prod = get_object_or_404(Product, pk=pk)
    if prod.owner.id != request.session.get("user_id"):
        messages.error(request, "Not allowed.")
        return redirect("market:product_detail", slug=prod.slug)

    if request.method == "POST":
        prod.delete()
        messages.success(request, "Product deleted.")
        return redirect("market:product_list")

    return render(request, "market/product_delete_confirm.html", {"product": prod})



def _get_logged_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    try:
        return UserAccount.objects.get(id=user_id)
    except UserAccount.DoesNotExist:
        return None

@login_required_custom
def add_to_cart(request):
    """
    Accepts POST from product_detail form:
      - product_id
      - qty (optional)
    If item exists -> increment qty; else create.
    Redirects back to product_detail or cart.
    """
    if request.method != "POST":
        return redirect("market:product_list")

    user = _get_logged_user(request)
    if not user:
        messages.error(request, "Please log in to add items to cart.")
        return redirect("market:login")

    product_id = request.POST.get("product_id")
    qty = request.POST.get("qty") or 1
    try:
        qty = max(1, int(qty))
    except Exception:
        qty = 1

    product = get_object_or_404(Product, id=product_id)

    # enforce available quantity on first add
    if product.quantity is not None and qty > product.quantity:
        messages.error(request, "Requested quantity not available.")
        return redirect("market:product_detail", slug=product.slug)

    try:
        with transaction.atomic():
            cart_item, created = CartItem.objects.get_or_create(
                user=user, product=product, defaults={"qty": qty}
            )
            if not created:
                new_qty = cart_item.qty + qty
                if product.quantity is not None and new_qty > product.quantity:
                    messages.warning(
                        request,
                        f"Only {product.quantity} available. Cart updated to maximum allowed."
                    )
                    cart_item.qty = product.quantity
                else:
                    cart_item.qty = new_qty
                cart_item.save()
    except IntegrityError:
        messages.error(request, "Could not add to cart. Try again.")
        return redirect("market:product_detail", slug=product.slug)

    messages.success(request, "Added to cart.")
    return redirect("market:product_detail", slug=product.slug)



@login_required_custom
def cart_view(request):
    user = _get_logged_user(request)
    if not user:
        return redirect("market:login")

    items = CartItem.objects.filter(user=user).select_related("product")
    cart_items = []
    total = 0
    for it in items:
        subtotal = it.subtotal
        cart_items.append({
            "id": it.id,
            "product": it.product,
            "qty": it.qty,
            "subtotal": subtotal,
        })
        total += subtotal

    context = {
        "cart_items": cart_items,
        "cart_total": total,
    }
    return render(request, "market/cart.html", context)


@login_required_custom
def update_cart(request):
    if request.method != "POST":
        return redirect("market:cart")

    user = _get_logged_user(request)
    if not user:
        return redirect("market:login")

    item_id = request.POST.get("item_id")
    qty = request.POST.get("qty")
    try:
        qty = int(qty)
        if qty < 1:
            raise ValueError
    except Exception:
        messages.error(request, "Invalid quantity.")
        return redirect("market:cart")

    cart_item = get_object_or_404(CartItem, id=item_id, user=user)
    # check product stock
    if cart_item.product.quantity is not None and qty > cart_item.product.quantity:
        messages.error(request, "Not enough stock for requested quantity.")
        return redirect("market:cart")

    cart_item.qty = qty
    cart_item.save()
    messages.success(request, "Cart updated.")
    return redirect("market:cart")


@login_required_custom
def remove_from_cart(request):
    if request.method != "POST":
        return redirect("market:cart")

    user = _get_logged_user(request)
    if not user:
        return redirect("market:login")

    item_id = request.POST.get("item_id")
    cart_item = get_object_or_404(CartItem, id=item_id, user=user)
    cart_item.delete()
    messages.success(request, "Removed from cart.")
    return redirect("market:cart")


@login_required_custom
def checkout(request):
    user = _get_logged_user(request)
    if not user:
        return redirect("market:login")

    cart_items = CartItem.objects.filter(user=user).select_related("product")
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("market:cart")

    try:
        with transaction.atomic():
            # Lock products used by cart to avoid race conditions
            product_ids = [ci.product.id for ci in cart_items]
            products = Product.objects.select_for_update().filter(id__in=product_ids)
            prod_map = {p.id: p for p in products}

            # Validate stock for each cart item
            for ci in cart_items:
                p = prod_map.get(ci.product.id)
                if p is None:
                    messages.error(request, f"Product not found: {ci.product.title}")
                    raise ValueError("product missing")
                if not p.is_available or (p.quantity is not None and ci.qty > p.quantity):
                    messages.error(request, f"Not enough stock for {p.title}. Available: {p.quantity or 'unlimited'}")
                    raise ValueError("insufficient stock")

            # Create order (mark ordered=True since your model uses ordered to mean completed)
            order = Order.objects.create(user=user, ordered=True)

            # Create order items and deduct stock
            for ci in cart_items:
                p = prod_map[ci.product.id]

                OrderItem.objects.create(
                    order=order,
                    product_id=p.id,
                    title=p.title,
                    qty=ci.qty,
                    price_snapshot=p.price,
                )

                # deduct product quantity if tracked
                if p.quantity is not None:
                    p.quantity = max(0, p.quantity - ci.qty)
                    if p.quantity <= 0:
                        p.is_available = False
                    p.save(update_fields=["quantity", "is_available"])

            # clear cart only after order creation
            cart_items.delete()

    except ValueError:
        # ValueErrors above already added messages; redirect back to cart
        return redirect("market:cart")
    except Exception as e:
        # Unexpected error
        # log.exception(e)  # uncomment in real app
        messages.error(request, "Could not complete checkout. Please try again.")
        return redirect("market:cart")

    messages.success(request, "Checkout complete — order created.")
    # Redirect to order detail so user sees confirmation (better UX than previous_purchases)
    return redirect(reverse("market:order_detail", kwargs={"pk": order.id}))


@login_required_custom
def order_detail(request, pk):
    user = _get_logged_user(request)
    order = get_object_or_404(Order, pk=pk, user=user)
    return render(request, "market/order_detail.html", {"order": order})


@login_required_custom
def previous_purchases(request):
    user = _get_logged_user(request)
    if not user:
        return redirect("market:login")

    try:
        # fetch orders and prefetch items
        orders_qs = (
            Order.objects
                 .filter(user=user, ordered=True)
                 .order_by("-created_at")
                 .prefetch_related("items")
        )
    except Exception as e:
        # fallback: log and show friendly message
        # import logging; logging.exception(e)
        messages.error(request, "Could not load your orders. Please try again.")
        return redirect("market:product_list")

    # If some templates still expect list-of-dicts, we can provide both:
    # pass orders_qs and a list-of-dicts (orders_list) for compatibility
    orders_list = []
    for order in orders_qs:
        orders_list.append({
            "id": order.id,
            "ordered": order.ordered,
            "created_at": order.created_at,
            "items": list(order.items.all()),  # already prefetched
            "total_amount": order.total_amount
        })

    return render(request, "market/previous_purchases.html", {
        "orders": orders_qs,         # preferred: QuerySet of Order objects
        "orders_list": orders_list,  # optional: backwards-compatible list
    })




@login_required_custom
def user_dashboard(request):
    """
    Dashboard/profile update view compatible with your custom auth (hash_password).
    - Updates username, email, password (using hash_password), and optional avatar upload.
    - Shows user's listings (only available ones with quantity > 0), recent orders and cart count.
    """
    user = _get_logged_user(request)
    if not user:
        return redirect("market:login")

    if request.method == "POST":
        new_username = request.POST.get("username", "").strip()
        new_email = request.POST.get("email", "").strip()
        new_password = request.POST.get("password", "").strip()
        avatar = request.FILES.get("avatar")  # file input name 'avatar' in your template

        # basic validation
        if not new_username:
            messages.error(request, "Username cannot be empty.")
            return redirect("market:user_dashboard")

        if new_email and UserAccount.objects.filter(email=new_email).exclude(id=user.id).exists():
            messages.error(request, "Email already taken.")
            return redirect("market:user_dashboard")

        try:
            with transaction.atomic():
                user.username = new_username
                if new_email:
                    user.email = new_email

                # Use your custom hash function to set password (consistent with register/login)
                if new_password:
                    user.password = hash_password(new_password)

                # handle uploaded avatar (if your model has an ImageField named 'avatar')
                if avatar:
                    try:
                        # delete old avatar file if it exists and isn't the default
                        old = getattr(user, "avatar", None)
                        if old and getattr(old, "name", None) and "default-avatar" not in old.name:
                            try:
                                default_storage.delete(old.name)
                            except Exception:
                                pass
                    except Exception:
                        pass

                    # assign the new file
                    # ensure your model has avatar = models.ImageField(...)
                    user.avatar = avatar

                user.save()
        except Exception as e:
            # optionally log.exception(e)
            messages.error(request, "Could not update profile. Please try again.")
            return redirect("market:user_dashboard")

        # refresh session username so navbar shows updated name
        request.session["username"] = user.username

        messages.success(request, "Profile updated successfully.")
        return redirect("market:user_dashboard")

    # GET: prepare dashboard data
    # Only show listings that are available and quantity > 0
    my_listings = Product.objects.filter(owner=user, is_available=True, quantity__gt=0).order_by("-created_at")[:8]
    recent_orders = Order.objects.filter(user=user, ordered=True).order_by("-created_at")[:6]
    cart_count = CartItem.objects.filter(user=user).count()

    return render(request, "market/profile.html", {
        "user_obj": user,
        "my_listings": my_listings,
        "recent_orders": recent_orders,
        "cart_count": cart_count,
    })