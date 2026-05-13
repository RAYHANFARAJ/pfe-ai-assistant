"""Central registry of every constant used across modules.

No magic string is allowed inline — import from here instead.
"""
from __future__ import annotations


class AdminRoles:
    """Keycloak realm role names used for access control."""

    ADMIN = "admin"
    APP_USER = "app-user"


class AdminRoutePrefix:
    """URL prefixes for the admin module."""

    ROOT = "/api/admin"


class AdminResourceLabels:
    """Human-readable resource names used in 404 / error messages."""

    PRODUCT = "Product"
    CRITERION = "Criterion"
    CHOICE = "Choice"
    CAMPAIGN = "Campaign"
    SOURCE = "Source"


class JsonFileKeys:
    """Top-level keys expected inside the JSON reference files."""

    PRODUCT_ID = "id"
    PRODUCT_NAME = "name"
    CRITERION_ID = "id"
    CRITERION_PRODUCT_ID = "product_id"
    CRITERION_CAMPAIGN_ID = "campaign_id"
    CHOICE_ID = "id"
    CHOICE_CRITERIA_ID = "criteria_id"


class IdPrefixes:
    """UUID-based ID prefixes for each domain entity."""

    PRODUCT_ID_FORMAT = "P{:03d}"
    CRITERION = "QX"
    CHOICE = "CH"
    CAMPAIGN = "CX"
    SOURCE = "SRC"


class CampaignStatus:
    """Allowed values for the campaign status field."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVE = "archive"


class SourceType:
    """Allowed values for the data source type field."""

    WEBSITE = "website"
    LINKEDIN = "linkedin"
    NEWS = "news"
    DOCUMENT = "document"
    CRM = "crm"
    PIPELINE_TOOL = "pipeline_tool"


class ScoringAnswerType:
    """Allowed criterion answer types."""

    NUMERIC = "numeric"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"


class ElasticsearchRoutePrefix:
    """URL prefixes for the Elasticsearch module."""

    ACCOUNTS = "/api/accounts"
    PRODUCTS = "/api/products"
    DEBUG = "/api/debug/es"


class DocumentRoutingKeys:
    """Keys used in the document routing cache JSON."""

    FILENAME = "filename"
    CLIENT_ID = "client_id"


class MarcheToProductMapping:
    """Mapping from Salesforce Marche__c field values to product IDs."""

    MAPPING = {
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
