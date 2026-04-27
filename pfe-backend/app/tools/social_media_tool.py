from __future__ import annotations

from typing import Any, Dict


class SocialMediaTool:
    """
    Collects detected social media links from website crawl results.

    LinkedIn content is now handled by LinkedInCrawlTool as a full semantic
    source — this tool only surfaces link URLs for metadata purposes.
    """

    def run(self, client_data: Dict[str, Any], website_data: Dict[str, Any]) -> Dict[str, Any]:
        social_links = dict(website_data.get("social_links", {}))

        linkedin_from_client = (
            client_data.get("linkedin")
            or client_data.get("linkedin_url")
            or client_data.get("LinkedIn_URL__c")
        )
        if linkedin_from_client and "linkedin" not in social_links:
            social_links["linkedin"] = linkedin_from_client

        return {"links": social_links}
