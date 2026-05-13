from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

_PRODUCTS_FILE = OUTPUT_DIR / "products.json"
_CRITERIA_FILE = OUTPUT_DIR / "criteria.json"
_CHOICES_FILE  = OUTPUT_DIR / "choice.json"

_TARGET_INDEX    = "verse_sf_pipeline_campaign_target_raw_zone_v20240207"
_VERSE_INDEX     = "verse_sf_pipeline_campaign_target_raw_zone_v20240207"
_SOURCES_FILE    = OUTPUT_DIR / "sources.json"
# Local campaigns file for admin-created campaigns (ES is read-only)
_LOCAL_CAMPAIGNS_FILE = OUTPUT_DIR / "campaigns_admin.json"


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def _now() -> int:
    return int(time.time() * 1000)


def _read(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, data: List[Dict[str, Any]]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


# ── Products ──────────────────────────────────────────────────────────────────

def list_products() -> List[Dict[str, Any]]:
    return _read(_PRODUCTS_FILE)


def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    return next((p for p in _read(_PRODUCTS_FILE) if p["id"] == product_id), None)


def create_product(name: str) -> Dict[str, Any]:
    products = _read(_PRODUCTS_FILE)
    new_id = f"P{len(products) + 1:03d}"
    product = {"id": new_id, "name": name}
    products.append(product)
    _write(_PRODUCTS_FILE, products)
    return product


def update_product(product_id: str, name: str) -> Optional[Dict[str, Any]]:
    products = _read(_PRODUCTS_FILE)
    for p in products:
        if p["id"] == product_id:
            p["name"] = name
            _write(_PRODUCTS_FILE, products)
            return p
    return None


def delete_product(product_id: str) -> bool:
    products = _read(_PRODUCTS_FILE)
    filtered = [p for p in products if p["id"] != product_id]
    if len(filtered) == len(products):
        return False
    _write(_PRODUCTS_FILE, filtered)
    # cascade: remove criteria and choices
    criteria = [c for c in _read(_CRITERIA_FILE) if c.get("product_id") != product_id]
    removed_ids = {c["id"] for c in _read(_CRITERIA_FILE) if c.get("product_id") == product_id}
    choices = [ch for ch in _read(_CHOICES_FILE) if ch.get("criteria_id") not in removed_ids]
    _write(_CRITERIA_FILE, criteria)
    _write(_CHOICES_FILE, choices)
    return True


# ── Criteria ──────────────────────────────────────────────────────────────────

def list_criteria(product_id: Optional[str] = None) -> List[Dict[str, Any]]:
    criteria = _read(_CRITERIA_FILE)
    if product_id:
        criteria = [c for c in criteria if c.get("product_id") == product_id]
    return criteria


def get_criterion(criterion_id: str) -> Optional[Dict[str, Any]]:
    return next((c for c in _read(_CRITERIA_FILE) if c["id"] == criterion_id), None)


def create_criterion(product_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    if not get_product(product_id):
        return None
    criteria = _read(_CRITERIA_FILE)
    criterion = {
        "id":               _uid("QX"),
        "label":            data["label"],
        "label_normalized": _normalize(data["label"]),
        "agent_prompt":     data.get("agent_prompt") or f"Critère : {data['label']}",
        "expected_output":  "",
        "product_id":       product_id,
        "campaign_id":      None,
        "quiz_id":          None,
        "answer_type":      data.get("answer_type", "single_choice"),
        "can_pass":         False,
        "redirection_id":   None,
        "order":            data.get("order", len(criteria) + 1),
        "section_number":   data.get("section_number", 1),
        "unit":             data.get("unit"),
        "comment_enable":   data.get("comment_enable", True),
        "default_score":    data.get("default_score", 0),
        "is_main":          data.get("is_main", True),
        "created_at":       _now(),
        "deleted_at":       None,
        "updated_at":       _now(),
    }
    criteria.append(criterion)
    _write(_CRITERIA_FILE, criteria)
    return criterion


def update_criterion(criterion_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    criteria = _read(_CRITERIA_FILE)
    for c in criteria:
        if c["id"] == criterion_id:
            for k, v in updates.items():
                if v is not None:
                    c[k] = v
            if "label" in updates and updates["label"]:
                c["label_normalized"] = _normalize(updates["label"])
            c["updated_at"] = _now()
            _write(_CRITERIA_FILE, criteria)
            return c
    return None


def delete_criterion(criterion_id: str) -> bool:
    criteria = _read(_CRITERIA_FILE)
    filtered = [c for c in criteria if c["id"] != criterion_id]
    if len(filtered) == len(criteria):
        return False
    _write(_CRITERIA_FILE, filtered)
    choices = [ch for ch in _read(_CHOICES_FILE) if ch.get("criteria_id") != criterion_id]
    _write(_CHOICES_FILE, choices)
    return True


# ── Choices ───────────────────────────────────────────────────────────────────

def list_choices(criterion_id: str) -> List[Dict[str, Any]]:
    return [ch for ch in _read(_CHOICES_FILE) if ch.get("criteria_id") == criterion_id]


def create_choice(criterion_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not get_criterion(criterion_id):
        return None
    choices = _read(_CHOICES_FILE)
    body = data.get("condition_body") or f"return a >= 0"
    choice = {
        "id":            _uid("CH"),
        "criteria_id":   criterion_id,
        "campaign_id":   None,
        "quiz_id":       None,
        "label":         data["label"],
        "condition":     {"arg": "a", "body": body},
        "score":         data.get("score", 0),
        "is_blocking":   data.get("is_blocking", False),
        "redirection_id": None,
        "created_at":    _now(),
        "deleted_at":    None,
        "updated_at":    _now(),
    }
    choices.append(choice)
    _write(_CHOICES_FILE, choices)
    return choice


def update_choice(choice_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    choices = _read(_CHOICES_FILE)
    for ch in choices:
        if ch["id"] == choice_id:
            if data.get("label") is not None:
                ch["label"] = data["label"]
            if data.get("score") is not None:
                ch["score"] = data["score"]
            if data.get("is_blocking") is not None:
                ch["is_blocking"] = data["is_blocking"]
            if data.get("condition_body"):
                ch["condition"]["body"] = data["condition_body"]
            ch["updated_at"] = _now()
            _write(_CHOICES_FILE, choices)
            return ch
    return None


def delete_choice(choice_id: str) -> bool:
    choices = _read(_CHOICES_FILE)
    filtered = [ch for ch in choices if ch["id"] != choice_id]
    if len(filtered) == len(choices):
        return False
    _write(_CHOICES_FILE, filtered)
    return True


# ── Campaigns (Elasticsearch-backed) ─────────────────────────────────────────

def _es_client():
    from app.modules.elasticsearch.client import AbstractElasticsearchClient
    return AbstractElasticsearchClient()


def _campaign_product_ids() -> Dict[str, List[str]]:
    """Build a map of campaign_id → [product_ids] from criteria JSON."""
    mapping: Dict[str, List[str]] = {}
    for c in _read(_CRITERIA_FILE):
        cid = c.get("campaign_id")
        pid = c.get("product_id")
        if cid and pid:
            if cid not in mapping:
                mapping[cid] = []
            if pid not in mapping[cid]:
                mapping[cid].append(pid)
    return mapping


def _enrich(source: Dict[str, Any], product_map: Dict[str, List[str]]) -> Dict[str, Any]:
    cid = source.get("id", "")
    return {**source, "product_ids": product_map.get(cid, [])}


# Mapping Marche__c → product IDs
_MARCHE_TO_PRODUCTS: Dict[str, List[str]] = {
    "CIR":       ["P002"],
    "CEE":       ["P004"],
    "NRJ":       ["P005"],
    "ENERGIE":   ["P005"],
    "EFFI":      ["P001", "P006", "P007", "P008"],
    "FL":        ["P013"],
    "DAF":       ["P010", "P013"],
    "INNO":      ["P002", "P003", "P011"],
    "INTER":     ["P012", "P015"],
    "DRH":       ["P001", "P007", "P008", "P014"],
    "CTR":       ["P002"],
    "Marketing": [],
}

# Keyword mapping on campaign NAME when Marche__c is missing
_NAME_KEYWORDS: List[tuple] = [
    (["FORMATION", "ALTERNANCE", "APPRENTISSAGE", "BPO HR", "BPO FORMATION"], ["P001"]),
    (["CIR", "R&D", "RDTC", "RSDE", "SRED", "INNOV", "PATENT", "IDI", "RESEARCH"], ["P002"]),
    (["DECARBON", "CO2", "CARBONE", "CLIMAT", "EMISSION"], ["P003", "P011"]),
    (["CEE", "ENERGIE CALO", "CALO EXO"], ["P004"]),
    (["ENERGIE", "ENERGY", "NRJ", "ECO-EMBALLAGE", "EMBALLAGE", "REP"], ["P005"]),
    (["C3S", "CONTRIBUTION SOCIALE"], ["P006"]),
    (["MUTUELLE", "PREVOYANCE", "ASSURANCE PERSON"], ["P007"]),
    (["CHARGES SOCIALES", "URSSAF", "FILLON", "LODEOM"], ["P008"]),
    (["TRANSPORT", "COLIS", "LOGISTIQUE"], ["P009"]),
    (["AUDIT RECOVERY", "TROP VERS", "FOURNISSEUR"], ["P010"]),
    (["STRATEGIE CLIMAT", "COMPENSATION CARBONE", "CREDIT CARBONE"], ["P011"]),
    (["IP BOX", "PATENT BOX", "PROPRIETE INTELLECT"], ["P012"]),
    (["FISCALITE LOCALE", "CFE", "CVAE", "TAXE FONCIERE", "IAE", "BINS", "PROPERTY TAX",
      "PROPERTY TAX", "FISCAL", "FL EXO", "FL BINS", "TAX RECOVERY", "SALES TAX",
      "IMPUESTO", "BONIFICACION"], ["P013"]),
    (["INTERIM", "INTERIMAIRE", "INTÉRIMAIRE"], ["P014"]),
    (["TAX LEASE", "ESPAGNE", "SPAIN", "ES PRV.*64BIS"], ["P015"]),
]


def _infer_products_from_name(name: str) -> List[str]:
    """Infer product IDs from campaign name keywords."""
    name_upper = name.upper()
    products = set()
    for keywords, pids in _NAME_KEYWORDS:
        if any(kw in name_upper for kw in keywords):
            products.update(pids)
    return sorted(products)


def list_campaigns() -> List[Dict[str, Any]]:
    """
    Build campaign list from the verse index.
    Groups documents by nom_de_la_campagne_del__c in Python
    (fielddata cannot be enabled — read-only access to the index).
    Uses Statut__c (keyword) aggregation per campaign via filtered queries.
    """
    import logging as _logging
    _log = _logging.getLogger(__name__)
    es = _es_client()
    try:
        # Fetch a large sample — group by campaign name in Python
        res = es._es.search(
            index=_VERSE_INDEX,
            query={"match_all": {}},
            size=5000,
            source=["nom_de_la_campagne_del__c", "Id_campaign__c",
                    "Marche__c", "RC2__c", "Prospecteur__c",
                    "Statut__c", "Active__c", "IsDeleted"],
        )
        docs = [h["_source"] for h in res["hits"]["hits"]]

        # Group in Python
        groups: Dict[str, Dict[str, Any]] = {}
        for d in docs:
            name = d.get("nom_de_la_campagne_del__c") or ""
            if not name:
                continue
            if name not in groups:
                marche = d.get("Marche__c")
            groups[name] = {
                    "id":               name,
                    "title":            name,
                    "campaign_name":    name,
                    "sf_campaign_id":   d.get("Id_campaign__c", ""),
                    "pole":             marche,
                    "interlocutor":     d.get("RC2__c"),
                    "prospecteur":      d.get("Prospecteur__c"),
                    "total_targets":    0,
                    "status_breakdown": {},
                    "status":           "active",
                    # Map Marche__c first, then enrich with name-based inference
                    "product_ids": sorted(set(
                        _MARCHE_TO_PRODUCTS.get(marche, []) +
                        _infer_products_from_name(name)
                    )) if True else [],
                }
            groups[name]["total_targets"] += 1
            status = d.get("Statut__c") or "Unknown"
            groups[name]["status_breakdown"][status] = \
                groups[name]["status_breakdown"].get(status, 0) + 1

        campaigns = sorted(groups.values(), key=lambda c: c["title"])

        # Merge with locally created campaigns (admin-created, not in ES)
        local = _read_local_campaigns()
        verse_names = {c["title"] for c in campaigns}
        for lc in local:
            if lc["title"] not in verse_names:
                campaigns.append(lc)

        return campaigns
    except Exception as exc:
        import logging as _l
        _l.getLogger(__name__).error("list_campaigns (verse) failed: %s", exc)
        # Fallback: return only local campaigns
        return _read_local_campaigns()


def _read_local_campaigns() -> List[Dict[str, Any]]:
    return _read(_LOCAL_CAMPAIGNS_FILE)


def _write_local_campaigns(data: List[Dict[str, Any]]) -> None:
    _write(_LOCAL_CAMPAIGNS_FILE, data)


def get_campaign(campaign_id: str) -> Optional[Dict[str, Any]]:
    """Look in local file first, then verse index."""
    local = next((c for c in _read_local_campaigns() if c["id"] == campaign_id), None)
    if local:
        return local
    return None


def create_campaign(data: Dict[str, Any]) -> Dict[str, Any]:
    """Store in local file — ES is read-only."""
    campaigns = _read_local_campaigns()
    campaign = {
        "id":           _uid("CX"),
        "title":        data["name"],
        "campaign_name":data["name"],
        "description":  data.get("description"),
        "status":       data.get("status", "draft"),
        "pole":         data.get("pole"),
        "type":         data.get("type", "national"),
        "interlocutor": data.get("interlocutor"),
        "start_date":   data.get("start_date"),
        "end_date":     data.get("end_date"),
        "product_ids":  data.get("product_ids", []),
        "sf_campaigns": [],
        "total_targets": 0,
        "status_breakdown": {},
        "source":       "admin",
        "created_at":   _now(),
        "updated_at":   _now(),
    }
    campaigns.append(campaign)
    _write_local_campaigns(campaigns)
    return campaign


def update_campaign(campaign_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update in local file. Verse index campaigns can't be edited (read-only ES)."""
    campaigns = _read_local_campaigns()
    for c in campaigns:
        if c["id"] == campaign_id:
            field_map = {"name": "title"}
            for k, v in updates.items():
                key = field_map.get(k, k)
                if v is not None:
                    c[key] = v
            if "name" in updates:
                c["campaign_name"] = updates["name"]
            c["updated_at"] = _now()
            _write_local_campaigns(campaigns)
            return c
    return None


def delete_campaign(campaign_id: str) -> bool:
    """Delete from local file only."""
    campaigns = _read_local_campaigns()
    filtered = [c for c in campaigns if c["id"] != campaign_id]
    if len(filtered) == len(campaigns):
        return False
    _write_local_campaigns(filtered)
    return True


def get_campaign_targets(campaign_id: str, size: int = 50) -> Dict[str, Any]:
    """
    campaign_id = campaign name (nom_de_la_campagne_del__c) used as stable key.
    Uses match_phrase for exact campaign name matching.
    """
    es = _es_client()
    try:
        res = es._es.search(
            index=_VERSE_INDEX,
            query={"match_phrase": {"nom_de_la_campagne_del__c": campaign_id}},
            size=size,
            sort=[{"LastModifiedDate": {"order": "desc"}}],
        )
        hits  = res.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        raw   = [h["_source"] for h in hits.get("hits", [])]

        targets = []
        status_counts: Dict[str, int] = {}
        for d in raw:
            status = d.get("Statut__c") or "Unknown"
            status_counts[status] = status_counts.get(status, 0) + 1
            # Extract account ID from CampAcc__c by removing campaign name prefix
            camp_name = d.get("nom_de_la_campagne_del__c", "")
            camp_acc  = d.get("CampAcc__c", "")
            account_id = camp_acc.replace(camp_name, "").strip() or d.get("Compte__c", "")
            targets.append({
                "id":           d.get("Id"),
                "account_id":   account_id,
                "account_name": account_id,
                "campaign_name":camp_name,
                "status":       status,
                "market":       d.get("Marche__c"),
                "active":       d.get("Active__c", False),
                "rc1":          d.get("RC1__c"),
                "rc2":          d.get("RC2__c"),
                "prospecteur":  d.get("Prospecteur__c"),
                "nb_appels":    int(d.get("Nombre_d_appels__c") or 0),
                "type_statut":  d.get("Type_Statut__c"),
            })

        return {
            "total":            total,
            "status_breakdown": status_counts,
            "targets":          targets,
        }
    except Exception as exc:
        return {"total": 0, "status_breakdown": {}, "targets": [], "error": str(exc)}




# ── Data Sources ──────────────────────────────────────────────────────────────

def list_sources(client_id: Optional[str] = None) -> List[Dict[str, Any]]:
    sources = _read(_SOURCES_FILE)
    if client_id:
        sources = [s for s in sources if s.get("client_id") == client_id or s.get("client_id") is None]
    return sources


def get_source(source_id: str) -> Optional[Dict[str, Any]]:
    return next((s for s in _read(_SOURCES_FILE) if s["id"] == source_id), None)


def create_source(data: Dict[str, Any]) -> Dict[str, Any]:
    sources = _read(_SOURCES_FILE)
    source = {
        "id":          _uid("SRC"),
        "label":       data["label"],
        "source_type": data["source_type"],
        "client_id":   data.get("client_id"),
        "url":         data.get("url"),
        "enabled":     data.get("enabled", True),
        "config":      data.get("config") or {},
        "created_at":  _now(),
        "updated_at":  _now(),
    }
    sources.append(source)
    _write(_SOURCES_FILE, sources)
    return source


def update_source(source_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    sources = _read(_SOURCES_FILE)
    for s in sources:
        if s["id"] == source_id:
            for k, v in updates.items():
                if v is not None:
                    s[k] = v
            s["updated_at"] = _now()
            _write(_SOURCES_FILE, sources)
            return s
    return None


def delete_source(source_id: str) -> bool:
    sources = _read(_SOURCES_FILE)
    filtered = [s for s in sources if s["id"] != source_id]
    if len(filtered) == len(sources):
        return False
    _write(_SOURCES_FILE, filtered)
    return True
