from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Profile, Appointment


# ---------------- HOME ----------------

def home_view(request):
    return render(request, 'home.html')


# ---------------- REGISTER ----------------

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists'})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        login(request, user)
        return redirect('dashboard')

    return render(request, 'register.html')


# ---------------- LOGIN ----------------

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


# ---------------- LOGOUT ----------------

def logout_view(request):
    logout(request)
    return redirect('home')


# ---------------- DASHBOARD ----------------

@login_required
def dashboard_view(request):

    profile = Profile.objects.get(user=request.user)

    if profile.user_type == 'client':
        appointments = Appointment.objects.filter(client=request.user)
    else:
        appointments = Appointment.objects.filter(lawyer=request.user)

    return render(request, 'dashboard.html', {
        'appointments': appointments,
        'profile': profile
    })


# ---------------- LAWYER LIST ----------------

@login_required
def lawyer_list_view(request):
    query = request.GET.get('q')

    lawyers = Profile.objects.filter(user_type='lawyer')

    if query:
        lawyers = lawyers.filter(specialization__icontains=query)

    return render(request, 'lawyers.html', {
        'lawyers': lawyers
    })

# ---------------- LAWYER DETAIL ----------------

def lawyer_detail_view(request, pk):
    lawyer = get_object_or_404(Profile, pk=pk, user_type='lawyer')
    return render(request, 'lawyer_detail.html', {'lawyer': lawyer})


# ---------------- BOOK APPOINTMENT ----------------

@login_required
def book_appointment_view(request, pk):
    lawyer_profile = get_object_or_404(Profile, pk=pk, user_type='lawyer')
    lawyer_user = lawyer_profile.user

    if request.method == 'POST':
        message = request.POST.get('message')

        Appointment.objects.create(
            client=request.user,
            lawyer=lawyer_user,
            message=message
        )

        return redirect('dashboard')

    return render(request, 'book_appointment.html', {'lawyer': lawyer_profile})