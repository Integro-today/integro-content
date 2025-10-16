"""Tests for configuration management."""

import pytest
import asyncio
import json
import yaml
from pathlib import Path
import tempfile
import shutil
from integro.config import (
    AgentLoader, AgentConfig,
    KnowledgeBaseLoader, KnowledgeBaseConfig,
    ConfigStorage
)
from integro.config.kb_loader import DocumentExtractor, TextProcessor


class TestAgentConfig:
    """Test agent configuration."""
    
    def test_create_default_config(self):
        """Test creating default agent configuration."""
        config = AgentLoader.create_default_config("TestAgent")
        assert config.name == "TestAgent"
        assert config.description == "A helpful AI assistant named TestAgent"
        assert len(config.models) > 0
        assert len(config.instructions) > 0
    
    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = AgentConfig(
            name="TestAgent",
            description="Test description",
            user_id="test_user"
        )
        data = config.to_dict()
        assert data['name'] == "TestAgent"
        assert data['description'] == "Test description"
        assert data['user_id'] == "test_user"
    
    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            'name': 'TestAgent',
            'description': 'Test description',
            'user_id': 'test_user',
            'models': [{'provider': 'groq', 'model_id': 'test'}]
        }
        config = AgentConfig.from_dict(data)
        assert config.name == "TestAgent"
        assert config.user_id == "test_user"
        assert len(config.models) == 1


class TestAgentLoader:
    """Test agent loader."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = AgentLoader(Path(self.temp_dir))
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_load_yaml(self):
        """Test saving and loading YAML configuration."""
        config = AgentLoader.create_default_config("YAMLAgent")
        yaml_path = Path(self.temp_dir) / "agent.yaml"
        
        self.loader.save_to_file(config, yaml_path)
        assert yaml_path.exists()
        
        loaded = self.loader.load_from_file(yaml_path)
        assert loaded.name == config.name
        assert loaded.description == config.description
    
    def test_save_load_json(self):
        """Test saving and loading JSON configuration."""
        config = AgentLoader.create_default_config("JSONAgent")
        json_path = Path(self.temp_dir) / "agent.json"
        
        self.loader.save_to_file(config, json_path)
        assert json_path.exists()
        
        loaded = self.loader.load_from_file(json_path)
        assert loaded.name == config.name
        assert loaded.description == config.description
    
    def test_create_agent(self):
        """Test creating agent from configuration."""
        config = AgentLoader.create_default_config("TestAgent")
        agent = self.loader.create_agent(config)
        
        assert agent is not None
        assert agent.config.name == "TestAgent"


class TestKnowledgeBaseConfig:
    """Test knowledge base configuration."""
    
    def test_create_default_config(self):
        """Test creating default KB configuration."""
        config = KnowledgeBaseLoader.create_default_config("TestKB")
        assert config.name == "TestKB"
        assert config.id is not None
        assert config.collection_name == f"kb_{config.id}"
    
    def test_auto_collection_name(self):
        """Test automatic collection name generation."""
        config = KnowledgeBaseConfig(
            id="test123",
            name="TestKB"
        )
        assert config.collection_name == "kb_test123"


class TestDocumentExtractor:
    """Test document extraction."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = DocumentExtractor()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_extract_txt(self):
        """Test extracting from text file."""
        txt_path = Path(self.temp_dir) / "test.txt"
        txt_path.write_text("This is a test document.")
        
        text = self.extractor.extract(txt_path)
        assert text == "This is a test document."
    
    def test_extract_markdown(self):
        """Test extracting from markdown file."""
        md_path = Path(self.temp_dir) / "test.md"
        md_path.write_text("# Test\n\nThis is **markdown** content.")
        
        text = self.extractor.extract(md_path)
        assert "Test" in text
        assert "markdown" in text
    
    def test_extract_unknown_format(self):
        """Test extracting from unknown format (falls back to text)."""
        unknown_path = Path(self.temp_dir) / "test.xyz"
        unknown_path.write_text("Unknown format content")
        
        text = self.extractor.extract(unknown_path)
        assert text == "Unknown format content"


class TestTextProcessor:
    """Test text processing."""
    
    def test_chunk_text(self):
        """Test text chunking."""
        processor = TextProcessor()
        text = " ".join(["word"] * 1000)  # 1000 words
        
        chunks = processor.chunk_text(text, chunk_size=100, overlap=10)
        assert len(chunks) > 1
        
        # Ben, check that chunks have expected properties
        for chunk in chunks:
            assert len(chunk) <= 500  # Reasonable upper bound


