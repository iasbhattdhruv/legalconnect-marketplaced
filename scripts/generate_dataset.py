import random
from datetime import date, timedelta
from pathlib import Path
from openpyxl import Workbook

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = DATA_DIR / 'legal_booking_dataset.xlsx'

CATEGORIES = {
    'Criminal Law': ['FIR filing', 'Bail hearing', 'Court representation'],
    'Family Law': ['Divorce consultation', 'Child custody', 'Alimony review'],
    'Corporate Law': ['Business contract', 'Company formation', 'Compliance review'],
    'Property Law': ['Property dispute', 'Title search', 'Rental agreement'],
    'Civil Rights': ['Consumer complaint', 'Harassment case', 'Public interest'],
    'Immigration': ['Visa application', 'Immigration appeal', 'Residency support'],
    'Employment Law': ['Workplace disputes', 'Contract review', 'Termination advice'],
    'Intellectual Property': ['Trademark filing', 'Patent consultation', 'Copyright dispute']
}
LAWYERS = [
    ('Avni Mehta', 'Criminal Law'),
    ('Priya Singh', 'Family Law'),
    ('Rohit Sharma', 'Corporate Law'),
    ('Nisha Patel', 'Property Law'),
    ('Amit Gupta', 'Immigration'),
    ('Simran Kaur', 'Civil Rights'),
    ('Arjun Verma', 'Employment Law'),
    ('Neha Joshi', 'Intellectual Property'),
    ('Vikram Rao', 'Criminal Law'),
    ('Tanya Desai', 'Family Law'),
    ('Sahil Kapoor', 'Corporate Law'),
    ('Meera Nair', 'Property Law'),
    ('Karan Malhotra', 'Immigration'),
    ('Pooja Yadav', 'Civil Rights'),
    ('Himanshu Sinha', 'Employment Law'),
    ('Riya Bhatia', 'Intellectual Property'),
    ('Aditya Sen', 'Corporate Law'),
    ('Sana Khan', 'Family Law'),
    ('Rakesh Iyer', 'Criminal Law'),
    ('Megha Reddy', 'Property Law')
]
STATUS_CHOICES = ['Confirmed', 'Pending', 'Rejected', 'Cancelled']
CHANNELS = ['Web', 'AI Chat', 'Referral', 'Email']

wb = Workbook()
ws = wb.active
ws.title = 'Bookings'
headers = [
    'booking_id', 'username', 'legal_category', 'service_type', 'lawyer_id',
    'lawyer_name', 'lawyer_specialization', 'appointment_date', 'appointment_time',
    'booking_status', 'booking_channel', 'created_at'
]
ws.append(headers)

start_date = date(2024, 1, 1)
for i in range(1, 501):
    category = random.choice(list(CATEGORIES.keys()))
    service_type = random.choice(CATEGORIES[category])
    lawyer_name, lawyer_specialization = random.choice(LAWYERS)
    lawyer_id = 1000 + LAWYERS.index((lawyer_name, lawyer_specialization))
    appointment_date = start_date + timedelta(days=random.randint(0, 450))
    appointment_time = f"{random.randint(9, 16):02d}:{random.choice([0, 30]):02d}"
    status = random.choices(STATUS_CHOICES, [0.55, 0.25, 0.1, 0.1], k=1)[0]
    channel = random.choices(CHANNELS, [0.45, 0.3, 0.15, 0.1], k=1)[0]
    username = f'user{random.randint(1000, 9999)}'
    created_at = appointment_date - timedelta(days=random.randint(0, 30))

    ws.append([
        f'BK{i:04d}',
        username,
        category,
        service_type,
        lawyer_id,
        lawyer_name,
        lawyer_specialization,
        appointment_date.isoformat(),
        appointment_time,
        status,
        channel,
        created_at.isoformat()
    ])

wb.save(OUTPUT_FILE)
print(f'Generated dataset at {OUTPUT_FILE}')