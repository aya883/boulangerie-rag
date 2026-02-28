

import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from Config import DB_CONFIG, EMBEDDING_MODEL, TOP_K


print(f"[Search] Loading model '{EMBEDDING_MODEL}'...")
_model = SentenceTransformer(EMBEDDING_MODEL)
print(f"[Search] Model ready ✅")



def _get_connection():
    """Open a PostgreSQL connection using credentials from config.py."""
    return psycopg2.connect(**DB_CONFIG)


def _embed(text: str) -> str:
    """
    Convert a text string into a 384-dim vector and format it as a
    PostgreSQL-compatible string: '[0.123, -0.456, ...]'
    """
    vector = _model.encode(text, convert_to_numpy=True).tolist()
    return "[" + ",".join(map(str, vector)) + "]"



def semantic_search(question: str, top_k: int = TOP_K) -> list[dict]:
    """
    Find the most semantically similar fragments to the user's question.

    How it works:
      1. Embed the question with all-MiniLM-L6-v2  →  384-dim vector
      2. Run SQL: compare against all stored vectors using cosine distance (<=>)
      3. score = 1 - cosine_distance  (so 1.0 = perfect match, 0.0 = unrelated)
      4. Return the top_k results sorted by score descending

    Args:
        question : Natural language question from the user.
        top_k    : How many results to return (default 3, set in config.py).

    Returns:
        List of dicts:  { 'texte_fragment', 'score', 'id_document' }
    """
    vector_str = _embed(question)

    sql = """
        SELECT
            id_document,
            texte_fragment,
            1 - (vecteur <=> %s::vector) AS score
        FROM embeddings
        ORDER BY score DESC
        LIMIT %s;
    """

    try:
        conn = _get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (vector_str, top_k))
            rows = cur.fetchall()
        conn.close()

        return [
            {
                "id_document":    row["id_document"],
                "texte_fragment": row["texte_fragment"],
                "score":          round(float(row["score"]), 4),
            }
            for row in rows
        ]

    except psycopg2.OperationalError as e:
        print(f"[Search] ❌ DB connection error: {e}")
        return []
    except Exception as e:
        print(f"[Search] ❌ Unexpected error: {e}")
        return []


def test_connection() -> bool:
    """
    Check that PostgreSQL is reachable and the embeddings table exists.
    Called by app.py on startup to show a clear error if credentials are wrong.

    Returns:
        True  → DB is reachable, table exists, count shown.
        False → something is wrong (check config.py).
    """
    try:
        conn = _get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM embeddings;")
            count = cur.fetchone()[0]
        conn.close()
        print(f"[Search] ✅ Connected — {count} embeddings found.")
        return True
    except Exception as e:
        print(f"[Search] ❌ Connection failed: {e}")
        return False