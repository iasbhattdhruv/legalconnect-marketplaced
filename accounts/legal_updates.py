from datetime import datetime, timedelta


def get_latest_legal_updates():
    now = datetime.now()
    updates = [
        {
            'headline': 'Supreme Court affirms consumer digital rights',
            'description': 'A recent bench decision clarified the responsibilities of online marketplaces for defective goods and digital purchases.',
            'source': 'Supreme Court of India',
            'tag': 'Consumer Rights',
            'time_ago': '1 hour ago',
        },
        {
            'headline': 'New Aadhaar update window introduced',
            'description': 'UIDAI announced extended timelines for Aadhaar demographic updates and address corrections online.',
            'source': 'UIDAI',
            'tag': 'Aadhaar',
            'time_ago': '3 hours ago',
        },
        {
            'headline': 'Delhi court orders fast-track hearing for landlord disputes',
            'description': 'Landlord-tenant disputes in the national capital are now eligible for faster resolution under a new judicial directive.',
            'source': 'Delhi High Court',
            'tag': 'Property Law',
            'time_ago': 'Today',
        },
        {
            'headline': 'Government releases updated consumer protection guidelines',
            'description': 'New advisory covers online refunds, false advertising, and complaint escalation for Indian buyers.',
            'source': 'Ministry of Consumer Affairs',
            'tag': 'Consumer Law',
            'time_ago': 'Yesterday',
        },
    ]

    return updates
