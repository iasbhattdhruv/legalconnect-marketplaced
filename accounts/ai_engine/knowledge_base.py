def get_knowledge(intent):

    data = {

        "aadhaar_update": {
            "advice": "You can update your Aadhaar details online or by visiting an Aadhaar Seva Kendra.",
            "steps": [
                "Go to UIDAI official website",
                "Login using Aadhaar + OTP",
                "Select update option",
                "Upload required documents",
                "Pay fee if required"
            ],
            "links": [
                "https://uidai.gov.in/"
            ],
            "lawyer_type": None
        },

        "pan_update": {
            "advice": "You can update PAN details through NSDL or UTIITSL portal.",
            "steps": [
                "Visit NSDL website",
                "Fill correction form",
                "Upload documents",
                "Pay fees",
                "Track status online"
            ],
            "links": [
                "https://www.onlineservices.nsdl.com/"
            ],
            "lawyer_type": None
        },

        "vehicle_rc": {
            "advice": "RC related services can be handled through Parivahan portal.",
            "steps": [
                "Visit Parivahan website",
                "Select vehicle services",
                "Apply for duplicate RC",
                "Upload documents",
                "Pay fees"
            ],
            "links": [
                "https://parivahan.gov.in/"
            ],
            "lawyer_type": None
        },

        "divorce": {
            "advice": "You can file for divorce under Indian laws like Hindu Marriage Act or Special Marriage Act.",
            "steps": [
                "Consult a divorce lawyer",
                "Prepare legal documents",
                "File petition in family court",
                "Attend hearings",
                "Final decree issued by court"
            ],
            "links": [],
            "lawyer_type": "divorce"
        },

        "property": {
            "advice": "Property disputes require legal notice and possibly civil court action.",
            "steps": [
                "Consult property lawyer",
                "Send legal notice",
                "Attempt settlement",
                "File civil case if needed"
            ],
            "links": [],
            "lawyer_type": "property"
        }

    }

    return data.get(intent)