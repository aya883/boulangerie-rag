🥐 Recherche Sémantique : Boulangerie & Pâtisserie

Système RAG (Retrieval-Augmented Generation) pour l'assistance intelligente à la formulation en boulangerie et pâtisserie industrielle.



🎥 Démo en ligne
👉 https://drive.google.com/drive/folders/1-HB1ii0oywwCDCzrvJDv2ggTY5yaqv9x?usp=sharing

📌 Contexte
Dans un contexte où une base documentaire contient un grand volume d'informations (fiches techniques, procédures, recommandations), les utilisateurs rencontrent des difficultés à identifier rapidement les passages pertinents.
Ce module intelligent retrouve automatiquement les fragments les plus pertinents à partir d'une question en langage naturel.

✅ Fonctionnalités

🔍 Recherche sémantique via embeddings all-MiniLM-L6-v2 (384 dimensions)
📐 Similarité cosinus avec pgvector sur PostgreSQL
🏆 Top 3 fragments classés par pertinence décroissante
🤖 Réponse générée par LLaMA 3.3 (Groq) basée sur les fragments retrouvés
🌍 Interface bilingue Français / العربية (avec RTL)
📄 Ingestion automatique de fiches techniques PDF
🎨 UI professionnelle thème boulangerie


🏗️ Architecture
Question utilisateur
        ↓
Embedding (all-MiniLM-L6-v2)
        ↓
Similarité cosinus (pgvector)
        ↓
Top 3 fragments pertinents
        ↓
Génération réponse (Groq / LLaMA 3.3)
        ↓
Affichage FR / AR

🗂️ Structure du projet
boulangerie-rag/
├── App.py              # Interface Streamlit (UI + logique)
├── Search.py           # Module de recherche sémantique
├── Config.py           # Configuration DB + modèle
├── insert_pdf.py       # Ingestion des PDFs → embeddings → PostgreSQL
├── Requirements.txt    # Dépendances Python
├── .env                # Variables d'environnement (non pushé)
├── .gitignore
└── README.md

⚙️ Installation
1. Cloner le repo
bashgit clone https://github.com/YOUR_USERNAME/boulangerie-rag.git
cd boulangerie-rag
2. Installer les dépendances
bashpip install -r Requirements.txt
3. Configurer les variables d'environnement
Créer un fichier .env :
envGROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
4. Configurer la base de données
Dans Config.py, renseigner vos credentials PostgreSQL (Neon) :
pythonDB_CONFIG = {
    "host":     "your-neon-host.neon.tech",
    "port":     5432,
    "dbname":   "neondb",
    "user":     "your_user",
    "password": "your_password",
    "sslmode":  "require",
}
5. Insérer les données
Placer vos PDFs dans le dossier du projet et lancer :
bashpython insert_pdf.py
6. Lancer l'application
bashstreamlit run App.py

🛠️ Stack Technique
ComposantTechnologieInterfaceStreamlitEmbeddingall-MiniLM-L6-v2 (sentence-transformers)Base vectoriellePostgreSQL + pgvector (Neon)SimilaritéCosinus (<=>)LLMLLaMA 3.3 70B via GroqExtraction PDFpdfplumberLanguesFrançais / العربية

👥 Équipe
CS_Heroes — AI Night Hackathon
