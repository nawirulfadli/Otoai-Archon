"""
RAG Module for Archon MCP Server (HTTP-based version)

This module provides tools for:
- RAG query and search
- Source management
- Code example extraction and search

This version uses HTTP calls to the server service instead of importing
service modules directly, enabling true microservices architecture.
"""

import json
import logging
import os
from urllib.parse import urljoin

import httpx
from mcp.server.fastmcp import Context, FastMCP

# Import service discovery for HTTP communication
from src.server.config.service_discovery import get_api_url

logger = logging.getLogger(__name__)


def get_setting(key: str, default: str = "false") -> str:
    """Get a setting from environment variable."""
    return os.getenv(key, default)


def get_bool_setting(key: str, default: bool = False) -> bool:
    """Get a boolean setting from environment variable."""
    value = get_setting(key, "false" if not default else "true")
    return value.lower() in ("true", "1", "yes", "on")


def register_rag_tools(mcp: FastMCP):
    """Register all RAG tools with the MCP server."""

    @mcp.tool()
    async def rag_get_available_sources(ctx: Context) -> str:
        """
        Get list of available sources in the knowledge base.

        Returns:
            JSON string with structure:
            - success: bool - Operation success status
            - sources: list[dict] - Array of source objects
            - count: int - Number of sources
            - error: str - Error description if success=false
        """
        try:
            api_url = get_api_url()
            timeout = httpx.Timeout(30.0, connect=5.0)

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(urljoin(api_url, "/api/rag/sources"))

                if response.status_code == 200:
                    result = response.json()
                    sources = result.get("sources", [])

                    return json.dumps(
                        {"success": True, "sources": sources, "count": len(sources)}, indent=2
                    )
                else:
                    error_detail = response.text
                    return json.dumps(
                        {"success": False, "error": f"HTTP {response.status_code}: {error_detail}"},
                        indent=2,
                    )

        except Exception as e:
            logger.error(f"Error getting sources: {e}")
            return json.dumps({"success": False, "error": str(e)}, indent=2)

    @mcp.tool()
    async def search_automotive_insights(
        ctx: Context, query: str, source_id: str | None = None, match_count: int = 5
    ) -> str:
        """
        Search automotive knowledge base for insights, news, reviews, and tips (NON-CATALOG content).
        
        🚗 PERFECT FOR OtoAI Platform:
        - Automotive news and industry updates
        - Car reviews and expert opinions
        - Maintenance tips and guides
        - Driving tips and safety advice
        - Market trends and analysis
        - Brand comparisons and insights
        - Automotive technology articles
        - User experiences and testimonials
        
        ❌ NEVER USE FOR (Use Internal RAG instead):
        - Product catalog data (car models, specs, prices)
        - Inventory information
        - Dealer listings
        - Specific vehicle availability
        - Technical specifications from catalog
        - Spare parts catalog data
        
        Args:
            query: Automotive search query - Keep it SHORT and FOCUSED (2-5 keywords).
                   Good Examples: "Honda Civic review", "electric car maintenance", "SUV safety tips"
                   Bad Example: "comprehensive review of Honda Civic 2024 model with all features and specifications including engine performance and fuel efficiency"
            source_id: Optional source ID filter from rag_get_available_sources().
                      This is the 'id' field from available sources, NOT a URL or domain name.
                      Example: "src_automotive_news" not "otomotif.com"
            match_count: Max results (default: 5)

        Returns:
            JSON string with structure:
            - success: bool - Operation success status
            - results: list[dict] - Array of matching documents with content and metadata
            - reranked: bool - Whether results were reranked
            - error: str|null - Error description if success=false
        """
        try:
            api_url = get_api_url()
            timeout = httpx.Timeout(30.0, connect=5.0)

            async with httpx.AsyncClient(timeout=timeout) as client:
                request_data = {"query": query, "match_count": match_count}
                if source_id:
                    request_data["source"] = source_id

                response = await client.post(urljoin(api_url, "/api/rag/query"), json=request_data)

                if response.status_code == 200:
                    result = response.json()
                    return json.dumps(
                        {
                            "success": True,
                            "results": result.get("results", []),
                            "reranked": result.get("reranked", False),
                            "error": None,
                        },
                        indent=2,
                    )
                else:
                    error_detail = response.text
                    return json.dumps(
                        {
                            "success": False,
                            "results": [],
                            "error": f"HTTP {response.status_code}: {error_detail}",
                        },
                        indent=2,
                    )

        except Exception as e:
            logger.error(f"Error performing RAG query: {e}")
            return json.dumps({"success": False, "results": [], "error": str(e)}, indent=2)

    @mcp.tool()
    async def rag_search_code_examples(
        ctx: Context, query: str, source_id: str | None = None, match_count: int = 5
    ) -> str:
        """
        Search for relevant code examples in the knowledge base.

        Args:
            query: Search query - Keep it SHORT and FOCUSED (2-5 keywords).
                   Good: "React useState", "FastAPI middleware", "vector pgvector"
                   Bad: "React hooks useState useEffect useContext useReducer useMemo useCallback"
            source_id: Optional source ID filter from rag_get_available_sources().
                      This is the 'id' field from available sources, NOT a URL or domain name.
                      Example: "src_1234abcd" not "docs.anthropic.com"
            match_count: Max results (default: 5)

        Returns:
            JSON string with structure:
            - success: bool - Operation success status
            - results: list[dict] - Array of code examples with content and summaries
            - reranked: bool - Whether results were reranked
            - error: str|null - Error description if success=false
        """
        try:
            api_url = get_api_url()
            timeout = httpx.Timeout(30.0, connect=5.0)

            async with httpx.AsyncClient(timeout=timeout) as client:
                request_data = {"query": query, "match_count": match_count}
                if source_id:
                    request_data["source"] = source_id

                # Call the dedicated code examples endpoint
                response = await client.post(
                    urljoin(api_url, "/api/rag/code-examples"), json=request_data
                )

                if response.status_code == 200:
                    result = response.json()
                    return json.dumps(
                        {
                            "success": True,
                            "results": result.get("results", []),
                            "reranked": result.get("reranked", False),
                            "error": None,
                        },
                        indent=2,
                    )
                else:
                    error_detail = response.text
                    return json.dumps(
                        {
                            "success": False,
                            "results": [],
                            "error": f"HTTP {response.status_code}: {error_detail}",
                        },
                        indent=2,
                    )

        except Exception as e:
            logger.error(f"Error searching code examples: {e}")
            return json.dumps({"success": False, "results": [], "error": str(e)}, indent=2)

    @mcp.tool()
    async def determine_automotive_search_strategy(ctx: Context, user_query: str, context: str = "") -> str:
        """
        Determine which search tool to use for automotive queries: Internal Catalog RAG vs External Insights MCP.
        
        Args:
            user_query: The user's original automotive search request
            context: Additional context about what the user is looking for
            
        Returns:
            JSON recommendation for which tool to use and why
        """
        try:
            # Keywords that indicate CATALOG search (Internal RAG)
            catalog_keywords = [
                "specifications", "specs", "price", "harga", "model", "variant", 
                "features", "fitur", "engine", "mesin", "transmission", "fuel consumption",
                "available", "tersedia", "stock", "dealer", "showroom", "buy", "beli",
                "compare models", "bandingkan model", "which car", "mobil mana",
                "budget", "anggaran", "financing", "kredit", "dp", "cicilan"
            ]
            
            # Keywords that indicate INSIGHTS search (External MCP)
            insights_keywords = [
                "review", "ulasan", "opinion", "pendapat", "experience", "pengalaman",
                "tips", "advice", "saran", "maintenance", "perawatan", "service",
                "news", "berita", "trend", "tren", "market", "pasar", "industry",
                "safety", "keamanan", "reliability", "keandalan", "problems", "masalah",
                "recall", "award", "penghargaan", "test drive", "road test"
            ]
            
            query_lower = user_query.lower()
            context_lower = context.lower()
            combined_text = f"{query_lower} {context_lower}"
            
            catalog_score = sum(1 for keyword in catalog_keywords if keyword in combined_text)
            insights_score = sum(1 for keyword in insights_keywords if keyword in combined_text)
            
            recommendation = {
                "user_query": user_query,
                "platform": "OtoAI",
                "analysis": {
                    "catalog_indicators": catalog_score,
                    "insights_indicators": insights_score,
                    "detected_keywords": {
                        "catalog": [kw for kw in catalog_keywords if kw in combined_text],
                        "insights": [kw for kw in insights_keywords if kw in combined_text]
                    }
                }
            }
            
            if catalog_score > insights_score:
                recommendation["recommended_tool"] = "internal_catalog_rag"
                recommendation["reason"] = "Query indicates product catalog search (specs, prices, models)"
                recommendation["confidence"] = "high" if catalog_score >= 2 else "medium"
                recommendation["search_type"] = "catalog"
            elif insights_score > catalog_score:
                recommendation["recommended_tool"] = "external_automotive_mcp"
                recommendation["reason"] = "Query indicates automotive insights search (reviews, tips, news)"
                recommendation["confidence"] = "high" if insights_score >= 2 else "medium"
                recommendation["search_type"] = "insights"
            else:
                # Enhanced default logic for automotive context
                if any(word in combined_text for word in ["mobil", "motor", "car", "motorcycle", "vehicle"]):
                    if any(word in combined_text for word in ["beli", "buy", "pilih", "choose", "rekomendasi"]):
                        recommendation["recommended_tool"] = "internal_catalog_rag"
                        recommendation["reason"] = "Purchase intent detected - use catalog for product recommendations"
                        recommendation["search_type"] = "catalog"
                    else:
                        recommendation["recommended_tool"] = "external_automotive_mcp"
                        recommendation["reason"] = "General automotive query - use insights for additional information"
                        recommendation["search_type"] = "insights"
                else:
                    recommendation["recommended_tool"] = "external_automotive_mcp"
                    recommendation["reason"] = "Ambiguous query - default to insights search"
                    recommendation["search_type"] = "insights"
                recommendation["confidence"] = "low"
            
            return json.dumps(recommendation, indent=2)
            
        except Exception as e:
            logger.error(f"Error in automotive search strategy determination: {e}")
            return json.dumps({
                "error": str(e),
                "fallback_recommendation": "external_automotive_mcp",
                "reason": "Error occurred, defaulting to automotive insights search",
                "search_type": "insights"
            }, indent=2)

    @mcp.tool()
    async def get_automotive_market_insights(
        ctx: Context, topic: str, region: str = "indonesia", match_count: int = 3
    ) -> str:
        """
        Get automotive market insights, trends, and analysis for OtoAI platform.
        
        Args:
            topic: Market topic (e.g., "electric vehicles", "SUV trends", "motorcycle market")
            region: Geographic region for market data (default: "indonesia")
            match_count: Max results (default: 3)
            
        Returns:
            JSON with market insights, trends, and analysis
        """
        try:
            # Construct market-focused query
            market_query = f"{topic} market trends {region} automotive industry"
            
            api_url = get_api_url()
            timeout = httpx.Timeout(30.0, connect=5.0)

            async with httpx.AsyncClient(timeout=timeout) as client:
                request_data = {
                    "query": market_query, 
                    "match_count": match_count,
                    "source": "automotive_market"  # Filter to market-specific sources
                }

                response = await client.post(urljoin(api_url, "/api/rag/query"), json=request_data)

                if response.status_code == 200:
                    result = response.json()
                    
                    # Enhance response with market context
                    enhanced_result = {
                        "success": True,
                        "topic": topic,
                        "region": region,
                        "market_insights": result.get("results", []),
                        "analysis_type": "market_trends",
                        "reranked": result.get("reranked", False),
                        "error": None,
                    }
                    
                    return json.dumps(enhanced_result, indent=2)
                else:
                    error_detail = response.text
                    return json.dumps({
                        "success": False,
                        "topic": topic,
                        "region": region,
                        "market_insights": [],
                        "error": f"HTTP {response.status_code}: {error_detail}",
                    }, indent=2)

        except Exception as e:
            logger.error(f"Error getting automotive market insights: {e}")
            return json.dumps({
                "success": False,
                "topic": topic,
                "region": region,
                "market_insights": [],
                "error": str(e)
            }, indent=2)

    @mcp.tool()
    async def search_automotive_reviews(
        ctx: Context, vehicle_type: str, brand: str = "", focus: str = "general", match_count: int = 5
    ) -> str:
        """
        Search for automotive reviews and expert opinions (NON-CATALOG content for OtoAI).
        
        Args:
            vehicle_type: Type of vehicle ("car", "motorcycle", "SUV", "sedan", "hatchback", etc.)
            brand: Optional brand filter ("Honda", "Toyota", "Yamaha", etc.)
            focus: Review focus ("performance", "safety", "comfort", "fuel_efficiency", "general")
            match_count: Max results (default: 5)
            
        Returns:
            JSON with reviews, ratings, and expert opinions
        """
        try:
            # Construct review-focused query
            query_parts = [vehicle_type, "review"]
            if brand:
                query_parts.insert(1, brand)
            if focus != "general":
                query_parts.append(focus)
            
            review_query = " ".join(query_parts)
            
            api_url = get_api_url()
            timeout = httpx.Timeout(30.0, connect=5.0)

            async with httpx.AsyncClient(timeout=timeout) as client:
                request_data = {
                    "query": review_query,
                    "match_count": match_count,
                    "source": "automotive_reviews"  # Filter to review sources
                }

                response = await client.post(urljoin(api_url, "/api/rag/query"), json=request_data)

                if response.status_code == 200:
                    result = response.json()
                    
                    # Enhance response with review context
                    enhanced_result = {
                        "success": True,
                        "vehicle_type": vehicle_type,
                        "brand": brand or "all_brands",
                        "focus": focus,
                        "reviews": result.get("results", []),
                        "content_type": "reviews_and_opinions",
                        "reranked": result.get("reranked", False),
                        "error": None,
                    }
                    
                    return json.dumps(enhanced_result, indent=2)
                else:
                    error_detail = response.text
                    return json.dumps({
                        "success": False,
                        "vehicle_type": vehicle_type,
                        "brand": brand,
                        "focus": focus,
                        "reviews": [],
                        "error": f"HTTP {response.status_code}: {error_detail}",
                    }, indent=2)

        except Exception as e:
            logger.error(f"Error searching automotive reviews: {e}")
            return json.dumps({
                "success": False,
                "vehicle_type": vehicle_type,
                "brand": brand,
                "focus": focus,
                "reviews": [],
                "error": str(e)
            }, indent=2)

    @mcp.tool()
    async def get_automotive_sales_insights(
        ctx: Context, 
        vehicle_category: str, 
        budget_range: str = "", 
        usage_type: str = "daily", 
        match_count: int = 3
    ) -> str:
        """
        Get automotive sales insights untuk mendukung OtoAI sales conversation.
        Digunakan sebagai fallback/enrichment ketika PGVector RAG tidak cukup.
        
        Args:
            vehicle_category: Kategori kendaraan ("SUV", "MPV", "hatchback", "sedan", "motor", "listrik")
            budget_range: Range budget ("under_200", "200_400", "400_600", "above_600") dalam juta
            usage_type: Tipe penggunaan ("daily", "family", "long_trip", "business")
            match_count: Max results (default: 3)
            
        Returns:
            JSON dengan sales insights, tips, dan rekomendasi umum
        """
        try:
            # Construct sales-focused query
            query_parts = [vehicle_category]
            if budget_range:
                query_parts.append(f"budget {budget_range} juta")
            query_parts.extend([usage_type, "rekomendasi", "tips"])
            
            sales_query = " ".join(query_parts)
            
            api_url = get_api_url()
            timeout = httpx.Timeout(30.0, connect=5.0)

            async with httpx.AsyncClient(timeout=timeout) as client:
                request_data = {
                    "query": sales_query,
                    "match_count": match_count,
                    "source": "automotive_sales"  # Filter to sales-related sources
                }

                response = await client.post(urljoin(api_url, "/api/rag/query"), json=request_data)

                if response.status_code == 200:
                    result = response.json()
                    
                    # Enhance response with sales context
                    enhanced_result = {
                        "success": True,
                        "vehicle_category": vehicle_category,
                        "budget_range": budget_range,
                        "usage_type": usage_type,
                        "sales_insights": result.get("results", []),
                        "content_type": "sales_guidance",
                        "framing_context": "Berdasarkan informasi umum di industri otomotif",
                        "reranked": result.get("reranked", False),
                        "error": None,
                    }
                    
                    return json.dumps(enhanced_result, indent=2)
                else:
                    error_detail = response.text
                    return json.dumps({
                        "success": False,
                        "vehicle_category": vehicle_category,
                        "budget_range": budget_range,
                        "usage_type": usage_type,
                        "sales_insights": [],
                        "error": f"HTTP {response.status_code}: {error_detail}",
                    }, indent=2)

        except Exception as e:
            logger.error(f"Error getting automotive sales insights: {e}")
            return json.dumps({
                "success": False,
                "vehicle_category": vehicle_category,
                "budget_range": budget_range,
                "usage_type": usage_type,
                "sales_insights": [],
                "error": str(e)
            }, indent=2)

    @mcp.tool()
    async def get_brand_comparison_insights(
        ctx: Context, 
        brand_a: str, 
        brand_b: str, 
        comparison_aspect: str = "general", 
        match_count: int = 4
    ) -> str:
        """
        Get brand comparison insights untuk mendukung handling objection di OtoAI.
        Digunakan ketika customer membandingkan brand atau model.
        
        Args:
            brand_a: Brand pertama (e.g., "Honda", "Toyota", "Yamaha")
            brand_b: Brand kedua (e.g., "Mazda", "Mitsubishi", "Kawasaki") 
            comparison_aspect: Aspek perbandingan ("reliability", "maintenance", "resale_value", "performance", "general")
            match_count: Max results (default: 4)
            
        Returns:
            JSON dengan insights perbandingan brand
        """
        try:
            # Construct comparison-focused query
            comparison_query = f"{brand_a} vs {brand_b} {comparison_aspect} comparison"
            
            api_url = get_api_url()
            timeout = httpx.Timeout(30.0, connect=5.0)

            async with httpx.AsyncClient(timeout=timeout) as client:
                request_data = {
                    "query": comparison_query,
                    "match_count": match_count,
                    "source": "automotive_comparison"  # Filter to comparison sources
                }

                response = await client.post(urljoin(api_url, "/api/rag/query"), json=request_data)

                if response.status_code == 200:
                    result = response.json()
                    
                    # Enhance response with comparison context
                    enhanced_result = {
                        "success": True,
                        "brand_a": brand_a,
                        "brand_b": brand_b,
                        "comparison_aspect": comparison_aspect,
                        "comparison_insights": result.get("results", []),
                        "content_type": "brand_comparison",
                        "framing_context": "Di media otomotif, perbandingan ini biasanya menunjukkan",
                        "reranked": result.get("reranked", False),
                        "error": None,
                    }
                    
                    return json.dumps(enhanced_result, indent=2)
                else:
                    error_detail = response.text
                    return json.dumps({
                        "success": False,
                        "brand_a": brand_a,
                        "brand_b": brand_b,
                        "comparison_aspect": comparison_aspect,
                        "comparison_insights": [],
                        "error": f"HTTP {response.status_code}: {error_detail}",
                    }, indent=2)

        except Exception as e:
            logger.error(f"Error getting brand comparison insights: {e}")
            return json.dumps({
                "success": False,
                "brand_a": brand_a,
                "brand_b": brand_b,
                "comparison_aspect": comparison_aspect,
                "comparison_insights": [],
                "error": str(e)
            }, indent=2)

    @mcp.tool()
    async def get_automotive_maintenance_tips(
        ctx: Context, 
        vehicle_type: str, 
        maintenance_category: str = "general", 
        match_count: int = 3
    ) -> str:
        """
        Get automotive maintenance tips untuk mendukung after-sales conversation di OtoAI.
        
        Args:
            vehicle_type: Tipe kendaraan ("car", "motorcycle", "SUV", "MPV", "sedan", "hatchback")
            maintenance_category: Kategori maintenance ("routine", "seasonal", "troubleshooting", "cost_saving", "general")
            match_count: Max results (default: 3)
            
        Returns:
            JSON dengan tips maintenance dan perawatan
        """
        try:
            # Construct maintenance-focused query
            maintenance_query = f"{vehicle_type} {maintenance_category} maintenance tips perawatan"
            
            api_url = get_api_url()
            timeout = httpx.Timeout(30.0, connect=5.0)

            async with httpx.AsyncClient(timeout=timeout) as client:
                request_data = {
                    "query": maintenance_query,
                    "match_count": match_count,
                    "source": "automotive_maintenance"  # Filter to maintenance sources
                }

                response = await client.post(urljoin(api_url, "/api/rag/query"), json=request_data)

                if response.status_code == 200:
                    result = response.json()
                    
                    # Enhance response with maintenance context
                    enhanced_result = {
                        "success": True,
                        "vehicle_type": vehicle_type,
                        "maintenance_category": maintenance_category,
                        "maintenance_tips": result.get("results", []),
                        "content_type": "maintenance_guidance",
                        "framing_context": "Berdasarkan tips dari ahli otomotif",
                        "reranked": result.get("reranked", False),
                        "error": None,
                    }
                    
                    return json.dumps(enhanced_result, indent=2)
                else:
                    error_detail = response.text
                    return json.dumps({
                        "success": False,
                        "vehicle_type": vehicle_type,
                        "maintenance_category": maintenance_category,
                        "maintenance_tips": [],
                        "error": f"HTTP {response.status_code}: {error_detail}",
                    }, indent=2)

        except Exception as e:
            logger.error(f"Error getting automotive maintenance tips: {e}")
            return json.dumps({
                "success": False,
                "vehicle_type": vehicle_type,
                "maintenance_category": maintenance_category,
                "maintenance_tips": [],
                "error": str(e)
            }, indent=2)

    # Log successful registration
    logger.info("✓ OtoAI Automotive RAG tools registered (7 tools total) - HTTP-based version")
