from django.core.management.base import BaseCommand
from core.models import ClimateCreditApplication
from core.views import early_warning


class Command(BaseCommand):
    help = 'Update early warning messages for existing applications'

    def handle(self, *args, **options):
        applications = ClimateCreditApplication.objects.all()
        updated_count = 0

        for app in applications:
            warning_flag, warning_msg = early_warning(
                app.default_probability,
                app.climate_risk_score,
                app.esg_risk_score,
                app.adjusted_credit_score
            )

            if app.early_warning_flag != warning_flag or app.early_warning_message != warning_msg:
                app.early_warning_flag = warning_flag
                app.early_warning_message = warning_msg
                app.save(update_fields=['early_warning_flag', 'early_warning_message'])
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} applications with new warning messages')
        )