import streamlit as st
import anthropic
import base64  
import json
import csv
import io
from PIL import Image
  
st.set_page_config(   
    page_title="AI Receipt Scanner",
    page_icon="🧾",  
    layout="centered"    
)

st.markdown("""    
<style>
    .main { max-width: 720px; margin: 0 auto; }
    .receipt-header { font-size: 2rem; font-weight: 700; margin-bottom: 0; }
    .receipt-sub { color: #888; margin-top: 0; font-size: 0.95rem; }
    .item-row { display: flex; justify-content: space-between; padding: 6px 0;
                border-bottom: 1px solid #f0f0f0; font-size: 0.95rem; }
    .total-row { display: flex; justify-content: space-between; padding: 10px 0;
                 font-weight: 700; font-size: 1.05rem; border-top: 2px solid #222; }
    .tag-pill { display: inline-block; background: #f0f4ff; color: #3b5bdb;
                border-radius: 20px; padding: 2px 12px; font-size: 0.8rem;
                font-weight: 500; margin: 2px; }
    .error-box { background: #fff3f3; border: 1px solid #ffcdd2;
                 border-radius: 8px; padding: 1rem; color: #c62828; }
    .info-box { background: #f0f7ff; border: 1px solid #bbdefb;
                border-radius: 8px; padding: 0.75rem 1rem; color: #1565c0;
                font-size: 0.88rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown('<p class="receipt-header">🧾 AI Receipt Scanner</p>', unsafe_allow_html=True)
st.markdown('<p class="receipt-sub">Upload a receipt photo and extract every line item instantly.</p>', unsafe_allow_html=True)
st.divider()


# ── API key ──────────────────────────────────────────────────────────────────
api_key = st.sidebar.text_input(
    "Anthropic API Key",
    type="password",
    help="Get yours at console.anthropic.com"
)
if not api_key:
    st.markdown("""
    <div class="info-box">
    ℹ️ Add your Anthropic API key in the sidebar to get started.
    Don't have one? <a href="https://console.anthropic.com" target="_blank">console.anthropic.com</a>
    </div>
    """, unsafe_allow_html=True)


def encode_image(uploaded_file) -> tuple[str, str]:
    """Return (base64_data, media_type) from an uploaded file."""
    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    return base64.standard_b64encode(uploaded_file.read()).decode(), mime


def parse_receipt(image_b64: str, media_type: str, api_key: str) -> dict:
    """Send image to Claude and return structured receipt data."""
    client = anthropic.Anthropic(api_key=api_key)

    system = """You are a receipt parsing assistant. 
Extract all information from the receipt image and return ONLY valid JSON — no markdown, no explanation.

JSON schema:
{
  "merchant": "string",
  "date": "YYYY-MM-DD or null",
  "category": "one of: Restaurant, Grocery, Retail, Travel, Fuel, Other",
  "items": [
    {"name": "string", "qty": number, "unit_price": number, "total": number}
  ],
  "subtotal": number,
  "tax": number,
  "tip": number,
  "total": number,
  "currency": "USD",
  "payment_method": "string or null",
  "notes": "any unusual observations or null"
}

Rules:
- All prices as floats with 2 decimal places.
- If a field is not present on the receipt, use null.
- qty defaults to 1 if not shown.
- unit_price = total / qty if not shown separately.
"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=system,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_b64
                    }
                },
                {"type": "text", "text": "Parse this receipt and return JSON only."}
            ]
        }]
    )

    raw = message.content[0].text.strip()
    # Strip markdown code fences if Claude adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def to_csv(data: dict) -> str:
    """Convert parsed receipt dict to a CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Merchant", "Date", "Category", "Currency", "Payment Method"])
    writer.writerow([
        data.get("merchant", ""),
        data.get("date", ""),
        data.get("category", ""),
        data.get("currency", "USD"),
        data.get("payment_method", "")
    ])
    writer.writerow([])
    writer.writerow(["Item", "Qty", "Unit Price", "Total"])
    for item in data.get("items", []):
        writer.writerow([
            item.get("name", ""),
            item.get("qty", 1),
            f"{item.get('unit_price', 0):.2f}",
            f"{item.get('total', 0):.2f}"
        ])
    writer.writerow([])
    writer.writerow(["Subtotal", f"{data.get('subtotal') or 0:.2f}"])
    writer.writerow(["Tax", f"{data.get('tax') or 0:.2f}"])
    writer.writerow(["Tip", f"{data.get('tip') or 0:.2f}"])
    writer.writerow(["Total", f"{data.get('total') or 0:.2f}"])
    return output.getvalue()


# ── Upload ───────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Drop a receipt image here",
    type=["jpg", "jpeg", "png", "webp"],
    label_visibility="collapsed"
)

use_demo = st.checkbox("Use demo receipt (no image needed)", value=not bool(uploaded))

# Demo data so viewers can test without a real receipt
DEMO_DATA = {
    "merchant": "The Daily Grind Coffee Co.",
    "date": "2024-06-15",
    "category": "Restaurant",
    "currency": "USD",
    "payment_method": "Visa •••• 4242",
    "items": [
        {"name": "Oat Milk Latte (L)", "qty": 2, "unit_price": 6.50, "total": 13.00},
        {"name": "Avocado Toast", "qty": 1, "unit_price": 12.00, "total": 12.00},
        {"name": "Blueberry Muffin", "qty": 1, "unit_price": 4.25, "total": 4.25},
        {"name": "Sparkling Water", "qty": 1, "unit_price": 3.00, "total": 3.00},
    ],
    "subtotal": 32.25,
    "tax": 2.90,
    "tip": 5.00,
    "total": 40.15,
    "notes": None
}

# ── Scan button ───────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
scan_clicked = col1.button("✨ Scan Receipt", type="primary", use_container_width=True, disabled=not api_key and not use_demo)

if scan_clicked or (use_demo and "demo_loaded" not in st.session_state):
    if use_demo:
        st.session_state.result = DEMO_DATA
        st.session_state.demo_loaded = True
    elif uploaded and api_key:
        with st.spinner("Reading your receipt…"):
            try:
                uploaded.seek(0)
                b64, mime = encode_image(uploaded)
                st.session_state.result = parse_receipt(b64, mime, api_key)
                st.session_state.demo_loaded = False
            except json.JSONDecodeError:
                st.error("Claude returned unexpected output. Try a clearer photo.")
                st.session_state.result = None
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.result = None
    else:
        st.warning("Upload an image and add your API key, or enable demo mode.")

# ── Display results ───────────────────────────────────────────────────────────
if "result" in st.session_state and st.session_state.result:
    d = st.session_state.result

    if uploaded and not use_demo:
        with st.expander("View uploaded image"):
            st.image(Image.open(uploaded), use_column_width=True)

    st.divider()

    # Meta row
    c1, c2, c3 = st.columns(3)
    c1.metric("Merchant", d.get("merchant") or "Unknown")
    c2.metric("Date", d.get("date") or "—")
    c3.metric("Category", d.get("category") or "—")

    # Payment pill
    if d.get("payment_method"):
        st.markdown(f'<span class="tag-pill">💳 {d["payment_method"]}</span>', unsafe_allow_html=True)

    st.subheader("Line Items")

    # Items table
    items = d.get("items", [])
    if items:
        header = st.columns([5, 1, 2, 2])
        header[0].markdown("**Item**")
        header[1].markdown("**Qty**")
        header[2].markdown("**Unit**")
        header[3].markdown("**Total**")
        st.markdown('<hr style="margin:4px 0 8px;">', unsafe_allow_html=True)
        for item in items:
            row = st.columns([5, 1, 2, 2])
            row[0].write(item.get("name", "—"))
            row[1].write(str(item.get("qty", 1)))
            row[2].write(f"${item.get('unit_price', 0):.2f}")
            row[3].write(f"${item.get('total', 0):.2f}")
    else:
        st.info("No line items found.")

    st.divider()

    # Totals
    t1, t2 = st.columns(2)
    with t1:
        st.write(f"Subtotal: **${d.get('subtotal') or 0:.2f}**")
        st.write(f"Tax: **${d.get('tax') or 0:.2f}**")
        if d.get("tip"):
            st.write(f"Tip: **${d['tip']:.2f}**")
    with t2:
        st.metric("Total", f"${d.get('total') or 0:.2f}", delta=None)

    if d.get("notes"):
        st.info(f"📝 Note: {d['notes']}")

    # Downloads
    st.divider()
    dl1, dl2 = st.columns(2)
    dl1.download_button(
        "⬇️ Download CSV",
        data=to_csv(d),
        file_name=f"receipt_{d.get('date', 'unknown')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    dl2.download_button(
        "⬇️ Download JSON",
        data=json.dumps(d, indent=2),
        file_name=f"receipt_{d.get('date', 'unknown')}.json",
        mime="application/json",
        use_container_width=True
    )
