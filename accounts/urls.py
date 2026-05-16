from django.urls import path
from .views import *

urlpatterns = [
    path('', home_view),
    path('portal/user/', user_portal_entry, name='user_portal_entry'),
    path('portal/admin/', admin_portal_entry, name='admin_portal_entry'),
    path('register/', register_view),
    path('login/', login_view),
    path('logout/', logout_view),
    path('dashboard/', dashboard_view),
    path('profile/edit/', edit_profile_view, name='edit_profile'),
    path('appointment/<int:appointment_id>/delete/', delete_appointment, name='delete_appointment'),

    path('lawyers/', lawyer_list_view),
    path('lawyers/<int:lawyer_id>/', lawyer_detail_view),

    path('book/<int:lawyer_id>/', book_appointment_view),

    path('appointment/<int:appointment_id>/accept/', accept_appointment),
    path('appointment/<int:appointment_id>/reject/', reject_appointment),
    path('appointment/<int:appointment_id>/cancel/', cancel_appointment),
    path('appointment/<int:appointment_id>/reschedule/', request_reschedule),
    path('appointment/<int:appointment_id>/review/', review_appointment),
    path('appointment/<int:appointment_id>/upload-document/', upload_document),
    path('appointment/<int:appointment_id>/invoice/', invoice_view),
    path('appointment/<int:appointment_id>/receipt/', appointment_receipt_view, name='appointment_receipt'),
    path('appointment/<int:appointment_id>/chat/', appointment_chat_view),
    path('appointment/<int:appointment_id>/chat/messages/', appointment_chat_messages),

    path('admin-dashboard/', admin_dashboard_view),
    path('admin/manage-appointments/', admin_manage_appointments),
    path('admin/create-user/', admin_create_user),
    path('admin/create-lawyer/', admin_create_lawyer),
    path('admin/assign-lawyers/', admin_assign_lawyers),
    path('blog/', blog_list_view),
    path('blog/<slug:slug>/', blog_detail_view),
    path('lawyer-availability/', lawyer_availability_view),

    path('legal-ai/', legal_ai_view),
    path('legal-triage/', legal_triage_view, name='legal_triage'),
    path('ai-legal-assistant/', legal_ai_view, name='legal_ai'),
    path('ai-booking-chat/', ai_booking_chat_view, name='ai_booking_chat'),
    path('sync-users/', sync_users_from_excel_view, name='sync_users_from_excel'),
    path('appointment/<int:appointment_id>/confirmation/', appointment_confirmation_view, name='appointment_confirmation'),
    path('appointment/<int:appointment_id>/whatsapp/', whatsapp_share_view, name='whatsapp_share'),
]
