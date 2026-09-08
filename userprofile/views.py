from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import logout
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
    return redirect(request, 'logout.html')
