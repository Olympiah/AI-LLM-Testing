"""Fetch the source documents, chunk them, embed them and upload them to Pinecone.

This is the ingestion half of a RAG (retrieval-augmented generation) pipeline:
  1. fetch  -> download the raw text of each source and save it locally
  2. chunk  -> split long text into small overlapping pieces
  3. embed  -> turn each piece into a vector with OpenAI
  4. upload -> store the vectors (plus the original text) in Pinecone
The chatbot later searches those vectors to find passages relevant to a question.

Usage (run from the repo root):
  py ingest/ingest.py fetch    # download and clean the sources into data/raw/
  py ingest/ingest.py upload   # chunk, embed and upload (replaces all vectors in the index)
"""
import io
import os
import re
import sys
import time
from pathlib import Path

import requests                    # HTTP client used to download pages
from pypdf import PdfReader        # PDF reader used to extract text from the CBK legislation PDFs
from bs4 import BeautifulSoup      # HTML parser used to strip Kenya Law pages down to text
from dotenv import load_dotenv     # loads API keys from a .env file into environment variables

# Paths are resolved from this file's location, so the script works no matter
# which directory it is launched from.
ROOT = Path(__file__).resolve().parent.parent   # repo root (ingest/ingest.py -> ingest -> root)
RAW = ROOT / "data" / "raw"                      # where fetched text files are saved
load_dotenv(ROOT / "chatbot" / ".env")  # keys stay in chatbot/.env, never in this file

# Identify ourselves to the servers. A descriptive User-Agent with a contact URL is
# good scraping etiquette and reduces the chance of being blocked as an anonymous bot.
HEADERS = {
    "User-Agent": "AI-LLM-Testing-portfolio-bot/0.1 "
    "(educational project; +https://github.com/Olympiah/AI-LLM-Testing)"
}

# The knowledge base. Each entry has:
#   slug  - short unique name, used for the output filename and vector IDs
#   type  - which fetcher to use ("wikipedia" uses the API, "pdf" downloads and reads a PDF,
#           "html" scrapes a web page)
#   title - the Wikipedia article title (only needed for the Wikipedia API)
#   url   - the human-readable page; stored as metadata so answers can cite a source
SOURCES = [
    {"slug": "wikipedia-m-pesa", "type": "wikipedia", "title": "M-Pesa",
     "url": "https://en.wikipedia.org/wiki/M-Pesa"},
    {"slug": "wikipedia-safaricom", "type": "wikipedia", "title": "Safaricom",
     "url": "https://en.wikipedia.org/wiki/Safaricom"},
    {"slug": "wikipedia-central-bank-of-kenya", "type": "wikipedia",
     "title": "Central Bank of Kenya",
     "url": "https://en.wikipedia.org/wiki/Central_Bank_of_Kenya"},
    {"slug": "cbk-nps-act", "type": "pdf",
     "url": "https://www.centralbank.go.ke/wp-content/uploads/2016/08/NATIONAL-PAYMENT-SYSTEM-ACT-No-39-of-2011-21.pdf"},
    {"slug": "cbk-nps-regulations-2014", "type": "pdf",
     "url": "https://www.centralbank.go.ke/images/docs/legislation/NPSRegulations2014.pdf"},
]

EMBED_MODEL = "text-embedding-3-small"  # must match the chatbot (1536 dimensions)
CHUNK_SIZE = 1000    # max characters per chunk; small enough to be specific, big enough for context
CHUNK_OVERLAP = 150  # characters repeated between neighbouring chunks so sentences cut at a boundary aren't lost


def clean(text: str) -> str:
    """Normalise whitespace and drop blank lines."""
    # Collapse runs of spaces/tabs inside each line to a single space
    lines = [" ".join(line.split()) for line in text.splitlines()]
    # Keep only non-empty lines
    return "\n".join(line for line in lines if line)


def fetch_wikipedia(title: str) -> str:
    """Get an article's plain text through the MediaWiki API (cleaner than scraping HTML)."""
    r = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={"action": "query", "prop": "extracts", "explaintext": 1,  # explaintext = no HTML markup
                "format": "json", "titles": title, "redirects": 1},       # follow redirects to the real page
        headers=HEADERS, timeout=60,
    )
    r.raise_for_status()  # raise an error on 4xx/5xx instead of silently saving an error page
    pages = r.json()["query"]["pages"]
    # The API keys results by page ID, which we don't know in advance, so take the first one
    return next(iter(pages.values()))["extract"]


# Page headers, footers and page numbers that repeat on every page of the CBK PDFs.
# Lines are compared after replacing every digit with "#", so "... 2014 713" and
# "... 2014 714" count as the same line.
PDF_NOISE_LINES = {
    "NO. ## National Payment System",
    "Kenya Subsidiary Legislation, ####",
    "Kenya Subsidiary Legislation, #### ###",
}


