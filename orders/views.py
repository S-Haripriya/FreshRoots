from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from userprofile.models import GetCertified
from products.models import FarmerProduct
from .models import Order, SaleRecord, DeliveryPartner


# =========================================================
# CUSTOMER CHECKOUT
# =========================================================

@login_required
def buy_now(request, listing_id):
    if request.method != "POST":
        return redirect('browse_products')

    listing = get_object_or_404(FarmerProduct, id=listing_id, is_active=True)

    quantity = request.POST.get('quantity')
    delivery_address = request.POST.get('delivery_address')

    if not quantity or not quantity.isdigit() or int(quantity) <= 0:
        messages.error(request, "Please enter a valid quantity.")
        return redirect('browse_products')

    quantity = int(quantity)

    if quantity > listing.remaining:
        messages.error(
            request,
            f"Only {listing.remaining} kg of {listing.product.name} available."
        )
        return redirect('browse_products')

    if not delivery_address or not delivery_address.strip():
        messages.error(request, "Please enter a delivery address.")
        return redirect('browse_products')

    total_amount = quantity * listing.price

    order = Order.objects.create(
        customer=request.user,
        farmer_product=listing,
        quantity=quantity,
        price_per_unit=listing.price,
        total_amount=total_amount,
        delivery_address=delivery_address.strip(),
    )

    return render(request, 'payment_checkout.html', {"order": order})


@login_required
def confirm_payment(request, order_id):
    """
    Simulated payment confirmation — no real gateway involved.
    Marks payment as paid only. Delivery status starts at
    'placed' and progresses separately through the farmer and
    delivery partner fulfillment flow.
    """
    if request.method != "POST":
        return redirect('browse_products')

    order = get_object_or_404(
        Order, id=order_id, customer=request.user, status=Order.STATUS_PENDING
    )

    order.status = Order.STATUS_PAID
    order.save(update_fields=['status'])

    SaleRecord.objects.create(
        farmer_product=order.farmer_product,
        buyer=order.customer,
        quantity=order.quantity,
        price_at_sale=order.price_per_unit,
    )

    messages.success(
        request,
        "Payment successful! Your order has been placed and is being processed."
    )
    return redirect('order_success', order_id=order.id)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'order_success.html', {"order": order})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(
        Order, id=order_id, customer=request.user, status=Order.STATUS_PENDING
    )
    order.status = Order.STATUS_CANCELLED
    order.save(update_fields=['status'])
    messages.info(request, "Order cancelled.")
    return redirect('browse_products')


@login_required
def purchase_history(request):
    orders = Order.objects.filter(
        customer=request.user
    ).select_related(
        'farmer_product__product',
        'farmer_product__farm',
        'delivery_partner'
    ).prefetch_related(
        'status_updates'
    ).order_by('-created_at')

    total_spent = sum(
        order.total_amount for order in orders if order.status == Order.STATUS_PAID
    )

    context = {
        "orders": orders,
        "total_spent": total_spent,
    }

    return render(request, 'purchase_history.html', context)


# =========================================================
# FARMER ORDER MANAGEMENT
# =========================================================
# Farmer's responsibility ends at "Shipped" — from there,
# a delivery partner takes over (see next section below).

FARMER_NEXT_STATUS_MAP = {
    Order.DELIVERY_PLACED: Order.DELIVERY_CONFIRMED,
    Order.DELIVERY_CONFIRMED: Order.DELIVERY_PACKED,
    Order.DELIVERY_PACKED: Order.DELIVERY_SHIPPED,
}


@login_required
def farmer_orders(request):
    user_profile = request.user.userprofile

    farms = GetCertified.objects.filter(
        user_profile=user_profile, is_verified=True
    )

    if not farms.exists():
        messages.error(request, "You need a verified farm to view orders.")
        return redirect('profile')

    orders = Order.objects.filter(
        farmer_product__farm__in=farms,
        status=Order.STATUS_PAID
    ).select_related(
        'farmer_product__product',
        'farmer_product__farm',
        'customer',
        'delivery_partner'
    ).order_by('-created_at')

    context = {
        "orders": orders,
        "next_status_map": FARMER_NEXT_STATUS_MAP,
    }

    return render(request, 'farmer_orders.html', context)


