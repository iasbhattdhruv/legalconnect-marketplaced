from django.core.management.base import BaseCommand

from accounts.demo_data import ensure_demo_data


class Command(BaseCommand):
    help = 'Create starter admin, lawyers, and blog posts for fresh deployments.'

    def handle(self, *args, **options):
        result = ensure_demo_data(create_admin=True)
        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete. Created "
                f"{result['created_lawyers']} lawyers, "
                f"{result['created_posts']} blog posts, "
                f"admin_created={result['admin_created']}."
            )
        )
