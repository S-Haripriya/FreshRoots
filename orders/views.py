from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from products.models import FarmerProduct
from .models import Order, SaleRecord


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
    Replace this with real payment verification if/when you
    integrate an actual provider later.
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

    messages.success(request, "Payment successful! Your order has been placed and being processed.")
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
        'farmer_product__farm'
    ).order_by('-created_at')

    total_spent = sum(
        order.total_amount for order in orders if order.status == Order.STATUS_PAID
    )

    context = {
        "orders": orders,
        "total_spent": total_spent,
    }

    return render(request, 'purchase_history.html', context)    