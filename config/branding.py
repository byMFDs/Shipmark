"""Single source of branding. Edit this file to rebrand the site.

Exposed to every template as `brand` (see config/context_processors.py).
Logo paths are relative to the static folder: replace the files to change the logo.
"""
from django.utils.translation import gettext_lazy as _

SITE_NAME = "Shipmark"
TAGLINE = _("Proof of what you actually shipped")
CONTACT_EMAIL = "hello@example.com"
LEGAL_OWNER_NAME = "Your Name"

# Label -> URL. Shown in the footer once the design exists. Empty for now.
SOCIAL_LINKS = {}

LOGO = "brand/logo.svg"
LOGO_MARK = "brand/logo-mark.svg"
FAVICON = "brand/favicon.svg"
APPLE_TOUCH_ICON = "brand/apple-touch-icon.png"
OG_DEFAULT_IMAGE = "brand/og-default.png"
