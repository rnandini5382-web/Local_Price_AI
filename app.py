import streamlit as st
import os
import streamlit as st
from serpapi import GoogleSearch

def search_products(product, location):
    params = {
        "engine": "google_shopping",
        "q": product,
        "location": location,
        "api_key": SERPAPI_API_KEY,
        "hl": "en",
        "gl": "in"
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    return results.get("shopping_results", [])
st.title("🛍️ Local Price Finder AI")

product = st.text_input(
    "What product are you looking for?",
    placeholder="Example: iPhone 15 128GB"
)

location = st.text_input(
    "Enter your location",
    placeholder="Example: Hyderabad, Telangana"
)

if st.button("🔎 Find Best Prices"):
    if product and location:
        with st.spinner("Searching for the best prices..."):
            results = search_products(product, location)

        if results:
            st.success(f"Found {len(results)} results!")

            for item in results:
                st.write("###", item.get("title", "Unknown Product"))
                st.write("💰 Price:", item.get("price", "Not available"))
                st.write("🏪 Store:", item.get("source", "Unknown"))
                st.write("---")

        else:
            st.warning("No shopping results found.")
    else:
        st.error("Please enter both product and location.")

SERPAPI_API_KEY = st.secrets["SERPAPI_API_KEY"]

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Local Price AI",
    page_icon="🛍️",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>

.main {
    padding-top: 2rem;
}

.hero {
    text-align: center;
    padding: 25px;
}

.hero h1 {
    font-size: 42px;
    margin-bottom: 5px;
}

.hero p {
    font-size: 18px;
}

.card {
    padding: 25px;
    border-radius: 15px;
    border: 1px solid rgba(128,128,128,0.25);
    margin-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown("""
<div class="hero">

<h1>🛍️ Local Price AI</h1>

<p>
Find the best local and online prices for any product using AI + real-time search.
</p>

</div>
""", unsafe_allow_html=True)

st.divider()

# --------------------------------------------------
# PRODUCT SEARCH SECTION
# --------------------------------------------------

st.subheader("🔎 What are you looking for?")

product = st.text_input(
    "Product",
    placeholder="Example: iPhone 16, Nike shoes, laptop, headphones..."
)

# --------------------------------------------------
# LOCATION
# --------------------------------------------------

st.subheader("📍 Where are you located?")

location = st.text_input(
    "Location",
    placeholder="Example: Hyderabad, Telangana"
)

# --------------------------------------------------
# BUDGET
# --------------------------------------------------

st.subheader("💰 Your Budget")

budget = st.number_input(
    "Maximum budget (₹)",
    min_value=0,
    value=50000,
    step=1000
)

# --------------------------------------------------
# PREFERENCES
# --------------------------------------------------

st.subheader("⚙️ Preferences")

col1, col2 = st.columns(2)

with col1:

    condition = st.selectbox(
        "Product condition",
        [
            "Any",
            "New",
            "Used",
            "Refurbished"
        ]
    )

with col2:

    priority = st.selectbox(
        "What matters most?",
        [
            "Lowest Price",
            "Best Value",
            "Nearest Store",
            "Highest Rating"
        ]
    )

# --------------------------------------------------
# SEARCH BUTTON
# --------------------------------------------------

st.divider()

search = st.button(
    "🔍 Find Best Prices",
    use_container_width=True
)

# --------------------------------------------------
# DEMO RESPONSE
# --------------------------------------------------

if search:

    if not product:
        st.warning("⚠️ Please enter a product name.")

    elif not location:
        st.warning("⚠️ Please enter your location.")

    else:

        st.success("✅ Search request received!")

        st.info(
            f"""
            **Product:** {product}

            **Location:** {location}

            **Budget:** ₹{budget:,}

            **Condition:** {condition}

            **Priority:** {priority}
            """
        )

        st.markdown("### 🤖 AI Agent Status")

        st.write(
            "Your search is ready. In the next step, "
            "we will connect SERPAPI to find real products, "
            "prices, stores and offers."
        )
st.success("SerpApi key loaded successfully! 🔐")