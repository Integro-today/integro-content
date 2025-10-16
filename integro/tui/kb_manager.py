"""TUI for managing knowledge bases."""

import asyncio
from pathlib import Path
from typing import Optional, List
from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, Static, Button, Input, TextArea,
    DataTable, Label, Select, TabbedContent, TabPane,
    ProgressBar, DirectoryTree, LoadingIndicator
)
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.worker import Worker
from rich.text import Text

from integro.config import KnowledgeBaseLoader, KnowledgeBaseConfig, ConfigStorage
from integro.config.kb_loader import DocumentExtractor
from integro.utils.logging import get_logger

logger = get_logger(__name__)


class DocumentAddModal(ModalScreen):
    """Modal for adding documents to knowledge base."""
    
    DEFAULT_CSS = """
    DocumentAddModal {
        align: center middle;
    }
    
    #doc-add-container {
        width: 70%;
        height: 70%;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    #file-tree {
        height: 100%;
        width: 100%;
        border: solid $primary;
    }
    
    #selected-files {
        height: 10;
        border: solid $secondary;
    }
    
    #button-row {
        dock: bottom;
        height: 3;
        align: center middle;
    }
    """
    
    def __init__(self, kb_id: str):
        """Initialize document add modal."""
        super().__init__()
        self.kb_id = kb_id
        self.selected_files: List[Path] = []
    
    def compose(self) -> ComposeResult:
        """Compose the modal UI."""
        with Container(id="doc-add-container"):
            yield Label("Add Documents to Knowledge Base", id="add-title")
            
            with Vertical():
                yield Label("Select files to add:")
                yield DirectoryTree(".", id="file-tree")
                
                yield Label("Selected files:")
                yield TextArea("", id="selected-files", disabled=True)
                
                with Horizontal(classes="form-row"):
                    yield Label("Extract Mode:")
                    yield Select(
                        [("full", "Full Text"),
                         ("condensed", "Condensed"),
                         ("instructions", "Instructions")],
                        id="extract-mode",
                        value="full"
                    )
            
            with Horizontal(id="button-row"):
                yield Button("Add Selected", variant="primary", id="add-button")
                yield Button("Cancel", variant="default", id="cancel-button")
    
    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, event: DirectoryTree.FileSelected):
        """Handle file selection."""
        path = Path(event.path)
        if path not in self.selected_files:
            self.selected_files.append(path)
            self.update_selected_display()
    
    def update_selected_display(self):
        """Update selected files display."""
        text_area = self.query_one("#selected-files", TextArea)
        text_area.text = "\n".join(str(f) for f in self.selected_files)
    
    @on(Button.Pressed, "#add-button")
    def add_documents(self):
        """Add selected documents."""
        extract_mode = self.query_one("#extract-mode", Select).value
        self.dismiss((self.selected_files, extract_mode))
    
    @on(Button.Pressed, "#cancel-button")
    def cancel_add(self):
        """Cancel adding."""
        self.dismiss(None)


