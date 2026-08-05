import hashlib
import time
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile, BadZipFile
import httpx
from .config import SETTINGS
from .exceptions import NRBDownloadError, NRBFileValidationError
from .nrb_source import allowed

SIGNATURES={"xlsx":b"PK\x03\x04","pdf":b"%PDF-"}
class NRBDownloader:
    def download(self,url,file_type):
        if not allowed(url): raise NRBDownloadError("Only HTTPS downloads from allow-listed NRB domains are permitted.")
        SETTINGS.temp_directory.mkdir(parents=True,exist_ok=True); limit=SETTINGS.max_download_mb*1024*1024
        error=None
        for attempt in range(SETTINGS.retry_count):
            try:
                with httpx.stream("GET",url,timeout=SETTINGS.timeout_seconds,follow_redirects=True) as response:
                    response.raise_for_status()
                    content_type=response.headers.get("content-type","").lower()
                    allowed_types={"xlsx":("spreadsheet","octet-stream","zip"),"pdf":("pdf","octet-stream"),"csv":("csv","text/plain","octet-stream")}
                    if not any(token in content_type for token in allowed_types.get(file_type,())):
                        raise NRBFileValidationError("Official file returned an unexpected content type.")
                    data=bytearray()
                    for chunk in response.iter_bytes():
                        data.extend(chunk)
                        if len(data)>limit: raise NRBFileValidationError("NRB download exceeds the configured size limit.")
                signature=SIGNATURES.get(file_type)
                if signature and not bytes(data).startswith(signature): raise NRBFileValidationError(f"Downloaded file is not a valid {file_type.upper()} file.")
                if file_type=="xlsx":
                    try:
                        with ZipFile(BytesIO(data)) as archive:
                            if archive.testzip() is not None or "[Content_Types].xml" not in archive.namelist(): raise NRBFileValidationError("XLSX workbook ZIP is corrupt.")
                    except BadZipFile as exc: raise NRBFileValidationError("XLSX workbook ZIP is invalid.") from exc
                checksum=hashlib.sha256(data).hexdigest(); path=SETTINGS.temp_directory/f"{checksum}.{file_type}"; path.write_bytes(data)
                return path,checksum
            except NRBFileValidationError: raise
            except Exception as exc: error=exc; time.sleep(min(2**attempt,4))
        raise NRBDownloadError("Official NRB file download failed after limited retries.") from error
