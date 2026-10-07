import streamlit as st
from serpapi import GoogleSearch


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Local Price Finder AI",
    page_icon="🛍️",
    layout="wide"
)


# =========================================================
# ONLINE PRODUCT SEARCH
# =========================================================

def search_products(product, location):

    params = {
        "engine": "google_shopping",
        "q": product,
        "location": location,
        "api_key": st.secrets["SERPAPI_API_KEY"],
        "hl": "en",
        "gl": "in"
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "error" in results:
        st.error(
            f"SerpApi error: {results['error']}"
        )
        return []

    return results.get(
        "shopping_results",
        []
    )


# =========================================================
# LOCAL STORE SEARCH
# =========================================================

def search_local_stores(product, location):

    params = {
        "engine": "google_maps",
        "q": f"{product} stores near {location}",
        "type": "search",
        "api_key": st.secrets["SERPAPI_API_KEY"],
        "hl": "en",
        "gl": "in"
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "error" in results:
        st.error(
            f"SerpApi error: {results['error']}"
        )
        return []

    return results.get(
        "local_results",
        []
    )


# =========================================================
# DEAL SCORE
# =========================================================

def calculate_deal_score(
    price,
    rating,
    reviews
):

    score = 0

    if price is not None:
        score += 50

    if rating is not None:
        score += (
            float(rating) / 5
        ) * 30

    if reviews is not None:

        if reviews >= 1000:
            score += 20

        elif reviews >= 500:
            score += 15

        elif reviews >= 100:
            score += 10

        else:
            score += 5

    return round(
        min(score, 100),
        2
    )


# =========================================================
# TITLE
# =========================================================

st.title(
    "🛍️ Local Price Finder AI"
)

st.write(
    "Compare online prices, analyze your budget, "
    "and discover nearby local stores."
)


# =========================================================
# INPUTS
# =========================================================

product = st.text_input(
    "What product are you looking for?",
    placeholder="Example: Laptop"
)

location = st.text_input(
    "Enter your location",
    placeholder="Example: Hyderabad"
)

budget = st.number_input(
    "💰 Your Maximum Budget (₹)",
    min_value=0,
    value=50000,
    step=1000
)


# =========================================================
# SESSION STATE
# =========================================================

if "online_results" not in st.session_state:
    st.session_state.online_results = []

if "local_stores" not in st.session_state:
    st.session_state.local_stores = []


# =========================================================
# FIND BEST PRICES