class KnowledgeBaseEditModal(ModalScreen):
    """Modal for editing knowledge base configuration."""
    
    DEFAULT_CSS = """
    KnowledgeBaseEditModal {
        align: center middle;
    }
    
    #kb-edit-container {
        width: 70%;
        height: 60%;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .form-row {
        height: 3;
        margin: 1 0;
    }
    
    .form-label {
        width: 20;
        padding: 0 1;
    }
    
    .form-input {
        width: 100%;
    }
    
    #button-row {
        dock: bottom;
        height: 3;
        align: center middle;
    }
    """
    
    def __init__(self, kb_config: Optional[KnowledgeBaseConfig] = None):
        """Initialize edit modal."""
        super().__init__()
        self.kb_config = kb_config or KnowledgeBaseLoader.create_default_config("New KB")
    
    def compose(self) -> ComposeResult:
        """Compose the modal UI."""
        with Container(id="kb-edit-container"):
            yield Label("Edit Knowledge Base Configuration", id="edit-title")
            
            with ScrollableContainer():
                with Horizontal(classes="form-row"):
                    yield Label("Name:", classes="form-label")
                    yield Input(
                        value=self.kb_config.name,
                        placeholder="Knowledge base name",
                        id="name-input",
                        classes="form-input"
                    )
                
                with Horizontal(classes="form-row"):
                    yield Label("Description:", classes="form-label")
                    yield Input(
                        value=self.kb_config.description,
                        placeholder="Description",
                        id="desc-input",
                        classes="form-input"
                    )
                
                with Horizontal(classes="form-row"):
                    yield Label("Collection:", classes="form-label")
                    yield Input(
                        value=self.kb_config.collection_name,
                        placeholder="Collection name",
                        id="collection-input",
                        classes="form-input"
                    )
                
                with Horizontal(classes="form-row"):
                    yield Label("Chunk Size:", classes="form-label")
                    yield Input(
                        value=str(self.kb_config.chunk_size),
                        placeholder="500",
                        id="chunk-size-input",
                        classes="form-input"
                    )
                
                with Horizontal(classes="form-row"):
                    yield Label("Chunk Overlap:", classes="form-label")
                    yield Input(
                        value=str(self.kb_config.chunk_overlap),
                        placeholder="50",
                        id="overlap-input",
                        classes="form-input"
                    )
            
            with Horizontal(id="button-row"):
                yield Button("Save", variant="primary", id="save-button")
                yield Button("Cancel", variant="default", id="cancel-button")
    
    @on(Button.Pressed, "#save-button")
    def save_kb(self):
        """Save knowledge base configuration."""
        self.kb_config.name = self.query_one("#name-input", Input).value
        self.kb_config.description = self.query_one("#desc-input", Input).value
        self.kb_config.collection_name = self.query_one("#collection-input", Input).value
        
        try:
            self.kb_config.chunk_size = int(self.query_one("#chunk-size-input", Input).value)
            self.kb_config.chunk_overlap = int(self.query_one("#overlap-input", Input).value)
        except ValueError:
            self.notify("Invalid chunk size or overlap", severity="error")
            return
        
        self.dismiss(self.kb_config)
    
    @on(Button.Pressed, "#cancel-button")
    def cancel_edit(self):
        """Cancel editing."""
        self.dismiss(None)


