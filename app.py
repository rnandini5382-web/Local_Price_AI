import streamlit as st
import requests
from urllib.parse import quote


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Local Price Finder AI",
    page_icon="🛍️",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("🛍️ Local Price Finder AI")
st.markdown(
    """
    ### 🔎 Find the best product deals near you
    Compare online prices, discover nearby stores, analyze your
    budget, and get a smart deal recommendation using SERPAPI.
    """
)


# ============================================================
# SERPAPI KEY
# ============================================================

try:
    SERPAPI_API_KEY = st.secrets["SERPAPI_API_KEY"]
except Exception:
    SERPAPI_API_KEY = ""

    st.error(
        "❌ SERPAPI_API_KEY is missing. "
        "Please add it to Streamlit Secrets."
    )


# ============================================================
# SEARCH PRODUCTS USING GOOGLE SHOPPING
# ============================================================

def search_products(product, location):

    if not SERPAPI_API_KEY:
        return []

    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_shopping",
        "q": product,
        "location": location,
        "hl": "en",
        "gl": "in",
        "api_key": SERPAPI_API_KEY
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "shopping_results",
            []
        )

    except Exception as e:

       