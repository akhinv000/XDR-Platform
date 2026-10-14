import os
import time
from dotenv import load_dotenv
from opensearchpy import OpenSearch

load_dotenv()

OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD", "")
OPENSEARCH_USE_SSL = os.getenv("OPENSEARCH_USE_SSL", "true").lower() == "true"
OPENSEARCH_VERIFY_CERTS = os.getenv("OPENSEARCH_VERIFY_CERTS", "false").lower() == "true"

auth = (OPENSEARCH_USER, OPENSEARCH_PASSWORD) if OPENSEARCH_PASSWORD else None

client = OpenSearch(
    hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
    http_auth=auth,
    use_ssl=OPENSEARCH_USE_SSL,
    verify_certs=OPENSEARCH_VERIFY_CERTS,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
    timeout=1,
    max_retries=0,
)

_last_check = 0
_is_available = False

def is_opensearch_available():
    global _last_check, _is_available
    now = time.time()
    if now - _last_check > 30:
        _last_check = now
        try:
            _is_available = bool(client.ping())
        except Exception:
            _is_available = False
    return _is_available