class KnowledgeBaseManagerApp(App):
    """TUI application for managing knowledge bases."""
    
    CSS = """
    #kb-table {
        height: 50%;
    }
    
    #docs-table {
        height: 50%;
    }
    
    #button-bar {
        dock: bottom;
        height: 3;
        background: $boost;
    }
    
    .button-bar-button {
        margin: 0 1;
    }
    
    #details-panel {
        width: 40%;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
    }
    
    #progress-bar {
        width: 100%;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("n", "new_kb", "New KB"),
        Binding("e", "edit_kb", "Edit KB"),
        Binding("d", "delete_kb", "Delete KB"),
        Binding("a", "add_docs", "Add Documents"),
        Binding("r", "refresh", "Refresh"),
    ]
    
    def __init__(self, storage_path: str = "configs.db"):
        """Initialize KB manager."""
        super().__init__()
        self.storage = ConfigStorage(storage_path)
        self.loader = KnowledgeBaseLoader()
        self.kbs: List[KnowledgeBaseConfig] = []
        self.selected_kb: Optional[KnowledgeBaseConfig] = None
        self.processing = False
    
    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()
        
        with Container(id="main-container"):
            with Horizontal():
                # Ben, main tables
                with Vertical():
                    with TabbedContent():
                        with TabPane("Knowledge Bases", id="kb-tab"):
                            yield DataTable(id="kb-table")
                        
                        with TabPane("Documents", id="docs-tab"):
                            yield DataTable(id="docs-table")
                    
                    yield ProgressBar(id="progress-bar", show_eta=False)
                    
                    with Horizontal(id="button-bar"):
                        yield Button("New KB", id="new-btn", classes="button-bar-button")
                        yield Button("Edit", id="edit-btn", classes="button-bar-button")
                        yield Button("Delete", id="delete-btn", classes="button-bar-button")
                        yield Button("Add Docs", id="add-docs-btn", classes="button-bar-button")
                        yield Button("Process", id="process-btn", classes="button-bar-button")
                        yield Button("Refresh", id="refresh-btn", classes="button-bar-button")
                
                # Ben, details panel
                with ScrollableContainer(id="details-panel"):
                    yield Static("Select a knowledge base to view details", id="kb-details")
        
        yield Footer()
    
    async def on_mount(self):
        """Initialize on mount."""
        # Ben, set up tables
        kb_table = self.query_one("#kb-table", DataTable)
        kb_table.add_columns("Name", "Description", "Collection", "Docs", "Created")
        kb_table.cursor_type = "row"
        
        docs_table = self.query_one("#docs-table", DataTable)
        docs_table.add_columns("Doc ID", "Source", "Chunks", "Mode", "Created")
        docs_table.cursor_type = "row"
        
        # Ben, hide progress bar initially
        self.query_one("#progress-bar", ProgressBar).visible = False
        
        # Ben, load knowledge bases
        await self.load_kbs()
    
    async def load_kbs(self):
        """Load knowledge bases from storage."""
        try:
            kb_list = await self.storage.list_knowledge_bases()
            kb_table = self.query_one("#kb-table", DataTable)
            kb_table.clear()
            
            self.kbs = []
            for kb_data in kb_list:
                config = await self.storage.load_knowledge_base(kb_data['id'])
                if config:
                    self.kbs.append(config)
                    
                    # Ben, count documents
                    docs = await self.storage.load_kb_documents(kb_data['id'])
                    
                    kb_table.add_row(
                        kb_data['name'],
                        kb_data.get('description', '')[:50],
                        kb_data.get('collection_name', ''),
                        str(len(docs)),
                        kb_data.get('created_at', '')[:10]
                    )
            
            logger.info(f"Loaded {len(self.kbs)} knowledge bases")
        except Exception as e:
            logger.error(f"Error loading knowledge bases: {e}")
            self.notify(f"Error loading KBs: {e}", severity="error")
    
    async def load_documents(self, kb_id: str):
        """Load documents for a knowledge base."""
        try:
            docs = await self.storage.load_kb_documents(kb_id)
            docs_table = self.query_one("#docs-table", DataTable)
            docs_table.clear()
            
            for doc in docs:
                metadata = doc.get('metadata', {})
                docs_table.add_row(
                    doc['doc_id'],
                    Path(doc.get('file_path', 'Unknown')).name if doc.get('file_path') else 'Unknown',
                    str(metadata.get('total_chunks', 1)),
                    metadata.get('extract_mode', 'full'),
                    doc.get('created_at', '')[:10]
                )
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
    
    @on(DataTable.RowSelected, "#kb-table")
    async def on_kb_selected(self, event: DataTable.RowSelected):
        """Handle KB selection."""
        if 0 <= event.cursor_row < len(self.kbs):
            self.selected_kb = self.kbs[event.cursor_row]
            self.update_details_panel()
            await self.load_documents(self.selected_kb.id)
    
    def update_details_panel(self):
        """Update the details panel."""
        if not self.selected_kb:
            return
        
        details = self.query_one("#kb-details", Static)
        
        text = Text()
        text.append(f"Knowledge Base: {self.selected_kb.name}\n", style="bold cyan")
        text.append(f"\nID: {self.selected_kb.id}\n")
        text.append(f"Description:\n{self.selected_kb.description}\n")
        text.append(f"\nCollection: {self.selected_kb.collection_name}\n")
        text.append(f"Chunk Size: {self.selected_kb.chunk_size}\n")
        text.append(f"Chunk Overlap: {self.selected_kb.chunk_overlap}\n")
        text.append(f"Extract Mode: {self.selected_kb.extract_mode}\n")
        
        if self.selected_kb.embedding_model:
            text.append(f"\nEmbedding Model: {self.selected_kb.embedding_model}\n")
        
        details.update(text)
    
    @work(exclusive=True)
    async def action_new_kb(self):
        """Create new knowledge base."""
        config = await self.push_screen_wait(KnowledgeBaseEditModal())
        if config:
            await self.storage.save_knowledge_base(config)
            await self.load_kbs()
            # Ben, async workers don't need call_from_thread
            self.notify(f"Created KB: {config.name}")
    
    @work(exclusive=True)
    async def action_edit_kb(self):
        """Edit selected knowledge base."""
        if not self.selected_kb:
            # Ben, async workers don't need call_from_thread
            self.notify("No KB selected", severity="warning")
            return
        
        config = await self.push_screen_wait(KnowledgeBaseEditModal(self.selected_kb))
        if config:
            await self.storage.save_knowledge_base(config)
            await self.load_kbs()
            # Ben, async workers don't need call_from_thread
            self.notify(f"Updated KB: {config.name}")
    
    @work(exclusive=True)
    async def action_delete_kb(self):
        """Delete selected knowledge base."""
        if not self.selected_kb:
            # Ben, async workers don't need call_from_thread
            self.notify("No KB selected", severity="warning")
            return
        
        if await self.storage.delete_knowledge_base(self.selected_kb.id):
            await self.load_kbs()
            # Ben, async workers don't need call_from_thread
            self.notify(f"Deleted KB: {self.selected_kb.name}")
            self.selected_kb = None
            self.update_details_panel()
    
    @work(exclusive=True)
    async def action_add_docs(self):
        """Add documents to selected KB."""
        if not self.selected_kb:
            # Ben, async workers don't need call_from_thread
            self.notify("No KB selected", severity="warning")
            return
        
        result = await self.push_screen_wait(DocumentAddModal(self.selected_kb.id))
        if result:
            files, extract_mode = result
            await self.process_documents(files, extract_mode)
    
    @work(exclusive=True)
    async def process_documents(self, files: List[Path], extract_mode: str):
        """Process and add documents to KB."""
        if self.processing:
            return
        
        self.processing = True
        progress = self.query_one("#progress-bar", ProgressBar)
        progress.visible = True
        progress.total = len(files)
        
        try:
            # Ben, create KB instance
            kb = self.loader.create_knowledge_base(self.selected_kb)
            
            for i, file_path in enumerate(files):
                progress.update(advance=1)
                self.notify(f"Processing {file_path.name}...")
                
                # Ben, add document to KB
                doc_ids = self.loader.add_document_to_kb(
                    kb, file_path,
                    extract_mode=extract_mode,
                    chunk_size=self.selected_kb.chunk_size,
                    chunk_overlap=self.selected_kb.chunk_overlap
                )
                
                # Ben, save to storage
                for doc_id in doc_ids:
                    # Get document from KB
                    doc_data = kb.get_document(doc_id)
                    if doc_data:
                        await self.storage.save_kb_document(
                            kb_id=self.selected_kb.id,
                            doc_id=doc_id,
                            content=doc_data.get('content', ''),
                            file_path=str(file_path),
                            metadata={
                                'extract_mode': extract_mode,
                                'source': str(file_path)
                            }
                        )
            
            self.notify(f"Added {len(files)} documents to KB")
            await self.load_documents(self.selected_kb.id)
            
        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            self.notify(f"Error: {e}", severity="error")
        finally:
            progress.visible = False
            self.processing = False
    
    @work(exclusive=True)
    async def action_refresh(self):
        """Refresh knowledge bases."""
        await self.load_kbs()
        if self.selected_kb:
            await self.load_documents(self.selected_kb.id)
        # Ben, async workers don't need call_from_thread
        self.notify("Refreshed")
    
    @on(Button.Pressed, "#new-btn")
    async def on_new_button(self):
        """Handle new button."""
        await self.action_new_kb()
    
    @on(Button.Pressed, "#edit-btn")
    async def on_edit_button(self):
        """Handle edit button."""
        await self.action_edit_kb()
    
    @on(Button.Pressed, "#delete-btn")
    async def on_delete_button(self):
        """Handle delete button."""
        await self.action_delete_kb()
    
    @on(Button.Pressed, "#add-docs-btn")
    async def on_add_docs_button(self):
        """Handle add docs button."""
        await self.action_add_docs()
    
    @on(Button.Pressed, "#refresh-btn")
    async def on_refresh_button(self):
        """Handle refresh button."""
        await self.action_refresh()


if __name__ == "__main__":
    app = KnowledgeBaseManagerApp()
    app.run()