from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.services.scoring.scoring_pipeline_service import ScoringPipelineService
from app.tools.es_client_tool import ESClientTool
from app.tools.es_reference_tool import ESReferenceTool
from app.tools.social_media_tool import SocialMediaTool
from app.tools.website_crawl_tool import WebsiteCrawlTool

mcp = FastMCP(
    "PFE Scoring MCP",
    instructions=(
        "This MCP server exposes tools to score a client against a product. "
        "Use the reference tool to load product criteria, the ES tool to load client data, "
        "the website tool to crawl the website, the social tool to consolidate social signals, "
        "and the scoring tool to produce a final eligibility score."
    ),
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
)

es_client_tool = ESClientTool()
es_reference_tool = ESReferenceTool()
website_crawl_tool = WebsiteCrawlTool()
social_media_tool = SocialMediaTool()
scoring_pipeline = ScoringPipelineService()


@mcp.tool()
def get_client_account(client_id: str) -> dict:
    """Return internal client account data from Elasticsearch using client_id."""
    return es_client_tool.run(client_id)


@mcp.tool()
def get_product_reference(product_id: str) -> dict:
    """Return product metadata and criteria using product_id."""
    product = es_reference_tool.get_product(product_id)
    criteria = es_reference_tool.get_criteria(product_id)
    return {
        "product": product,
        "criteria": criteria,
    }


@mcp.tool()
def crawl_client_website(website_url: str) -> dict:
    """Crawl a client website and return key pages and detected social links."""
    return website_crawl_tool.run(website_url)


@mcp.tool()
def get_social_signals(client_id: str, website_url: str | None = None) -> dict:
    """Return consolidated social links and social snippets for a client."""
    client_data = es_client_tool.run(client_id)
    website_data = website_crawl_tool.run(website_url or client_data.get("website"))
    return social_media_tool.run(client_data, website_data)


@mcp.tool()
def score_client_product(client_id: str, product_id: str) -> dict:
    """Run the full scoring pipeline for one client and one product."""
    return scoring_pipeline.run(client_id=client_id, product_id=product_id)

