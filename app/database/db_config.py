import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Add it to your .env file or your host's environment variables."
    )

# SSL is only switched on when DB_SSL_CA is set, so a local database keeps working as before
CONNECT_ARGS = {}
_ssl_ca = os.getenv("DB_SSL_CA")
if _ssl_ca:
    ca_path = Path(_ssl_ca)
    if not ca_path.is_absolute():
        # relative paths are resolved from this file's folder, not the working directory
        ca_path = Path(__file__).resolve().parent / ca_path
    if not ca_path.exists():
        raise RuntimeError(f"DB_SSL_CA file not found: {ca_path}")
    CONNECT_ARGS["ssl"] = {"ca": str(ca_path)}

ENGINE_OPTIONS = {
    "pool_pre_ping": True,   # test a connection before using it, replace it if dead
    "pool_recycle": 280,     # drop connections older than ~5 minutes
    "connect_args": CONNECT_ARGS,
}