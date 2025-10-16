#!/usr/bin/env python3
"""Create Qdrant collections and upload therapeutic books with proper timeout handling."""

import os
import sys
import time
import logging
from pathlib import Path
import hashlib
from typing import List, Dict, Any
import re

# Document processing
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# Qdrant and embeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RobustKnowledgeUploader:
    """Robust uploader for therapeutic knowledge with retry logic."""
    
    def __init__(self):
        """Initialize with extended timeouts."""
        self.qdrant_url = 'https://qdrant-staging-staging.up.railway.app'
        
        # Get collection names from env or use defaults
        self.ifs_collection = os.getenv('IFS_KNOWLEDGE_BASE_ID', 'ifs-knowledge-base')
        self.byron_katie_collection = os.getenv('BYRON_KATIE_KNOWLEDGE_BASE_ID', 'byron-katie-knowledge-base')
        
        logger.info(f"Configured collections:")
        logger.info(f"  IFS: {self.ifs_collection}")
        logger.info(f"  Byron Katie: {self.byron_katie_collection}")
        
        # Initialize with longer timeout
        logger.info(f"Connecting to Qdrant at: {self.qdrant_url}")
        self.client = QdrantClient(url=self.qdrant_url, timeout=30)  # 30 second timeout
        
        # Initialize sentence transformer
        logger.info("Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Smaller chunks for faster uploads
        self.chunk_size = 300  # words per chunk
        self.chunk_overlap = 30
        self.batch_size = 20  # smaller batches to avoid timeouts
    
    def create_collection_with_retry(self, collection_name: str, max_retries: int = 3) -> bool:
        """Create collection with retry logic."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}: Creating collection '{collection_name}'...")
                
                # Check if exists
                try:
                    info = self.client.get_collection(collection_name)
                    logger.info(f"Collection '{collection_name}' already exists with {info.points_count} points")
                    
                    response = input(f"Delete and recreate {collection_name}? (y/n): ")
                    if response.lower() == 'y':
                        self.client.delete_collection(collection_name)
                        logger.info(f"Deleted existing collection")
                        time.sleep(2)  # Wait after deletion
                    else:
                        return True
                except:
                    pass  # Collection doesn't exist, continue to create
                
                # Create collection
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                
                # Verify creation
                time.sleep(2)  # Give it time to propagate
                info = self.client.get_collection(collection_name)
                logger.info(f"✅ Successfully created collection '{collection_name}'")
                return True
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to create collection after {max_retries} attempts")
                    return False
        
        return False
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF."""
        logger.info(f"Extracting text from: {Path(pdf_path).name}")
        text = ""
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                    
                    if (page_num + 1) % 100 == 0:
                        logger.info(f"  Processed {page_num + 1}/{num_pages} pages...")
                
                logger.info(f"  Extracted {len(text)} characters")
                
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            
        return text
    
    def extract_text_from_epub(self, epub_path: str) -> str:
        """Extract text from EPUB."""
        logger.info(f"Extracting text from: {Path(epub_path).name}")
        text = ""
        
        try:
            book = epub.read_epub(epub_path)
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    chapter_text = soup.get_text()
                    chapter_text = re.sub(r'\s+', ' ', chapter_text)
                    text += chapter_text + "\n\n"
            
            logger.info(f"  Extracted {len(text)} characters")
            
        except Exception as e:
            logger.error(f"Error extracting EPUB: {e}")
            
        return text
    
    def create_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Create smaller chunks for faster upload."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text) > 50:
                chunks.append({
                    'text': chunk_text,
                    'chunk_index': len(chunks)
                })
        
        logger.info(f"  Created {len(chunks)} chunks")
        return chunks
    
    def upload_chunks_with_retry(self, collection_name: str, chunks: List[Dict], source: str) -> bool:
        """Upload chunks with retry logic and progress tracking."""
        logger.info(f"Uploading {len(chunks)} chunks to '{collection_name}'...")
        
        total_uploaded = 0
        failed_batches = []
        
        for batch_start in range(0, len(chunks), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(chunks))
            batch = chunks[batch_start:batch_end]
            batch_num = batch_start // self.batch_size + 1
            total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size
            
            logger.info(f"  Batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
            
            # Prepare points
            points = []
            for i, chunk in enumerate(batch):
                embedding = self.model.encode(chunk['text']).tolist()
                chunk_id = hashlib.md5(f"{chunk['text'][:50]}_{batch_start + i}".encode()).hexdigest()
                
                point = PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload={
                        'text': chunk['text'],
                        'source': source,
                        'chunk_index': chunk['chunk_index']
                    }
                )
                points.append(point)
            
            # Try to upload batch
            success = False
            for attempt in range(3):
                try:
                    self.client.upsert(
                        collection_name=collection_name,
                        points=points,
                        wait=True
                    )
                    total_uploaded += len(points)
                    logger.info(f"    ✅ Uploaded: {total_uploaded}/{len(chunks)} total")
                    success = True
                    break
                    
                except Exception as e:
                    logger.warning(f"    Attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        time.sleep(5)
                    else:
                        failed_batches.append((batch_num, batch_start, batch_end))
            
            if not success:
                logger.error(f"    ❌ Failed batch {batch_num}")
            
            # Small delay between batches
            time.sleep(1)
        
        if failed_batches:
            logger.warning(f"Failed to upload {len(failed_batches)} batches")
            return False
        
        logger.info(f"✅ Successfully uploaded all {total_uploaded} chunks")
        return True
    
    def process_and_upload_book(self, file_path: str, collection_name: str, book_name: str) -> bool:
        """Process a book and upload to Qdrant."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {book_name}")
        logger.info(f"{'='*60}")
        
        # Extract text based on file type
        if file_path.endswith('.pdf'):
            text = self.extract_text_from_pdf(file_path)
        elif file_path.endswith('.epub'):
            text = self.extract_text_from_epub(file_path)
        else:
            logger.error("Unsupported file type")
            return False
        
        if not text:
            logger.error("No text extracted")
            return False
        
        # Create chunks
        chunks = self.create_chunks(text)
        
        # Upload chunks
        return self.upload_chunks_with_retry(collection_name, chunks, book_name)
    
    def verify_collection(self, collection_name: str):
        """Verify collection was created and populated."""
        try:
            info = self.client.get_collection(collection_name)
            logger.info(f"\n✅ Collection '{collection_name}':")
            logger.info(f"   Points: {info.points_count}")
            
            # Test search
            test_vector = self.model.encode("therapy healing integration").tolist()
            results = self.client.search(
                collection_name=collection_name,
                query_vector=test_vector,
                limit=2
            )
            
            if results:
                logger.info(f"   Sample search results:")
                for r in results:
                    preview = r.payload.get('text', '')[:80]
                    logger.info(f"     - {preview}...")
                    
        except Exception as e:
            logger.error(f"❌ Failed to verify {collection_name}: {e}")


def main():
    """Main function."""
    print("\n" + "="*70)
    print("🚀 Robust Knowledge Base Creator & Uploader")
    print("="*70)
    
    # Book files
    ifs_book = "/home/ben/integro-agents/Internal Family Systems Therapy -- Richard C_ Schwartz -- The Guilford Press (1).epub"
    byron_book = "/home/ben/integro-agents/Loving What Is, Revised Edition -- Byron Katie & Stephen Mitchell -- 2021 -- Harmony_Rodale.pdf"
    
    # Check files exist
    if not Path(ifs_book).exists():
        print(f"❌ IFS book not found")
        return
    
    if not Path(byron_book).exists():
        print(f"❌ Byron Katie book not found")
        return
    
    print("\n📚 Books found:")
    print(f"  ✅ IFS: {Path(ifs_book).name}")
    print(f"  ✅ Byron Katie: {Path(byron_book).name}")
    
    print(f"\n📍 Target: {RobustKnowledgeUploader().qdrant_url}")
    
    print("\nThis will:")
    print("1. Create collections with retry logic")
    print("2. Extract text from books")
    print("3. Create smaller chunks (300 words)")
    print("4. Upload in small batches (20 chunks)")
    
    response = input("\nProceed? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Initialize uploader
    uploader = RobustKnowledgeUploader()
    
    # Step 1: Create collections
    print("\n" + "="*60)
    print("Step 1: Creating Collections")
    print("="*60)
    
    ifs_created = uploader.create_collection_with_retry(uploader.ifs_collection)
    byron_created = uploader.create_collection_with_retry(uploader.byron_katie_collection)
    
    if not ifs_created or not byron_created:
        print("\n⚠️ Failed to create one or more collections")
        response = input("Continue with available collections? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Step 2: Upload books
    print("\n" + "="*60)
    print("Step 2: Uploading Books")
    print("="*60)
    
    if ifs_created:
        uploader.process_and_upload_book(
            ifs_book,
            uploader.ifs_collection,
            "IFS Therapy - Schwartz"
        )
    
    if byron_created:
        uploader.process_and_upload_book(
            byron_book,
            uploader.byron_katie_collection,
            "Loving What Is - Byron Katie"
        )
    
    # Step 3: Verify
    print("\n" + "="*60)
    print("Step 3: Verification")
    print("="*60)
    
    uploader.verify_collection(uploader.ifs_collection)
    uploader.verify_collection(uploader.byron_katie_collection)
    
    print("\n" + "="*70)
    print("✅ Complete! Your agents can now access the knowledge bases.")
    print("="*70)


if __name__ == "__main__":
    main()