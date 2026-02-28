

import re
import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv
load_dotenv()
from Search import semantic_search, test_connection


TRANSLATIONS = {
    "fr": {
        "page_title":    "Recherche Sémantique — Boulangerie",
        "header_title":  "Recherche Sémantique",
        "header_sub":    "Boulangerie & Pâtisserie — Fiches Techniques Ingrédients",
        "search_label":  "Posez votre question",
        "placeholder":   "Ex : Quelles sont les quantités recommandées d'alpha-amylase, xylanase et d'acide ascorbique ?",
        "btn_search":    "🔍  Rechercher",
        "btn_examples":  "💡 Exemples",
        "db_error":      "❌ Connexion à la base de données impossible. Vérifiez `Config.py`.",
        "no_result":     "😕 Aucun résultat trouvé.<br><small>Essayez de reformuler votre question.</small>",
        "warn_empty":    "⚠️ Veuillez entrer une question.",
        "spinner_search":"🔍 Recherche des fragments pertinents…",
        "spinner_answer":"🤖 Génération de la réponse…",
        "ai_section":    "🤖 Réponse générée",
        "ai_header":     "🥐 Réponse basée sur les fiches techniques",
        "src_section":   "📚 Fragments sources",
        "fragment":      "Fragment",
        "document":      "Document",
        "score":         "Score",
        "very_relevant": "✅ Très pertinent",
        "relevant":      "🟡 Pertinent",
        "low_relevant":  "🔸 Faiblement pertinent",
        "footer_model":  "Modèle embedding",
        "footer_sim":    "Similarité",
        "footer_db":     "Base",
        "footer_team":   "Team",
        "lang_btn":      "🇸🇦 العربية",
        "dir":           "ltr",
        "examples": [
            "Quelles sont les quantités recommandées d'alpha-amylase et de xylanase ?",
            "Quel est le dosage de l'acide ascorbique pour la surgélation ?",
            "Comment la transglutaminase améliore-t-elle la texture du pain ?",
            "Quels sont les allergènes présents dans les enzymes BVZyme ?",
            "Dosage recommandé pour la glucose oxidase en panification ?",
        ],
        "prompt": lambda context, question: f"""Tu es un expert en formulation boulangerie et pâtisserie industrielle.

Voici des extraits de fiches techniques d'ingrédients et d'additifs :

{context}

Question posée : {question}

Instructions :
- Réponds en français, de façon claire et directement compréhensible par un professionnel de boulangerie.
- Structure ta réponse avec des points clés si nécessaire.
- Cite les noms des produits (ex: BVZyme TG881) quand tu mentionnes des données spécifiques.
- Inclus les dosages, unités (ppm, %) et conditions d'utilisation si disponibles.
- Si une information est absente des fragments, dis-le clairement.
- Ne répète pas les fragments bruts — synthétise et explique."""
    },
    "ar": {
        "page_title":    "البحث الدلالي — المخبزة",
        "header_title":  "البحث الدلالي",
        "header_sub":    "المخبزة والمعجنات — البطاقات التقنية للمكونات",
        "search_label":  "اطرح سؤالك",
        "placeholder":   "مثال: ما هي الجرعات الموصى بها للألفا أميلاز والزيلاناز وحمض الأسكوربيك؟",
        "btn_search":    "🔍  بحث",
        "btn_examples":  "💡 أمثلة",
        "db_error":      "❌ تعذر الاتصال بقاعدة البيانات. تحقق من Config.py",
        "no_result":     "😕 لم يتم العثور على نتائج.<br><small>حاول إعادة صياغة سؤالك.</small>",
        "warn_empty":    "⚠️ الرجاء إدخال سؤال.",
        "spinner_search":"🔍 جارٍ البحث عن المقاطع ذات الصلة…",
        "spinner_answer":"🤖 جارٍ توليد الإجابة…",
        "ai_section":    "🤖 الإجابة المولَّدة",
        "ai_header":     "🥐 إجابة مستندة إلى البطاقات التقنية",
        "src_section":   "📚 المقاطع المصدرية",
        "fragment":      "مقطع",
        "document":      "وثيقة",
        "score":         "النتيجة",
        "very_relevant": "✅ ذو صلة جداً",
        "relevant":      "🟡 ذو صلة",
        "low_relevant":  "🔸 صلة ضعيفة",
        "footer_model":  "نموذج التضمين",
        "footer_sim":    "التشابه",
        "footer_db":     "قاعدة البيانات",
        "footer_team":   "الفريق",
        "lang_btn":      "🇫🇷 Français",
        "dir":           "rtl",
        "examples": [
            "ما هي الجرعات الموصى بها للألفا أميلاز والزيلاناز؟",
            "ما هو جرعة حمض الأسكوربيك للتجميد؟",
            "كيف تحسّن الترانسغلوتاميناز نسيج الخبز؟",
            "ما هي مسببات الحساسية في إنزيمات BVZyme؟",
            "الجرعة الموصى بها للغلوكوز أوكسيداز في صناعة الخبز؟",
        ],
        "prompt": lambda context, question: f"""أنت خبير في صياغة منتجات المخابز والمعجنات الصناعية.

فيما يلي مقتطفات من البطاقات التقنية للمكونات والإضافات:

{context}

السؤال المطروح: {question}

التعليمات:
- أجب باللغة العربية بطريقة واضحة ومفهومة لمتخصص في المخابز.
- نظّم إجابتك بنقاط رئيسية عند الحاجة.
- اذكر أسماء المنتجات (مثل BVZyme TG881) عند الإشارة إلى بيانات محددة.
- أدرج الجرعات والوحدات (ppm، %) وشروط الاستخدام إن توفرت.
- إذا كانت المعلومات غير متوفرة في المقاطع، صرّح بذلك بوضوح.
- لا تكرر المقاطع الخام — لخّص واشرح."""
    }
}


