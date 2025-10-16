#!/usr/bin/env python3
"""Upload books to Qdrant using HTTP API to avoid timeout issues."""

import os
import httpx
import json
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any
import logging

# Document processing
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class HTTPKnowledgeUploader:
    """Upload knowledge using Qdrant HTTP API."""
    
    def __init__(self):
        self.base_url = 'https://qdrant-staging-staging.up.railway.app'
        self.ifs_collection = 'kb_4d86758e'  # From env
        self.byron_collection = 'kb_c38f320c'  # From env
        
        # Load embedding model
        logger.info("Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Small chunks and batches for reliability
        self.chunk_size = 200  # words
        self.batch_size = 10   # points per request
    
    def extract_pdf(self, path: str) -> str:
        """Extract text from PDF."""
        logger.info(f"Extracting PDF: {Path(path).name}")
        text = ""
        with open(path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            for page in pdf.pages:
                text += page.extract_text()
        logger.info(f"  Extracted {len(text)} characters")
        return text
    
    def extract_epub(self, path: str) -> str:
        """Extract text from EPUB."""
        logger.info(f"Extracting EPUB: {Path(path).name}")
        text = ""
        book = epub.read_epub(path)
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text += soup.get_text() + "\n"
        text = re.sub(r'\s+', ' ', text)
        logger.info(f"  Extracted {len(text)} characters")
        return text
    
    def create_chunks(self, text: str) -> List[str]:
        """Create text chunks."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size):
            chunk = ' '.join(words[i:i + self.chunk_size])
            if len(chunk) > 50:
                chunks.append(chunk)
        
        logger.info(f"  Created {len(chunks)} chunks")
        return chunks
    
    def upload_batch(self, collection: str, batch: List[Dict], batch_num: int) -> bool:
        """Upload a batch of points via HTTP API."""
        try:
            # Prepare points
            points = []
            for item in batch:
                embedding = self.model.encode(item['text']).tolist()
                point_id = hashlib.md5(f"{item['text'][:30]}_{item['index']}".encode()).hexdigest()[:16]
                
                points.append({
                    'id': point_id,
                    'vector': embedding,
                    'payload': {
                        'text': item['text'],
                        'source': item['source'],
                        'chunk_index': item['index']
                    }
                })
            
            # Upload via HTTP API
            response = httpx.put(
                f'{self.base_url}/collections/{collection}/points',
                json={'points': points},
                timeout=60.0
            )
            
            if response.status_code == 200:
                logger.info(f"    Batch {batch_num}: ✅ Uploaded {len(batch)} points")
                return True
            else:
                logger.error(f"    Batch {batch_num}: Failed with {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"    Batch {batch_num}: Error - {e}")
            return False
    
    def upload_book(self, file_path: str, collection: str, book_name: str) -> bool:
        """Process and upload a book."""
        logger.info(f"\nProcessing: {book_name}")
        logger.info("="*50)
        
        # Extract text
        if file_path.endswith('.pdf'):
            text = self.extract_pdf(file_path)
        else:
            text = self.extract_epub(file_path)
        
        if not text:
            logger.error("No text extracted")
            return False
        
        # Create chunks
        chunks = self.create_chunks(text)
        
        # Prepare data
        data = []
        for i, chunk_text in enumerate(chunks):
            data.append({
                'text': chunk_text,
                'source': book_name,
                'index': i
            })
        
        # Upload in batches
        logger.info(f"Uploading {len(data)} chunks to {collection}...")
        success_count = 0
        
        for batch_start in range(0, len(data), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(data))
            batch = data[batch_start:batch_end]
            batch_num = batch_start // self.batch_size + 1
            
            if self.upload_batch(collection, batch, batch_num):
                success_count += len(batch)
        
        logger.info(f"✅ Uploaded {success_count}/{len(data)} chunks successfully")
        return success_count > 0
    
    def verify_collection(self, collection: str):
        """Check collection status."""
        try:
            response = httpx.get(f'{self.base_url}/collections/{collection}', timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                count = data['result']['points_count']
                logger.info(f"✅ {collection}: {count} points")
            else:
                logger.error(f"❌ {collection}: Not found")
        except Exception as e:
            logger.error(f"❌ {collection}: {e}")


def main():
    print("\n" + "="*70)
    print("📚 HTTP API Knowledge Base Uploader")
    print("="*70)
    
    # Files
    ifs_book = "/home/ben/integro-agents/Internal Family Systems Therapy -- Richard C_ Schwartz -- The Guilford Press (1).epub"
    byron_book = "/home/ben/integro-agents/Loving What Is, Revised Edition -- Byron Katie & Stephen Mitchell -- 2021 -- Harmony_Rodale.pdf"
    
    if not Path(ifs_book).exists() or not Path(byron_book).exists():
        print("❌ Book files not found")
        return
    
    print("\nThis will upload books to existing collections:")
    print(f"  IFS → kb_4d86758e")
    print(f"  Byron Katie → kb_c38f320c")
    
    response = input("\nProceed? (y/n): ")
    if response.lower() != 'y':
        return
    
    uploader = HTTPKnowledgeUploader()
    
    # Upload IFS book
    uploader.upload_book(ifs_book, uploader.ifs_collection, "IFS Therapy - Schwartz")
    
    # Upload Byron Katie book
    uploader.upload_book(byron_book, uploader.byron_collection, "Loving What Is - Byron Katie")
    
    # Verify
    print("\nVerifying collections:")
    print("-"*40)
    uploader.verify_collection(uploader.ifs_collection)
    uploader.verify_collection(uploader.byron_collection)
    
    print("\n" + "="*70)
    print("✅ Upload complete!")
    print("="*70)


if __name__ == "__main__":
    main()