from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from userprofile.models import GetCertified
from .models import Product, FarmerProduct, SaleRecord

@login_required
def my_products(request):
    user_profile = request.user.userprofile
    farms = GetCertified.objects.filter(user_profile=user_profile, is_verified=True)

    if not farms.exists():
        messages.error(request, "You need a verified farm before you can add products.")
        return redirect('profile')

    if request.method == "POST":
        farm_id = request.POST.get("farm")
        product_id = request.POST.get("product")
        quantity = request.POST.get("quantity")
        image = request.FILES.get("image")

        farm = get_object_or_404(farms, id=farm_id)
        product = get_object_or_404(Product, id=product_id)

        if not quantity or not quantity.isdigit() or int(quantity) <= 0:
            messages.error(request, "Please enter a valid quantity.")
            return redirect('my_products')

        quantity = int(quantity)

        listing, created = FarmerProduct.objects.get_or_create(
            farm=farm,
            product=product,
            defaults={"quantity": quantity, "image": image}
        )

        if not created:
            # Reactivate if it was previously removed, otherwise just add stock
            if not listing.is_active:
                listing.is_active = True
                listing.quantity = quantity
                if image:
                    listing.image = image
                listing.save(update_fields=["is_active", "quantity", "image"])
                messages.success(request, f"{product.name} has been re-listed.")
            else:
                listing.quantity += quantity
                if image:
                    listing.image = image
                listing.save(update_fields=["quantity", "image"])
                messages.success(request, f"Added {quantity} more units of {product.name}.")
        else:
            messages.success(request, f"{product.name} has been added to your products.")

        return redirect('my_products')

    listings = FarmerProduct.objects.filter(
        farm__in=farms, is_active=True
    ).select_related('product', 'farm')

    total_earned = sum(listing.money_earned for listing in listings)
    total_quantity = sum(listing.quantity for listing in listings)
    total_sold = sum(listing.sold_quantity for listing in listings)

    sales_history = SaleRecord.objects.filter(
        farmer_product__farm__in=farms
    ).select_related('farmer_product__product', 'farmer_product__farm').order_by('-sold_at')

    available_products = Product.objects.all().order_by('name')

    context = {
        "farms": farms,
        "listings": listings,
        "available_products": available_products,
        "total_earned": total_earned,
        "total_quantity": total_quantity,
        "total_sold": total_sold,
        "sales_history": sales_history,
    }

    return render(request, 'my_products.html', context)


@login_required
def remove_farmer_product(request, listing_id):
    if request.method != "POST":
        return redirect('my_products')

    user_profile = request.user.userprofile

    listing = get_object_or_404(
        FarmerProduct,
        id=listing_id,
        farm__user_profile=user_profile
    )

    listing.is_active = False
    listing.save(update_fields=['is_active'])

    messages.success(
        request,
        f"{listing.product.name} has been removed from your listings."
    )

    return redirect('my_products')