<div align="center">
  <img src="https://cdn.pensieriincodice.it/images/pensieriincodice-locandina.png" alt="Logo Progetto" width="150"/>
  <h1>Pensieri in codice — News to Hugo</h1>
  <p>Pubblica automaticamente le news di PIC nel sito pensieriincodice.it, prelevandole da Readwise.</p>
  <p>
    <img src="https://img.shields.io/github/stars/valeriogalano/pensieriincodice-news-to-hugo?style=for-the-badge" alt="GitHub Stars"/>
    <img src="https://img.shields.io/github/forks/valeriogalano/pensieriincodice-news-to-hugo?style=for-the-badge" alt="GitHub Forks"/>
    <img src="https://img.shields.io/github/last-commit/valeriogalano/pensieriincodice-news-to-hugo?style=for-the-badge" alt="Last Commit"/>
    <a href="https://pensieriincodice.it/sostieni" target="_blank" rel="noopener noreferrer">
      <img src="https://img.shields.io/badge/sostieni-Pensieri_in_codice-fb6400?style=for-the-badge" alt="Sostieni Pensieri in codice"/>
    </a>
  </p>
</div>

---

## Come funziona

Lo script interroga l'API di Readwise per recuperare i documenti taggati con `hugo-news`, ne recupera le highlights tramite l'API classica e genera un articolo in formato markdown che viene pubblicato direttamente nel repository del sito Hugo tramite la GitHub API.

---

## Requisiti

- Python 3.11+
- Un account Readwise con access token
- Un Personal Access Token GitHub con permesso `contents: write` sul repository del sito

---

## Variabili di ambiente

Copia `.env.example` in `.env` e imposta i seguenti valori:

```
READWISE_ACCESS_TOKEN="<token di accesso Readwise>"
GH_TOKEN_WEBSITE="<Personal Access Token GitHub>"
GH_REPO_OWNER="<owner del repository del sito>"
GH_REPO_NAME="<nome del repository del sito>"
READWISE_TAG="<tag da monitorare su Readwise Reader>"
```

| Variabile | Descrizione |
|---|---|
| `READWISE_ACCESS_TOKEN` | Token di accesso Readwise ([ottienilo qui](https://readwise.io/access_token)) |
| `GH_TOKEN_WEBSITE` | PAT GitHub con permesso `contents: write` sul repo del sito |
| `GH_REPO_OWNER` | Owner del repository del sito (es. `valeriogalano`) |
| `GH_REPO_NAME` | Nome del repository del sito (es. `pensieriincodice-website`) |
| `READWISE_TAG` | Tag da monitorare su Readwise Reader (default: `hugo-news`) |

---

## Installazione e avvio

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
python main.py
```

Per eseguire i test:

```bash
pytest tests/ -v
```

---

## Contributi

Se noti qualche problema o hai suggerimenti, sentiti libero di aprire una **Issue** e successivamente una **Pull Request**. Ogni contributo è ben accetto!

---

## Importante

Vorremmo mantenere questo repository aperto e gratuito per tutti, ma lo scraping del contenuto di questo repository **NON È CONSENTITO**. Se ritieni che questo lavoro ti sia utile e vuoi utilizzare qualche risorsa, ti preghiamo di citare come fonte il podcast e/o questo repository.
