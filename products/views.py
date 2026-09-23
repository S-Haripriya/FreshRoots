from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse

from django.db.models import Q, F
from userprofile.models import GetCertified
from .models import Product, FarmerProduct
from orders.models import SaleRecord

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

def browse_products(request):
    query = request.GET.get('q', '').strip()

    listings = FarmerProduct.objects.filter(
        is_active=True
    ).filter(
        sold_quantity__lt=F('quantity')   # only in-stock listings
    ).select_related('product', 'farm')

    if query:
        listings = listings.filter(
            Q(product__name__icontains=query) |
            Q(farm__farm_name__icontains=query) |
            Q(farm__farm_address__icontains=query)
        )

    context = {
        "listings": listings,
        "query": query,
    }

    return render(request, 'browse_products.html', context)


def get_listing_reviews(request, listing_id):
    listing = get_object_or_404(FarmerProduct, id=listing_id)

    reviews = listing.reviews.select_related('customer').order_by('-created_at')

    data = [
        {
            "customer_name": review.customer.first_name or review.customer.username,
            "rating": review.rating,
            "comment": review.comment,
            "date": review.created_at.strftime("%d %b %Y"),
        }
        for review in reviews
    ]

    return JsonResponse({
        "product_name": listing.product.name,
        "average_rating": listing.average_rating,
        "review_count": listing.review_count,
        "reviews": data,
    })