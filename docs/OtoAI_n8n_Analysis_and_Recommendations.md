# 🔍 Analisa n8n Workflow OtoAI & Rekomendasi Modifikasi

## 📊 **Current Workflow Analysis**

### **Struktur Workflow Saat Ini:**
```
Chat Trigger/Webhook → Edit Fields → RAG AI Agent → Respond to Webhook
                                        ↓
                                   Tools Connected:
                                   • Postgres PGVector Store (Primary)
                                   • List Documents
                                   • Get File Contents  
                                   • Query Document Rows
                                   • MCP Client (Limited: 2 tools)
```

### **Tools yang Sudah Ada:**

#### **1. PGVector RAG Tools (Internal Catalog):**
- ✅ **Postgres PGVector Store** - Vector search dengan reranker Cohere
- ✅ **List Documents** - Metadata dokumen
- ✅ **Get File Contents** - Konten dokumen lengkap
- ✅ **Query Document Rows** - SQL query untuk data tabular

#### **2. MCP Tools (External Insights) - TERBATAS:**
- ⚠️ **Hanya 2 tools**: `rag_get_available_sources`, `rag_search_knowledge_base`
- ❌ **Missing 5 tools** yang sudah saya buat untuk OtoAI

### **System Prompt Analysis:**
✅ **Sudah Perfect** - Sesuai dengan prioritas RAG → MCP → RAG fallback
✅ **Framing context** sudah tepat
✅ **Sales conversation flow** sudah terstruktur

## 🎯 **Rekomendasi Modifikasi**

### **1. Update MCP Client Configuration**

**Current MCP Client:**
```json
{
  "endpointUrl": "http://116.193.190.118:8051/mcp",
  "include": "selected",
  "includeTools": [
    "rag_get_available_sources",
    "rag_search_knowledge_base"  // ← Tool lama
  ]
}
```

**Recommended MCP Client:**
```json
{
  "endpointUrl": "http://116.193.190.118:8051/mcp",
  "include": "selected", 
  "includeTools": [
    "rag_get_available_sources",
    "search_automotive_insights",           // ← Tool baru (renamed)
    "determine_automotive_search_strategy", // ← Tool routing
    "get_automotive_sales_insights",        // ← Sales support
    "search_automotive_reviews",            // ← Reviews & opinions
    "get_brand_comparison_insights",        // ← Brand comparison
    "get_automotive_maintenance_tips"       // ← After-sales support
  ]
}
```

### **2. Update Tool Descriptions**

**Current PGVector Description:**
```
"Gunakan tool ini sebagai sumber utama untuk semua pertanyaan terkait mobil atau motor, 
katalog produk resmi, spesifikasi, harga, promo, dan dokumen. 
Selalu cari jawaban di sini terlebih dahulu sebelum menggunakan tool lain."
```

**Enhanced PGVector Description:**
```
"🎯 SUMBER UTAMA: Gunakan tool ini PERTAMA untuk semua pertanyaan terkait:
• Katalog produk resmi (mobil, motor, spareparts)
• Spesifikasi teknis dan fitur
• Harga, promo, dan penawaran khusus  
• Data inventory dan ketersediaan
• Informasi dealer dan financing

⚡ PRIORITAS TINGGI: Selalu cari di sini dulu sebelum menggunakan MCP tools!"
```

### **3. Workflow Enhancement (Optional)**

Jika ingin optimasi lebih lanjut, bisa tambahkan node untuk **intelligent routing**:

```json
{
  "name": "Query Intent Analyzer",
  "type": "n8n-nodes-base.code",
  "parameters": {
    "jsCode": `
      const query = $json.chatInput.toLowerCase();
      
      // Catalog indicators
      const catalogKeywords = ['harga', 'price', 'spek', 'specification', 'promo', 'diskon', 'kredit', 'dp', 'cicilan', 'tersedia', 'stock', 'dealer'];
      
      // Insights indicators  
      const insightsKeywords = ['review', 'ulasan', 'tips', 'maintenance', 'perawatan', 'bandingkan', 'vs', 'bagus mana', 'rekomendasi'];
      
      const catalogScore = catalogKeywords.filter(kw => query.includes(kw)).length;
      const insightsScore = insightsKeywords.filter(kw => query.includes(kw)).length;
      
      return {
        ...($json),
        query_intent: {
          catalog_score: catalogScore,
          insights_score: insightsScore,
          primary_source: catalogScore >= insightsScore ? 'catalog' : 'insights',
          confidence: Math.max(catalogScore, insightsScore) >= 2 ? 'high' : 'medium'
        }
      };
    `
  }
}
```

## 🚀 **Implementation Steps**

### **Step 1: Update MCP Server (Sudah Selesai)**
✅ Tools sudah diupdate dengan 7 automotive-specific tools
✅ Routing logic sudah dioptimalkan
✅ Framing context sudah disesuaikan

