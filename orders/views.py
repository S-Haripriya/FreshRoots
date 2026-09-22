from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from userprofile.models import GetCertified
from products.models import FarmerProduct
from .models import Order, SaleRecord, DeliveryPartner, Cart, CartItem

import uuid
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

    delivery_address = delivery_address.strip()
    total_amount = quantity * listing.price

    checkout_id = uuid.uuid4().hex

    # Nothing is created yet — just remember this checkout attempt
    request.session['pending_buy_now'] = {
        "checkout_id": checkout_id,
        "listing_id": listing.id,
        "quantity": quantity,
        "delivery_address": delivery_address,
    }

    context = {
        "listing": listing,
        "quantity": quantity,
        "delivery_address": delivery_address,
        "total_amount": total_amount,
        "checkout_id": checkout_id,
    }

    return render(request, 'payment_checkout.html', context)
@login_required
def confirm_payment(request, checkout_id):
    if request.method != "POST":
        return redirect('browse_products')

    pending = request.session.get('pending_buy_now')

    if not pending or pending.get('checkout_id') != checkout_id:
        messages.error(request, "This checkout session has expired. Please try again.")
        return redirect('browse_products')

    listing = get_object_or_404(FarmerProduct, id=pending['listing_id'], is_active=True)
    quantity = pending['quantity']
    delivery_address = pending['delivery_address']

    # Re-validate stock, since time has passed
    if quantity > listing.remaining:
        messages.error(
            request,
            f"Only {listing.remaining} kg of {listing.product.name} available. Please try again."
        )
        del request.session['pending_buy_now']
        return redirect('browse_products')

    total_amount = quantity * listing.price

    order = Order.objects.create(
        customer=request.user,
        farmer_product=listing,
        quantity=quantity,
        price_per_unit=listing.price,
        total_amount=total_amount,
        delivery_address=delivery_address,
    )

    order.status = Order.STATUS_PAID
    order.save(update_fields=['status'])

    SaleRecord.objects.create(
        farmer_product=order.farmer_product,
        buyer=order.customer,
        quantity=order.quantity,
        price_at_sale=order.price_per_unit,
    )

    del request.session['pending_buy_now']

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

# =========================================================
# SHOPPING CART
# =========================================================

@login_required
def view_cart(request):
    cart, _ = Cart.objects.get_or_create(customer=request.user)

    items = cart.items.select_related(
        'farmer_product__product', 'farmer_product__farm'
    )

    context = {
        "cart": cart,
        "items": items,
    }

    return render(request, 'cart.html', context)


@login_required
def add_to_cart(request, listing_id):
    if request.method != "POST":
        return redirect('browse_products')

    listing = get_object_or_404(FarmerProduct, id=listing_id, is_active=True)

    quantity = request.POST.get('quantity')

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

    cart, _ = Cart.objects.get_or_create(customer=request.user)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        farmer_product=listing,
        defaults={"quantity": quantity}
    )

    if not created:
        new_quantity = item.quantity + quantity
        if new_quantity > listing.remaining:
            messages.error(
                request,
                f"Only {listing.remaining} kg of {listing.product.name} available. "
                f"You already have {item.quantity} kg in your cart."
            )
            return redirect('browse_products')

        item.quantity = new_quantity
        item.save(update_fields=['quantity'])

    messages.success(request, f"{listing.product.name} added to your cart.")
    return redirect('browse_products')


@login_required
def update_cart_item(request, item_id):
    if request.method != "POST":
        return redirect('view_cart')

    item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)

    quantity = request.POST.get('quantity')

    if not quantity or not quantity.isdigit() or int(quantity) <= 0:
        messages.error(request, "Please enter a valid quantity.")
        return redirect('view_cart')

    quantity = int(quantity)

    if quantity > item.farmer_product.remaining:
        messages.error(
            request,
            f"Only {item.farmer_product.remaining} kg of "
            f"{item.farmer_product.product.name} available."
        )
        return redirect('view_cart')

    item.quantity = quantity
    item.save(update_fields=['quantity'])

    messages.success(request, "Cart updated.")
    return redirect('view_cart')


