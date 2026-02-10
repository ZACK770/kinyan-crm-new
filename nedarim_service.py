"""
KUPA CRM - Nedarim Plus Integration Service
Handles synchronization of donations from Nedarim Plus payment gateway
Using Matara.pro Reporting API (Manage3.aspx)
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
import json
import csv
import io
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import urllib.parse

from app.core.config import settings
from app.models.finance import Donation, DonationStatus, PaymentMethod
from app.models.people import Person
import logging

logger = logging.getLogger(__name__)


class NedariminPlusAPIError(Exception):
    """Custom exception for Nedarim Plus API errors"""
    pass


class NedariminPlusService:
    """
    Service for integrating with Nedarim Plus (Matara Reports API)
    """

    def __init__(
        self,
        mosad_id: Optional[str] = None,
        api_password: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: int = 60
    ):
        """
        Initialize Nedarim Plus service
        """
        self.mosad_id = mosad_id or getattr(settings, 'NEDARIM_MOSAD_ID', None)
        self.api_password = api_password or getattr(settings, 'NEDARIM_API_PASSWORD', None)
        self.api_url = api_url or getattr(settings, 'NEDARIM_API_URL', 'https://matara.pro/nedarimplus/Reports/Manage3.aspx')
        self.timeout = timeout

        if not self.mosad_id or not self.api_password:
            logger.warning("Nedarim Plus Mosad ID or Password not configured")

    async def fetch_donations(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Fetch donations from Nedarim Plus API (Manage3.aspx) via CSV
        """
        if not self.mosad_id or not self.api_password:
            raise NedariminPlusAPIError("Nedarim Plus credentials not configured")

        # Default dates if not provided
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        if not date_to:
            date_to = datetime.now()

        # Build payload for Manage3.aspx - GetHistoryCSV
        payload = {
            "MosadNumber": self.mosad_id, # Note: CSV API uses MosadNumber
            "ApiPassword": self.api_password,
            "Action": "GetHistoryCSV",
            "From": date_from.strftime("%d/%m/%Y"),
            "To": date_to.strftime("%d/%m/%Y"),
            "ToMail": 0
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    data=payload
                )
                response.raise_for_status()
                
                content = response.content
                # Decode: try UTF-16 (common for Nedarim CSV), then others
                try:
                    text = content.decode('utf-16')
                except UnicodeDecodeError:
                    try:
                        text = content.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            text = content.decode('windows-1255')
                        except:
                            text = content.decode('latin-1')

                # Check for errors
                if "Error" in text and len(text) < 200:
                    raise NedariminPlusAPIError(f"API Error: {text}")
                
                # Parse CSV
                # Detect delimiter (Tab or Comma)
                # Check first line for tab
                first_line = text.split('\n')[0]
                delimiter = '\t' if '\t' in first_line else ','
                
                f = io.StringIO(text)
                reader = csv.DictReader(f, delimiter=delimiter)
                
                donations = []
                for row in reader:
                    # Filter out empty rows
                    if not row or not any(row.values()):
                        continue
                    donations.append(self._map_transaction(row))

                return {
                    "donations": donations,
                    "has_more": False, # CSV returns all in range
                    "total": len(donations)
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"Nedarim Plus API error: {e.response.status_code}")
            raise NedariminPlusAPIError(f"API returned status {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Nedarim Plus connection error: {str(e)}")
            raise NedariminPlusAPIError(f"Failed to connect: {str(e)}")

    def _map_transaction(self, t: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Nedarim transaction fields (Hebrew CSV headers) to internal format
        """
        def clean_val(v):
            if isinstance(v, str):
                # Remove Excel escape chars like ="123" -> 123
                if v.startswith('="') and v.endswith('"'):
                    return v[2:-1]
                return v.strip()
            return v

        # Map Hebrew keys to internal keys
        # Headers: מספר זהות, שם, כתובת, טלפון, מייל, סכום, מטבע, תאריך עסקה, ...
        
        nedarim_id = clean_val(t.get('מספר עסקה', ''))
        amount = clean_val(t.get('סכום', 0))
        
        # Parse Amount (remove currency symbol or commas if any)
        if isinstance(amount, str):
            amount = amount.replace(',', '').replace('₪', '').replace('$', '').strip()
        
        payer_name = clean_val(t.get('שם', 'Unknown'))
        payer_tz = clean_val(t.get('מספר זהות', ''))
        if payer_tz == '':
            payer_tz = None
            
        payer_phone = clean_val(t.get('טלפון', ''))
        payer_email = clean_val(t.get('מייל', ''))
        
        # Date
        date_str = clean_val(t.get('תאריך עסקה', ''))
        try:
            # Usually DD/MM/YYYY or DD/MM/YYYY HH:MM:SS
            # Or DD/MM/YY HH:MM (as seen in debug output: 01/02/25 22:48)
            if ' ' in date_str:
                # Try with seconds
                try:
                    donation_date = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
                except ValueError:
                    # Try without seconds and 2 digit year
                    try:
                        donation_date = datetime.strptime(date_str, "%d/%m/%y %H:%M")
                    except ValueError:
                         # Try 4 digit year without seconds
                         donation_date = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            else:
                donation_date = datetime.strptime(date_str, "%d/%m/%Y")
        except:
            # Fallback
            donation_date = datetime.now()

        return {
            "donation_id": nedarim_id,
            "payer_id": payer_tz, # This is TZ
            "amount": amount,
            "currency": "ILS", # Assuming ILS mostly, check 'מטבע' field if needed
            "status": "success", 
            "donation_date": donation_date.isoformat(),
            "reference": clean_val(t.get('מספר אישור', '')),
            "notes": clean_val(t.get('הערות', '')),
            "payer_first_name": payer_name.split()[0] if payer_name else "",
            "payer_last_name": " ".join(payer_name.split()[1:]) if payer_name else "",
            "payer_email": payer_email,
            "payer_phone": payer_phone,
            "raw_data": t
        }

    async def sync_donation(
        self,
        db: AsyncSession,
        nedarim_data: Dict[str, Any],
        auto_create_person: bool = True
    ) -> Donation:
        """
        Sync a single donation from Nedarim Plus to local database
        """
        nedarim_donation_id = nedarim_data.get("donation_id")
        
        if not nedarim_donation_id:
             # Try to construct ID if missing? No, skip.
             return None

        # Check if donation already exists
        existing_query = select(Donation).filter(
            Donation.nedarim_donation_id == nedarim_donation_id
        )
        result = await db.execute(existing_query)
        existing_donation = result.scalar_one_or_none()
        
        # If not found by ID, check by reference (to avoid unique constraint error)
        ref = nedarim_data.get("reference")
        if not existing_donation and ref:
             ref_query = select(Donation).filter(Donation.donation_ref == ref)
             result = await db.execute(ref_query)
             existing_donation = result.scalar_one_or_none()
             if existing_donation:
                 logger.info(f"Found existing donation by ref {ref} (Nedarim ID {nedarim_donation_id})")

        # Find or create Person
        person = None
        payer_tz = nedarim_data.get("payer_id")
        
        if payer_tz:
             # Try finding by TZ
             person_query = select(Person).filter(Person.teudat_zehut == payer_tz)
             result = await db.execute(person_query)
             person = result.scalar_one_or_none()

        if not person and nedarim_data.get('payer_email'):
             email = nedarim_data['payer_email']
             if email:
                 person_query = select(Person).filter(Person.email == email)
                 result = await db.execute(person_query)
                 person = result.scalar_one_or_none()

        # Auto-create person
        if not person and auto_create_person:
            # Final check if TZ exists (to avoid integrity error if created in parallel or race condition)
            if payer_tz:
                existing_check = await db.execute(select(Person).filter(Person.teudat_zehut == payer_tz))
                existing_person = existing_check.scalar_one_or_none()
                if existing_person:
                    person = existing_person
                else:
                    person = Person(
                        first_name=nedarim_data.get("payer_first_name", "Unknown"),
                        last_name=nedarim_data.get("payer_last_name", ""),
                        email=nedarim_data.get("payer_email"),
                        phone=nedarim_data.get("payer_phone"),
                        teudat_zehut=payer_tz,
                        is_donor=True
                    )
                    db.add(person)
                    await db.flush()
                    logger.info(f"Created new person for donation {nedarim_donation_id}")
            else:
                # No TZ, create anyway?
                person = Person(
                    first_name=nedarim_data.get("payer_first_name", "Unknown"),
                    last_name=nedarim_data.get("payer_last_name", ""),
                    email=nedarim_data.get("payer_email"),
                    phone=nedarim_data.get("payer_phone"),
                    is_donor=True
                )
                db.add(person)
                await db.flush()

        if not person:
            logger.error(f"Could not find or create person for donation {nedarim_donation_id}")
            return None

        # Map to Donation fields
        try:
            amount_val = float(nedarim_data.get("amount", 0))
        except:
            amount_val = 0

        donation_dict = {
            "person_id": person.id,
            "amount": amount_val,
            "currency": "ILS",
            "payment_method": PaymentMethod.NEDARIM,
            "status": DonationStatus.SUCCESSFUL,
            "donation_date": datetime.fromisoformat(nedarim_data["donation_date"]),
            "donation_ref": nedarim_data.get("reference"),
            "notes": nedarim_data.get("notes"),
            "nedarim_donation_id": nedarim_donation_id,
            "nedarim_raw_data": nedarim_data.get("raw_data"),
        }

        if existing_donation:
            for k, v in donation_dict.items():
                if k != "person_id":
                    setattr(existing_donation, k, v)
            await db.commit()
            return existing_donation
        else:
            new_don = Donation(**donation_dict)
            db.add(new_don)
            await db.commit()
            return new_don

    async def sync_donations_batch(
        self,
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        max_pages: int = 10
    ) -> Dict[str, Any]:
        """
        Sync multiple donations
        """
        try:
            response = await self.fetch_donations(date_from, date_to)
            donations = response.get("donations", [])
            
            created = 0
            updated = 0
            errors = []
            
            for don_data in donations:
                try:
                    res = await self.sync_donation(db, don_data)
                    if res:
                         updated += 1 
                except Exception as e:
                    errors.append(str(e))
            
            return {
                "created_count": created,
                "updated_count": updated,
                "error_count": len(errors),
                "errors": errors,
                "message": f"סונכרנו {len(donations)} תרומות"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "message": f"שגיאה בסנכרון: {str(e)}"
            }

    async def update_donation_status(self, db: AsyncSession, nedarim_donation_id: str):
        pass

    def is_configured(self) -> bool:
        return bool(self.mosad_id and self.api_password)

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection
        """
        if not self.is_configured():
             return {"success": False, "message": "Missing credentials"}
        
        try:
            # Try fetching with very short range
            await self.fetch_donations(
                date_from=datetime.now(),
                date_to=datetime.now()
            )
            return {"success": True, "message": "חיבור תקין לנדרים פלוס"}
        except Exception as e:
            return {"success": False, "message": f"חיבור נכשל: {str(e)}"}
