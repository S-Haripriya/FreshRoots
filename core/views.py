from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import UserProfile



def home(request):
    return render(request, 'home.html')


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
