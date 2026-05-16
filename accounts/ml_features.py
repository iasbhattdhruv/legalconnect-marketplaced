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

URGENCY_SIGNAL_GROUPS = {
    "Immediate legal process": [
        "summon", "summons", "court date", "hearing", "warrant", "fir", "police called",
        "legal notice", "notice received", "arrest", "bail", "custody"
    ],
    "Personal safety": [
        "threat", "threatening", "violence", "harassment", "blackmail", "abuse", "stalking",
        "unsafe", "hit me", "assault", "domestic violence"
    ],
    "Time pressure": [
        "today", "tomorrow", "tonight", "within 24 hours", "immediately", "urgent",
        "deadline", "last date", "right now", "asap"
    ],
    "Housing or job loss": [
        "eviction", "throw me out", "forcing me to leave", "locked me out", "termination",
        "fired", "salary not paid", "notice period", "job loss"
    ],
    "Financial harm": [
        "money stolen", "fraud", "scam", "upi fraud", "bank account", "deposit not returned",
        "large amount", "loan", "cheque bounce", "payment stuck"
    ],
    "Evidence risk": [
        "deleted messages", "account hacked", "hacked", "evidence", "documents missing",
        "fake signature", "forged", "identity misused"
    ],
}

DOCUMENT_REQUIREMENTS = {
    "Criminal Law": [
        "FIR or complaint copy",
        "Police notice or summons, if received",
        "Identity proof",
        "Incident timeline with dates",
        "Photos, videos, chats, or witness details",
    ],
    "Family Law": [
        "Marriage certificate or proof of marriage",
        "Identity and address proofs",
        "Income proofs and bank statements",
        "Child-related documents, if custody is involved",
        "Past notices, chats, or settlement records",
    ],
    "Property Law": [
        "Sale deed, rent agreement, or ownership papers",
        "Payment receipts and bank transfer proofs",
        "Property tax or utility records",
        "Legal notices or society letters",
        "Photos, site details, and possession proof",
    ],
    "Corporate Law": [
        "Contracts, agreements, or purchase orders",
        "Invoices and payment records",
        "Company registration details",
        "Email or chat communication",
        "Compliance notices, if any",
    ],
    "Consumer Law": [
        "Invoice or bill",
        "Warranty card or service terms",
        "Complaint emails or ticket numbers",
        "Product photos or delivery proof",
        "Payment proof",
    ],
    "Employment Law": [
        "Offer letter and employment agreement",
        "Salary slips and bank statements",
        "Termination or warning letters",
        "Attendance or work records",
        "Email/chat communication with employer",
    ],
    "Cyber Law": [
        "Transaction IDs and bank messages",
        "Screenshots of chats, profiles, or websites",
        "Phone numbers, email IDs, or account handles",
        "Cyber complaint acknowledgement, if filed",
        "Bank freeze or dispute request proof",
    ],
    "General Legal": [
        "Identity proof",
        "Short written case summary",
        "All notices, emails, chats, and receipts",
        "Timeline of events",
    ],
}

NEXT_ACTIONS = {
    "Criminal Law": [
        "Book an urgent consultation if arrest, bail, or police notice is involved.",
        "Keep all police documents and communication in one folder.",
        "Avoid giving written statements without legal advice.",
    ],
    "Family Law": [
        "Prepare a clear timeline of marriage, dispute, and financial facts.",
        "Collect income and child-related documents before consultation.",
        "Discuss mediation, notice, and court filing options with the lawyer.",
    ],
    "Property Law": [
        "Verify ownership or tenancy documents before taking action.",
        "Preserve payment proof and written communication.",
        "Ask the lawyer whether a legal notice is the best first step.",
    ],
    "Corporate Law": [
        "Map the exact contract clause or payment obligation in dispute.",
        "Collect invoices, emails, and agreement versions.",
        "Discuss negotiation, legal notice, and compliance risk.",
    ],
    "Consumer Law": [
        "Raise a written complaint with the seller/service provider.",
        "Keep ticket number, invoice, and payment proof ready.",
        "Discuss consumer forum escalation if the issue is unresolved.",
    ],
    "Employment Law": [
        "Review notice period, salary dues, and termination clauses.",
        "Preserve written communication and salary records.",
        "Discuss a formal representation or legal notice.",
    ],
    "Cyber Law": [
        "Act fast: report to cyber portal and bank if money is involved.",
        "Do not delete messages, transaction logs, or screenshots.",
        "Consult a cyber-law specialist for evidence preservation.",
    ],
    "General Legal": [
        "Write a one-page summary with dates and people involved.",
        "Collect all supporting documents before booking.",
        "Use the recommendation score to choose a suitable lawyer.",
    ],
}