def fetch_pdf(url: str) -> str:
    """Download a PDF and extract its text, page by page."""
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()  # fail loudly on 4xx/5xx instead of parsing an error page
    reader = PdfReader(io.BytesIO(r.content))  # read the PDF from memory, no temp file needed
    # extract_text() can return None for a page with no text layer (e.g. a scanned image)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    kept = []
    for line in text.split("\n"):
        # Collapse runs of whitespace first (the PDF text has odd gaps), then digits -> "#"
        masked = re.sub(r"\d", "#", " ".join(line.split()))
        # Drop the known header/footer lines and lines that are only a 1-4 digit page number
        if masked in PDF_NOISE_LINES or re.fullmatch(r"#{1,4}", masked):
            continue
        kept.append(line)
    return "\n".join(kept)


def fetch_html(url: str) -> str:
    """Download an ordinary HTML page and extract its main text."""
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body
    if root is None:
        raise RuntimeError(
            f"No page content at {url} (status {r.status_code}, {len(r.text)} bytes). "
            "The site may be blocking automated access. Do not work around it."
        )
    return root.get_text("\n")


def fetch_all() -> None:
    """Stage 1: download every source, clean it and save it as data/raw/<slug>.txt."""
    RAW.mkdir(parents=True, exist_ok=True)  # create data/raw/ if it doesn't exist yet
    for s in SOURCES:
        print(f"Fetching {s['url']}")
        # Pick the fetcher that matches the source type
        if s["type"] == "wikipedia":
            text = fetch_wikipedia(s["title"])
        elif s["type"] == "pdf":
            text = fetch_pdf(s["url"])
        elif s["type"] == "html":
            text = fetch_html(s["url"])
        else:
            sys.exit(f"Unknown source type: {s['type']}")
        text = clean(text)
        (RAW / f"{s['slug']}.txt").write_text(text, encoding="utf-8")
        print(f"  saved {len(text):,} characters")
        # Sanity check: a real article or Act is far longer than this, so a tiny
        # result usually means an empty, blocked or error page
        if len(text) < 5000:
            print("  WARNING: very short. The page may be empty or blocked. Check the file.")
        time.sleep(2)  # be polite to the servers


def chunk(text: str) -> list[str]:
    """Split text into chunks of roughly CHUNK_SIZE characters with CHUNK_OVERLAP overlap."""
    # Step 1: break the text into pieces no longer than CHUNK_SIZE.
    # Lines are kept whole where possible; a single very long line is hard-split.
    pieces = []
    for para in text.split("\n"):
        pieces += [para[i:i + CHUNK_SIZE] for i in range(0, len(para), CHUNK_SIZE)]
    # Step 2: pack pieces into chunks until adding another would exceed CHUNK_SIZE
    chunks, cur = [], ""
    for p in pieces:
        if cur and len(cur) + len(p) + 1 > CHUNK_SIZE:   # +1 accounts for the joining newline
            chunks.append(cur)                           # current chunk is full, save it
            cur = cur[-CHUNK_OVERLAP:] + "\n" + p        # start the next chunk with the tail of the last
        else:
            cur = f"{cur}\n{p}" if cur else p            # still room, keep appending
    if cur:
        chunks.append(cur)                               # don't forget the final partial chunk
    return chunks


def upload_all() -> None:
    """Stage 2: chunk every saved file, embed the chunks and upload them to Pinecone."""
    # Imported here so the fetch stage works even if these libraries aren't needed/installed yet
    from openai import OpenAI
    from pinecone import Pinecone

    client = OpenAI()  # reads OPENAI_API_KEY loaded from chatbot/.env
    index = Pinecone(api_key=os.environ["PINECONE_API_KEY"]).Index(os.environ["PINECONE_INDEX"])

    # Build a flat list of (vector_id, text, source_url) for every chunk of every source
    records = []
    for s in SOURCES:
        path = RAW / f"{s['slug']}.txt"
        if not path.exists():
            sys.exit(f"Missing {path}. Run the fetch step first.")
        chunks = chunk(path.read_text(encoding="utf-8"))
        print(f"{s['slug']}: {len(chunks)} chunks")
        # ID like "wikipedia-m-pesa-0", "wikipedia-m-pesa-1", ... is unique and traceable
        records += [(f"{s['slug']}-{i}", c, s["url"]) for i, c in enumerate(chunks)]

    try:
        index.delete(delete_all=True)  # start clean so old chunks never linger
    except Exception as e:
        # Deleting from an empty index can raise an error; that's harmless, so carry on
        print(f"(nothing to delete: {e})")

    # Process in batches of 100 to keep each API request a reasonable size
    for start in range(0, len(records), 100):
        batch = records[start:start + 100]
        # One API call embeds the whole batch; results come back in the same order as the input
        emb = client.embeddings.create(model=EMBED_MODEL, input=[b[1] for b in batch])
        index.upsert(vectors=[
            # Store the vector plus the original text and source URL, so the chatbot
            # can show the passage and cite where it came from
            {"id": rid, "values": e.embedding, "metadata": {"text": text, "source": url}}
            for (rid, text, url), e in zip(batch, emb.data)
        ])
        print(f"  uploaded {start + len(batch)}/{len(records)}")
    print("Done.")


# Command-line entry point: exactly one argument, either "fetch" or "upload"
if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("fetch", "upload"):
        sys.exit("Usage: py ingest/ingest.py fetch | upload")
    fetch_all() if sys.argv[1] == "fetch" else upload_all()
