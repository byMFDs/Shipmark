"""Single source of branding. Edit this file to rebrand the site.

Exposed to every template as `brand` (see config/context_processors.py).
Logo paths are relative to the static folder: replace the files to change the logo.
"""
from django.utils.translation import gettext_lazy as _

# SITE_NAME is used in running text ("Shipmark"). The logo files spell it lowercase ("shipmark").
SITE_NAME = "Shipmark"
# Shown where a URL is natural: footer, badges, profile URL, embed snippets. No scheme, no slash.
SITE_DOMAIN = "shipmark.me"
TAGLINE = _("Proof, not promises.")
CONTACT_EMAIL = "shipmark@gmail.com"
LEGAL_OWNER_NAME = "Shipmark. A Danylo Rudenko production."

# Label -> URL. Shown in the footer once the design exists. Empty for now.
SOCIAL_LINKS = {}

LOGO = "brand/logo.svg"
LOGO_MARK = "brand/logo-mark.svg"
# Light-colored copies for dark backgrounds (the admin in dark mode). Same shapes: change both together.
LOGO_DARK = "brand/logo-dark.svg"
LOGO_MARK_DARK = "brand/logo-mark-dark.svg"
FAVICON = "brand/favicon.svg"
# For browsers without SVG icons (older Safari) and for /favicon.ico. Made from logo C by `python manage.py make_icons` (pages/brand_icons.py).
FAVICON_ICO = "brand/favicon.ico"
APPLE_TOUCH_ICON = "brand/apple-touch-icon.png"
OG_DEFAULT_IMAGE = "brand/og-default.png"

# Name of the domain verification record: TXT "shipmark-verify=<token>" and
# <meta name="shipmark-verify">. Do NOT change it after launch: every verified domain
# would fail its next re-check and lose the Live hallmark.
VERIFY_TOKEN_NAME = "shipmark-verify"
