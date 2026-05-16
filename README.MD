# LegalConnect – Legal Consultation Marketplace

LegalConnect is a Django-based legal consultation marketplace where users can:

- Register & Login
- Browse verified lawyers
- Search by specialization
- Book consultation requests
- Admin approval system for lawyers
- Dashboard for clients

## Tech Stack
- Python
- Django
- SQLite
- Tailwind CSS
- Git & GitHub

## Features Implemented
- Custom Authentication
- Lawyer Listing & Filtering
- Appointment Booking
- Admin Lawyer Approval
- Professional UI Design
- Administrator and lawyer workflows for assignment, rescheduling, deletion, and profile management
- Advanced analytics for booking trends, top specializations, and forecasted demand
- **AI Legal Assistant** - Chat-based legal guidance
- **AI Booking Chat** - Interactive appointment booking with predefined options (Zomato-style)

## AI Features
- **AI Legal Assistant**: General legal questions and advice
- **AI Booking Chat**: Step-by-step guided booking process
  - Select legal category
  - Choose from available lawyers
  - Pick date and time
  - Confirm appointment booking

---

🚀 Built as part of internship project.

## Setup & Run

1. Open a terminal and change into the project folder:
   ```powershell
   cd c:\projint\internship
   ```
2. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Install dependencies if needed:
   ```powershell
   pip install -r requirements.txt
   ```
4. Run database migrations:
   ```powershell
   python manage.py migrate
   ```
5. Create a superuser for admin access:
   ```powershell
   python manage.py createsuperuser
   ```
6. Start the development server:
   ```powershell
   python manage.py runserver
   ```
7. Open `http://127.0.0.1:8000/` in your browser.

## Deployment Notes

- Set `DEBUG = False` in `config/settings.py` for production.
- Add your domain or server IP to `ALLOWED_HOSTS`.
- Use a production WSGI server such as Gunicorn or Waitress.
- Serve static files with `python manage.py collectstatic` and a web server.
- Create a `media/` directory next to `manage.py` for uploaded documents.
- Keep the `SECRET_KEY` secret by moving it into an environment variable or `.env` file.