### **Step 2: Update n8n MCP Client**

1. **Edit MCP Client Node**
2. **Update includeTools** dengan 7 tools baru
3. **Test connection** ke MCP server

### **Step 3: Enhanced Tool Descriptions (Optional)**

Update description untuk clarity:

```json
{
  "search_automotive_insights": {
    "description": "🔍 FALLBACK TOOL: Gunakan HANYA jika PGVector RAG tidak cukup. Untuk insights otomotif eksternal: berita, review, tips, trend pasar. Frame dengan 'Berdasarkan informasi umum di industri otomotif...'"
  },
  "get_automotive_sales_insights": {
    "description": "💼 SALES SUPPORT: Untuk rekomendasi umum berdasarkan kategori kendaraan, budget, dan usage type. Gunakan saat customer butuh guidance pemilihan."
  },
  "search_automotive_reviews": {
    "description": "⭐ REVIEWS & OPINIONS: Untuk review expert dan user experience. Gunakan saat customer tanya 'bagaimana reviewnya?' atau perlu validasi pilihan."
  },
  "get_brand_comparison_insights": {
    "description": "🆚 BRAND COMPARISON: Untuk handling objection dan perbandingan brand. Gunakan saat customer bingung pilih antara 2 brand."
  },
  "get_automotive_maintenance_tips": {
    "description": "🔧 AFTER-SALES: Untuk tips perawatan dan maintenance. Gunakan saat customer tanya tentang perawatan kendaraan."
  }
}
```

### **Step 4: Testing Scenarios**

Test dengan queries berikut untuk memastikan routing bekerja:

```javascript
// Should use PGVector RAG (Catalog)
const catalogQueries = [
  "Berapa harga Honda Civic 2024?",
  "Spesifikasi Toyota Camry Hybrid",
  "Ada promo DP 0% untuk SUV?",
  "Motor Yamaha NMAX tersedia di dealer mana?"
];

// Should use MCP (Insights) as fallback/enrichment
const insightsQueries = [
  "Bagaimana review Honda Civic dari expert?",
  "Tips perawatan mesin hybrid",
  "Honda vs Toyota mana yang lebih bagus?",
  "Trend pasar mobil listrik di Indonesia"
];

// Should use BOTH (Hybrid)
const hybridQueries = [
  "Saya mau beli SUV budget 400 juta, ada rekomendasi?",
  "Mazda CX-5 vs Honda CR-V, mana yang lebih worth it?",
  "Mobil keluarga yang irit BBM dan reliable"
];
```

## 📈 **Expected Benefits**

### **Before (Current):**
- ✅ Strong PGVector RAG untuk catalog
- ⚠️ Limited MCP (hanya 2 tools)
- ❌ No specialized automotive tools
- ❌ Generic insights only

### **After (Enhanced):**
- ✅ **Comprehensive Coverage**: Catalog + Insights + Sales Support
- ✅ **Smart Routing**: 7 specialized automotive tools
- ✅ **Sales-Optimized**: Tools untuk setiap conversation phase
- ✅ **Robust Fallback**: Multiple fallback mechanisms
- ✅ **Better UX**: Tidak pernah "tidak ada data"

## 🔧 **Quick Implementation Guide**

### **Immediate Actions (5 minutes):**

1. **Edit MCP Client Node** di n8n workflow
2. **Update includeTools** dengan list 7 tools baru:
   ```
   rag_get_available_sources
   search_automotive_insights
   determine_automotive_search_strategy  
   get_automotive_sales_insights
   search_automotive_reviews
   get_brand_comparison_insights
   get_automotive_maintenance_tips
   ```
3. **Save & Test** workflow

### **Optional Enhancements (15 minutes):**

1. **Update tool descriptions** untuk clarity
2. **Add query intent analyzer** node
3. **Enhanced monitoring** dan logging

### **Data Preparation:**

1. **Crawl automotive sources** untuk MCP:
   - otomotif.kompas.com
   - oto.detik.com  
   - gridoto.com
   - carmudi.co.id/journal
   - mobil123.com/berita

2. **Ensure PGVector** memiliki catalog data yang lengkap

## 🎯 **Success Metrics**

- **Tool Selection Accuracy**: >90% correct routing
- **Response Completeness**: Tidak ada "tidak ada data"  
- **User Satisfaction**: Informasi lebih comprehensive
- **Conversation Flow**: Smooth sales progression
- **Fallback Success**: Robust error handling

Dengan modifikasi ini, OtoAI akan memiliki **Hybrid RAG/MCP Agent** yang sangat powerful dan sesuai dengan workflow yang sudah ada, tanpa perlu perubahan arsitektur besar-besaran!