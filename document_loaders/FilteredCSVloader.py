import csv
from io import TextIOWrapper
from typing import Dict, List, Optional

from langchain.docstore.document import Document
from langchain_community.document_loaders import CSVLoader
from langchain_community.document_loaders.helpers import detect_file_encodings


class FilteredCSVLoader(CSVLoader):
    """A CSV loader that filters specific columns."""
    
    def __init__(
        self,
        file_path: str,
        columns_to_read: List[str],
        source_column: Optional[str] = None,
        metadata_columns: List[str] = [],
        csv_args: Optional[Dict] = None,
        encoding: Optional[str] = None,
        autodetect_encoding: bool = False,
    ):
        super().__init__(
            file_path=file_path,
            source_column=source_column,
            metadata_columns=metadata_columns,
            csv_args=csv_args or {},
            encoding=encoding,
            autodetect_encoding=autodetect_encoding,
        )
        self.columns_to_read = columns_to_read

    def load(self) -> List[Document]:
        """Load data into document objects."""
        docs = []
        try:
            with open(self.file_path, newline="", encoding=self.encoding) as csvfile:
                docs = self._read_file(csvfile)
        except UnicodeDecodeError as e:
            if self.autodetect_encoding:
                detected_encodings = detect_file_encodings(self.file_path)
                for encoding in detected_encodings:
                    try:
                        with open(
                            self.file_path, newline="", encoding=encoding.encoding
                        ) as csvfile:
                            docs = self._read_file(csvfile)
                            break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise RuntimeError(f"Failed to decode {self.file_path}") from e
            else:
                raise RuntimeError(f"Error loading {self.file_path}") from e
        except Exception as e:
            raise RuntimeError(f"Error loading {self.file_path}") from e
        return docs

    def _read_file(self, csvfile: TextIOWrapper) -> List[Document]:
        """Read and process CSV file content."""
        docs = []
        csv_reader = csv.DictReader(csvfile, **self.csv_args)
        for i, row in enumerate(csv_reader):
            content = [
                f"{col}:{str(row[col])}"
                for col in self.columns_to_read
                if col in row
            ]
            if len(content) != len(self.columns_to_read):
                missing = set(self.columns_to_read) - set(row.keys())
                raise ValueError(f"Columns not found in CSV: {missing}")
            
            content_text = "\n".join(content)
            source = (
                row.get(self.source_column, self.file_path)
                if self.source_column
                else self.file_path
            )
            metadata = {"source": source, "row": i}
            metadata.update(
                {col: row[col] for col in self.metadata_columns if col in row}
            )
            docs.append(Document(page_content=content_text, metadata=metadata))
        return docs