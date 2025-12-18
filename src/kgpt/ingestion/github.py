"""GitHub repository document ingester."""

import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from langchain_core.documents import Document
from loguru import logger

from kgpt.ingestion.base import DocumentIngester


class GitHubIngester(DocumentIngester):
    """Ingest documents from a GitHub repository."""

    # File extensions to include
    SUPPORTED_EXTENSIONS = {
        ".md",
        ".mdx",
        ".txt",
        ".rst",
        ".py",
        ".java",
        ".scala",
        ".js",
        ".ts",
        ".go",
        ".yaml",
        ".yml",
        ".json",
        ".properties",
        ".conf",
    }

    # Directories to skip
    SKIP_DIRS = {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "build",
        "dist",
        ".idea",
        ".vscode",
    }

    def __init__(
        self,
        url: str,
        branch: str = "main",
        include_code: bool = True,
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
    ):
        """
        Initialize GitHub ingester.

        Args:
            url: GitHub repository URL
            branch: Branch to clone
            include_code: Whether to include code files (not just docs)
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.url = self._normalize_url(url)
        self.branch = branch
        self.include_code = include_code
        self._temp_dir: Path | None = None

    def _normalize_url(self, url: str) -> str:
        """Normalize GitHub URL to HTTPS format."""
        url = url.strip().rstrip("/")
        if not url.endswith(".git"):
            url = f"{url}.git"
        if url.startswith("git@"):
            # Convert SSH to HTTPS
            url = url.replace("git@github.com:", "https://github.com/")
        return url

    def get_source_name(self) -> str:
        """Get source name from repo URL."""
        parsed = urlparse(self.url)
        path = parsed.path.rstrip(".git")
        return path.split("/")[-1] or "github-repo"

    def get_source_type(self) -> str:
        """Get source type."""
        return "github"

    def get_collection_name(self) -> str:
        """Get collection name based on repo."""
        parsed = urlparse(self.url)
        path = parsed.path.strip("/").rstrip(".git")
        name = path.replace("/", "_").replace("-", "_").lower()
        return f"github_{name}"

    def _detect_default_branch(self) -> str:
        """Detect the default branch of the repository."""
        import git

        try:
            # Use ls-remote to get the HEAD reference which points to the default branch
            repo_url = self.url.rstrip(".git")
            remote_refs = git.cmd.Git().ls_remote(repo_url)

            # Parse the output to find HEAD reference (points to default branch)
            head_sha = None
            for line in remote_refs.split("\n"):
                if "\tHEAD" in line:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        head_sha = parts[0].strip()
                        break

            # If we found HEAD, find which branch it points to
            if head_sha:
                for line in remote_refs.split("\n"):
                    if head_sha in line and "refs/heads/" in line:
                        branch = line.split("refs/heads/")[-1].strip()
                        if branch:
                            logger.info(f"Detected default branch: {branch}")
                            return branch

            # Fallback: try to find common branch names from all branches
            branches = []
            for line in remote_refs.split("\n"):
                if "refs/heads/" in line:
                    branch = line.split("refs/heads/")[-1].strip()
                    if branch:
                        branches.append(branch)

            # Prefer common default branch names
            for preferred in ["main", "master", "develop", "dev"]:
                if preferred in branches:
                    logger.info(f"Using fallback branch: {preferred}")
                    return preferred

            # If we found any branches, use the first one
            if branches:
                logger.info(f"Using first available branch: {branches[0]}")
                return branches[0]

            # Last resort: return main (will fail gracefully if it doesn't exist)
            logger.warning("Could not detect default branch, using 'main' as fallback")
            return "main"

        except Exception as e:
            logger.warning(f"Error detecting default branch: {e}, using fallback")
            # Fallback to common branch names
            return "main"

    def _clone_repo(self) -> Path:
        """Clone the repository to a temporary directory."""
        import git

        self._temp_dir = Path(tempfile.mkdtemp())
        logger.info(f"Cloning {self.url} to {self._temp_dir}")

        # Try cloning with the requested branch first
        branch_to_use = self.branch
        try:
            git.Repo.clone_from(
                self.url,
                self._temp_dir,
                branch=branch_to_use,
                depth=1,  # Shallow clone
            )
            logger.info(f"Successfully cloned branch: {branch_to_use}")
            return self._temp_dir
        except git.exc.GitCommandError as e:
            error_msg = str(e)
            # Check if it's a branch-not-found error
            if "not found" in error_msg.lower() or "exit code(128)" in error_msg:
                logger.warning(f"Branch '{branch_to_use}' not found, detecting default branch...")
                # Clean up failed clone attempt
                self._cleanup()
                self._temp_dir = Path(tempfile.mkdtemp())

                # Detect and use the default branch
                branch_to_use = self._detect_default_branch()
                self.branch = branch_to_use  # Update the branch attribute

                # Try cloning with the detected branch
                try:
                    git.Repo.clone_from(
                        self.url,
                        self._temp_dir,
                        branch=branch_to_use,
                        depth=1,  # Shallow clone
                    )
                    logger.info(f"Successfully cloned with detected branch: {branch_to_use}")
                    return self._temp_dir
                except Exception as retry_error:
                    logger.error(
                        f"Error cloning repository with branch '{branch_to_use}': {retry_error}"
                    )
                    self._cleanup()
                    raise
            else:
                # Some other error occurred
                logger.error(f"Error cloning repository: {e}")
                self._cleanup()
                raise
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            self._cleanup()
            raise

    def _cleanup(self):
        """Clean up temporary directory."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
            self._temp_dir = None

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if a file should be included."""
        # Check extension
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False

        # Skip non-doc files if include_code is False
        if not self.include_code:
            doc_extensions = {".md", ".mdx", ".txt", ".rst"}
            if file_path.suffix.lower() not in doc_extensions:
                return False

        # Check if in a skipped directory
        return all(parent.name not in self.SKIP_DIRS for parent in file_path.parents)

    def load_documents(self) -> list[Document]:
        """Load documents from the GitHub repository."""
        try:
            repo_path = self._clone_repo()
            documents = []

            for file_path in repo_path.rglob("*"):
                if not file_path.is_file():
                    continue

                if not self._should_include_file(file_path):
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    if not content.strip():
                        continue

                    # Create relative path for metadata
                    rel_path = file_path.relative_to(repo_path)

                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": str(rel_path),
                            "file_type": file_path.suffix.lower(),
                            "repo_url": self.url.rstrip(".git"),
                            "branch": self.branch,
                        },
                    )
                    documents.append(doc)

                except Exception as e:
                    logger.warning(f"Error reading {file_path}: {e}")
                    continue

            logger.info(f"Loaded {len(documents)} files from repository")
            return documents

        finally:
            self._cleanup()
