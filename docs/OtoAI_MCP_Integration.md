# 🚗 OtoAI MCP Integration Guide

## Overview
Integrasi MCP Archon dengan platform OtoAI untuk menyediakan informasi otomotif non-catalog sebagai fallback dan enrichment data.

## Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   OtoAI Platform    │    │   n8n Workflow     │    │   Archon MCP        │
│                     │    │                     │    │                     │
│ ┌─────────────────┐ │    │ ┌─────────────────┐ │    │ ┌─────────────────┐ │
│ │ Internal RAG    │ │◄──►│ │ RAG AI Agent    │ │◄──►│ │ Automotive      │ │
│ │ (Catalog Data)  │ │    │ │                 │ │    │ │ Insights RAG    │ │
│ └─────────────────┘ │    │ └─────────────────┘ │    │ └─────────────────┘ │
│                     │    │                     │    │                     │
│ • Product Specs     │    │ • Tool Routing      │    │ • News & Articles   │
│ • Prices & Models   │    │ • Query Analysis    │    │ • Reviews & Tips    │
│ • Inventory Data    │    │ • Response Merge    │    │ • Market Insights   │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## MCP Tools for OtoAI

### 1. search_automotive_insights
**Primary tool untuk pencarian insights otomotif**

```python
search_automotive_insights(
    query="Honda Civic review",
    source_id="automotive_news",  # Optional
    match_count=5
)
```

**Use Cases:**
- ✅ Car reviews dan expert opinions
- ✅ Maintenance tips dan guides
- ✅ Driving tips dan safety advice
- ✅ Market trends dan analysis
- ❌ Product catalog data (gunakan Internal RAG)

### 2. determine_automotive_search_strategy
**Tool untuk routing decision antara Internal RAG vs MCP**

```python
determine_automotive_search_strategy(
    user_query="Saya mau beli Honda Civic, bagaimana reviewnya?",
    context="user looking for car purchase decision"
)
```

**Response:**
```json
{
  "recommended_tool": "external_automotive_mcp",
  "reason": "Query indicates automotive insights search (reviews, tips, news)",
  "search_type": "insights",
  "confidence": "high"
}
```

### 3. get_automotive_market_insights
**Specialized tool untuk market analysis**

```python
get_automotive_market_insights(
    topic="electric vehicles",
    region="indonesia",
    match_count=3
)
```

### 4. search_automotive_reviews
**Dedicated tool untuk reviews dan opinions**

```python
search_automotive_reviews(
    vehicle_type="SUV",
    brand="Toyota",
    focus="safety",
    match_count=5
)
```

## Query Classification

### Internal RAG (Catalog) Keywords:
```
specifications, specs, price, harga, model, variant, features, fitur, 
engine, mesin, transmission, fuel consumption, available, tersedia, 
stock, dealer, showroom, buy, beli, compare models, bandingkan model, 
which car, mobil mana, budget, anggaran, financing, kredit, dp, cicilan
```

### External MCP (Insights) Keywords:
```
review, ulasan, opinion, pendapat, experience, pengalaman, tips, 
advice, saran, maintenance, perawatan, service, news, berita, 
trend, tren, market, pasar, industry, safety, keamanan, reliability, 
keandalan, problems, masalah, recall, award, penghargaan, test drive
```

## n8n Workflow Configuration untuk OtoAI

### Workflow Structure Sesuai System Prompt:

