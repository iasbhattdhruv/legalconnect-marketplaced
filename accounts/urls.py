from django.urls import path
from .views import *

urlpatterns = [
    path('', home_view),
    path('register/', register_view),
    path('login/', login_view),
    path('logout/', logout_view),
    path('dashboard/', dashboard_view),

    path('lawyers/', lawyer_list_view),
    path('lawyers/<int:lawyer_id>/', lawyer_detail_view),

    path('book/<int:lawyer_id>/', book_appointment_view),

    path('appointment/<int:appointment_id>/accept/', accept_appointment),
    path('appointment/<int:appointment_id>/reject/', reject_appointment),

    path('appointment/cancel/<int:appointment_id>/', cancel_appointment_view),
    path('appointment/add-link/<int:appointment_id>/', add_meeting_link_view),
    path('legal-ai/', legal_ai_view),
]