from collections import Counter
from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone

from .models import Appointment, Profile, Review


LEGAL_CATEGORY_KEYWORDS = {
    "Criminal Law": [
        "fir", "bail", "arrest", "police", "criminal", "ipc", "jail", "complaint", "fraud", "assault"
    ],
    "Family Law": [
        "divorce", "custody", "maintenance", "marriage", "domestic", "wife", "husband", "child", "alimony"
    ],
    "Property Law": [
        "property", "land", "rent", "tenant", "landlord", "flat", "house", "registry", "ownership"
    ],
    "Corporate Law": [
        "company", "contract", "agreement", "startup", "business", "partnership", "compliance", "vendor"
    ],
    "Consumer Law": [
        "refund", "defective", "consumer", "warranty", "ecommerce", "online order", "service complaint"
    ],
    "Employment Law": [
        "salary", "termination", "job", "employee", "employer", "notice period", "workplace", "pf"
    ],
    "Cyber Law": [
        "cyber", "online fraud", "upi", "hacked", "otp", "social media", "privacy", "phishing"
    ],
}

URGENT_KEYWORDS = [
    "arrest", "bail", "police", "threat", "violence", "notice", "summon", "court date",
    "eviction", "fraud", "hacked", "deadline", "emergency"
]


def classify_legal_issue(text):
    """Return a practical local classification for a user's legal problem."""
    text = (text or "").lower()
    scores = {}
    for category, keywords in LEGAL_CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for keyword in keywords if keyword in text)

    category, score = max(scores.items(), key=lambda item: item[1])
    if score == 0:
        category = "General Legal"

    urgency_score = sum(1 for keyword in URGENT_KEYWORDS if keyword in text)
    if urgency_score >= 2:
        urgency = "High"
    elif urgency_score == 1:
        urgency = "Medium"
    else:
        urgency = "Low"

    return {
        "category": category,
        "urgency": urgency,
        "confidence": min(95, 45 + score * 18 + urgency_score * 5),
    }


def _rating_for_lawyer(user):
    aggregate = Review.objects.filter(lawyer=user).aggregate(avg_rating=Avg("rating"))
    return float(aggregate["avg_rating"] or 0)


def recommend_lawyers(query="", limit=None):
    """Score lawyers using specialization, experience, rating, fee, and workload."""
    analysis = classify_legal_issue(query)
    category = analysis["category"]
    lawyers = Profile.objects.filter(user_type="lawyer").select_related("user")
    recommendations = []

    for lawyer in lawyers:
        specialization = (lawyer.specialization or "").lower()
        category_match = category != "General Legal" and category.lower().replace(" law", "") in specialization
        text_match = query and (
            query.lower() in specialization
            or query.lower() in (lawyer.profession or "").lower()
            or query.lower() in lawyer.user.username.lower()
        )

        accepted_count = Appointment.objects.filter(lawyer=lawyer.user, status="accepted").count()
        pending_count = Appointment.objects.filter(lawyer=lawyer.user, status="pending").count()
        rating = _rating_for_lawyer(lawyer.user) or lawyer.rating

        score = 35
        if category_match:
            score += 28
        if text_match:
            score += 18
        score += min(15, (lawyer.experience or 0) * 1.5)
        score += min(12, rating * 2)
        score += max(0, 10 - pending_count * 2)
        if lawyer.consultation_fee and lawyer.consultation_fee <= 1500:
            score += 4

        recommendations.append({
            "profile": lawyer,
            "score": round(min(score, 100)),
            "analysis": analysis,
            "accepted_count": accepted_count,
            "pending_count": pending_count,
            "rating": round(rating, 1),
        })

    recommendations.sort(key=lambda item: item["score"], reverse=True)
    if query:
        filtered = [
            item for item in recommendations
            if item["score"] >= 55 or query.lower() in (item["profile"].specialization or "").lower()
        ]
        recommendations = filtered or recommendations

    return recommendations[:limit] if limit else recommendations


def appointment_risk(appointment):
    text_analysis = classify_legal_issue(appointment.message or "")
    now = timezone.now().date()
    days_left = (appointment.appointment_date - now).days if appointment.appointment_date else 99
    score = 10

    if text_analysis["urgency"] == "High":
        score += 35
    elif text_analysis["urgency"] == "Medium":
        score += 20
    if appointment.status == "pending":
        score += 25
    if days_left <= 1:
        score += 20
    if appointment.reschedule_status == "requested":
        score += 15

    return {
        "score": min(score, 100),
        "category": text_analysis["category"],
        "urgency": text_analysis["urgency"],
    }


def build_case_guidance(text):
    analysis = classify_legal_issue(text)
    category = analysis["category"]
    steps = {
        "Criminal Law": ["Preserve FIR/complaint copies.", "Write a clear timeline.", "Consult a criminal lawyer quickly."],
        "Family Law": ["Collect marriage and identity documents.", "List financial and custody facts.", "Discuss mediation and court options."],
        "Property Law": ["Collect ownership/rent papers.", "Verify registry and payment records.", "Prepare a notice or reply strategy."],
        "Corporate Law": ["Collect contracts and invoices.", "Identify breach/compliance points.", "Prepare negotiation or legal notice steps."],
        "Consumer Law": ["Save invoice and complaint proofs.", "Raise a written grievance.", "Escalate to consumer forum if unresolved."],
        "Employment Law": ["Save offer letter and salary records.", "Check notice-period clauses.", "Prepare a formal representation."],
        "Cyber Law": ["Freeze payment channels if needed.", "Save screenshots and transaction IDs.", "File cyber complaint quickly."],
    }.get(category, ["Write a clear summary.", "Collect all related documents.", "Book a consultation with a suitable lawyer."])

    return {
        "analysis": analysis,
        "steps": steps,
        "disclaimer": "This is general guidance, not a substitute for advice from a qualified lawyer.",
    }


def operational_insights():
    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    upcoming = Appointment.objects.filter(appointment_date__range=(today, next_week))
    risk_items = sorted(
        [{"appointment": apt, **appointment_risk(apt)} for apt in upcoming],
        key=lambda item: item["score"],
        reverse=True,
    )[:5]

    category_counter = Counter()
    for appointment in Appointment.objects.all():
        category_counter[classify_legal_issue(appointment.message or "")["category"]] += 1

    return {
        "high_risk_appointments": risk_items,
        "case_category_mix": [
            {"label": label, "count": count}
            for label, count in category_counter.most_common(6)
        ],
    }