```json
{
  "workflow_name": "OtoAI_Hybrid_RAG_MCP_Agent",
  "description": "Prioritas PGVector RAG → MCP fallback → PGVector fallback",
  "nodes": [
    {
      "name": "1_Primary_PGVector_Search",
      "type": "Vector DB",
      "description": "Selalu mulai dari PGVector RAG (sumber utama)",
      "parameters": {
        "operation": "search",
        "collection": "automotive_catalog", 
        "query": "{{ $json.user_query }}",
        "limit": 10,
        "threshold": 0.7
      }
    },
    {
      "name": "2_Evaluate_RAG_Results",
      "type": "Code",
      "description": "Evaluasi apakah hasil RAG cukup relevan",
      "parameters": {
        "jsCode": `
          const ragResults = $input.first();
          const resultCount = ragResults?.data?.length || 0;
          const avgScore = ragResults?.data?.reduce((sum, item) => sum + (item.score || 0), 0) / resultCount || 0;
          
          return {
            rag_results: ragResults.data || [],
            result_count: resultCount,
            avg_relevance: avgScore,
            is_sufficient: resultCount >= 3 && avgScore >= 0.7,
            needs_mcp_enrichment: resultCount < 3 || avgScore < 0.7,
            user_query: "{{ $json.user_query }}"
          };
        `
      }
    },
    {
      "name": "3_Route_Decision",
      "type": "Switch", 
      "description": "Route berdasarkan kecukupan hasil RAG",
      "rules": [
        {
          "condition": "{{ $json.is_sufficient === true }}",
          "output": "sufficient_rag"
        },
        {
          "condition": "{{ $json.needs_mcp_enrichment === true }}",
          "output": "mcp_enrichment"
        }
      ]
    },
    {
      "name": "4A_MCP_Query_Analysis",
      "type": "MCP Client",
      "description": "Analisa query untuk MCP yang tepat",
      "parameters": {
        "tool": "determine_automotive_search_strategy",
        "user_query": "{{ $json.user_query }}",
        "context": "enrichment_needed"
      }
    },
    {
      "name": "4B_MCP_Insights_Search",
      "type": "MCP Client",
      "description": "Cari insights dari MCP",
      "parameters": {
        "tool": "search_automotive_insights",
        "query": "{{ $json.user_query }}",
        "match_count": 5
      }
    },
    {
      "name": "4C_MCP_Sales_Support",
      "type": "MCP Client", 
      "description": "Untuk sales conversation support",
      "parameters": {
        "tool": "get_automotive_sales_insights",
        "vehicle_category": "{{ $json.vehicle_category || 'general' }}",
        "budget_range": "{{ $json.budget_range || '' }}",
        "usage_type": "{{ $json.usage_type || 'daily' }}",
        "match_count": 3
      }
    },
    {
      "name": "5_Evaluate_MCP_Results",
      "type": "Code",
      "description": "Evaluasi hasil MCP, fallback ke RAG jika perlu",
      "parameters": {
        "jsCode": `
          const mcpResults = $input.all();
          const hasValidMCP = mcpResults.some(result => 
            result.success && result.results?.length > 0
          );
          
          if (!hasValidMCP) {
            // MCP tidak memberikan hasil memadai, fallback ke RAG
            return {
              use_rag_fallback: true,
              mcp_results: [],
              message: "MCP tidak cukup, gunakan RAG sebagai fallback"
            };
          }
          
          return {
            use_rag_fallback: false,
            mcp_results: mcpResults,
            message: "MCP memberikan hasil yang memadai"
          };
        `
      }
    },
    {
      "name": "6_RAG_Fallback_Search",
      "type": "Vector DB",
      "description": "Fallback ke RAG jika MCP tidak cukup",
      "parameters": {
        "operation": "search",
        "collection": "automotive_catalog",
        "query": "{{ $json.user_query }}",
        "limit": 15,
        "threshold": 0.5
      }
    },
    {
      "name": "7_Final_Response_Merger",
      "type": "Code",
      "description": "Gabungkan semua hasil sesuai prioritas OtoAI",
      "parameters": {
        "jsCode": `
          const primaryRAG = $('1_Primary_PGVector_Search').first()?.data || [];
          const mcpResults = $('4B_MCP_Insights_Search').first()?.results || [];
          const salesInsights = $('4C_MCP_Sales_Support').first()?.sales_insights || [];
          const fallbackRAG = $('6_RAG_Fallback_Search').first()?.data || [];
          
          return {
            primary_source: "PGVector RAG",
            rag_results: primaryRAG.length > 0 ? primaryRAG : fallbackRAG,
            mcp_insights: mcpResults,
            sales_support: salesInsights,
            framing: {
              rag_context: "Berdasarkan katalog produk resmi",
              mcp_context: "Berdasarkan informasi umum di industri otomotif",
              sales_context: "Di media otomotif, produk ini biasanya dikenal dengan"
            },
            total_sources: primaryRAG.length + mcpResults.length + salesInsights.length + fallbackRAG.length,
            search_strategy: "hybrid_rag_mcp_with_fallback"
          };
        `
      }
    }
  ]
}
```

## Enhanced System Prompt Integration

