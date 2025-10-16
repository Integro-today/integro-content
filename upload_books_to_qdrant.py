#!/usr/bin/env python3
"""Upload IFS and Byron Katie books to Railway Qdrant collections."""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
from dotenv import load_dotenv

# Document processing
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re

# Qdrant and embeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BookKnowledgeUploader:
    """Upload books to Qdrant collections for therapeutic knowledge bases."""
    
    def __init__(self, qdrant_url: str = None):
        """Initialize the uploader."""
        self.qdrant_url = qdrant_url or os.getenv('QDRANT_HOST', 'https://qdrant-staging-staging.up.railway.app')
        
        # Initialize Qdrant client
        logger.info(f"Connecting to Qdrant at: {self.qdrant_url}")
        self.client = QdrantClient(url=self.qdrant_url)
        
        # Initialize sentence transformer
        logger.info("Loading sentence transformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions
        
        # Collection names
        self.ifs_collection = 'ifs-knowledge-base'
        self.byron_katie_collection = 'byron-katie-knowledge-base'
        
        # Chunk settings
        self.chunk_size = 500  # words per chunk
        self.chunk_overlap = 50  # overlapping words
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file."""
        logger.info(f"Extracting text from PDF: {pdf_path}")
        text = ""
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                logger.info(f"  Found {num_pages} pages")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    
                    if (page_num + 1) % 50 == 0:
                        logger.info(f"  Processed {page_num + 1}/{num_pages} pages...")
                
                logger.info(f"✅ Extracted {len(text)} characters from PDF")
                
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            
        return text
    
    def extract_text_from_epub(self, epub_path: str) -> str:
        """Extract text from an EPUB file."""
        logger.info(f"Extracting text from EPUB: {epub_path}")
        text = ""
        
        try:
            book = epub.read_epub(epub_path)
            items = list(book.get_items())
            logger.info(f"  Found {len(items)} items in EPUB")
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    # Extract text and clean it
                    chapter_text = soup.get_text()
                    # Clean up extra whitespace
                    chapter_text = re.sub(r'\s+', ' ', chapter_text)
                    chapter_text = re.sub(r'\n\s*\n', '\n\n', chapter_text)
                    text += chapter_text + "\n\n"
            
            logger.info(f"✅ Extracted {len(text)} characters from EPUB")
            
        except Exception as e:
            logger.error(f"Error extracting EPUB text: {e}")
            
        return text
    
    def create_chunks(self, text: str, source: str) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata."""
        logger.info(f"Creating chunks from {source}...")
        
        # Clean the text
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Split into words
        words = text.split()
        chunks = []
        
        # Create overlapping chunks
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text) > 50:  # Minimum chunk size
                chunks.append({
                    'text': chunk_text,
                    'metadata': {
                        'source': source,
                        'chunk_index': len(chunks),
                        'word_count': len(chunk_words)
                    }
                })
        
        logger.info(f"✅ Created {len(chunks)} chunks from {source}")
        return chunks
    
    def create_collection_if_not_exists(self, collection_name: str):
        """Create a collection if it doesn't exist."""
        try:
            collections = self.client.get_collections()
            existing_names = [c.name for c in collections.collections]
            
            if collection_name in existing_names:
                logger.info(f"Collection '{collection_name}' already exists")
                # Optional: delete and recreate for fresh upload
                response = input(f"Collection exists. Delete and recreate? (y/n): ")
                if response.lower() == 'y':
                    self.client.delete_collection(collection_name)
                    logger.info(f"Deleted existing collection: {collection_name}")
                else:
                    return True
            
            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            logger.info(f"✅ Created collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False
    
    def upload_chunks_to_collection(self, collection_name: str, chunks: List[Dict[str, Any]]):
        """Upload chunks to a Qdrant collection."""
        logger.info(f"Uploading {len(chunks)} chunks to '{collection_name}'...")
        
        if not self.create_collection_if_not_exists(collection_name):
            return False
        
        # Process in batches
        batch_size = 100
        total_uploaded = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            points = []
            
            for chunk in batch:
                # Generate embedding
                embedding = self.model.encode(chunk['text']).tolist()
                
                # Create unique ID
                chunk_id = hashlib.md5(f"{chunk['text'][:100]}_{i}".encode()).hexdigest()
                
                point = PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload={
                        'text': chunk['text'],
                        **chunk['metadata']
                    }
                )
                points.append(point)
            
            # Upload batch
            try:
                self.client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                total_uploaded += len(points)
                logger.info(f"  Uploaded batch: {total_uploaded}/{len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Failed to upload batch: {e}")
                return False
        
        logger.info(f"✅ Successfully uploaded all {total_uploaded} chunks")
        return True
    
    def upload_ifs_book(self, epub_path: str):
        """Upload IFS book to Qdrant."""
        logger.info("\n" + "="*60)
        logger.info("📚 Processing IFS Book")
        logger.info("="*60)
        
        # Extract text
        text = self.extract_text_from_epub(epub_path)
        if not text:
            logger.error("Failed to extract text from IFS book")
            return False
        
        # Create chunks
        chunks = self.create_chunks(text, "Internal Family Systems Therapy - Schwartz")
        
        # Upload to Qdrant
        return self.upload_chunks_to_collection(self.ifs_collection, chunks)
    
    def upload_byron_katie_book(self, pdf_path: str):
        """Upload Byron Katie book to Qdrant."""
        logger.info("\n" + "="*60)
        logger.info("📚 Processing Byron Katie Book")
        logger.info("="*60)
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            logger.error("Failed to extract text from Byron Katie book")
            return False
        
        # Create chunks
        chunks = self.create_chunks(text, "Loving What Is - Byron Katie")
        
        # Upload to Qdrant
        return self.upload_chunks_to_collection(self.byron_katie_collection, chunks)
    
    def verify_collections(self):
        """Verify that collections were created and populated."""
        logger.info("\n" + "="*60)
        logger.info("🔍 Verifying Collections")
        logger.info("="*60)
        
        for collection_name in [self.ifs_collection, self.byron_katie_collection]:
            try:
                info = self.client.get_collection(collection_name)
                logger.info(f"\n✅ Collection: {collection_name}")
                logger.info(f"   Documents: {info.points_count}")
                logger.info(f"   Vector size: {info.config.params.vectors.size}")
                
                # Test search
                test_query = "therapy healing integration parts" if "ifs" in collection_name else "four questions turnaround"
                test_vector = self.model.encode(test_query).tolist()
                
                results = self.client.search(
                    collection_name=collection_name,
                    query_vector=test_vector,
                    limit=3
                )
                
                logger.info(f"   Sample search for '{test_query[:30]}...':")
                for i, result in enumerate(results, 1):
                    text_preview = result.payload.get('text', '')[:80]
                    logger.info(f"     {i}. Score {result.score:.3f}: {text_preview}...")
                    
            except Exception as e:
                logger.error(f"❌ Failed to verify {collection_name}: {e}")


