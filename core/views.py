from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import UserProfile
from django.db.models import F
from products.models import FarmerProduct
from userprofile.models import GetCertified
from orders.models import DeliveryPartner, Order
from products.models import Product


def home(request):
    featured_listings = FarmerProduct.objects.filter(
        is_active=True
    ).filter(
        sold_quantity__lt=F('quantity')
    ).select_related('product', 'farm').order_by('-created_at')[:6]

    context = {
        "featured_listings": featured_listings,
    }

    return render(request, 'home.html', context)


def about(request):
    return render(request, 'about.html')


def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        # Check email and password
        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:

            # Log the user in
            login(request, user)

            # Delivery partners don't have a UserProfile,
            # so send them straight to their own dashboard
            # instead of pages that assume user.userprofile exists.
            if hasattr(user, 'delivery_partner_profile'):
                return redirect("delivery_dashboard")

            return redirect("home")

        # Invalid login
        messages.error(
            request,
            "Invalid email or password."
        )

        return redirect("login")

    return render(request, 'login.html')


def register(request):

    if request.method == "POST":

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        contact_number = request.POST.get("contact_number")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Check passwords
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        # Check existing email
        if User.objects.filter(email=email).exists():
            messages.error(
                request,
                "An account with this email already exists."
            )
            return redirect("register")

        # Use email as username
        username = email

        # Create User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create UserProfile
        UserProfile.objects.create(
            user=user,
            contact_number=contact_number
        )

        messages.success(
            request,
            "Account created successfully. You can now log in."
        )

        return redirect("login")

    return render(request, 'register.html')


@staff_member_required
def admin_dashboard(request):
    pending_farms = GetCertified.objects.filter(
        is_verified=False
    ).select_related('user_profile__user').order_by('-id')

    approved_farms = GetCertified.objects.filter(
        is_verified=True
    ).select_related('user_profile__user').order_by('-id')

    pending_delivery_partners = DeliveryPartner.objects.filter(
        is_approved=False
    ).select_related('user').order_by('-id')

    approved_delivery_partners = DeliveryPartner.objects.filter(
        is_approved=True
    ).select_related('user').order_by('-id')

    context = {
        "pending_farms": pending_farms,
        "approved_farms": approved_farms,
        "pending_delivery_partners": pending_delivery_partners,
        "approved_delivery_partners": approved_delivery_partners,
    }

    return render(request, 'admin_dashboard.html', context)


@staff_member_required
def approve_farm(request, farm_id):
    if request.method != "POST":
        return redirect('admin_dashboard')

    farm = get_object_or_404(GetCertified, id=farm_id)
    farm.is_verified = True
    farm.save(update_fields=['is_verified'])

    messages.success(request, f"{farm.farm_name} has been approved.")
    return redirect('admin_dashboard')


@staff_member_required
def reject_farm(request, farm_id):
    if request.method != "POST":
        return redirect('admin_dashboard')

    farm = get_object_or_404(GetCertified, id=farm_id)
    farm_name = farm.farm_name
    farm.delete()

    messages.info(request, f"{farm_name}'s registration request has been rejected and removed.")
    return redirect('admin_dashboard')


@staff_member_required
def revoke_farm(request, farm_id):
    """Move an already-approved farm back to pending/unverified."""
    if request.method != "POST":
        return redirect('admin_dashboard')

    farm = get_object_or_404(GetCertified, id=farm_id)
    farm.is_verified = False
    farm.save(update_fields=['is_verified'])

    messages.info(request, f"{farm.farm_name}'s verification has been revoked.")
    return redirect('admin_dashboard')


@staff_member_required
def approve_delivery_partner(request, partner_id):
    if request.method != "POST":
        return redirect('admin_dashboard')

    partner = get_object_or_404(DeliveryPartner, id=partner_id)
    partner.is_approved = True
    partner.save(update_fields=['is_approved'])

    messages.success(request, f"{partner.user.get_full_name() or partner.user.username} has been approved.")
    return redirect('admin_dashboard')


