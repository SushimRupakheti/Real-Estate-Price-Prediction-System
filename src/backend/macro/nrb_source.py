from dataclasses import dataclass
from datetime import date, datetime
from urllib.parse import urljoin, urlparse
import re
import httpx
from bs4 import BeautifulSoup
from .config import SETTINGS
from .exceptions import NRBSourceDiscoveryError

@dataclass(frozen=True)
class NRBSource:
    title:str; page_url:str; file_url:str; publication_date:date|None; file_type:str

def allowed(url):
    parsed=urlparse(url)
    return parsed.scheme=="https" and (parsed.hostname or "").lower() in SETTINGS.allowed_domains

class NRBSourceDiscovery:
    PATTERN=re.compile(r"current\s+macroeconomic\s+and\s+financial\s+situation",re.I)
    def discover(self):
        try:
            response=httpx.get(SETTINGS.archive_url,timeout=SETTINGS.timeout_seconds,follow_redirects=True); response.raise_for_status()
        except Exception as exc: raise NRBSourceDiscoveryError("Unable to read the official NRB publication archive.") from exc
        candidates=[]
        soup=BeautifulSoup(response.text,"html.parser")
        for link in soup.find_all("a",href=True):
            title=" ".join(link.get_text(" ",strip=True).split()); url=urljoin(str(response.url),link["href"])
            if self.PATTERN.search(title) and allowed(url):
                context=" ".join(link.parent.get_text(" ",strip=True).split()) if link.parent else title
                match=re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}",context)
                published=datetime.strptime(match.group(0),"%B %d, %Y").date() if match else None
                candidates.append((title,url,published))
        discovered=[]
        for title,page,published in candidates:
            try:
                html=httpx.get(page,timeout=SETTINGS.timeout_seconds,follow_redirects=True); html.raise_for_status()
                content_type=html.headers.get("content-type","").lower()
                direct_type="xlsx" if "spreadsheet" in content_type or bytes(html.content).startswith(b"PK\x03\x04") else "pdf" if "pdf" in content_type or bytes(html.content).startswith(b"%PDF-") else None
                if direct_type:
                    discovered.append((0 if direct_type=="xlsx" else 2,NRBSource(title,page,str(html.url),published,direct_type)))
                    continue
                page_soup=BeautifulSoup(html.text,"html.parser")
                files=[]
                for a in page_soup.find_all("a",href=True):
                    u=urljoin(str(html.url),a["href"]); ext=urlparse(u).path.lower().rsplit(".",-1)[-1]
                    if ext in {"xlsx","csv","pdf"} and allowed(u): files.append((0 if ext=="xlsx" else 1 if ext=="csv" else 2,u,ext))
                if files:
                    _,file_url,file_type=sorted(files)[0]
                    time=page_soup.find("time"); page_date=date.fromisoformat(time.get("datetime")[:10]) if time and time.get("datetime") else published
                    discovered.append((0 if file_type=="xlsx" else 1 if file_type=="csv" else 2,NRBSource(title,page,file_url,page_date,file_type)))
            except Exception: continue
        if discovered: return sorted(discovered,key=lambda item:item[0])[0][1]
        raise NRBSourceDiscoveryError("No supported official NRB macroeconomic tables or PDF was found.")
