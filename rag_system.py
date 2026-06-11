#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) System for RupeeBoss Conversations.
Uses sentence-transformers to embed conversations and find similar ones.
"""

import sqlite3
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime

DB_PATH = '/root/.openclaw/workspace/rupeeboss/conversations.db'

class RupeeBossRAG:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        """Initialize with embedding model"""
        print(f"🔄 Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embeddings = None
        self.conversations = []
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded. Embedding dimension: {self.dimension}")
    
    def load_from_db(self, limit=None):
        """Load conversations from SQLite DB"""
        print(f"📂 Loading conversations from DB...")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        query = """
            SELECT conversation_id, date, client_name, client_phone, 
                   call_summary_title, call_summary, transcript
            FROM conversations
            WHERE transcript != '' AND transcript IS NOT NULL
            ORDER BY date DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        c.execute(query)
        rows = c.fetchall()
        conn.close()
        
        self.conversations = []
        for row in rows:
            conv = {
                'conversation_id': row[0],
                'date': row[1],
                'client_name': row[2] or '',
                'client_phone': row[3] or '',
                'title': row[4] or '',
                'summary': row[5] or '',
                'transcript': row[6] or ''
            }
            # Create searchable text
            conv['search_text'] = self._create_search_text(conv)
            self.conversations.append(conv)
        
        print(f"📊 Loaded {len(self.conversations)} conversations")
        return len(self.conversations)
    
    def _create_search_text(self, conv):
        """Combine fields into searchable text"""
        parts = []
        if conv['title']:
            parts.append(f"Title: {conv['title']}")
        if conv['summary']:
            parts.append(f"Summary: {conv['summary']}")
        if conv['transcript']:
            # Extract user messages (customer questions)
            user_lines = re.findall(r'\[USER\]: (.+)', conv['transcript'])
            if user_lines:
                parts.append(f"Customer said: {' '.join(user_lines[:5])}")  # First 5 user messages
        return ' '.join(parts)
    
    def build_index(self):
        """Create embeddings for all conversations"""
        if not self.conversations:
            print("❌ No conversations loaded. Run load_from_db() first.")
            return
        
        print(f"🔨 Building embeddings for {len(self.conversations)} conversations...")
        texts = [c['search_text'] for c in self.conversations]
        
        # Encode in batches to manage memory
        batch_size = 64
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            emb = self.model.encode(batch, show_progress_bar=False)
            all_embeddings.append(emb)
            if (i // batch_size) % 10 == 0:
                print(f"  Processed {min(i+batch_size, len(texts))}/{len(texts)}")
        
        self.embeddings = np.vstack(all_embeddings)
        print(f"✅ Index built. Shape: {self.embeddings.shape}")
    
    def save_index(self, filepath='/root/.openclaw/workspace/rupeeboss/rag_index.npz'):
        """Save embeddings and metadata to disk"""
        metadata = [{k: v for k, v in c.items() if k != 'transcript'} 
                    for c in self.conversations]
        np.savez(filepath, 
                 embeddings=self.embeddings,
                 metadata=json.dumps(metadata))
        print(f"💾 Index saved to {filepath}")
    
    def load_index(self, filepath='/root/.openclaw/workspace/rupeeboss/rag_index.npz'):
        """Load embeddings from disk"""
        data = np.load(filepath, allow_pickle=True)
        self.embeddings = data['embeddings']
        self.conversations = json.loads(str(data['metadata']))
        print(f"📂 Loaded index: {self.embeddings.shape[0]} conversations")
    
    def search(self, query, top_k=5):
        """Find conversations similar to query"""
        if self.embeddings is None:
            print("❌ No index built. Run build_index() first.")
            return []
        
        # Encode query
        query_embedding = self.model.encode([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            conv = self.conversations[idx]
            results.append({
                'conversation_id': conv['conversation_id'],
                'date': conv['date'],
                'client_name': conv.get('client_name', ''),
                'client_phone': conv.get('client_phone', ''),
                'title': conv.get('title', ''),
                'summary': conv.get('summary', ''),
                'similarity_score': float(similarities[idx]),
                'transcript_preview': conv.get('transcript', '')[:300]
            })
        
        return results
    
    def search_by_customer(self, phone=None, name=None):
        """Search for specific customer conversations"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        if phone:
            c.execute("""
                SELECT date, client_name, client_phone, call_summary_title, 
                       call_summary, transcript
                FROM conversations WHERE client_phone = ? ORDER BY date DESC
            """, (phone,))
        elif name:
            c.execute("""
                SELECT date, client_name, client_phone, call_summary_title, 
                       call_summary, transcript
                FROM conversations WHERE client_name LIKE ? ORDER BY date DESC
            """, (f'%{name}%',))
        else:
            return []
        
        rows = c.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                'date': row[0],
                'name': row[1] or 'Unknown',
                'phone': row[2] or '',
                'title': row[3] or '',
                'summary': row[4] or '',
                'transcript_preview': (row[5] or '')[:300]
            })
        return results


def demo():
    """Demonstrate the RAG system"""
    print("="*70)
    print("RupeeBoss RAG System Demo")
    print("="*70)
    
    # Initialize
    rag = RupeeBossRAG()
    
    # Load data
    rag.load_from_db(limit=500)  # Load first 500 for demo speed
    
    # Build index
    rag.build_index()
    
    # Demo queries
    queries = [
        "startup business loan",
        "home loan transfer from another bank",
        "partner registration problem",
        "machine loan for factory",
        "customer wants lower interest rate",
        "loan against property",
        "personal loan for salaried employee"
    ]
    
    print("\n" + "="*70)
    print("SEARCH DEMONSTRATIONS")
    print("="*70)
    
    for query in queries:
        print(f"\n🔍 Query: \"{query}\"")
        print("-" * 70)
        
        results = rag.search(query, top_k=3)
        
        for i, result in enumerate(results, 1):
            print(f"\n  {i}. Date: {result['date']} | Score: {result['similarity_score']:.3f}")
            print(f"     Phone: {result['client_phone'] or 'N/A'} | Name: {result['client_name'] or 'Unknown'}")
            print(f"     Title: {result['title'] or 'N/A'}")
            if result['summary']:
                print(f"     Summary: {result['summary'][:100]}")
            print(f"     Transcript: {result['transcript_preview'][:150]}...")
    
    # Demo: Search by customer
    print("\n" + "="*70)
    print("CUSTOMER SEARCH")
    print("="*70)
    
    # Find a customer with multiple calls
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT client_phone, COUNT(*) as count 
        FROM conversations 
        WHERE client_phone != '' 
        GROUP BY client_phone 
        ORDER BY count DESC LIMIT 1
    """)
    row = c.fetchone()
    conn.close()
    
    if row:
        phone = row[0]
        print(f"\n🔍 Searching for customer: {phone}")
        results = rag.search_by_customer(phone=phone)
        
        for r in results:
            print(f"\n  📅 {r['date']} | {r['name']}")
            print(f"     Title: {r['title'] or 'N/A'}")
            print(f"     Preview: {r['transcript_preview'][:200]}...")
    
    print("\n" + "="*70)
    print("Demo complete!")
    print("="*70)


if __name__ == '__main__':
    demo()