def main():
    """Main function to upload books."""
    print("\n" + "="*70)
    print("📚 Therapeutic Books Knowledge Base Uploader")
    print("="*70)
    
    # Check for book files
    ifs_book = "/home/ben/integro-agents/Internal Family Systems Therapy -- Richard C_ Schwartz -- The Guilford Press (1).epub"
    byron_book = "/home/ben/integro-agents/Loving What Is, Revised Edition -- Byron Katie & Stephen Mitchell -- 2021 -- Harmony_Rodale.pdf"
    
    if not Path(ifs_book).exists():
        print(f"❌ IFS book not found: {ifs_book}")
        return
    
    if not Path(byron_book).exists():
        print(f"❌ Byron Katie book not found: {byron_book}")
        return
    
    print("\n📋 Found books:")
    print(f"  ✅ IFS: {Path(ifs_book).name}")
    print(f"  ✅ Byron Katie: {Path(byron_book).name}")
    
    # Confirm Qdrant server
    qdrant_url = os.getenv('QDRANT_HOST', 'https://qdrant-staging-staging.up.railway.app')
    print(f"\n📍 Target Qdrant: {qdrant_url}")
    
    print("\n⚠️  This will:")
    print("  1. Extract text from both books")
    print("  2. Create chunks of ~500 words each")
    print("  3. Generate embeddings for each chunk")
    print("  4. Upload to Qdrant collections")
    
    response = input("\nProceed with upload? (y/n): ")
    if response.lower() != 'y':
        print("Upload cancelled.")
        return
    
    # Initialize uploader
    uploader = BookKnowledgeUploader(qdrant_url)
    
    # Upload books
    success = True
    
    if not uploader.upload_ifs_book(ifs_book):
        success = False
    
    if not uploader.upload_byron_katie_book(byron_book):
        success = False
    
    # Verify uploads
    uploader.verify_collections()
    
    print("\n" + "="*70)
    if success:
        print("✅ Books uploaded successfully!")
        print("\nUpdate your .env file with:")
        print(f"  IFS_KNOWLEDGE_BASE_ID={uploader.ifs_collection}")
        print(f"  BYRON_KATIE_KNOWLEDGE_BASE_ID={uploader.byron_katie_collection}")
    else:
        print("⚠️ Some uploads failed. Check the logs above.")
    print("="*70)


if __name__ == "__main__":
    # Check dependencies
    try:
        import PyPDF2
        import ebooklib
        from bs4 import BeautifulSoup
    except ImportError as e:
        print("Missing dependencies. Install with:")
        print("pip install PyPDF2 ebooklib beautifulsoup4 sentence-transformers qdrant-client")
        sys.exit(1)
    
    main()