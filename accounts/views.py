from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, Appointment
from django.db import IntegrityError
from datetime import date
from .ai_engine.ai_processor import process_query

# ======================
# HOME
# ======================
def home_view(request):
    return render(request, 'home.html')


# ======================
# ======================
# REGISTER
# ======================
def register_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')

        gender = request.POST.get('gender')
        birthdate = request.POST.get('birthdate')
        profession = request.POST.get('profession')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('/register/')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # IMPORTANT: Update profile AFTER creation
        profile = user.profile
        profile.user_type = user_type
        profile.gender = gender
        profile.birthdate = birthdate
        profile.profession = profession
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



@login_required
def book_appointment_view(request, lawyer_id):

    lawyer_profile = get_object_or_404(Profile, id=lawyer_id, user_type='lawyer')

    if request.method == 'POST':

        message = request.POST.get('message')
        appointment_date = request.POST.get('date')
        appointment_time = request.POST.get('time')

        try:
            Appointment.objects.create(
                client=request.user,
                lawyer=lawyer_profile.user,
                message=message,
                appointment_date=appointment_date,
                appointment_time=appointment_time
            )

            messages.success(request, "Appointment booked successfully.")
            return redirect('/dashboard/')

        except IntegrityError:

            messages.error(request, "This time slot is already booked. Please choose another time.")
            return redirect(f'/book/{lawyer_id}/')

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

    # lawyer availability check
    is_available = True

    context = {
        'lawyer': lawyer_profile,
        'is_available': is_available
    }

    return render(request, 'lawyer_detail.html', context)

    return render(request, 'lawyer_detail.html', context)
@login_required
def cancel_appointment_view(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    if appointment.client != request.user:
        messages.error(request, "Not allowed.")
        return redirect('/dashboard/')

    if not appointment.can_cancel():
        messages.error(request, "Cancellation window closed.")
        return redirect('/dashboard/')

    appointment.status = "cancelled"
    appointment.save()

    messages.success(request, "Appointment cancelled successfully.")
    return redirect('/dashboard/')
@login_required
def add_meeting_link_view(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    if appointment.lawyer != request.user:
        messages.error(request, "Not allowed.")
        return redirect('/dashboard/')

    if request.method == "POST":

        meeting_link = request.POST.get("meeting_link")

        appointment.meeting_link = meeting_link
        appointment.status = "accepted"
        appointment.save()

        messages.success(request, "Meeting link added.")
        return redirect('/dashboard/')

    return render(request, "add_meeting_link.html", {"appointment": appointment})
@login_required
def add_meeting_link_view(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.user != appointment.lawyer:
        return redirect('/dashboard/')

    if request.method == 'POST':

        meeting_link = request.POST.get('meeting_link')

        appointment.meeting_link = meeting_link
        appointment.save()

        messages.success(request, "Meeting link added successfully.")

        return redirect('/dashboard/')

    return render(request, 'add_meeting_link.html', {'appointment': appointment})
@login_required
def cancel_appointment_view(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.user == appointment.client and appointment.status == 'pending':

        appointment.status = 'cancelled'
        appointment.save()

        messages.success(request, "Appointment cancelled.")

    return redirect('/dashboard/')
@login_required
def legal_ai_view(request):

    result = None
    recommended_lawyers = None

    if request.method == "POST":

        problem = request.POST.get("problem")

        result = process_query(problem)

        if result["lawyer_type"]:

            recommended_lawyers = Profile.objects.filter(
                specialization__icontains=result["lawyer_type"]
            )

    return render(request, "legal_ai.html", {
        "result": result,
        "recommended_lawyers": recommended_lawyers
    })