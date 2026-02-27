from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, Appointment


# ======================
# HOME
# ======================
def home_view(request):
    return render(request, 'home.html')


# ======================
# REGISTER
# ======================
def register_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('/register/')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        profile = user.profile
        profile.user_type = user_type
        profile.save()

        login(request, user)
        return redirect('/dashboard/')

    return render(request, 'register.html')


# ======================
# LOGIN
# ======================
def login_view(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('/dashboard/')
        else:
            messages.error(request, "Invalid credentials")

    return render(request, 'login.html')


# ======================
# LOGOUT
# ======================
def logout_view(request):
    logout(request)
    return redirect('/')


# ======================
# DASHBOARD
# ======================
@login_required
def dashboard_view(request):

    profile = request.user.profile

    if profile.user_type == 'lawyer':
        appointments = Appointment.objects.filter(
            lawyer=request.user
        ).order_by('-created_at')

        total = appointments.count()
        pending = appointments.filter(status='pending').count()
        accepted = appointments.filter(status='accepted').count()
        rejected = appointments.filter(status='rejected').count()

        revenue = 0
        if profile.consultation_fee:
            revenue = accepted * profile.consultation_fee

    else:
        appointments = Appointment.objects.filter(
            client=request.user
        ).order_by('-created_at')

        total = appointments.count()
        pending = appointments.filter(status='pending').count()
        accepted = appointments.filter(status='accepted').count()
        rejected = appointments.filter(status='rejected').count()
        revenue = None

    context = {
        'profile': profile,
        'appointments': appointments,
        'total': total,
        'pending': pending,
        'accepted': accepted,
        'rejected': rejected,
        'revenue': revenue
    }

    return render(request, 'dashboard.html', context)


# ======================
# LAWYER LIST
# ======================
@login_required
def lawyer_list_view(request):

    lawyers = Profile.objects.filter(user_type='lawyer')

    return render(request, 'lawyers.html', {'lawyers': lawyers})


# ======================
# ======================
# BOOK APPOINTMENT
# ======================
from datetime import date, datetime

@login_required
def book_appointment_view(request, lawyer_id):

    lawyer_profile = get_object_or_404(Profile, id=lawyer_id, user_type='lawyer')

    if request.method == 'POST':

        message = request.POST.get('message')
        appointment_date = request.POST.get('date')
        time_input = request.POST.get('time')

        # ✅ Convert time properly (handles both 05:00 PM and 17:00)
        try:
            if "AM" in time_input or "PM" in time_input:
                appointment_time = datetime.strptime(time_input, "%I:%M %p").time()
            else:
                appointment_time = datetime.strptime(time_input, "%H:%M").time()
        except:
            messages.error(request, "Invalid time format.")
            return redirect(f'/book/{lawyer_id}/')

        # Check if slot already accepted
        existing = Appointment.objects.filter(
            lawyer=lawyer_profile.user,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status='accepted'
        ).exists()

        if existing:
            messages.error(request, "This slot is already booked.")
            return redirect(f'/book/{lawyer_id}/')

        Appointment.objects.create(
            client=request.user,
            lawyer=lawyer_profile.user,
            message=message,
            appointment_date=appointment_date,
            appointment_time=appointment_time
        )

        messages.success(request, "Appointment booked successfully.")
        return redirect('/dashboard/')

    context = {
        'lawyer': lawyer_profile,
        'today': date.today()
    }

    return render(request, 'book_appointment.html', context)
# ======================
# ACCEPT APPOINTMENT
# ======================
@login_required
def accept_appointment(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.user == appointment.lawyer:
        appointment.status = 'accepted'
        appointment.save()

    return redirect('/dashboard/')


# ======================
# REJECT APPOINTMENT
# ======================
@login_required
def reject_appointment(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.user == appointment.lawyer:
        appointment.status = 'rejected'
        appointment.save()

    return redirect('/dashboard/')
# ======================
# LAWYER DETAIL
# ======================
@login_required
def lawyer_detail_view(request, lawyer_id):

    lawyer_profile = get_object_or_404(Profile, id=lawyer_id, user_type='lawyer')

    client_profile = None
    if hasattr(request.user, 'profile'):
        client_profile = request.user.profile

    context = {
        'lawyer': lawyer_profile,
        'client_profile': client_profile
    }

    return render(request, 'lawyer_detail.html', context)