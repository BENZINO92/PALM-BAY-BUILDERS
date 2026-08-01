"""Brevard County BASS Permit Scraper using Playwright"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from database import BuilderDatabase
from config import (
    BASS_URL, PERMIT_SEARCH_URL, DAYS_BACK, HEADLESS,
    BROWSER_TIMEOUT, TIMEOUT_SECONDS, TARGET_CITY, TARGET_STATE,
    RESIDENTIAL_KEYWORDS, EXCLUDE_KEYWORDS, APPLICATION_TYPE
)

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Playwright not installed. Install with: pip install playwright")
    print("Then run: playwright install")


class BrevardPermitScraper:
    def __init__(self):
        self.db = BuilderDatabase()
        self.permits_found = []
        self.builders_found = []

    async def run(self):
        """Main scraper execution"""
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"🚀 Starting Brevard Permit Scraper - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Searching for permits from TODAY ONLY ({today})...")
        print(f"   (Fresh data - no historical permits)")
        print(f"📍 Section: DEVELOPMENT tab")
        print(f"💰 Application Type: {APPLICATION_TYPE}")
        print(f"📍 Property City: {TARGET_CITY}, {TARGET_STATE}")
        print(f"🏠 Type Filter: RESIDENTIAL ONLY (no commercial)\n")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                print("📍 Navigating to Brevard BASS portal...")
                await page.goto(PERMIT_SEARCH_URL, wait_until="networkidle", timeout=BROWSER_TIMEOUT)
                await page.wait_for_timeout(2000)

                await self._search_recent_permits(page)
                await self._extract_permits(page)
                self._process_permits()

                print(f"\n✅ Scraper completed successfully!")
                print(f"   Found {len(self.builders_found)} unique builders")
                print(f"   Found {len(self.permits_found)} total permits\n")

            except Exception as e:
                print(f"❌ Error during scraping: {str(e)}")
                print("   This might be due to website changes or timeout")

            finally:
                await browser.close()

    async def _search_recent_permits(self, page):
        """Search for development permits in DEVELOPMENT tab - Palm Bay only"""
        try:
            await page.wait_for_load_state("networkidle", timeout=BROWSER_TIMEOUT)
            print("✓ Page loaded (DEVELOPMENT section)")
            print("  Searching for residential permits with Palm Bay property address...")

            await page.wait_for_timeout(3000)

            search_inputs = await page.query_selector_all("input[type='text'], input[type='date']")
            print(f"  Found {len(search_inputs)} input fields")

            buttons = await page.query_selector_all("button")
            print(f"  Found {len(buttons)} buttons")

            for btn in buttons[:10]:
                text = await btn.text_content()
                if text.strip():
                    print(f"    - Button: {text.strip()}")

        except Exception as e:
            print(f"  Note: Could not automate search fields: {e}")
            print("  Attempting to extract data from current DEVELOPMENT page...")

    async def _extract_permits(self, page):
        """Extract permit data from page"""
        print("\n📊 Extracting permit data from page...")

        try:
            await page.wait_for_timeout(2000)

            selectors = [
                "table tbody tr",
                "div[role='row']",
                "div.record",
                "tr[data-permit-id]",
                ".permit-row"
            ]

            rows = []
            for selector in selectors:
                try:
                    rows = await page.query_selector_all(selector)
                    if rows:
                        print(f"✓ Found {len(rows)} rows using selector: {selector}")
                        break
                except:
                    continue

            if not rows:
                print("⚠️  No permit rows found on page")
                return

            for i, row in enumerate(rows[:100]):
                try:
                    cells = await row.query_selector_all("td, div[role='gridcell']")

                    if len(cells) >= 3:
                        cell_texts = []
                        for cell in cells:
                            text = await cell.text_content()
                            cell_texts.append(text.strip())

                        if i < 5:
                            print(f"  Row {i}: {cell_texts[:4]}")

                        permit = self._parse_permit_row(cell_texts)
                        if permit:
                            self.permits_found.append(permit)

                except Exception as e:
                    continue

            print(f"✓ Extracted {len(self.permits_found)} permits from page")

        except Exception as e:
            print(f"  Error extracting permits: {str(e)}")

    def _is_palm_bay_address(self, address: str) -> bool:
        """Check if CITY is Palm Bay, FL (exact city match)"""
        if not address or address.lower() == "unknown":
            return False

        address_lower = address.lower()
        has_palm_bay = "palm bay" in address_lower
        has_state = TARGET_STATE.lower() in address_lower or "fl" in address_lower

        return has_palm_bay and has_state

    def _is_residential_builder(self, permit_type: str, address: str = "") -> bool:
        """Check if permit is for residential home building only"""
        if not permit_type:
            return False

        permit_lower = permit_type.lower()
        address_lower = address.lower() if address else ""

        for keyword in EXCLUDE_KEYWORDS:
            if keyword.lower() in permit_lower or keyword.lower() in address_lower:
                return False

        for keyword in RESIDENTIAL_KEYWORDS:
            if keyword.lower() in permit_lower or keyword.lower() in address_lower:
                return True

        if "building" in permit_lower or "residential" in permit_lower:
            return True

        return False

    def _extract_zipcode(self, address: str) -> str:
        """Extract zipcode from address"""
        if not address:
            return ""

        import re
        match = re.search(r'\b(\d{5})\b', address)
        return match.group(1) if match else ""

    def _parse_permit_row(self, cells: List[str]) -> Dict:
        """Parse permit data from table row - Extract: Builder Name from APPLICATION NAME, Address, Zipcode, Lot Size"""
        if not cells or len(cells) < 3:
            return None

        try:
            permit_id = cells[0] if len(cells) > 0 else f"permit_{datetime.now().timestamp()}"

            application_name = cells[1] if len(cells) > 1 else ""
            builder_name = application_name if application_name else cells[2] if len(cells) > 2 else ""

            property_address = cells[3] if len(cells) > 3 else "Unknown"
            date_issued = cells[4] if len(cells) > 4 else datetime.now().isoformat()
            permit_type = cells[5] if len(cells) > 5 else "Building"
            application_type = cells[6] if len(cells) > 6 else ""
            lot_size = cells[7] if len(cells) > 7 else ""

            zipcode = self._extract_zipcode(property_address)

            if APPLICATION_TYPE.lower() not in application_type.lower():
                return None

            if not self._is_palm_bay_address(property_address):
                return None

            if not self._is_residential_builder(permit_type, property_address):
                return None

            permit = {
                'permit_id': permit_id,
                'builder_name': builder_name,
                'property_address': property_address,
                'zipcode': zipcode,
                'lot_size': lot_size,
                'permit_type': permit_type,
                'application_type': application_type,
                'date_issued': date_issued,
                'amount': None
            }

            if permit['permit_id'] and permit['builder_name'] and permit['property_address']:
                return permit

        except Exception as e:
            pass

        return None

    def _process_permits(self):
        """Process and store permits in database"""
        print(f"\n💾 Processing {len(self.permits_found)} permits...")

        for permit in self.permits_found:
            try:
                builder = self.db.get_builder_by_license(permit['builder_name'])

                if not builder:
                    builder_id = self.db.add_builder(
                        license_id=permit['builder_name'],
                        name=permit['builder_name'],
                        license_type="General Contractor"
                    )
                    self.builders_found.append({
                        'id': builder_id,
                        'name': permit['builder_name'],
                        'license_id': permit['builder_name'],
                        'permit_count': 1,
                        'latest_permit': permit['date_issued']
                    })
                    print(f"  ✨ NEW BUILDER: {permit['builder_name']}")
                else:
                    builder_id = builder['id']

                self.db.add_permit(
                    permit_id=permit['permit_id'],
                    builder_id=builder_id,
                    builder_name=permit['builder_name'],
                    property_address=permit['property_address'],
                    zipcode=permit.get('zipcode', ''),
                    lot_size=permit.get('lot_size', ''),
                    permit_type=permit.get('permit_type', ''),
                    application_type=permit.get('application_type', ''),
                    date_issued=permit['date_issued'],
                    amount=permit.get('amount')
                )

            except Exception as e:
                print(f"  ❌ Error processing permit {permit.get('permit_id')}: {e}")
                continue


async def run_scraper():
    """Entry point for scraper"""
    scraper = BrevardPermitScraper()
    await scraper.run()
    return scraper.builders_found


if __name__ == "__main__":
    asyncio.run(run_scraper())
