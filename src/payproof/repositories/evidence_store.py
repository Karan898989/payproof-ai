import hashlib
from pathlib import Path
from uuid import uuid4
from ..config import settings
from ..domain.enums import EvidenceType
from ..domain.models import EvidenceObject

class EvidenceStore:
    def __init__(self, root_path: Path | None = None):
        self.root_path = root_path or settings.evidence_store_path
        self.root_path.mkdir(parents=True, exist_ok=True)

    def save_file(
        self,
        case_id: str,
        filename: str,
        content: bytes,
        mime_type: str,
        evidence_type: EvidenceType,
    ) -> EvidenceObject:
        evidence_id = str(uuid4())
        # Clean filename to avoid path traversal
        clean_filename = Path(filename).name
        
        # Structure: root / case_id / evidence_id / clean_filename
        dest_dir = self.root_path / case_id / evidence_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / clean_filename

        with open(dest_file, "wb") as f:
            f.write(content)

        sha256 = hashlib.sha256(content).hexdigest()
        byte_size = len(content)

        return EvidenceObject(
            id=evidence_id,
            case_id=case_id,
            evidence_type=evidence_type,
            original_filename=clean_filename,
            mime_type=mime_type,
            sha256=sha256,
            byte_size=byte_size,
            local_path=str(dest_file),
        )

    def read_file(self, local_path: str) -> bytes:
        p = Path(local_path).resolve()
        # Ensure path stays within evidence store
        root = self.root_path.resolve()
        if not str(p).startswith(str(root)):
            raise PermissionError("Path traversal detected outside evidence store")
        with open(p, "rb") as f:
            return f.read()

evidence_store = EvidenceStore()
