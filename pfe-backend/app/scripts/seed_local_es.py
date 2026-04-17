"""
Seed the LOCAL Elasticsearch instance for development without VPN.

Run:
    cd pfe-backend
    poetry run python app/scripts/seed_local_es.py

What it does:
  1. Waits for local ES (localhost:9200) to be ready.
  2. Tries to copy the target document from the REMOTE ES (10.0.4.125).
     - If remote is reachable → copies real data.
     - If remote is unreachable → inserts a realistic sample document so
       the scoring pipeline can be exercised locally.
  3. Creates the index with a mapping compatible with ESClientTool.
"""
from __future__ import annotations

import json
import sys
import time
from typing import Any, Dict, Optional

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOCAL_ES = "http://localhost:9200"
REMOTE_ES = "http://10.0.4.125:9200"
REMOTE_AUTH = ("data_guest", "data_guest")

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from app.core.config import settings
INDEX = settings.index_account

# Accounts to seed.  Add more Salesforce Ids here as needed.
TARGET_IDS = [
    "0016700005gBzdBAAS",
]

# ---------------------------------------------------------------------------
# Realistic sample document
# (used only when the remote ES is unreachable)
# Fields mirror exactly what ESClientTool._format_client() reads.
# Numbers in Description are intentionally chosen to exercise numeric criteria:
#   - "750 salariés"  → employee count criterion
#   - "60 personnes par an" → hire count criterion
#   - "15%"           → apprentice percentage criterion
# ---------------------------------------------------------------------------
SAMPLE_ACCOUNTS: Dict[str, Dict[str, Any]] = {
    "0016700005gBzdBAAS": {
        "Id": "0016700005gBzdBAAS",
        "Name": "Tech Solutions SAS",
        "Industry": "Technology",
        "sect__c": "Technologie & Numérique",
        "Website": "https://www.sodexo.com",          # real crawlable site for testing
        "SalesLoft_Domain__c": None,
        "LinkedIn_URL__c": "https://www.linkedin.com/company/sodexo",
        "Description": (
            "Tech Solutions SAS est une entreprise de services numériques basée en France. "
            "L'entreprise compte un effectif de 750 salariés répartis sur 5 sites. "
            "Nous recrutons en moyenne 60 personnes par an, tous profils confondus. "
            "Notre politique RH intègre 15% d'alternants (contrats d'apprentissage "
            "et de professionnalisation). Nous rencontrons des difficultés dans "
            "l'organisation de notre plan de formation annuel et souhaitons optimiser "
            "la récupération des aides financières liées à l'alternance."
        ),
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wait_for_local_es(timeout: int = 60) -> None:
    print(f"Waiting for local ES at {LOCAL_ES} …", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{LOCAL_ES}/_cluster/health", timeout=3)
            if r.status_code == 200:
                print(" ready.")
                return
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(2)
    print()
    print("ERROR: local ES did not become ready within timeout.")
    sys.exit(1)


def fetch_from_remote(doc_id: str) -> Optional[Dict[str, Any]]:
    try:
        url = f"{REMOTE_ES}/{INDEX}/_doc/{doc_id}"
        r = requests.get(url, auth=REMOTE_AUTH, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("found"):
                print(f"  ✓ Copied '{doc_id}' from remote ES.")
                return data["_source"]
        print(f"  ✗ Remote returned {r.status_code} for '{doc_id}'.")
    except Exception as exc:
        print(f"  ✗ Remote ES unreachable ({exc}). Using sample data.")
    return None


def ensure_index(session: requests.Session) -> None:
    url = f"{LOCAL_ES}/{INDEX}"
    r = session.head(url)
    if r.status_code == 200:
        print(f"Index '{INDEX}' already exists.")
        return

    mapping = {
        "mappings": {
            "properties": {
                "Id":               {"type": "keyword"},
                "Name":             {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "Industry":         {"type": "keyword"},
                "sect__c":          {"type": "keyword"},
                "Website":          {"type": "keyword"},
                "SalesLoft_Domain__c": {"type": "keyword"},
                "LinkedIn_URL__c":  {"type": "keyword"},
                "Description":      {"type": "text"},
            }
        }
    }
    r = session.put(url, json=mapping)
    r.raise_for_status()
    print(f"Index '{INDEX}' created.")


def index_document(session: requests.Session, doc_id: str, source: Dict[str, Any]) -> None:
    url = f"{LOCAL_ES}/{INDEX}/_doc/{doc_id}"
    r = session.put(url, json=source)
    r.raise_for_status()
    result = r.json().get("result", "?")
    print(f"  Document '{doc_id}' → {result}.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("PFE — Local Elasticsearch Seeder")
    print("=" * 60)

    wait_for_local_es()

    session = requests.Session()
    session.headers["Content-Type"] = "application/json"

    ensure_index(session)

    print(f"\nSeeding {len(TARGET_IDS)} account(s)…")
    for doc_id in TARGET_IDS:
        source = fetch_from_remote(doc_id) or SAMPLE_ACCOUNTS.get(doc_id)
        if source is None:
            print(f"  SKIP '{doc_id}': no remote data and no sample defined.")
            continue
        index_document(session, doc_id, source)

    # Refresh so the documents are immediately searchable
    session.post(f"{LOCAL_ES}/{INDEX}/_refresh")

    print("\nDone. Local ES is seeded and ready.")
    print(f"Test: GET {LOCAL_ES}/{INDEX}/_doc/{TARGET_IDS[0]}")
    print("=" * 60)


if __name__ == "__main__":
    main()
