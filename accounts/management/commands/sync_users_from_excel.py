from django.core.management.base import BaseCommand
from accounts.excel_utils import sync_users_from_excel, ensure_users_excel


class Command(BaseCommand):
    help = 'Sync users from users.xlsx into Django auth users.'

    def handle(self, *args, **options):
        excel_path = ensure_users_excel()
        self.stdout.write(self.style.SUCCESS(f'Syncing from Excel: {excel_path}'))
        result = sync_users_from_excel()
        self.stdout.write(self.style.SUCCESS(f"Created: {result['created']}, Skipped: {result['skipped']}"))
        if result['errors']:
            self.stdout.write(self.style.ERROR('Errors:'))
            for error in result['errors']:
                self.stdout.write(self.style.ERROR(f'- {error}'))