class TestKnowledgeBaseLoader:
    """Test knowledge base loader."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = KnowledgeBaseLoader(Path(self.temp_dir))
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_load_yaml(self):
        """Test saving and loading KB YAML configuration."""
        config = KnowledgeBaseLoader.create_default_config("TestKB")
        yaml_path = Path(self.temp_dir) / "kb.yaml"
        
        self.loader.save_to_file(config, yaml_path)
        assert yaml_path.exists()
        
        loaded = self.loader.load_from_file(yaml_path)
        assert loaded.name == config.name
        assert loaded.id == config.id
    
    def test_create_knowledge_base(self):
        """Test creating knowledge base from configuration."""
        config = KnowledgeBaseLoader.create_default_config("TestKB")
        kb = self.loader.create_knowledge_base(config)
        
        assert kb is not None
        assert kb.collection_name == config.collection_name
    
    def test_add_document_to_kb(self):
        """Test adding document to knowledge base."""
        # Ben, create a test document
        doc_path = Path(self.temp_dir) / "test.txt"
        doc_path.write_text("This is test content for the knowledge base.")
        
        config = KnowledgeBaseLoader.create_default_config("TestKB")
        kb = self.loader.create_knowledge_base(config)
        
        doc_ids = self.loader.add_document_to_kb(
            kb, doc_path,
            extract_mode="full",
            chunk_size=50,
            chunk_overlap=10
        )
        
        assert len(doc_ids) > 0


@pytest.mark.asyncio
class TestConfigStorage:
    """Test configuration storage."""
    
    def setup_method(self, method):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.storage = ConfigStorage(self.db_path)
    
    def teardown_method(self, method):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    async def test_save_load_agent(self):
        """Test saving and loading agent from database."""
        config = AgentLoader.create_default_config("DBAgent")
        
        agent_id = await self.storage.save_agent(config)
        assert agent_id is not None
        
        loaded = await self.storage.load_agent(agent_id)
        assert loaded is not None
        assert loaded.name == config.name
    
    async def test_list_agents(self):
        """Test listing agents."""
        # Ben, save multiple agents
        for i in range(3):
            config = AgentLoader.create_default_config(f"Agent{i}")
            await self.storage.save_agent(config)
        
        agents = await self.storage.list_agents()
        assert len(agents) == 3
        assert all('name' in agent for agent in agents)
    
    async def test_delete_agent(self):
        """Test deleting agent."""
        config = AgentLoader.create_default_config("DeleteMe")
        agent_id = await self.storage.save_agent(config)
        
        deleted = await self.storage.delete_agent(agent_id)
        assert deleted
        
        loaded = await self.storage.load_agent(agent_id)
        assert loaded is None
    
    async def test_save_load_knowledge_base(self):
        """Test saving and loading KB from database."""
        config = KnowledgeBaseLoader.create_default_config("DBKB")
        
        kb_id = await self.storage.save_knowledge_base(config)
        assert kb_id == config.id
        
        loaded = await self.storage.load_knowledge_base(kb_id)
        assert loaded is not None
        assert loaded.name == config.name
    
    async def test_link_agent_to_kb(self):
        """Test linking agent to knowledge base."""
        agent_config = AgentLoader.create_default_config("LinkedAgent")
        kb_config = KnowledgeBaseLoader.create_default_config("LinkedKB")
        
        agent_id = await self.storage.save_agent(agent_config)
        kb_id = await self.storage.save_knowledge_base(kb_config)
        
        linked = await self.storage.link_agent_to_kb(agent_id, kb_id)
        assert linked
        
        result = await self.storage.get_agent_with_kb(agent_id)
        assert result is not None
        assert 'agent' in result
        assert 'knowledge_base' in result
        assert result['knowledge_base'].id == kb_id
    
    async def test_save_kb_document(self):
        """Test saving knowledge base document."""
        kb_config = KnowledgeBaseLoader.create_default_config("DocKB")
        kb_id = await self.storage.save_knowledge_base(kb_config)
        
        doc_id = await self.storage.save_kb_document(
            kb_id=kb_id,
            doc_id="doc1",
            content="Test document content",
            file_path="/test/path.txt",
            metadata={"type": "test"}
        )
        
        assert doc_id is not None
        
        documents = await self.storage.load_kb_documents(kb_id)
        assert len(documents) == 1
        assert documents[0]['doc_id'] == "doc1"
        assert documents[0]['content'] == "Test document content"