COMPLEXITY_KEYWORDS = [
    "court", "notice", "summon", "appeal", "multiple", "company", "property", "fraud",
    "police", "custody", "contract", "high court", "agreement", "eviction"
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

    urgency_reasons = []
    urgency_score = sum(1 for keyword in URGENT_KEYWORDS if keyword in text) * 12
    for group, phrases in URGENCY_SIGNAL_GROUPS.items():
        matches = [phrase for phrase in phrases if phrase in text]
        if matches:
            urgency_reasons.append({
                "signal": group,
                "evidence": matches[:3],
            })
            urgency_score += 18 + min(12, len(matches) * 4)

    if any(word in text for word in ["minor child", "child custody", "domestic violence", "arrest", "warrant"]):
        urgency_score += 18
    if any(word in text for word in ["today", "tomorrow", "tonight"]) and any(word in text for word in ["notice", "police", "eviction", "deadline", "hearing"]):
        urgency_score += 15

    if urgency_score >= 55:
        urgency = "High"
    elif urgency_score >= 22:
        urgency = "Medium"
    else:
        urgency = "Low"

    return {
        "category": category,
        "urgency": urgency,
        "confidence": min(95, 45 + score * 18 + min(20, urgency_score // 4)),
        "urgency_score": min(100, urgency_score),
        "urgency_reasons": urgency_reasons or [{
            "signal": "No strong urgency signal detected",
            "evidence": ["Routine consultation wording"],
        }],
    }


def score_case_complexity(text, analysis=None):
    text = (text or "").lower()
    analysis = analysis or classify_legal_issue(text)
    keyword_score = sum(1 for keyword in COMPLEXITY_KEYWORDS if keyword in text)
    length_score = min(20, len(text.split()) // 12)
    urgency_score = {"Low": 5, "Medium": 18, "High": 30}.get(analysis["urgency"], 5)
    category_score = 12 if analysis["category"] in ["Criminal Law", "Cyber Law", "Property Law"] else 7
    score = min(100, 20 + keyword_score * 8 + length_score + urgency_score + category_score)

    if score >= 75:
        label = "Complex"
    elif score >= 45:
        label = "Moderate"
    else:
        label = "Simple"

    return {
        "score": score,
        "label": label,
    }


def estimate_priority_window(analysis, complexity):
    if analysis["urgency"] == "High" or complexity["score"] >= 80:
        return "Same day"
    if analysis["urgency"] == "Medium" or complexity["score"] >= 55:
        return "24-48 hours"
    return "2-4 days"


def build_triage_report(text, limit=5):
    analysis = classify_legal_issue(text)
    complexity = score_case_complexity(text, analysis)
    category = analysis["category"]
    recommendations = recommend_lawyers(text, limit=limit)
    risk_score = min(
        100,
        round(
            complexity["score"] * 0.45
            + analysis["urgency_score"] * 0.45
            + (10 if category in ["Criminal Law", "Cyber Law"] else 5 if category in ["Property Law", "Employment Law"] else 0)
        ),
    )

    if risk_score >= 75:
        risk_label = "High Risk"
    elif risk_score >= 45:
        risk_label = "Needs Review"
    else:
        risk_label = "Standard"

    admin_flags = []
    if analysis["urgency"] == "High":
        admin_flags.append("Prioritize assignment because urgency is high.")
    if complexity["score"] >= 75:
        admin_flags.append("Route to an experienced lawyer because complexity is high.")
    if not recommendations:
        admin_flags.append("No matching lawyer found; admin should manually assign.")
    if category in ["Cyber Law", "Criminal Law"]:
        admin_flags.append("Evidence preservation is time-sensitive.")

    return {
        "summary": text,
        "analysis": analysis,
        "complexity": complexity,
        "risk_score": risk_score,
        "risk_label": risk_label,
        "urgency_reasons": analysis["urgency_reasons"],
        "priority_window": estimate_priority_window(analysis, complexity),
        "documents": DOCUMENT_REQUIREMENTS.get(category, DOCUMENT_REQUIREMENTS["General Legal"]),
        "next_actions": NEXT_ACTIONS.get(category, NEXT_ACTIONS["General Legal"]),
        "recommended_lawyers": recommendations,
        "admin_flags": admin_flags or ["Standard queue handling is suitable."],
        "disclaimer": "This triage report is decision support, not legal advice.",
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
    report = build_triage_report(text, limit=3)

    return {
        "analysis": report["analysis"],
        "steps": report["next_actions"],
        "documents": report["documents"],
        "complexity": report["complexity"],
        "risk_score": report["risk_score"],
        "priority_window": report["priority_window"],
        "disclaimer": report["disclaimer"],
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
