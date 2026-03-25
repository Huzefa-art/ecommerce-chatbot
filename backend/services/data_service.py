from config import settings
from services.airtable_service import airtable_service
from services.sqlite_service import sqlite_service

def get_data_service():
    if settings.data_source.lower() == "sqlite":
        return sqlite_service
    else:
        return airtable_service
