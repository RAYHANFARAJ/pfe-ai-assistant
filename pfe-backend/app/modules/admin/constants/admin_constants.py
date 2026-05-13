"""Admin module constants — paths and tool keys."""
from __future__ import annotations

from pathlib import Path

OUTPUT_DIR = Path("output")

PRODUCTS_FILE         = OUTPUT_DIR / "products.json"
CRITERIA_FILE         = OUTPUT_DIR / "criteria.json"
CHOICES_FILE          = OUTPUT_DIR / "choice.json"
SOURCES_FILE          = OUTPUT_DIR / "sources.json"
LOCAL_CAMPAIGNS_FILE  = OUTPUT_DIR / "campaigns_admin.json"

VERSE_INDEX  = "verse_sf_pipeline_campaign_target_raw_zone_v20240207"
TARGET_INDEX = VERSE_INDEX

PIPELINE_TOOL_SOURCE_VALUE = "pipeline_tool"
