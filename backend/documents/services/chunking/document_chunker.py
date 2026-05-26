import re
from sentence_transformers import SentenceTransformer
import numpy as np


class SemanticChunking:

    def __init__(
        self, model: str = "all-MiniLM-L6-v2", similarity_threshold: float = 0.6
    ):
        self.model = SentenceTransformer(model)
        self.similarity_threshold = similarity_threshold
        
    def semantic_chunking(self, text: str):
        # Split text into sentences using punctuation while stripping extra whitespace
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        
        if not sentences:
            return []
            
        embeddings = self.model.encode(sentences)
        
        # Normalize embeddings upfront for faster cosine similarity calculation
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1 
        norm_embeddings = embeddings / norms
        
        chunks = []
        current_chunk = [sentences[0]]
        
        for i in range(1, len(sentences)):
            # Cosine similarity simplifies to a dot product when vectors are normalized
            similarity = np.dot(norm_embeddings[i-1], norm_embeddings[i])
        
            if similarity < self.similarity_threshold:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentences[i]]
            else:
                current_chunk.append(sentences[i])
                
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks


# --- Execution and Testing Block ---
if __name__ == "__main__":
    # Sample text transitioning through three distinct topics: Space, Cooking, and Programming
    sample_text = (
        "The Apollo 11 mission successfully landed humans on the Moon in 1969. "
        "Neil Armstrong and Buzz Aldrin collected samples of lunar material to bring back to Earth. "
        "Speaking of creations, baking a perfect sourdough bread requires a healthy starter culture. "
        "You need to feed it water and flour consistently to maintain its wild yeast. "
        "In the tech world, Python remains one of the most popular programming languages. "
        "Its clean syntax makes it a favorite choice for data science and machine learning applications."
    )
    
    print("Initializing Semantic Chunker...")
    # You can tweak the similarity_threshold depending on how strict you want the grouping to be
    chunker = SemanticChunking(similarity_threshold=0.5)
    
    print("\nProcessing text and generating semantic chunks...")
    semantic_chunks = chunker.semantic_chunking(sample_text)
    
    print(f"\nGenerated {len(semantic_chunks)} Chunks:\n")
    for index, chunk in enumerate(semantic_chunks, start=1):
        print(f"--- Chunk {index} ---")
        print(chunk)
        print()