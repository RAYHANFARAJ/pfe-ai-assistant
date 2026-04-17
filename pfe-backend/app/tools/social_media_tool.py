from __future__ import annotations

from typing import Any, Dict


class SocialMediaTool:
    def run(self, client_data: Dict[str, Any], website_data: Dict[str, Any]) -> Dict[str, Any]:
        social_links = dict(website_data.get("social_links", {}))

        # Resolve linkedin from any field variant present in client_data
        linkedin_from_client = (
            client_data.get("linkedin")
            or client_data.get("linkedin_url")
            or client_data.get("LinkedIn_URL__c")
        )
        if linkedin_from_client and "linkedin" not in social_links:
            social_links["linkedin"] = linkedin_from_client

        snippets = []

        if "linkedin" in social_links:
            snippets.append("LinkedIn presence detected for the company.")
        if "instagram" in social_links:
            snippets.append("Instagram presence detected for the company.")
        if "facebook" in social_links:
            snippets.append("Facebook presence detected for the company.")
        if "youtube" in social_links:
            snippets.append("YouTube presence detected for the company.")

        return {
            "links": social_links,
            "snippets": snippets,
        }
