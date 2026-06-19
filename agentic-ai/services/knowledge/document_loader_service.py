"""
Document Loader Service — Phase 13.
"""
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DocumentLoaderService:
    """
    Loads markdown documents from the local filesystem to be ingested into ChromaDB.
    """
    
    def __init__(self, base_dir: str = "./knowledge"):
        self.base_dir = os.path.abspath(base_dir)

    def load_all_documents(self) -> List[Dict[str, Any]]:
        """
        Recursively scans the base directory for .md files and loads their content.
        
        Returns:
            A list of dictionaries, each containing:
            - 'content': the raw text content of the file
            - 'source': the relative path to the file
            - 'category': the immediate parent directory name (e.g., 'runbooks')
            - 'title': extracted from the first H1 tag, or the filename if missing
        """
        documents = []
        if not os.path.exists(self.base_dir):
            logger.warning(f"Knowledge base directory does not exist: {self.base_dir}")
            return documents

        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.base_dir)
                    # Use the immediate parent dir as category
                    category = os.path.dirname(rel_path).split(os.sep)[0]
                    if not category:
                        category = "uncategorized"
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Extract title from first H1 if present
                        title = file.replace('.md', '')
                        for line in content.splitlines():
                            if line.startswith('# '):
                                title = line[2:].strip()
                                break
                                
                        documents.append({
                            "content": content,
                            "source": rel_path,
                            "category": category,
                            "title": title
                        })
                    except Exception as e:
                        logger.error(f"Failed to read document {file_path}: {e}")
                        
        logger.info(f"Loaded {len(documents)} documents from {self.base_dir}")
        return documents
