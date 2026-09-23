from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.models import User
from .models import GetCertified


@login_required
def account(request):
    user = request.user
    user_profile = user.userprofile

    if request.method == "POST":
        farm_name = request.POST.get("farm_name")
        farm_address = request.POST.get("farm_address")
        farm_type = request.POST.get("farm_type")
        certificate = request.FILES.get("certificate")

        # Check that all fields are provided
        if not farm_name or not farm_address or not farm_type or not certificate:
            messages.error(request, "Please fill in all the fields.")
            return redirect("profile")

        # Create the farm/producer request
        GetCertified.objects.create(
            user_profile=user_profile,
            farm_name=farm_name,
            farm_address=farm_address,
            farm_type=farm_type,
            certificate=certificate,
            is_verified=False
        )

        messages.success(
            request,
            "Your request has been submitted successfully."
        )

        return redirect("profile")

    farms = GetCertified.objects.filter(
        user_profile=user_profile
    )

    context = {
        "user": user,
        "user_profile": user_profile,
        "farms": farms,
    }

    return render(request, 'profile.html', context)


def logout_view(request):

    if request.method == "POST":
        logout(request)
        return redirect("home")
    return redirect("home")


@login_required
def edit_profile(request):
    if request.method != "POST":
        return redirect('profile')

    user = request.user
    user_profile = user.userprofile

    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    email = request.POST.get("email", "").strip()
    contact_number = request.POST.get("contact_number", "").strip()

    if not first_name or not email or not contact_number:
        messages.error(request, "First name, email, and contact number are required.")
        return redirect('profile')

    # Check if email is changing and already taken by someone else
    if email != user.email:
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "That email is already in use by another account.")
            return redirect('profile')

        user.email = email
        user.username = email   # keep username in sync, since login uses email as username

    user.first_name = first_name
    user.last_name = last_name
    user.save()

    user_profile.contact_number = contact_number
    user_profile.save()

    messages.success(request, "Your profile has been updated.")
    return redirect('profile')