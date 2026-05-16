def get_knowledge(intent):
    data = {
        "aadhaar_update": {
            "title": "Update Aadhaar Details",
            "advice": "You can update your Aadhaar details online or by visiting an Aadhaar Seva Kendra.",
            "steps": [
                "Visit the UIDAI portal at https://uidai.gov.in/.",
                "Choose the Aadhaar update option and authenticate with OTP.",
                "Upload the required documents and verify the information.",
                "Submit the request and note the URN for tracking.",
                "Check the update status on UIDAI after a few days."
            ],
            "links": ["https://uidai.gov.in/"],
            "lawyer_type": None,
        },
        "pan_update": {
            "title": "Correct PAN Details",
            "advice": "PAN corrections can be completed using the official NSDL or UTIITSL portal.",
            "steps": [
                "Visit the official PAN correction page.",
                "Fill in the required fields and upload supporting documents.",
                "Pay the correction fee and submit the application.",
                "Keep the acknowledgement receipt for future tracking.",
                "Track application status using the PAN acknowledgement number."
            ],
            "links": ["https://www.onlineservices.nsdl.com/"],
            "lawyer_type": None,
        },
        "pan_card": {
            "title": "Correct PAN Details",
            "advice": "PAN corrections can be completed using the official NSDL or UTIITSL portal.",
            "steps": [
                "Visit the official PAN correction page.",
                "Fill in the required fields and upload supporting documents.",
                "Pay the correction fee and submit the application.",
                "Keep the acknowledgement receipt for future tracking.",
                "Track application status using the PAN acknowledgement number."
            ],
            "links": ["https://www.onlineservices.nsdl.com/"],
            "lawyer_type": None,
        },
        "vehicle_rc": {
            "title": "Update or Replace Vehicle RC",
            "advice": "Vehicle RC changes and duplicate RC requests are processed through the Parivahan portal.",
            "steps": [
                "Visit https://parivahan.gov.in/ and choose vehicle services.",
                "Select the appropriate option for RC correction or duplicate RC.",
                "Provide vehicle and owner details, then upload proof documents.",
                "Pay the fees and submit the application.",
                "Track the request status online using the application number."
            ],
            "links": ["https://parivahan.gov.in/"],
            "lawyer_type": None,
        },
        "divorce": {
            "title": "File for Divorce",
            "advice": "Divorce cases are handled under family law and require a court petition and documentation.",
            "steps": [
                "Consult a family law attorney to determine the right petition type.",
                "Collect marriage proof, identity documents, and any evidence of mutual consent.",
                "File the divorce petition in the family court with jurisdiction.",
                "Attend court hearings and mediation sessions as scheduled.",
                "Receive the divorce decree once the court issues the final order."
            ],
            "links": [],
            "lawyer_type": "divorce",
        },
        "property": {
            "title": "Resolve Property Disputes",
            "advice": "Property disputes often begin with a legal notice and may move to civil court if settlement fails.",
            "steps": [
                "Gather sale deeds, title documents, and ownership records.",
                "Consult a property lawyer to review the dispute and draft a legal notice.",
                "Send the notice and try to settle the matter outside court.",
                "If settlement fails, file a civil suit in the appropriate court.",
                "Attend hearings and present evidence for a judgement."
            ],
            "links": [],
            "lawyer_type": "property",
        },
        "property_dispute": {
            "title": "Resolve Property Disputes",
            "advice": "Property disputes often begin with a legal notice and may move to civil court if settlement fails.",
            "steps": [
                "Gather sale deeds, title documents, and ownership records.",
                "Consult a property lawyer to review the dispute and draft a legal notice.",
                "Send the notice and try to settle the matter outside court.",
                "If settlement fails, file a civil suit in the appropriate court.",
                "Attend hearings and present evidence for a judgement."
            ],
            "links": [],
            "lawyer_type": "property",
        },
        "cyber_crime": {
            "title": "Report Cyber Crime",
            "advice": "Cyber crime complaints can be registered through the Indian Cyber Crime portal.",
            "steps": [
                "Collect screenshots and copies of messages, emails, or transaction records.",
                "Visit the cyber crime reporting portal and fill out the complaint form.",
                "Upload supporting evidence and submit the complaint.",
                "Keep the incident number for tracking status.",
                "Consult a cyber law expert if your complaint needs escalation."
            ],
            "links": ["https://cybercrime.gov.in/"],
            "lawyer_type": "cyber crime",
        },
        "consumer_rights": {
            "title": "Protect Consumer Rights",
            "advice": "Indian consumers can file a complaint under the Consumer Protection Act for unfair trade or defective products.",
            "steps": [
                "Collect invoices, receipts, and proof of communication with the seller.",
                "Send a formal complaint to the seller or service provider first.",
                "If unresolved, file a complaint with the district consumer forum.",
                "Attend hearings and present documentary evidence.",
                "Follow the forum order until the matter is resolved."
            ],
            "links": [],
            "lawyer_type": "consumer disputes",
        },
        "employment_rights": {
            "title": "Understand Employment Rights",
            "advice": "Workplace disputes over salary, termination, or harassment are governed by labour and industrial laws.",
            "steps": [
                "Review your employment contract and company policy.",
                "Raise an internal grievance if one is available.",
                "Consult an employment lawyer for notice or termination issues.",
                "File a complaint with the labour commissioner or court if required.",
                "Keep clear records of all communication and document important dates."
            ],
            "links": [],
            "lawyer_type": "employment",
        },
    }
    return data.get(intent)


def get_topics():
    return [
        {
            'id': 'aadhaar_update',
            'title': 'Update Aadhaar details',
            'description': 'Correct your Aadhaar information step-by-step.',
        },
        {
            'id': 'pan_update',
            'title': 'Correct PAN details',
            'description': 'Fix PAN data errors quickly and legally.',
        },
        {
            'id': 'vehicle_rc',
            'title': 'Vehicle RC update',
            'description': 'Get guidance for RC correction and duplicate RC.',
        },
        {
            'id': 'divorce',
            'title': 'File for divorce',
            'description': 'Learn the practical stages for a divorce petition.',
        },
        {
            'id': 'property',
            'title': 'Property dispute help',
            'description': 'Find the right steps to resolve land or tenancy issues.',
        },
        {
            'id': 'consumer_rights',
            'title': 'Consumer rights',
            'description': 'Protect yourself from unfair trade practices.',
        },
        {
            'id': 'employment_rights',
            'title': 'Employment law',
            'description': 'Understand your workplace rights and remedies.',
        },
    ]
