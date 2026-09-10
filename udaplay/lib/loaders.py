from typing import List
import json as _json
import pdfplumber
from lib.documents import Corpus, Document


class PDFLoader:
    """
    Document loader for extracting text content from PDF files.
    
    This class provides functionality to parse PDF documents and convert them
    into a structured format suitable for vector storage and retrieval. Each
    page of the PDF becomes a separate Document object, enabling page-level
    search and retrieval in RAG applications.
    
    The loader uses pdfplumber for robust PDF text extraction, handling:
    - Multi-page PDF documents
    - Text extraction with layout preservation
    - Automatic page numbering and identification
    - Filtering of empty or whitespace-only pages
    
    Example:
        >>> loader = PDFLoader("research_paper.pdf")
        >>> corpus = loader.load()
        >>> print(f"Loaded {len(corpus)} pages")
        >>> print(f"First page content: {corpus[0].content[:100]}...")
    """
    def __init__(self, pdf_path:str):
        self.pdf_path = pdf_path

    def load(self) -> Document:
        corpus = Corpus()

        with pdfplumber.open(self.pdf_path) as pdf:
            for num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    corpus.append(
                        Document(
                            id=str(num),
                            content=text
                        )
                    )
        return corpus


class JSONGameLoader:
    """
    Document loader for video game records stored in a JSON array.

    Each game object becomes a single Document whose content is a natural-language
    summary of all fields, enabling rich semantic search over the collection.

    Expected JSON schema per game object::

        {
          "id": "game_001",
          "title": "FIFA 21",
          "developer": "EA Sports",
          "publisher": "Electronic Arts",
          "release_date": "2020-10-09",
          "platforms": ["PS4", "Xbox One", ...],
          "genre": "Sports",
          "description": "..."
        }

    Example::

        >>> loader = JSONGameLoader("games.json")
        >>> corpus = loader.load()
        >>> print(f"Loaded {len(corpus)} games")
    """

    def __init__(self, json_path: str):
        self.json_path = json_path

    def load(self) -> Corpus:
        corpus = Corpus()

        with open(self.json_path, "r", encoding="utf-8") as f:
            games = _json.load(f)

        for game in games:
            game_id = game.get("id", "")
            platforms = ", ".join(game.get("platforms", []))
            content = (
                f"Title: {game.get('title', '')}\n"
                f"Developer: {game.get('developer', '')}\n"
                f"Publisher: {game.get('publisher', '')}\n"
                f"Release Date: {game.get('release_date', '')}\n"
                f"Platforms: {platforms}\n"
                f"Genre: {game.get('genre', '')}\n"
                f"Description: {game.get('description', '')}"
            )
            corpus.append(
                Document(
                    id=game_id,
                    content=content,
                    metadata={
                        "title": game.get("title", ""),
                        "developer": game.get("developer", ""),
                        "publisher": game.get("publisher", ""),
                        "genre": game.get("genre", ""),
                        "release_date": game.get("release_date", ""),
                        "json_data": _json.dumps(game),
                    },
                )
            )

        return corpus
