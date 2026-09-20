import sqlite3
import hashlib
import json
import os
import asyncio
from typing import List, Dict, Any

class HolographicASTGraph:
    def __init__(self, db_path: str):
        self.db_path = db_path
        print(f"[HolographicAST] Binding to NodeOS Graph at: {self.db_path}")
        
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
        
    def _generate_pseudo_embedding(self, content: str) -> List[float]:
        h = hashlib.sha256(content.encode()).digest()
        return [(b / 128.0) - 1.0 for b in h[:16]]
        
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(v1, v2))
        mag1 = sum(a * a for a in v1) ** 0.5
        mag2 = sum(b * b for b in v2) ** 0.5
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot_product / (mag1 * mag2)

    async def generate_embeddings_background_task(self, on_batch_complete=None):
        """Scans the NodeOS db and generates embeddings asynchronously without spiking CPU."""
        if not os.path.exists(self.db_path):
            return

        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("ALTER TABLE nodes ADD COLUMN vector_embedding TEXT")
            conn.commit()
            print("[HolographicAST] Extended polymath-nodeos schema with 'vector_embedding'.")
        except sqlite3.OperationalError:
            pass

        while True:
            # Batch process 10 nodes at a time to keep CPU usage near 0%
            cursor.execute("SELECT node_id, name, node_type FROM nodes WHERE vector_embedding IS NULL LIMIT 10")
            unindexed = cursor.fetchall()
            
            if not unindexed:
                break # All nodes mapped
                
            for node_id, name, node_type in unindexed:
                semantic_content = f"{node_type} {name}"
                vector = self._generate_pseudo_embedding(semantic_content)
                cursor.execute("UPDATE nodes SET vector_embedding = ? WHERE node_id = ?", (json.dumps(vector), node_id))
                
            conn.commit()
            # Yield control to the asyncio event loop (throttles CPU usage)
            if on_batch_complete: await on_batch_complete(len(unindexed))
            await asyncio.sleep(0.5)

        conn.close()

    def semantic_search(self, intent: str, top_k: int = 3) -> List[Dict[str, Any]]:
        intent_vector = self._generate_pseudo_embedding(intent)
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT node_id, name, node_type, vector_embedding FROM nodes WHERE vector_embedding IS NOT NULL")
        all_nodes = cursor.fetchall()
        conn.close()
        
        results = []
        for node_id, name, node_type, vec_str in all_nodes:
            node_vec = json.loads(vec_str)
            score = self._cosine_similarity(intent_vector, node_vec)
            results.append({
                "id": node_id,
                "name": name,
                "type": node_type,
                "similarity": round(score, 3)
            })
            
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
