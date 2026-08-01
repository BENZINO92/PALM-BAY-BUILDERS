"""Configuration for Brevard Builder Discovery System"""

# Email Configuration
EMAIL_FROM = "admin@bjbacquisitiongroup.com"
EMAIL_ALERTS_TO = ["admin@bjbacquisitiongroup.com"]
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
GMAIL_APP_PASSWORD = import os
GMAIL_APP_PASSWORD = os.getenv('GMAIL_PASSWORD', 'YOUR_GMAIL_APP_PASSWORD_HERE')

# Brevard BASS Portal - DEVELOPMENT SECTION
BASS_URL = "https://acaweb.brevardcounty.us/citizenaccess/"
PERMIT_SEARCH_URL = "https://aca-prod.accela.com/BREVARD/Cap/CapHome.aspx?module=Development&TabName=Development&TabList=HOME%7C0%7CBuilding%7C1%7CDevelopment%7C2%7CEnforce%7C3%7CCurrentTabIndex%7C2"

# Database
DATABASE_FILE = "builder_discovery.db"

# Search Settings
DAYS_BACK = 1
TARGET_CITY = "Palm Bay"
TARGET_STATE = "FL"

# DATA FIELD MAPPING
# Builder Name extracted from: APPLICATION NAME field in BASS
# Property Address: Full address field
# Zipcode: Auto-extracted from address (5-digit zip)
# Lot Size: Lot size field

# SCHEDULE: Monday through Friday only (weekdays)
# 8:15 AM Monday-Friday: Scrape today's IMPACT FEES RESIDENTIAL applications
# Skip weekends (Saturday, Sunday)

# FILTER: Property City = Palm Bay, FL (exact city match required)

APPLICATION_TYPE = "IMPACT FEES RESIDENTIAL"

# RESIDENTIAL ONLY - Keywords to identify residential home builders
RESIDENTIAL_KEYWORDS = [
    "residential",
    "single family",
    "single-family",
    "sfr",
    "home",
    "house",
    "dwelling",
    "family residence",
    "new construction residential"
]

# Exclude commercial/industrial builders
EXCLUDE_KEYWORDS = [
    "commercial",
    "industrial",
    "warehouse",
    "retail",
    "office",
    "apartment",
    "multifamily",
    "multi-family",
    "condo",
    "condominium"
]

PERMIT_TYPES_TO_MONITOR = [
    "Building",
    "Residential",
    "New Construction",
    "SFR",
    "Single Family Residence"
]

# Scraper Settings
HEADLESS = True
TIMEOUT_SECONDS = 30
BROWSER_TIMEOUT = 60000

# Alert Settings
MIN_PERMITS_FOR_ALERT = 1
SCRAPE_TIME = "08:15"
ALERT_TIME = "08:30"
