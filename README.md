# 🧾 AI Receipt Scanner

> Upload any receipt photo → get structured line items, totals, and a CSV export in seconds — powered by Claude's vision API.

![Demo](https://img.shields.io/badge/demo-live-brightgreen) ![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-ff4b4b)

---

## What it does

- 📸 Accepts JPG / PNG / WebP receipt photos
- 🤖 Uses **Claude claude-opus-4-6 vision** to extract merchant, date, every line item, tax, tip, and total
- 📊 Displays a clean itemized breakdown
- ⬇️ Exports to **CSV** and **JSON** with one click
- 🎮 Ships with a built-in demo so reviewers can try it instantly (no API key needed)

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/receipt-scanner.git
cd receipt-scanner

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

Add your Anthropic API key in the sidebar when prompted.  
Get one free at [console.anthropic.com](https://console.anthropic.com).

---

## Project structure

```
receipt-scanner/
├── app.py            # Main Streamlit app
├── requirements.txt  # Dependencies
└── README.md
```

---

## How it works

```
User uploads image
       │
       ▼
Base64 encode → Claude claude-opus-4-6 vision API
       │
       ▼
Structured JSON response (merchant, items, totals)
       │
       ▼
Streamlit renders table + download buttons
```

The system prompt instructs Claude to return **only valid JSON** matching a fixed schema, making the output trivially parseable and reliable.

---

## Deploy free on Hugging Face Spaces

1. Create a new Space → SDK: **Streamlit**
2. Upload `app.py` and `requirements.txt`
3. Add `ANTHROPIC_API_KEY` as a Space secret (Settings → Variables)
4. Update `app.py` to read it: `api_key = os.environ.get("ANTHROPIC_API_KEY", "")`

---

## Tech stack

| Layer | Tool |
|---|---|
| UI | Streamlit |
| Vision AI | Anthropic Claude claude-opus-4-6 |
| Image handling | Pillow |
| Export | Python csv / json stdlib |

---

## License

MIT