@staff_member_required
def reject_delivery_partner(request, partner_id):
    if request.method != "POST":
        return redirect('admin_dashboard')

    partner = get_object_or_404(DeliveryPartner, id=partner_id)
    name = partner.user.get_full_name() or partner.user.username
    partner.user.delete()   # cascades and deletes the DeliveryPartner too

    messages.info(request, f"{name}'s delivery partner application has been rejected and removed.")
    return redirect('admin_dashboard')


@staff_member_required
def revoke_delivery_partner(request, partner_id):
    """Move an already-approved delivery partner back to pending."""
    if request.method != "POST":
        return redirect('admin_dashboard')

    partner = get_object_or_404(DeliveryPartner, id=partner_id)
    partner.is_approved = False
    partner.save(update_fields=['is_approved'])

    messages.info(request, f"{partner.user.username}'s approval has been revoked.")
    return redirect('admin_dashboard')


@staff_member_required
def manage_products(request):
    products = Product.objects.all().order_by('-created_at')

    context = {
        "products": products,
    }

    return render(request, 'manage_products.html', context)


@staff_member_required
def add_product(request):
    if request.method != "POST":
        return redirect('manage_products')

    name = request.POST.get("name", "").strip()
    price = request.POST.get("price")
    description = request.POST.get("description", "").strip()
    image = request.FILES.get("image")

    if not name or not price:
        messages.error(request, "Product name and price are required.")
        return redirect('manage_products')

    try:
        price = float(price)
        if price <= 0:
            raise ValueError
    except ValueError:
        messages.error(request, "Please enter a valid price.")
        return redirect('manage_products')

    if Product.objects.filter(name__iexact=name).exists():
        messages.error(request, f"A product named '{name}' already exists.")
        return redirect('manage_products')

    Product.objects.create(
        name=name,
        price=price,
        description=description,
        image=image,
    )

    messages.success(request, f"'{name}' has been added to the catalog.")
    return redirect('manage_products')


@staff_member_required
def edit_product(request, product_id):
    if request.method != "POST":
        return redirect('manage_products')

    product = get_object_or_404(Product, id=product_id)

    name = request.POST.get("name", "").strip()
    price = request.POST.get("price")
    description = request.POST.get("description", "").strip()
    image = request.FILES.get("image")

    if not name or not price:
        messages.error(request, "Product name and price are required.")
        return redirect('manage_products')

    try:
        price = float(price)
        if price <= 0:
            raise ValueError
    except ValueError:
        messages.error(request, "Please enter a valid price.")
        return redirect('manage_products')

    if Product.objects.filter(name__iexact=name).exclude(id=product.id).exists():
        messages.error(request, f"A product named '{name}' already exists.")
        return redirect('manage_products')

    product.name = name
    product.price = price
    product.description = description

    if image:
        product.image = image

    product.save()

    messages.success(request, f"'{name}' has been updated.")
    return redirect('manage_products')


@staff_member_required
def delete_product(request, product_id):
    if request.method != "POST":
        return redirect('manage_products')

    product = get_object_or_404(Product, id=product_id)

    if product.farmer_listings.exists():
        messages.error(
            request,
            f"Cannot delete '{product.name}' — farmers currently have active "
            f"listings for it. Remove those listings first."
        )
        return redirect('manage_products')

    name = product.name
    product.delete()

    messages.success(request, f"'{name}' has been removed from the catalog.")
    return redirect('manage_products')


@staff_member_required
def order_overview(request):
    orders = Order.objects.select_related(
        'customer',
        'farmer_product__product',
        'farmer_product__farm',
        'delivery_partner__user'
    ).order_by('-created_at')

    status_filter = request.GET.get('status', '')
    delivery_filter = request.GET.get('delivery_status', '')

    if status_filter:
        orders = orders.filter(status=status_filter)

    if delivery_filter:
        orders = orders.filter(delivery_status=delivery_filter)

    context = {
        "orders": orders,
        "status_filter": status_filter,
        "delivery_filter": delivery_filter,
        "status_choices": Order.STATUS_CHOICES,
        "delivery_status_choices": Order.DELIVERY_STATUS_CHOICES,
        "total_orders": orders.count(),
        "total_revenue": sum(o.total_amount for o in orders if o.status == Order.STATUS_PAID),
    }

    return render(request, 'order_overview.html', context)