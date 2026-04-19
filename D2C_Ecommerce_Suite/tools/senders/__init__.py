"""Shared senders — email, WhatsApp, Slack. Used by every D2C module.

Design note: these are library modules (not CLIs) so modules can call them
directly. CLIs exist on the Multi_Channel_Onboarding side for ad-hoc testing;
these keep the same provider choices to avoid behavioural drift.
"""

from tools.senders.email import send_email  # noqa: F401
from tools.senders.whatsapp import send_whatsapp  # noqa: F401
from tools.senders.slack import send_slack  # noqa: F401
