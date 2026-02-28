

import os
import re
import psycopg2
import pdfplumber
from sentence_transformers import SentenceTransformer
from Config import DB_CONFIG, EMBEDDING_MODEL

PDF_FOLDER = "."


NOISE_LINES = [
    r'vtr\s*&?\s*beyond',
    r'no\.\s*8.*pingbei',
    r'stresemann',
    r'tel\s*:',
    r'mail\s*:',
    r'website\s*:',
    r'last\s*updating',
    r'www\.',
    r'info@',
    r'\+49',
    r'86-756',
    r'nanping.*zhuhai',
    r'zone.*china',
    r'berlin.*germany',
    r'food\s+enzy',          # logo text
    r'innovators',
    r'^p$',                  # stray letter P
    r'^g$',                  # stray letter g
    r'^u$',
    r'^\d{1,2}$',            # lone numbers like "5" "10"
]

# ── Sections we WANT to keep ─────────────────────────────────────────────────
GOOD_SECTIONS = {
    "product description", "effective material", "application",
    "function", "dosage", "activity", "allergens", "storage",
    "description du produit", "matière active", "fonction",
    "dosage recommandé", "allergènes", "conservation",
}

# ── Sections to SKIP ─────────────────────────────────────────────────────────
SKIP_SECTIONS = {
    "microbiology", "heavy metals", "ionization status", "package",
    "gmo status", "physicochemical", "organoleptic", "food safety data",
    "food safty data", "indicatives values", "satisfactory", "acceptable",
    "bakery enzyme", "technical data sheet",
}


# ── Text extraction with pdfplumber ──────────────────────────────────────────
def extract_text(pdf_path: str) -> str:
    lines_out = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract words with their x position to detect columns
            words = page.extract_words(x_tolerance=3, y_tolerance=3)
            if not words:
                continue

            # Find page midpoint to separate left/right columns
            page_mid = page.width / 2

            # Group words by line (y position)
            lines = {}
            for w in words:
                y = round(w['top'] / 5) * 5  # bucket by ~5px
                lines.setdefault(y, []).append(w)

            # Sort lines top to bottom
            for y in sorted(lines.keys()):
                row_words = sorted(lines[y], key=lambda w: w['x0'])

                # Separate left-column words from right-column (header/address) words
                left_words  = [w['text'] for w in row_words if w['x0'] < page_mid * 1.1]
                right_words = [w['text'] for w in row_words if w['x0'] >= page_mid * 1.1]

                # Only keep left column (main content)
                # Right column is usually address/logo noise on these PDFs
                line_text = " ".join(left_words).strip()
                if line_text:
                    lines_out.append(line_text)

    return "\n".join(lines_out)


# ── Remove noise lines ────────────────────────────────────────────────────────
def clean_lines(text: str) -> str:
    cleaned = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip if matches any noise pattern
        skip = False
        for pat in NOISE_LINES:
            if re.search(pat, line, re.IGNORECASE):
                skip = True
                break
        if not skip and len(line) > 2:
            cleaned.append(line)
    return "\n".join(cleaned)


# ── Detect product name ───────────────────────────────────────────────────────
def get_product_name(text: str, filename: str) -> str:
    match = re.search(r'BVZyme\s+[\w\d®\s]+', text)
    if match:
        name = match.group(0).strip()
        # Trim at first known section keyword
        for kw in ["Bakery", "Product", "Enzyme", "Technical"]:
            if kw in name:
                name = name[:name.index(kw)].strip()
        if len(name) > 3:
            return name
    for line in text.splitlines()[:6]:
        line = line.strip()
        if 4 < len(line) < 55:
            return line
    return re.sub(r'[_\-]+', ' ', os.path.splitext(filename)[0]).strip()


# ── Section-based chunking ────────────────────────────────────────────────────
def chunk_sections(text: str, product_name: str) -> list[str]:
    header_pattern = "|".join(re.escape(h) for h in
                               ["Product Description", "Effective material",
                                "Application", "Function", "Dosage", "Activity",
                                "Allergens", "Storage", "Description du produit",
                                "Matière active", "Fonction", "Dosage recommandé",
                                "Allergènes", "Conservation"])

    pattern = re.compile(rf'(?im)^({header_pattern})\s*:?\s*$|^({header_pattern})\s*:', )
    parts   = pattern.split(text)

    chunks = []

    if len(parts) <= 1:
        # No sections — use whole cleaned text as one chunk
        paras = [p.strip() for p in re.split(r'\n{2,}', text) if len(p.strip()) > 30]
        return [f"[{product_name}] {p}" for p in paras]

    i = 0
    while i < len(parts):
        part = parts[i]
        if part is None:
            i += 1
            continue
        part = part.strip()
        if not part:
            i += 1
            continue

        # Check if this part is a section header
        if part.lower() in GOOD_SECTIONS:
            header  = part
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            content = re.sub(r'\n+', ' ', content).strip()
            content = re.sub(r'\s{2,}', ' ', content)

            if content and len(content) > 8:
                chunk = f"[{product_name}] {header}: {content}"
                if len(chunk) > 650:
                    chunk = chunk[:647] + "..."
                chunks.append(chunk)
            i += 2
        elif part.lower() in SKIP_SECTIONS:
            i += 2  # skip header + content
        else:
            i += 1

    if not chunks:
        # Fallback: cleaned text paragraph by paragraph
        for para in re.split(r'\n', text):
            para = para.strip()
            if len(para) > 30:
                chunks.append(f"[{product_name}] {para}")

    return chunks


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    pdf_files = sorted([f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")])
    if not pdf_files:
        print(f"⚠️  No PDF files found in '{PDF_FOLDER}/'.")
        return

    print(f"📂 {len(pdf_files)} PDF(s) found\n")
    print(f"🔄 Loading model '{EMBEDDING_MODEL}'...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("✅ Model loaded.\n")

    print("🔌 Connecting to PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("✅ Connected.\n")

    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id             SERIAL PRIMARY KEY,
                id_document    INT,
                texte_fragment TEXT,
                vecteur        VECTOR(384)
            );
        """)
        cur.execute("TRUNCATE TABLE embeddings RESTART IDENTITY;")
        print("🗑️  Table cleared.\n")

        total = 0

        for doc_id, pdf_file in enumerate(pdf_files, start=1):
            print(f"📄 [{doc_id}/{len(pdf_files)}] {pdf_file}")

            raw   = extract_text(os.path.join(PDF_FOLDER, pdf_file))
            text  = clean_lines(raw)

            if not text:
                print("   ⚠️  No usable text, skipping.\n")
                continue

            product_name = get_product_name(text, pdf_file)
            print(f"   🏷️  Product : {product_name}")

            chunks = chunk_sections(text, product_name)
            print(f"   ✂️  {len(chunks)} chunks:")
            for i, chunk in enumerate(chunks, 1):
                preview = chunk[:100].replace('\n', ' ')
                print(f"      {i}. {preview}...")
                vec = model.encode(chunk).tolist()
                vec_str = "[" + ",".join(map(str, vec)) + "]"
                cur.execute(
                    "INSERT INTO embeddings (id_document, texte_fragment, vecteur) "
                    "VALUES (%s, %s, %s::vector);",
                    (doc_id, chunk, vec_str)
                )

            total += len(chunks)
            print()

        conn.commit()

    conn.close()
    print("=" * 55)
    print(f"✅ Done! {total} clean chunks inserted from {len(pdf_files)} PDF(s).")
    print("🚀 Run: streamlit run app.py")


if __name__ == "__main__":
    main()