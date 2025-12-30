import streamlit as st
import json, re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

st.set_page_config(page_title="Quotation Chat Bot", page_icon="💬")
st.title("💬 Interior Quotation Chat Bot")

DATA_FILE = "rates.json"

# ---------- LOAD / SAVE RATES ---------- #

def load_rates():
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"fixed": {}, "sqft": {}, "rft": {}}

rates = load_rates()

# ---------- SESSION ---------- #

if "client_name" not in st.session_state:
    st.session_state.client_name = ""

if "chat" not in st.session_state:
    st.session_state.chat = []
    st.session_state.total = 0

# ---------- CLIENT NAME ---------- #

if not st.session_state.client_name:
    st.subheader("👤 Enter Client Name")
    name = st.text_input("Client Name")
    if st.button("Start Quotation") and name.strip():
        st.session_state.client_name = name.strip()
        st.rerun()
    st.stop()

st.success(f"Client: **{st.session_state.client_name}**")

# ---------- HELPERS ---------- #

def extract_size(text):
    m = re.search(r"(\d+\.?\d*)\s*(by|x)\s*(\d+\.?\d*)", text)
    return (float(m.group(1)), float(m.group(3))) if m else (None, None)

def extract_ft(text):
    m = re.search(r"(\d+\.?\d*)\s*(ft|rft)", text)
    return float(m.group(1)) if m else None

def extract_sqft(text):
    m = re.search(r"(\d+\.?\d*)\s*(sq\.? ?ft|sqft)", text)
    return float(m.group(1)) if m else None

# ---------- PROCESS ITEM ---------- #

def process_item(msg):
    msg = msg.lower()

    for item, rate in rates["fixed"].items():
        if item in msg:
            return f"{item.title()} (Fixed)", rate

    for item, rate in rates["sqft"].items():
        if item in msg:
            w, h = extract_size(msg)
            sqft = w * h if w and h else extract_sqft(msg)
            if sqft:
                return f"{item.title()} ({sqft:.2f} sq.ft × ₹{rate})", sqft * rate

    for item, rate in rates["rft"].items():
        if item in msg:
            ft = extract_ft(msg)
            if ft:
                return f"{item.title()} ({ft} rft × ₹{rate})", ft * rate

    return None, None

# ---------- CHAT ---------- #

user_input = st.text_input("You:", placeholder="e.g. sliding wardrobe 7 by 7")

if st.button("Send") and user_input:
    desc, amt = process_item(user_input)
    if desc:
        st.session_state.chat.append((desc, amt))
        st.session_state.total += amt
    else:
        st.warning("Item not found in rate list")

# ---------- DISPLAY ---------- #

st.subheader("🧾 Quotation Items")
for desc, amt in st.session_state.chat:
    st.write(f"- {desc} → ₹{amt:,.0f}")

st.divider()
st.success(f"💰 Total Amount: ₹ {st.session_state.total:,.0f}")

# ---------- PDF GENERATION ---------- #

def generate_pdf():
    filename = f"Quotation_{st.session_state.client_name}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "INTERIOR QUOTATION")

    y -= 30
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Client Name: {st.session_state.client_name}")
    y -= 20
    c.drawString(50, y, f"Date: {datetime.now().strftime('%d-%m-%Y')}")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Details:")

    y -= 20
    c.setFont("Helvetica", 11)
    for desc, amt in st.session_state.chat:
        if y < 80:
            c.showPage()
            y = height - 50
        c.drawString(60, y, f"- {desc} : ₹{amt:,.0f}")
        y -= 18

    y -= 20
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, f"Total Amount: ₹ {st.session_state.total:,.0f}")

    c.save()
    return filename

if st.button("📄 Generate PDF"):
    pdf_file = generate_pdf()
    with open(pdf_file, "rb") as f:
        st.download_button(
            label="⬇ Download Quotation PDF",
            data=f,
            file_name=pdf_file,
            mime="application/pdf"
        )

# ---------- RESET ---------- #

if st.button("Reset Quotation"):
    st.session_state.chat = []
    st.session_state.total = 0
    st.session_state.client_name = ""
    st.rerun()
