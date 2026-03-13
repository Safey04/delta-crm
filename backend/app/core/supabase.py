from functools import lru_cache

from supabase import Client, create_client

from app.core.config import settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a cached Supabase client using the anon key.

    Suitable for general operations that respect Row Level Security.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


@lru_cache(maxsize=1)
def get_supabase_admin_client() -> Client:
    """Return a cached Supabase client using the service-role key.

    Suitable for admin operations that bypass Row Level Security,
    such as creating auth users or managing data across tenants.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