### MCP Tools Mapping untuk OtoAI Sales Flow:

```
## 🛠️ MCP Tools untuk Sales Conversation

### 1. Identifikasi Kebutuhan Phase:
- `get_automotive_sales_insights()` → untuk rekomendasi umum berdasarkan kategori
- `get_automotive_market_insights()` → untuk trend pasar dan analisis

### 2. Rekomendasi Mobil/Motor Phase:  
- `search_automotive_reviews()` → untuk review dan expert opinion
- `get_brand_comparison_insights()` → untuk perbandingan brand

### 3. Handling Objection Phase:
- `get_brand_comparison_insights()` → untuk menjelaskan plus-minus brand
- `search_automotive_insights()` → untuk informasi umum pendukung

### 4. After-Sales Support:
- `get_automotive_maintenance_tips()` → untuk tips perawatan

## 🎯 Framing Context untuk MCP Results:

Ketika menggunakan MCP results, selalu frame dengan konteks yang tepat:

**Sales Insights**: "Berdasarkan informasi umum di industri otomotif..."
**Reviews**: "Di media otomotif, model ini biasanya dikenal dengan..."  
**Market Trends**: "Menurut analisis pasar terkini..."
**Maintenance**: "Berdasarkan tips dari ahli otomotif..."
**Comparisons**: "Perbandingan di industri umumnya menunjukkan..."

## 🔄 Fallback Strategy:

1. **Primary**: PGVector RAG (katalog resmi)
2. **Enrichment**: MCP Tools (insights eksternal)  
3. **Fallback**: PGVector RAG (jika MCP kosong)
4. **Last Resort**: LLM knowledge dengan disclaimer

Jangan pernah mengatakan "tidak ada data" - selalu ada fallback!
```

## Example Queries & Routing

### Catalog Queries (Internal RAG):
```
❓ "Berapa harga Honda Civic 2024?"
🎯 Route: internal_catalog_rag
📊 Data: Pricing, variants, dealer info

❓ "Bandingkan spesifikasi Toyota Camry vs Honda Accord"  
🎯 Route: internal_catalog_rag
📊 Data: Technical specs, features comparison

❓ "Mobil SUV budget 300 juta ada apa saja?"
🎯 Route: internal_catalog_rag  
📊 Data: Available models, pricing, features
```

### Insights Queries (External MCP):
```
❓ "Bagaimana review Honda Civic dari expert?"
🎯 Route: external_automotive_mcp
📊 Data: Expert reviews, ratings, opinions

❓ "Tips perawatan mesin mobil hybrid"
🎯 Route: external_automotive_mcp
📊 Data: Maintenance guides, expert advice

❓ "Trend pasar mobil listrik di Indonesia"  
🎯 Route: external_automotive_mcp
📊 Data: Market analysis, industry trends
```

### Hybrid Queries (Both Sources):
```
❓ "Saya mau beli Honda Civic, bagaimana spek dan reviewnya?"
🎯 Route: BOTH
📊 Internal: Specifications, pricing, variants
📊 External: Reviews, expert opinions, user experiences
```

## Data Sources to Crawl

### Recommended Sources for MCP:
```
🏢 Automotive News Sites:
- otomotif.kompas.com
- oto.detik.com  
- gridoto.com
- carmudi.co.id/journal

📝 Review Sites:
- mobil123.com/berita
- seva.id/blog
- moladin.com/blog

🔧 Maintenance & Tips:
- suzuki.co.id/tips
- toyota.astra.co.id/tips-berkendara
- honda-indonesia.com/tips

📊 Market Analysis:
- gaikindo.or.id
- aisi.or.id (motorcycle)
```

## Performance Optimization

### Caching Strategy:
```python
# Cache frequently accessed insights
CACHE_DURATION = {
    "market_insights": 24 * 60 * 60,  # 24 hours
    "reviews": 12 * 60 * 60,          # 12 hours  
    "news": 6 * 60 * 60,              # 6 hours
    "tips": 7 * 24 * 60 * 60          # 7 days
}
```

### Query Optimization:
```python
# Keep queries short and focused
GOOD_QUERIES = [
    "Honda Civic review",
    "SUV safety tips", 
    "electric car maintenance"
]

BAD_QUERIES = [
    "comprehensive review of Honda Civic 2024 model with all features and specifications including engine performance and fuel efficiency compared to competitors"
]
```