@login_required
def remove_cart_item(request, item_id):
    if request.method != "POST":
        return redirect('view_cart')

    item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)
    product_name = item.farmer_product.product.name
    item.delete()

    messages.success(request, f"{product_name} removed from your cart.")
    return redirect('view_cart')

@login_required
def checkout_cart(request):
    if request.method != "POST":
        return redirect('view_cart')

    cart, _ = Cart.objects.get_or_create(customer=request.user)
    items = list(cart.items.select_related('farmer_product__product', 'farmer_product__farm'))

    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    delivery_address = request.POST.get('delivery_address')

    if not delivery_address or not delivery_address.strip():
        messages.error(request, "Please enter a delivery address.")
        return redirect('view_cart')

    delivery_address = delivery_address.strip()

    # Re-validate stock before showing the payment screen
    for item in items:
        if item.quantity > item.farmer_product.remaining:
            messages.error(
                request,
                f"Only {item.farmer_product.remaining} kg of "
                f"{item.farmer_product.product.name} available. Please update your cart."
            )
            return redirect('view_cart')

    checkout_id = uuid.uuid4().hex

    # Nothing is created yet — just remember this checkout attempt.
    # The cart itself is left completely untouched.
    request.session['pending_checkout_id'] = checkout_id
    request.session['pending_delivery_address'] = delivery_address

    total_amount = sum(item.subtotal for item in items)

    return render(request, 'cart_payment_checkout.html', {
        "items": items,
        "checkout_id": checkout_id,
        "total_amount": total_amount,
    })


@login_required
def confirm_cart_payment(request, checkout_id):
    if request.method != "POST":
        return redirect('view_cart')

    # Make sure this is the same checkout the user actually started —
    # protects against replaying a stale/abandoned payment page.
    if request.session.get('pending_checkout_id') != checkout_id:
        messages.error(request, "This checkout session has expired. Please try again.")
        return redirect('view_cart')

    delivery_address = request.session.get('pending_delivery_address')

    cart, _ = Cart.objects.get_or_create(customer=request.user)
    items = list(cart.items.select_related('farmer_product__product', 'farmer_product__farm'))

    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    # Re-validate stock one last time, since time has passed
    for item in items:
        if item.quantity > item.farmer_product.remaining:
            messages.error(
                request,
                f"Only {item.farmer_product.remaining} kg of "
                f"{item.farmer_product.product.name} available. Please update your cart."
            )
            return redirect('view_cart')

    created_orders = []

    for item in items:
        order = Order.objects.create(
            customer=request.user,
            farmer_product=item.farmer_product,
            quantity=item.quantity,
            price_per_unit=item.farmer_product.price,
            total_amount=item.subtotal,
            delivery_address=delivery_address,
            cart_checkout_id=checkout_id,
        )
        order.status = Order.STATUS_PAID
        order.save(update_fields=['status'])

        SaleRecord.objects.create(
            farmer_product=order.farmer_product,
            buyer=order.customer,
            quantity=order.quantity,
            price_at_sale=order.price_per_unit,
        )

        created_orders.append(order)

    # Only now, after successful "payment", clear the cart
    cart.items.all().delete()

    del request.session['pending_checkout_id']
    del request.session['pending_delivery_address']

    messages.success(
        request,
        "Payment successful! Your order has been placed and is being processed."
    )
    return redirect('cart_order_success', checkout_id=checkout_id)


@login_required
def cart_order_success(request, checkout_id):
    orders = Order.objects.filter(
        cart_checkout_id=checkout_id,
        customer=request.user
    ).select_related('farmer_product__product', 'farmer_product__farm')

    if not orders.exists():
        return redirect('browse_products')

    total_amount = sum(o.total_amount for o in orders)

    context = {
        "orders": orders,
        "total_amount": total_amount,
    }

    return render(request, 'cart_order_success.html', context)