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

        profile = user.profile
        profile.user_type = user_type
        profile.gender = gender
        profile.birthdate = birthdate
        profile.profession = profession
        profile.save()

        append_user_to_excel(user, password=password)

        login(request, user)
        return redirect('/dashboard/')

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
                profile.experience_years = int(experience)
            profile.save()

            append_user_to_excel(user, password=password)
            messages.success(request, f"{user_type.title()} {username} created successfully.")
            return redirect('/admin/create-user/')

    return render(request, 'admin_create_user.html')


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
                appointment.status = 'confirmed'
                appointment.save()
                messages.success(request, f"Appointment #{appointment.id} confirmed.")
            elif action == 'reject':
                appointment.status = 'cancelled'
                appointment.save()
                messages.success(request, f"Appointment #{appointment.id} cancelled.")
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
                    appointment.status = 'rescheduled'
                    appointment.save()
                    messages.success(request, f"Appointment #{appointment.id} rescheduled.")

        return redirect('/admin/manage-appointments/')

    lawyers = User.objects.filter(profile__user_type='lawyer')

    return render(request, 'admin_manage_appointments.html', {
        'appointments': appointments,
        'lawyers': lawyers,
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
    today_appointments = Appointment.objects.filter(appointment_date=datetime.date.today()).count()
    this_week_appointments = Appointment.objects.filter(
        appointment_date__gte=datetime.date.today() - timedelta(days=7)
    ).count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    confirmed_appointments = Appointment.objects.filter(status='confirmed').count()

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
        'confirmed_appointments': confirmed_appointments,
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


def set_language_view(request, language_code):
    if language_code in ['en', 'hi']:
        request.session['language'] = language_code
    return redirect(request.META.get('HTTP_REFERER', '/'))


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
            ai_response = get_ai_response(user_message)

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

        return redirect('ai_booking_chat')

    # Get current options
    current_options = conversation.get_next_options()

    # Get conversation messages
    messages_list = []

    if conversation.state == 'welcome':
        messages_list.append({
            'type': 'ai',
            'content': "👋 Welcome to LegalConnect AI Booking Assistant!\n\nI can help you book a consultation with a qualified lawyer. Let's get started!",
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
                'content': f"📅 **Booking Summary**\n\n"
                          f"**Lawyer:** {lawyer.user.first_name} {lawyer.user.last_name}\n"
                          f"**Specialization:** {lawyer.specialization or 'General'}\n"
                          f"**Date:** {conversation.selected_date.strftime('%A, %B %d, %Y')}\n"
                          f"**Time:** {conversation.selected_time.strftime('%I:%M %p')}\n"
                          f"**Fee:** ₹{lawyer.consultation_fee or 'To be discussed'}\n\n"
                          f"Would you like to confirm this appointment?",
                'options': {
                    'type': 'confirmation',
                    'options': [
                        {'id': 'yes', 'label': '✅ Confirm Booking', 'type': 'primary'},
                        {'id': 'no', 'label': '❌ Start Over', 'type': 'secondary'}
                    ]
                }
            }
        ])

    elif conversation.state == 'completed':
        messages_list.append({
            'type': 'ai',
            'content': "🎉 Your appointment has been booked successfully! You can view it in your dashboard.",
            'options': None
        })

    return render(request, "ai_booking_chat.html", {
        "conversation": conversation,
        "messages": messages_list,
        "current_options": current_options
    })


@login_required
def lawyer_detail_view(request, lawyer_id):

    lawyer = get_object_or_404(Profile, id=lawyer_id, user_type='lawyer')

    return render(request, 'lawyer_detail.html', {
        'lawyer': lawyer
    })