import logging
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import settings
from utils import generate_event_ics

logger = logging.getLogger(__name__)


def _build_mime_message(
        recipient_email: str,
        subject: str,
        body_text: str,
        ics_bytes: bytes,
        method: str = "REQUEST"
) -> MIMEMultipart:
    msg = MIMEMultipart("mixed")
    msg["From"] = settings.SENDER_EMAIL
    msg["To"] = recipient_email
    msg["Subject"] = subject

    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(body_text, "plain", "utf-8"))

    cal_part = MIMEText(
        ics_bytes.decode("utf-8"),
        f"calendar; method={method}; charset=UTF-8"
    )
    cal_part.add_header("Content-Class",
                        "urn:content-classes:calendarmessage")
    alt_part.attach(cal_part)
    msg.attach(alt_part)

    attachment = MIMEBase("application", "ics")
    attachment.set_payload(ics_bytes)
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename="invite.ics"
    )
    msg.attach(attachment)

    return msg

def _send_calendar_messages_batch(
        recipients: list[str] | str,
        subject: str,
        body_text: str,
        ics_bytes: bytes,
        method: str = "REQUEST"
):
    if isinstance(recipients, str):
        recipients = [recipients]

    if not recipients:
        return

    if not settings.SENDER_EMAIL or not settings.SENDER_PASSWORD:
        logger.warning("SMTP credentials are not configured; skipping email notification.")
        return

    try:
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT,
                          timeout=15) as server:
            server.starttls()
            server.login(settings.SENDER_EMAIL, settings.SENDER_PASSWORD)

            for email in recipients:
                try:
                    msg = _build_mime_message(
                        recipient_email=email,
                        subject=subject,
                        body_text=body_text,
                        ics_bytes=ics_bytes,
                        method=method
                    )
                    server.send_message(msg)
                    logger.info(f"Notification successfully sent to {email}")
                except Exception as user_err:
                    logger.error(f"Failed to send email to {email}:{user_err}")

    except Exception as connection_err:
        logger.error(f"SMTP Connection/Auth error: {connection_err}")


def send_event_email(
        recipients: list[str] | str,
        event_id: int,
        event_title: str,
        description: str | None,
        start_time: datetime,
        end_time: datetime,
        room_name: str | None = None
):
    ics_bytes = generate_event_ics(
        event_id=event_id,
        title=event_title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        location=room_name,
        sequence=0,
        status="CONFIRMED",
        method="REQUEST"
    )

    location_info = f"Office/Room: {room_name}" if room_name else "Format: Online"
    description_info = f"Description: {description}\n" if description else ""

    body = (
        f"Hello,\n\n"
        f"You have been invited to a new event: {event_title}\n\n"
        f"Start time: {start_time.strftime('%Y-%m-%d %H:%M')}\n"
        f"End time: {end_time.strftime('%Y-%m-%d %H:%M')}\n"
        f"{location_info}\n"
        f"{description_info}\n"
        f"The calendar event is attached to this email. You can accept or decline this invitation directly from your email client.\n\n" 
        f"Best regards,\n"
        f"ScheduleNow Team"
    )

    _send_calendar_messages_batch(
        recipients=recipients,
        subject=f"Invitation: {event_title}",
        body_text=body,
        ics_bytes=ics_bytes,
        method="REQUEST"
    )


def send_event_updated_email(
        recipients: list[str] | str,
        event_id: int,
        event_title: str,
        description: str | None,
        start_time: datetime,
        end_time: datetime,
        room_name: str | None = None
):
    ics_bytes = generate_event_ics(
        event_id=event_id,
        title=event_title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        location=room_name,
        sequence=1,
        status="CONFIRMED",
        method="REQUEST"
    )

    location_info = f"Office/Room: {room_name}" if room_name else "Format: Online"
    description_info = f"Description: {description}\n" if description else ""

    body = (
        f"Hello,\n\n"
        f"Please note that the event '{event_title}' has been updated.\n\n"
        f"New schedule: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}\n"
        f"{location_info}\n"
        f"{description_info}\n"
        f"The updated calendar event is attached to this email and your calendar will sync automatically.\n\n"
        f"Best regards,\n"
        f"ScheduleNow Team"
    )

    _send_calendar_messages_batch(
        recipients=recipients,
        subject=f"Updated: {event_title}",
        body_text=body,
        ics_bytes=ics_bytes,
        method="REQUEST"
    )


def send_event_cancelled_email(
        recipients: list[str] | str,
        event_id: int,
        event_title: str,
        start_time: datetime,
        end_time: datetime
):
    ics_bytes = generate_event_ics(
        event_id=event_id,
        title=event_title,
        description="This event has been cancelled by the organizer.",
        start_time=start_time,
        end_time=end_time,
        sequence=2,
        status="CANCELLED",
        method="CANCEL"
    )

    body = (
        f"Hello,\n\n"
        f"We would like to inform you that the event '{event_title}' has been cancelled by the organizer.\n\n" 
        f"The event has been automatically removed or marked as cancelled in your calendar.\n\n" 
        f"Best regards,\n"
        f"ScheduleNow Team"
    )

    _send_calendar_messages_batch(
        recipients=recipients,
        subject=f"Cancelled: {event_title}",
        body_text=body,
        ics_bytes=ics_bytes,
        method="CANCEL"
    )