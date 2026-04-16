"""Notification service - in-app + email notifications."""
from abstractions.IServiceManagerBase import IServiceManagerBase
from database.schemas.notification import NotificationItem


class NotificationService(IServiceManagerBase):
    def __init__(self, config=None):
        super().__init__(config)
        self._email_service = None
        self._db = None

    def initialize(self):
        pass

    def set_email_service(self, email_service):
        self._email_service = email_service

    def set_db(self, db_service):
        self._db = db_service

    def send(self, user_id: str, notification_type: str, title: str, message: str, org_id: str = None, action_url: str = None):
        notif = NotificationItem(user_id=user_id, org_id=org_id, notification_type=notification_type, title=title, message=message, action_url=action_url)
        self._db.notifications.create(notif)
        return notif

    def send_timesheet_reminder(self, user_id: str, org_id: str):
        return self.send(user_id, "timesheet_reminder", "Timesheet Reminder", "Don't forget to submit your timesheet.", org_id, "/timesheet")

    def send_approval_notification(self, user_id: str, org_id: str, status: str):
        title = f"Timesheet {status.title()}"
        message = f"Your timesheet has been {status}."
        return self.send(user_id, f"timesheet_{status}", title, message, org_id, "/timesheet")