## Monitoring & Analytics

### Key Metrics:
- Tool selection accuracy
- Query routing success rate  
- Response relevance scores
- User satisfaction feedback
- Search result diversity

### Logging:
```python
{
  "timestamp": "2024-01-15T10:30:00Z",
  "query": "Honda Civic review",
  "routing_decision": "external_mcp",
  "confidence": "high", 
  "results_count": 5,
  "response_time_ms": 1250,
  "user_satisfaction": 4.5
}
```

## 💬 Contoh Sales Conversation Flow dengan MCP

### Scenario 1: Customer Mencari SUV Budget 400 Juta

```
👤 User: "Saya mau cari SUV budget 400 jutaan untuk keluarga"

🤖 OtoAI Flow:
1. PGVector RAG → cari SUV 350-450 juta (katalog resmi)
2. MCP get_automotive_sales_insights(vehicle_category="SUV", budget_range="400", usage_type="family")
3. Response: 
   "Berdasarkan katalog kami, ada 3 pilihan SUV terbaik di budget 400 jutaan:
   1. Honda CR-V - Rp 398 juta ✅ Spacious, reliable
   2. Mazda CX-5 - Rp 415 juta ✅ Premium feel, safety
   3. Toyota RAV4 - Rp 425 juta ✅ Resale value tinggi
   
   Berdasarkan informasi umum di industri otomotif, SUV di range ini biasanya 
   paling cocok untuk keluarga karena kombinasi comfort dan safety yang optimal."
```

### Scenario 2: Customer Bingung Pilih Brand

```
👤 User: "Honda vs Toyota mana yang lebih bagus?"

🤖 OtoAI Flow:
1. MCP get_brand_comparison_insights(brand_a="Honda", brand_b="Toyota", comparison_aspect="reliability")
2. PGVector RAG → cari model Honda vs Toyota (untuk data spesifik)
3. Response:
   "Di media otomotif, perbandingan Honda vs Toyota biasanya menunjukkan:
   
   🏆 Honda: Lebih sporty, teknologi canggih, fun to drive
   🏆 Toyota: Reliability legend, resale value tinggi, after-sales luas
   
   Dari katalog kami, bisa saya rekomendasikan:
   - Honda: Civic (sedan), CR-V (SUV), HR-V (crossover)  
   - Toyota: Camry (sedan), RAV4 (SUV), C-HR (crossover)
   
   Mau fokus ke kategori apa dulu, Pak?"
```

### Scenario 3: After-Sales Question

```
👤 User: "Kalau beli Honda CR-V, perawatannya gimana?"

🤖 OtoAI Flow:
1. PGVector RAG → cari info service Honda CR-V (official data)
2. MCP get_automotive_maintenance_tips(vehicle_type="SUV", maintenance_category="routine")
3. Response:
   "Untuk Honda CR-V, service resmi setiap 10.000 km dengan biaya sekitar Rp 800rb-1.2 juta.
   
   Berdasarkan tips dari ahli otomotif, SUV Honda umumnya:
   ✅ Spare parts mudah dicari
   ✅ Bengkel resmi tersebar luas  
   ✅ Maintenance cost reasonable
   
   Mau saya bantu jadwalkan test drive dulu, Pak? 🚗"
```

## 🎯 Key Benefits untuk OtoAI

### 1. **Comprehensive Information**
- Katalog resmi (specs, harga, promo) dari PGVector RAG
- Industry insights (reviews, tips, trends) dari MCP
- Fallback mechanism yang robust

### 2. **Natural Sales Flow**  
- Tools yang mendukung setiap tahap sales conversation
- Framing yang tepat untuk setiap sumber informasi
- Handling objection yang lebih kuat

### 3. **Enhanced User Experience**
- Tidak pernah "tidak ada data"
- Informasi yang lebih lengkap dan kontekstual
- Rekomendasi yang lebih personal dan akurat

### 4. **Scalable Architecture**
- MCP sebagai enrichment layer yang bisa dikembangkan
- Separation of concerns yang jelas
- Easy monitoring dan optimization

This integration transforms OtoAI from a simple catalog search into a comprehensive automotive advisor that combines official product data with industry expertise, creating a more engaging and informative customer experience.