st.set_page_config(page_title="Recherche Sémantique — Boulangerie", page_icon="🥐", layout="centered")

if "lang" not in st.session_state:
    st.session_state.lang = "fr"

T = TRANSLATIONS[st.session_state.lang]
is_rtl = T["dir"] == "rtl"


st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Sans+3:wght@400;500;600&family=Noto+Naskh+Arabic:wght@400;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: {'Noto Naskh Arabic, Source Sans 3' if is_rtl else 'Source Sans 3'}, sans-serif;
    direction: {T['dir']};
}}
.stApp {{ background: #faf7f2; }}

.header-block {{
    background: linear-gradient(135deg, #3d2b1f 0%, #6b3f2a 100%);
    border-radius: 16px; padding: 2.5rem 2rem 2rem;
    margin-bottom: 2rem; text-align: center;
    box-shadow: 0 8px 32px rgba(61,43,31,0.18);
}}
.header-block h1 {{
    font-family: {'Noto Naskh Arabic' if is_rtl else 'Playfair Display'}, serif;
    color: #f5e6c8; font-size: 2.1rem; margin: 0 0 0.3rem;
}}
.header-block p {{ color: #c9a97a; font-size: 1rem; margin: 0; }}
.header-icon {{ font-size: 2.8rem; margin-bottom: 0.5rem; }}

/* Language toggle */
.lang-bar {{
    display: flex;
    justify-content: flex-end;
    margin-bottom: 1rem;
}}

.search-label {{
    font-family: {'Noto Naskh Arabic' if is_rtl else 'Playfair Display'}, serif;
    font-size: 1.1rem; color: #3d2b1f; font-weight: 600; margin-bottom: 0.3rem;
    text-align: {'right' if is_rtl else 'left'};
}}

.ai-answer-box {{
    background: linear-gradient(135deg, #fffdf7, #fff8ee);
    border: 2px solid #c9813a; border-radius: 14px;
    padding: 1.4rem 1.6rem; margin-bottom: 1.8rem;
    box-shadow: 0 4px 20px rgba(201,129,58,0.12);
    direction: {T['dir']};
    text-align: {'right' if is_rtl else 'left'};
}}
.ai-answer-header {{
    display: flex; align-items: center; gap: 0.6rem;
    font-family: {'Noto Naskh Arabic' if is_rtl else 'Playfair Display'}, serif;
    font-size: 1rem; font-weight: 700; color: #6b3f2a;
    margin-bottom: 0.8rem;
    border-bottom: 1px solid #f0dcc0; padding-bottom: 0.5rem;
    justify-content: {'flex-end' if is_rtl else 'flex-start'};
}}
.ai-answer-text {{
    font-size: 0.97rem; color: #2c1f14; line-height: 1.9;
}}

div[data-testid="stExpander"] .stButton > button {{
    background: #f5ede0 !important; color: #3d2b1f !important;
    text-align: {'right' if is_rtl else 'left'} !important;
    font-size: 0.83rem !important; font-weight: 500 !important;
    padding: 0.4rem 0.8rem !important; border-radius: 8px !important;
    white-space: normal !important; word-break: break-word !important;
    height: auto !important; line-height: 1.45 !important;
    border: 1px solid #ddd0c0 !important; margin-bottom: 0.3rem !important;
}}
div[data-testid="stExpander"] .stButton > button:hover {{
    background: #ede0cc !important; opacity: 1 !important;
}}

.result-card {{
    background: #fff; border-radius: 12px; padding: 0;
    margin-bottom: 1rem; box-shadow: 0 2px 12px rgba(61,43,31,0.07);
    border: 1px solid #ede4d8; overflow: hidden;
    transition: box-shadow 0.2s, transform 0.2s;
    direction: ltr;
}}
.result-card:hover {{ box-shadow: 0 4px 20px rgba(61,43,31,0.13); transform: translateY(-2px); }}
.result-card-bar {{ height: 4px; width: 100%; }}
.bar-high   {{ background: linear-gradient(90deg, #2d6a2d, #4caf50); }}
.bar-medium {{ background: linear-gradient(90deg, #c9813a, #f0a050); }}
.bar-low    {{ background: linear-gradient(90deg, #7a5c3a, #a07850); }}
.result-card-body {{ padding: 1rem 1.3rem 0.9rem; }}
.result-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; }}
.result-rank {{ display: flex; align-items: center; gap: 0.5rem; }}
.rank-number {{
    background: #3d2b1f; color: #f5e6c8;
    font-size: 0.82rem; font-weight: 700;
    width: 26px; height: 26px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
}}
.rank-label {{ font-size: 0.9rem; font-weight: 700; color: #6b3f2a; }}
.score-pill {{ padding: 0.25rem 0.8rem; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }}
.score-pill.high   {{ background: #e8f5e9; color: #2d6a2d; border: 1px solid #a5d6a7; }}
.score-pill.medium {{ background: #fff3e0; color: #c9813a; border: 1px solid #ffcc80; }}
.score-pill.low    {{ background: #f3ede6; color: #7a5c3a; border: 1px solid #d4b896; }}
.score-bar-wrap {{ background: #f0e8d8; border-radius: 4px; height: 4px; margin-bottom: 0.7rem; overflow: hidden; }}
.score-bar-fill {{ height: 100%; border-radius: 4px; }}
.fill-high   {{ background: linear-gradient(90deg, #2d6a2d, #4caf50); }}
.fill-medium {{ background: linear-gradient(90deg, #c9813a, #f0a050); }}
.fill-low    {{ background: linear-gradient(90deg, #7a5c3a, #a07850); }}
.result-text {{
    font-size: 0.88rem; color: #2c1f14; line-height: 1.6;
    padding: 0.7rem; background: #faf7f2;
    border-radius: 7px; border: 1px solid #ede4d8; margin-bottom: 0.6rem;
}}
.result-footer {{ display: flex; align-items: center; justify-content: space-between; }}
.doc-tag {{ font-size: 0.75rem; color: #9e7a56; background: #f0e8d8; padding: 0.2rem 0.5rem; border-radius: 6px; }}
.score-value {{ font-size: 0.75rem; color: #9e7a56; }}

.section-title {{
    font-family: {'Noto Naskh Arabic' if is_rtl else 'Playfair Display'}, serif;
    font-size: 1rem; color: #3d2b1f; font-weight: 700;
    margin: 1.2rem 0 0.6rem;
    padding-bottom: 0.3rem; border-bottom: 2px solid #e8d8c0;
    text-align: {'right' if is_rtl else 'left'};
}}

.empty-state {{
    text-align: center; color: #9e7a56; padding: 2.5rem;
    font-size: 1rem; background: #fff; border-radius: 12px;
    border: 1px dashed #ddd0c0;
}}
.footer {{
    text-align: center; color: #b5967a; font-size: 0.82rem;
    margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid #e8ddd0;
}}
div[data-testid="stTextArea"] textarea {{
    border: 2px solid #ddd0c0 !important; border-radius: 10px !important;
    background: #fff !important; font-size: 0.97rem !important; color: #2c1f14 !important;
    direction: {T['dir']} !important;
}}
div[data-testid="stTextArea"] textarea:focus {{
    border-color: #c9813a !important; box-shadow: 0 0 0 2px rgba(201,129,58,0.15) !important;
}}
.stButton > button {{
    background: linear-gradient(135deg, #6b3f2a, #c9813a) !important;
    color: #fff !important; border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; font-size: 1rem !important;
    padding: 0.6rem 2rem !important; width: 100% !important;
}}
.stButton > button:hover {{ opacity: 0.88 !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)


col_lang = st.columns([4, 1])
with col_lang[1]:
    if st.button(T["lang_btn"], key="lang_toggle"):
        st.session_state.lang = "ar" if st.session_state.lang == "fr" else "fr"
        st.rerun()


st.markdown(f"""
<div class="header-block">
    <div class="header-icon">🥐</div>
    <h1>{T['header_title']}</h1>
    <p>{T['header_sub']}</p>
</div>
""", unsafe_allow_html=True)


@st.cache_resource
def check_db():
    return test_connection()

db_ok = check_db()
if not db_ok:
    st.error(T["db_error"])
    st.stop()


def generate_answer(question: str, chunks: list[dict], lang: str) -> str:
    context = "\n\n".join([
        f"Fragment {i+1}:\n{c['texte_fragment']}"
        for i, c in enumerate(chunks)
    ])
    prompt = TRANSLATIONS[lang]["prompt"](context, question)
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"*(Génération indisponible : {e})*"


def score_class(s): return "high" if s >= 0.75 else "medium" if s >= 0.50 else "low"
def score_label(s, T):
    if s >= 0.75: return T["very_relevant"]
    if s >= 0.50: return T["relevant"]
    return T["low_relevant"]
def score_pct(s): return min(100, max(0, int(s * 100)))


st.markdown(f'<div class="search-label">{T["search_label"]}</div>', unsafe_allow_html=True)

question = st.text_area(
    label="question", label_visibility="collapsed",
    placeholder=T["placeholder"],
    height=100, key="question_input"
)

col1, col2 = st.columns([3, 1])
with col1:
    search_clicked = st.button(T["btn_search"], use_container_width=True)
with col2:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    with st.expander(T["btn_examples"]):
        for ex in T["examples"]:
            if st.button(ex, key=ex):
                question = ex
                search_clicked = True


if search_clicked:
    q = question.strip()
    if not q:
        st.warning(T["warn_empty"])
    else:
        with st.spinner(T["spinner_search"]):
            results = semantic_search(q, top_k=3)

        if not results:
            st.markdown(f'<div class="empty-state">{T["no_result"]}</div>', unsafe_allow_html=True)
        else:
            with st.spinner(T["spinner_answer"]):
                answer = generate_answer(q, results, st.session_state.lang)

            # ── AI Answer ──
            st.markdown(f'<div class="section-title">{T["ai_section"]}</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="ai-answer-box">
                <div class="ai-answer-header">{T['ai_header']}</div>
                <div class="ai-answer-text">{answer.replace(chr(10), '<br>')}</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Source Fragments ──
            st.markdown(f'<div class="section-title">{T["src_section"]}</div>', unsafe_allow_html=True)

            for i, result in enumerate(results, start=1):
                sc     = result["score"]
                cls    = score_class(sc)
                label  = score_label(sc, T)
                raw    = re.sub(r'\n{2,}', '\n', result["texte_fragment"]).strip()
                text   = raw.replace("\n", "<br>")
                doc_id = result["id_document"]
                pct    = score_pct(sc)

                st.markdown(f"""
                <div class="result-card">
                    <div class="result-card-bar bar-{cls}"></div>
                    <div class="result-card-body">
                        <div class="result-header">
                            <div class="result-rank">
                                <div class="rank-number">{i}</div>
                                <span class="rank-label">{T['fragment']} {i}</span>
                            </div>
                            <span class="score-pill {cls}">{label}</span>
                        </div>
                        <div class="score-bar-wrap">
                            <div class="score-bar-fill fill-{cls}" style="width:{pct}%"></div>
                        </div>
                        <div class="result-text">{text}</div>
                        <div class="result-footer">
                            <span class="doc-tag">📄 {T['document']} #{doc_id}</span>
                            <span class="score-value">{T['score']} : {sc:.4f}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)


st.markdown(f"""
<div class="footer">
    {T['footer_model']} : <strong>all-MiniLM-L6-v2</strong> &nbsp;·&nbsp;
    {T['footer_sim']} : <strong>Cosinus</strong> &nbsp;·&nbsp;
    {T['footer_db']} : <strong>PostgreSQL / pgvector</strong> &nbsp;·&nbsp;
    {T['footer_team']} : <strong>CS_Heroes</strong>
</div>
""", unsafe_allow_html=True)