@login_required
def advance_delivery_status(request, order_id):
    """
    Farmer-side status advance. Only works up to 'Shipped' —
    FARMER_NEXT_STATUS_MAP has no entry beyond Packed, so this
    naturally refuses to advance further once Shipped is reached.
    """
    if request.method != "POST":
        return redirect('farmer_orders')

    user_profile = request.user.userprofile

    order = get_object_or_404(
        Order,
        id=order_id,
        farmer_product__farm__user_profile=user_profile
    )

    next_status = FARMER_NEXT_STATUS_MAP.get(order.delivery_status)

    if not next_status:
        messages.error(
            request,
            "This order can no longer be updated from your side."
        )
        return redirect('farmer_orders')

    order.delivery_status = next_status
    order.save(update_fields=['delivery_status'])

    messages.success(
        request,
        f"Order #{order.id} updated to '{order.get_delivery_status_display()}'."
    )
    return redirect('farmer_orders')


# =========================================================
# DELIVERY PARTNER
# =========================================================
# Takes over once a farmer marks an order 'Shipped'.
# Handles: Shipped -> Out for Delivery -> Delivered

def delivery_partner_register(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        phone_number = request.POST.get("phone_number")
        vehicle_number = request.POST.get("vehicle_number")

        if not all([email, password, phone_number]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('delivery_partner_register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect('delivery_partner_register')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
        )

        DeliveryPartner.objects.create(
            user=user,
            phone_number=phone_number,
            vehicle_number=vehicle_number,
            is_approved=False,
        )

        messages.success(
            request,
            "Registration submitted! You'll be able to log in once an admin approves your account."
        )
        return redirect('login')

    return render(request, 'delivery_register.html')


@login_required
def delivery_dashboard(request):
    partner = get_object_or_404(DeliveryPartner, user=request.user)

    if not partner.is_approved:
        messages.error(
            request,
            "Your delivery partner account is pending admin approval."
        )
        return redirect('home')

    available_orders = Order.objects.filter(
        delivery_status=Order.DELIVERY_SHIPPED,
        delivery_partner__isnull=True
    ).select_related('farmer_product__product', 'farmer_product__farm')

    my_deliveries = Order.objects.filter(
        delivery_partner=partner,
        delivery_status=Order.DELIVERY_OUT_FOR_DELIVERY
    ).select_related('farmer_product__product', 'customer')

    completed_deliveries = Order.objects.filter(
        delivery_partner=partner,
        delivery_status=Order.DELIVERY_DELIVERED
    ).select_related('farmer_product__product').order_by('-delivered_at')[:20]

    context = {
        "available_orders": available_orders,
        "my_deliveries": my_deliveries,
        "completed_deliveries": completed_deliveries,
    }

    return render(request, 'delivery_dashboard.html', context)


@login_required
def accept_delivery(request, order_id):
    if request.method != "POST":
        return redirect('delivery_dashboard')

    partner = get_object_or_404(DeliveryPartner, user=request.user, is_approved=True)

    order = get_object_or_404(
        Order,
        id=order_id,
        delivery_status=Order.DELIVERY_SHIPPED,
        delivery_partner__isnull=True
    )

    order.delivery_partner = partner
    order.delivery_status = Order.DELIVERY_OUT_FOR_DELIVERY
    order.save(update_fields=['delivery_partner', 'delivery_status'])

    messages.success(request, f"Order #{order.id} accepted for delivery.")
    return redirect('delivery_dashboard')


@login_required
def mark_delivered(request, order_id):
    if request.method != "POST":
        return redirect('delivery_dashboard')

    partner = get_object_or_404(DeliveryPartner, user=request.user, is_approved=True)

    order = get_object_or_404(
        Order,
        id=order_id,
        delivery_partner=partner,
        delivery_status=Order.DELIVERY_OUT_FOR_DELIVERY
    )

    order.delivery_status = Order.DELIVERY_DELIVERED
    order.save(update_fields=['delivery_status'])   # delivered_at auto-set by your existing pre_save signal

    messages.success(request, f"Order #{order.id} marked as delivered.")
    return redirect('delivery_dashboard')