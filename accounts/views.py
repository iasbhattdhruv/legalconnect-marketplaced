from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import IntegrityError
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, datetime, timedelta
from openpyxl import Workbook, load_workbook
import os
import urllib.parse

from .models import (
    Profile,
    Appointment,
    Review,
    AppointmentDocument,
    Invoice,
    BlogPost,
    ChatMessage,
    AvailabilitySlot,
    AIChat,
    AIConversation,
)
from .ai_engine.ai_processor import get_ai_response
from .ai_engine.intent_detector import detect_intent
from .ai_engine.knowledge_base import get_knowledge, get_topics
from .analytics import summarize_booking_data
from .excel_utils import append_user_to_excel, sync_users_from_excel
from .legal_updates import get_latest_legal_updates
from .ml_features import build_case_guidance, build_triage_report, classify_legal_issue, recommend_lawyers


# ======================
# HOME
# ======================
def home_view(request):
    booking_insights = summarize_booking_data()
    legal_updates = get_latest_legal_updates()
    return render(request, 'home.html', {
        'booking_insights': booking_insights,
        'legal_updates': legal_updates,
        'show_excel_sync': request.user.is_authenticated and request.user.is_superuser,
    })


def user_portal_entry(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.profile.user_type == 'admin':
            messages.success(request, "Admin session detected. Opening admin dashboard.")
            return redirect('/admin-dashboard/')
        return redirect('/dashboard/')
    return redirect('/login/?next=/dashboard/')


def admin_portal_entry(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.profile.user_type == 'admin':
            return redirect('/admin-dashboard/')
        logout(request)
        messages.error(request, "Admin portal requires an admin account. Please login with admin credentials.")
        return redirect('/login/?next=/admin-dashboard/')
    return redirect('/login/?next=/admin-dashboard/')


# ======================
# REGISTER
# ======================
def register_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')
        if user_type not in ('client', 'lawyer'):
            user_type = 'client'

        gender = request.POST.get('gender')
        birthdate = request.POST.get('birthdate')
        profession = request.POST.get('profession')
        specialization = request.POST.get('specialization')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('/register/')

        if birthdate:
            try:
                birthdate = date.fromisoformat(birthdate)
            except ValueError:
                birthdate = None

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        profile = user.profile
        profile.user_type = user_type
        profile.gender = gender
        profile.birthdate = birthdate
        profile.profession = profession
        if user_type == 'lawyer' and specialization:
            profile.specialization = specialization
        profile.save()

        append_user_to_excel(user, password=password)

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
        next_url = request.POST.get('next') or request.GET.get('next') or '/dashboard/'

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            if next_url == '/admin-dashboard/' and not (user.is_superuser or user.profile.user_type == 'admin'):
                logout(request)
                messages.error(request, "That account is not allowed to access the admin portal.")
                return redirect('/login/?next=/admin-dashboard/')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid credentials")

    return render(request, 'login.html', {
        'next': request.GET.get('next', '/dashboard/')
    })


# ======================
# LOGOUT
# ======================
def logout_view(request):
    logout(request)
    return redirect('/')


@login_required
@user_passes_test(lambda user: user.is_superuser)
def sync_users_from_excel_view(request):
    result = sync_users_from_excel()
    messages.success(request, f"Excel sync complete. Created {result['created']}, skipped {result['skipped']}.")
    if result['errors']:
        messages.error(request, "Excel sync completed with some errors. Check server logs for details.")
    return redirect('/')


# ======================
# DASHBOARD
# ======================
@login_required
def dashboard_view(request):

    profile = request.user.profile

    if profile.user_type == 'lawyer':
        appointments = Appointment.objects.filter(lawyer=request.user)
    elif profile.user_type == 'admin':
        appointments = Appointment.objects.all().order_by('-created_at')
    else:
        appointments = Appointment.objects.filter(client=request.user)

    stats = {
        'total': appointments.count(),
        'pending': appointments.filter(status='pending').count(),
        'accepted': appointments.filter(status='accepted').count(),
        'rejected': appointments.filter(status='rejected').count(),
    }

    return render(request, 'dashboard.html', {
        'profile': profile,
        'appointments': appointments,
        **stats
    })


@login_required
def edit_profile_view(request):
    profile = request.user.profile

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.save()

        profile.gender = request.POST.get('gender', profile.gender)
        birthdate_value = request.POST.get('birthdate')
        if birthdate_value:
            try:
                profile.birthdate = date.fromisoformat(birthdate_value)
            except ValueError:
                pass
        profile.profession = request.POST.get('profession', profile.profession)
        profile.bio = request.POST.get('bio', profile.bio)
        if profile.user_type == 'lawyer':
            profile.specialization = request.POST.get('specialization', profile.specialization)
            profile.experience = request.POST.get('experience') or profile.experience
            profile.consultation_fee = request.POST.get('consultation_fee') or profile.consultation_fee
        profile.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('/dashboard/')

    return render(request, 'edit_profile.html', {
        'profile': profile
    })


@login_required
def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.user.is_superuser or appointment.client == request.user or appointment.lawyer == request.user:
        appointment.delete()
        messages.success(request, 'Appointment deleted successfully.')
    else:
        messages.error(request, 'You are not authorized to delete this appointment.')

    if request.user.is_superuser:
        return redirect('/admin/manage-appointments/')
    return redirect('/dashboard/')


# ======================
# LAWYER LIST
# ======================
@login_required
def lawyer_list_view(request):

    query = request.GET.get('q')
    recommendation_items = recommend_lawyers(query or "")
    lawyers = [item['profile'] for item in recommendation_items]
    query_analysis = classify_legal_issue(query or "") if query else None

    return render(request, 'lawyers.html', {
        'lawyers': lawyers,
        'query': query,
        'recommendation_items': recommendation_items,
        'query_analysis': query_analysis,
    })


@login_required
def legal_triage_view(request):
    report = None
    issue_text = ""

    if request.method == "POST":
        issue_text = request.POST.get("issue", "").strip()
        if issue_text:
            report = build_triage_report(issue_text, limit=5)
        else:
            messages.error(request, "Please describe your legal issue for triage.")

    return render(request, "legal_triage.html", {
        "report": report,
        "issue_text": issue_text,
    })


# ======================
# BOOK APPOINTMENT
# ======================
@login_required
def book_appointment_view(request, lawyer_id):

    if request.user.profile.user_type == 'admin':
        messages.error(request, "Admin users should manage appointments from the Admin Dashboard.")
        return redirect('/admin-dashboard/')

    lawyer_profile = get_object_or_404(Profile, id=lawyer_id, user_type='lawyer')

    if request.method == 'POST':
        issue_text = request.POST.get('message')
        appointment = Appointment.objects.create(
            client=request.user,
            lawyer=lawyer_profile.user,
            message=issue_text,
            appointment_date=request.POST.get('date'),
            appointment_time=request.POST.get('time'),
            mobile_number=request.POST.get('mobile_number')
        )

        messages.success(request, "Appointment booked. You can share it on WhatsApp.")
        return redirect(f'/appointment/{appointment.id}/confirmation/')

    return render(request, 'book_appointment.html', {
        'lawyer': lawyer_profile,
        'today': date.today().isoformat(),
        'case_guidance': build_case_guidance(request.GET.get('issue', '')),
    })


# ======================
# ACCEPT / REJECT
# ======================
@login_required
def accept_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.status = 'accepted'
    if not appointment.meeting_link:
        appointment.meeting_link = f"https://meet.jit.si/legalconnect-{appointment.id}"
    appointment.save()

    if not hasattr(appointment, 'invoice'):
        Invoice.objects.create(
            appointment=appointment,
            invoice_number=f"INV{appointment.id:05d}",
            amount=getattr(appointment.lawyer.profile, 'consultation_fee', 0) or 0,
            due_date=timezone.now().date()
        )

    messages.success(request, "Appointment accepted and meeting link generated.")
    return redirect('/dashboard/')


@login_required
def reject_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.status = 'rejected'
    appointment.save()
    return redirect('/dashboard/')


@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if appointment.client != request.user:
        return redirect('/dashboard/')
    appointment.status = 'cancelled'
    appointment.save()
    messages.success(request, "Appointment cancelled.")
    return redirect('/dashboard/')


@login_required
def request_reschedule(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if appointment.client != request.user:
        return redirect('/dashboard/')

    if request.method == 'POST':
        appointment.reschedule_request_date = request.POST.get('new_date')
        appointment.reschedule_request_time = request.POST.get('new_time')
        appointment.reschedule_request_message = request.POST.get('reason')
        appointment.reschedule_status = 'requested'
        appointment.save()
        messages.success(request, "Reschedule request sent to the lawyer.")
        return redirect('/dashboard/')

    return render(request, 'request_reschedule.html', {
        'appointment': appointment,
        'today': date.today().isoformat()
    })


@login_required
def review_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if appointment.client != request.user:
        return redirect('/dashboard/')

    if request.method == 'POST':
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment')
        Review.objects.update_or_create(
            appointment=appointment,
            defaults={
                'user': request.user,
                'lawyer': appointment.lawyer,
                'rating': rating,
                'comment': comment,
            }
        )
        messages.success(request, "Thank you for the review.")
        return redirect('/dashboard/')

    return render(request, 'review_appointment.html', {
        'appointment': appointment
    })


@login_required
def upload_document(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.user not in [appointment.client, appointment.lawyer]:
        return redirect('/dashboard/')

    if request.method == 'POST' and request.FILES.get('document'):
        AppointmentDocument.objects.create(
            appointment=appointment,
            file=request.FILES['document'],
            title=request.POST.get('title', 'Uploaded document')
        )
        messages.success(request, "Document uploaded successfully.")
        return redirect(f'/appointment/{appointment.id}/confirmation/')

    return render(request, 'upload_document.html', {
        'appointment': appointment
    })


@login_required
def invoice_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    invoice = getattr(appointment, 'invoice', None)
    if not invoice:
        messages.error(request, "Invoice not found.")
        return redirect('/dashboard/')

    return render(request, 'invoice.html', {
        'invoice': invoice,
        'appointment': appointment,
    })


@login_required
def admin_create_user(request):
    if not request.user.is_superuser:
        return redirect('/dashboard/')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        user_type = request.POST.get('user_type')
        specialization = request.POST.get('specialization', '')
        experience = request.POST.get('experience', 0)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            profile = user.profile
            profile.user_type = user_type
            if specialization:
                profile.specialization = specialization
            if experience:
                try:
                    profile.experience = int(experience)
                except (ValueError, TypeError):
                    profile.experience = 0
            profile.save()

            append_user_to_excel(user, password=password)
            messages.success(request, f"{user_type.title()} {username} created successfully.")
            return redirect('/admin/create-user/')

    return render(request, 'admin_create_user.html')


@login_required
def admin_create_lawyer(request):
    if not request.user.is_superuser:
        return redirect('/dashboard/')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        specialization = request.POST.get('specialization', '')
        experience = request.POST.get('experience', 0)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            profile = user.profile
            profile.user_type = 'lawyer'
            if specialization:
                profile.specialization = specialization
            if experience:
                try:
                    profile.experience = int(experience)
                except (ValueError, TypeError):
                    profile.experience = 0
            profile.save()

            append_user_to_excel(user, password=password)
            messages.success(request, f"Lawyer {username} created successfully.")
            return redirect('/admin/create-lawyer/')

    return render(request, 'admin_create_user.html', {
        'page_title': 'Create New Lawyer',
        'submit_label': 'Create Lawyer',
        'fixed_user_type': 'lawyer',
        'hide_user_type': True,
    })


@login_required
def admin_assign_lawyers(request):
    if not request.user.is_superuser:
        return redirect('/dashboard/')

    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        lawyer_id = request.POST.get('lawyer_id')
        if appointment_id and lawyer_id:
            appointment = get_object_or_404(Appointment, id=appointment_id)
            lawyer = get_object_or_404(User, id=lawyer_id, profile__user_type='lawyer')
            appointment.lawyer = lawyer
            if appointment.status == 'pending':
                appointment.status = 'accepted'
            appointment.save()
            messages.success(request, f"Lawyer assigned to appointment #{appointment.id}.")
            return redirect('/admin/assign-lawyers/')

    appointments = Appointment.objects.filter(status='pending').order_by('-created_at')
    lawyers = User.objects.filter(profile__user_type='lawyer')

    return render(request, 'admin_assign_lawyers.html', {
        'appointments': appointments,
        'lawyers': lawyers,
    })


@login_required
def admin_manage_appointments(request):
    if not request.user.is_superuser:
        return redirect('/dashboard/')

    appointments = Appointment.objects.all().order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')
        appointment_id = request.POST.get('appointment_id')

        if action and appointment_id:
            appointment = get_object_or_404(Appointment, id=appointment_id)

            if action == 'accept':
                appointment.status = 'accepted'
                if not appointment.meeting_link:
                    appointment.meeting_link = f"https://meet.jit.si/legalconnect-{appointment.id}"
                appointment.save()
                if not hasattr(appointment, 'invoice'):
                    Invoice.objects.create(
                        appointment=appointment,
                        invoice_number=f"INV{appointment.id:05d}",
                        amount=getattr(appointment.lawyer.profile, 'consultation_fee', 0) or 0,
                        due_date=timezone.now().date()
                    )
                messages.success(request, f"Appointment #{appointment.id} accepted.")
            elif action == 'reject':
                appointment.status = 'rejected'
                appointment.save()
                messages.success(request, f"Appointment #{appointment.id} rejected.")
            elif action == 'assign_lawyer':
                lawyer_id = request.POST.get('lawyer_id')
                if lawyer_id:
                    lawyer = get_object_or_404(User, id=lawyer_id, profile__user_type='lawyer')
                    appointment.lawyer = lawyer
                    appointment.save()
                    messages.success(request, f"Lawyer assigned to appointment #{appointment.id}.")
            elif action == 'reschedule':
                new_date = request.POST.get('new_date')
                new_time = request.POST.get('new_time')
                if new_date and new_time:
                    appointment.appointment_date = new_date
                    appointment.appointment_time = new_time
                    if appointment.status != 'accepted':
                        appointment.status = 'accepted'
                    appointment.save()
                    messages.success(request, f"Appointment #{appointment.id} rescheduled.")
            elif action == 'delete':
                appointment.delete()
                messages.success(request, f"Appointment #{appointment_id} deleted.")

        return redirect('/admin/manage-appointments/')

    lawyers = User.objects.filter(profile__user_type='lawyer')
    status_counts = {
        'pending': appointments.filter(status='pending').count(),
        'accepted': appointments.filter(status='accepted').count(),
        'rejected': appointments.filter(status='rejected').count(),
        'cancelled': appointments.filter(status='cancelled').count(),
    }

    return render(request, 'admin_manage_appointments.html', {
        'appointments': appointments,
        'lawyers': lawyers,
        'status_counts': status_counts,
    })


@login_required
def admin_dashboard_view(request):
    if not request.user.is_superuser:
        return redirect('/dashboard/')

    total_users = User.objects.count()
    lawyer_count = Profile.objects.filter(user_type='lawyer').count()
    client_count = Profile.objects.filter(user_type='client').count()
    total_appointments = Appointment.objects.count()
    latest_appointments = Appointment.objects.order_by('-created_at')[:10]
    recent_reviews = Review.objects.order_by('-created_at')[:8]
    total_invoices = Invoice.objects.count()
    paid_invoices = Invoice.objects.filter(status='paid').count()

    # Real-time analytics
    booking_insights = summarize_booking_data()

    # Additional analytics
    today_appointments = Appointment.objects.filter(appointment_date=date.today()).count()
    this_week_appointments = Appointment.objects.filter(
        appointment_date__gte=date.today() - timedelta(days=7)
    ).count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    accepted_appointments = Appointment.objects.filter(status='accepted').count()

    return render(request, 'admin_dashboard.html', {
        'total_users': total_users,
        'lawyer_count': lawyer_count,
        'client_count': client_count,
        'total_appointments': total_appointments,
        'latest_appointments': latest_appointments,
        'recent_reviews': recent_reviews,
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'booking_insights': booking_insights,
        'today_appointments': today_appointments,
        'this_week_appointments': this_week_appointments,
        'pending_appointments': pending_appointments,
        'accepted_appointments': accepted_appointments,
    })


@login_required
def blog_list_view(request):
    posts = BlogPost.objects.filter(is_published=True).order_by('-published_at')
    return render(request, 'blog_list.html', {
        'posts': posts
    })


@login_required
def blog_detail_view(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, 'blog_detail.html', {
        'post': post
    })


@login_required
def appointment_chat_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.user not in [appointment.client, appointment.lawyer]:
        return redirect('/dashboard/')

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            receiver = appointment.lawyer if request.user == appointment.client else appointment.client
            ChatMessage.objects.create(
                appointment=appointment,
                sender=request.user,
                receiver=receiver,
                message=message
            )
            return redirect(f'/appointment/{appointment.id}/chat/')

    messages = ChatMessage.objects.filter(appointment=appointment).order_by('created_at')
    return render(request, 'appointment_chat.html', {
        'appointment': appointment,
        'messages': messages,
    })


@login_required
def appointment_chat_messages(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.user not in [appointment.client, appointment.lawyer]:
        return JsonResponse({'messages': []})

    messages = ChatMessage.objects.filter(appointment=appointment).order_by('created_at')
    return JsonResponse({
        'messages': [
            {'sender': msg.sender.username, 'message': msg.message, 'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}
            for msg in messages
        ]
    })


@login_required
def lawyer_availability_view(request):
    profile = request.user.profile
    if profile.user_type != 'lawyer':
        return redirect('/dashboard/')

    if request.method == 'POST':
        AvailabilitySlot.objects.filter(lawyer=profile).delete()
        for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
            start = request.POST.get(f'{day}_start')
            end = request.POST.get(f'{day}_end')
            if start and end:
                AvailabilitySlot.objects.create(
                    lawyer=profile,
                    day=day,
                    start_time=start,
                    end_time=end,
                    is_active=True
                )
        messages.success(request, "Availability updated.")
        return redirect('/lawyer-availability/')

    slots = AvailabilitySlot.objects.filter(lawyer=profile)
    return render(request, 'lawyer_availability.html', {
        'slots': slots,
        'profile': profile,
        'days': ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
    })


@login_required
def appointment_confirmation_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if appointment.client != request.user:
        return redirect('/dashboard/')

    if request.method == 'POST':
        mobile_number = request.POST.get('mobile_number', '').strip()
        if mobile_number:
            appointment.mobile_number = mobile_number
            appointment.save()
            messages.success(request, "Mobile number added! You can now share on WhatsApp.")
            return redirect(f'/appointment/{appointment.id}/confirmation/')

    return render(request, 'appointment_confirmation.html', {
        'appointment': appointment,
        'lawyer': appointment.lawyer.profile,
        'whatsapp_link': appointment.whatsapp_link,
    })


@login_required
def appointment_receipt_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.user not in [appointment.client, appointment.lawyer] and not request.user.is_superuser:
        return redirect('/dashboard/')

    lawyer_profile = appointment.lawyer.profile
    receipt_text = "\n".join([
        "LegalConnect Booking Receipt",
        f"Receipt No: LC-RCPT-{appointment.id:05d}",
        f"Booking Ref: LC-{appointment.id:05d}",
        f"Client: {appointment.client.get_full_name() or appointment.client.username}",
        f"Lawyer: {appointment.lawyer.get_full_name() or appointment.lawyer.username}",
        f"Specialization: {lawyer_profile.specialization or 'General Legal'}",
        f"Date: {appointment.appointment_date.strftime('%d %B %Y')}",
        f"Time: {appointment.appointment_time.strftime('%I:%M %p')}",
        f"Status: {appointment.status.title()}",
        f"Consultation Fee: {lawyer_profile.display_fee}",
        f"Case Summary: {appointment.message or 'N/A'}",
    ])
    whatsapp_receipt_link = None
    if appointment.mobile_number:
        phone = appointment.mobile_number.replace('+', '').replace('-', '').replace(' ', '')
        whatsapp_receipt_link = f"https://wa.me/{phone}?text={urllib.parse.quote(receipt_text)}"

    return render(request, 'appointment_receipt.html', {
        'appointment': appointment,
        'lawyer': lawyer_profile,
        'receipt_number': f"LC-RCPT-{appointment.id:05d}",
        'booking_reference': f"LC-{appointment.id:05d}",
        'whatsapp_receipt_link': whatsapp_receipt_link,
    })


@login_required
def whatsapp_share_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if appointment.client != request.user or not appointment.whatsapp_link:
        return redirect('/dashboard/')

    return redirect(appointment.whatsapp_link)


# ======================
# AI ASSISTANT (FINAL FIXED)
# ======================
@login_required
def legal_ai_view(request):

    if request.method == "POST":
        selected_topic = request.POST.get("topic")
        user_message = request.POST.get("problem", "").strip()
        knowledge = None

        if selected_topic:
            knowledge = get_knowledge(selected_topic)
            question_text = next((topic['title'] for topic in get_topics() if topic['id'] == selected_topic), selected_topic)
        else:
            question_text = user_message
            intent = detect_intent(user_message or "")
            if intent:
                knowledge = get_knowledge(intent)

        if knowledge:
            ai_response = "".join([
                f"{knowledge.get('title', 'Legal Guidance')}\n\n",
                f"{knowledge.get('advice')}\n\n",
                "Steps you can follow:\n",
                "\n".join([f"{idx + 1}. {step}" for idx, step in enumerate(knowledge.get('steps', []))]),
                "\n\n",
                "Helpful links:\n",
                "\n".join(knowledge.get('links', [])) if knowledge.get('links') else "No direct link available. Use official portals.",
            ])
        else:
            report = build_triage_report(user_message, limit=3)
            analysis = report['analysis']
            recommended = report['recommended_lawyers']
            lawyer_lines = [
                f"- {item['profile'].user.get_full_name() or item['profile'].user.username} "
                f"({item['profile'].specialization or 'General Legal'}) - Match score {item['score']}%"
                for item in recommended
            ]
            ai_response = "\n".join([
                "LegalConnect case-intake analysis",
                "",
                f"Detected category: {analysis['category']}",
                f"Urgency level: {analysis['urgency']}",
                f"Confidence: {analysis['confidence']}%",
                f"Complexity: {report['complexity']['label']} ({report['complexity']['score']}/100)",
                f"Risk score: {report['risk_score']}/100 - {report['risk_label']}",
                f"Recommended response window: {report['priority_window']}",
                "",
                "Suggested next steps:",
                *[f"{idx + 1}. {step}" for idx, step in enumerate(report['next_actions'])],
                "",
                "Documents to keep ready:",
                *[f"- {document}" for document in report['documents']],
                "",
                "Recommended lawyers:",
                *(lawyer_lines or ["- No lawyer profiles are available yet."]),
                "",
                report['disclaimer'],
            ])

        AIChat.objects.create(
            user=request.user,
            question=question_text,
            answer=ai_response
        )

        return redirect('legal_ai')

    chat_history = AIChat.objects.filter(user=request.user).order_by('-created_at')
    faq_topics = get_topics()

    return render(request, "legal_ai.html", {
        "chat_history": chat_history,
        "faq_topics": faq_topics,
    })


@login_required
def ai_booking_chat_view(request):
    """Interactive AI booking chat with predefined options"""

    # Get or create conversation
    conversation, created = AIConversation.objects.get_or_create(
        user=request.user,
        defaults={'state': 'welcome'}
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "reset":
            conversation.reset()
            return redirect('ai_booking_chat')

        elif action == "select_option":
            option_type = request.POST.get("option_type")
            option_id = request.POST.get("option_id")

            if option_type == "category":
                conversation.state = 'lawyer_selection'
                conversation.selected_category = option_id
                conversation.save()

            elif option_type == "lawyer":
                conversation.state = 'date_selection'
                conversation.selected_lawyer_id = int(option_id)
                conversation.save()

            elif option_type == "date":
                from datetime import datetime
                conversation.state = 'time_selection'
                conversation.selected_date = datetime.fromisoformat(option_id).date()
                conversation.save()

            elif option_type == "time":
                from datetime import datetime
                conversation.state = 'confirmation'
                conversation.selected_time = datetime.strptime(option_id, '%H:%M').time()
                conversation.save()

            elif option_type == "confirm":
                # Handle confirmation response
                if option_id == 'yes':
                    # Create the appointment
                    try:
                        lawyer_profile = Profile.objects.get(id=conversation.selected_lawyer_id, user_type='lawyer')

                        appointment = Appointment.objects.create(
                            client=request.user,
                            lawyer=lawyer_profile.user,
                            appointment_date=conversation.selected_date,
                            appointment_time=conversation.selected_time,
                            status='pending'
                        )

                        conversation.state = 'completed'
                        conversation.save()

                        messages.success(request, f"Appointment booked successfully with {lawyer_profile.user.first_name} {lawyer_profile.user.last_name}!")
                        return redirect(f'/appointment/{appointment.id}/confirmation/')

                    except Exception as e:
                        messages.error(request, "Failed to book appointment. Please try again.")
                        conversation.reset()
                elif option_id == 'no':
                    # Cancel and go back to lawyer selection
                    conversation.state = 'lawyer_selection'
                    conversation.selected_date = None
                    conversation.selected_time = None
                    conversation.save()

        return redirect('ai_booking_chat')

    # Get current options
    current_options = conversation.get_next_options()

    # Get conversation messages
    messages_list = []

    if conversation.state == 'welcome':
        messages_list.append({
            'type': 'ai',
            'content': "Welcome to LegalConnect AI Booking Assistant.\n\nI can help you book a consultation with a qualified lawyer. Let's get started.",
            'options': current_options
        })

    elif conversation.state == 'lawyer_selection':
        category_names = {
            'criminal': 'Criminal Law',
            'family': 'Family Law',
            'corporate': 'Corporate Law',
            'property': 'Property Law',
            'other': 'General Legal'
        }
        category_name = category_names.get(conversation.selected_category, conversation.selected_category)

        messages_list.extend([
            {
                'type': 'user',
                'content': f"I need help with {category_name}"
            },
            {
                'type': 'ai',
                'content': f"Great! I found lawyers specializing in {category_name}. Please select a lawyer:",
                'options': current_options
            }
        ])

    elif conversation.state == 'date_selection':
        lawyer = Profile.objects.get(id=conversation.selected_lawyer_id)
        messages_list.extend([
            {
                'type': 'user',
                'content': f"I selected {lawyer.user.first_name} {lawyer.user.last_name}"
            },
            {
                'type': 'ai',
                'content': f"Perfect! Now let's choose a convenient date for your consultation with {lawyer.user.first_name}:",
                'options': current_options
            }
        ])

    elif conversation.state == 'time_selection':
        messages_list.extend([
            {
                'type': 'user',
                'content': f"I selected {conversation.selected_date.strftime('%A, %B %d')}"
            },
            {
                'type': 'ai',
                'content': "Now please choose a time slot:",
                'options': current_options
            }
        ])

    elif conversation.state == 'confirmation':
        lawyer = Profile.objects.get(id=conversation.selected_lawyer_id)
        messages_list.extend([
            {
                'type': 'user',
                'content': f"I selected {conversation.selected_time.strftime('%I:%M %p')}"
            },
            {
                'type': 'ai',
                'content': f"Perfect! Here's a summary of your appointment:\n\nDate: {conversation.selected_date.strftime('%A, %B %d, %Y')}\nTime: {conversation.selected_time.strftime('%I:%M %p')}\nLawyer: {lawyer.user.first_name} {lawyer.user.last_name}\nSpecialization: {lawyer.specialization or 'General Legal'}\n\nWould you like to confirm this appointment?",
                'options': current_options
            }
        ])

    elif conversation.state == 'completed':
        messages_list.append({
            'type': 'ai',
            'content': "Your appointment has been successfully booked. You can share the appointment details on WhatsApp from the confirmation page.",
            'options': [{'text': 'Book Another Appointment', 'action': 'reset'}]
        })

    return render(request, 'ai_booking_chat.html', {
        'conversation': conversation,
        'chat_messages': messages_list,
        'current_options': current_options,
    })


@login_required
def lawyer_detail_view(request, lawyer_id):

    lawyer = get_object_or_404(Profile, id=lawyer_id, user_type='lawyer')

    return render(request, 'lawyer_detail.html', {
        'lawyer': lawyer
    })
