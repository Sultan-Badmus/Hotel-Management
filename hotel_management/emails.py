from djoser.email import ActivationEmail


class ActivationReminderEmail(ActivationEmail):
    template_name = "email/activation_reminder.html"
