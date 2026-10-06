import streamlit as st
import requests
import os

# -----------------------------
# PAGE CONFIGURATION
# -----------------------------

st.set_page_config(
    page_title="Local Price AI",
    page_icon="🛍️",
    layout="wide"
)

# -----------------------------
# TITLE
# -----------------------------

st.title("🛍️ Local Price AI")
st.subheader("Find the best local prices with AI")

st.write(
    "Compare prices from online and local sources, "
    "analyze deals, and get an AI-powered recommendation."
)

st.divider()

# -----------------------------
# INPUT SECTION
# -----------------------------

st.markdown("### 🔎 What are you looking for?")

product = st.text_input(
    "Product name",
    placeholder="Example: iPhone 15 128GB"
)

location = st.text_input(
    "📍 Your location",
    placeholder="Example: Hyderabad"
)

budget = st.number_input(
    "💰 Maximum budget (₹)",
    min_value=0,
    value=50000,
    step=1000
)

radius = st.selectbox(
    "📍 Search radius",
    ["5 km", "10 km", "25 km", "50 km"]
)

st.markdown("### ⚙️ Your preferences")

col1, col2 = st.columns(2)

with col1:
    condition = st.selectbox(
        "Product condition",
        ["Any", "New", "Used", "Refurbished"]
    )

with col2:
    priority = st.selectbox(
        "What matters most?",
        [
            "Lowest Price",
            "Best Overall Deal",
            "Nearest Store",
            "Best Rating"
        ]
    )

st.divider()

# -----------------------------
# SERPAPI SEARCH FUNCTION
# -----------------------------

def search_serpapi(product, location):

    api_key = st.secrets["SERPAPI_API_KEY"]

    params = {
        "engine": "google_shopping",
        "q": product,
        "location": location,
        "hl": "en",
        "gl": "in",
        "api_key": api_key
    }

    response = requests.get(
        "https://serpapi.com/search.json",
        params=params
    )

    if response.status_code != 200:
        return None

    return response.json()


# -----------------------------
# SEARCH BUTTON
# -----------------------------

if st.button("🚀 Find Best Prices", use_container_width=True):

    if not product:
        st.warning("⚠️ Please enter a product name.")

    elif not location:
        st.warning("⚠️ Please enter your location.")

    else:

        with st.spinner("🔎 Searching the web for the best prices..."):

            try:

                results = search_serpapi(
                    product,
                    location
                )

                if results is None:
                    st.error("❌ SerpApi request failed.")

                else:

                    st.success("✅ Search completed!")

                    # -----------------------------
                    # SHOPPING RESULTS
                    # -----------------------------

                    shopping_results = results.get(
                        "shopping_results",
                        []
                    )

                    st.markdown("## 🛒 Price Results")

                    if not shopping_results:

                        st.warning(
                            "No shopping results were found."
                        )

                    else:

                        for item in shopping_results:

                            title = item.get(
                                "title",
                                "Unknown Product"
                            )

                            price = item.get(
                                "price",
                                "Price unavailable"
                            )

                            source = item.get(
                                "source",
                                "Unknown seller"
                            )

                            link = item.get(
                                "link",
                                "#"
                            )

                            rating = item.get(
                                "rating",
                                "N/A"
                            )

                            reviews = item.get(
                                "reviews",
                                "N/A"
                            )

                            with st.container():

                                st.markdown(
                                    f"### 🛍️ {title}"
                                )

                                st.write(
                                    f"💰 **Price:** {price}"
                                )

                                st.write(
                                    f"🏪 **Seller:** {source}"
                                )

                                st.write(
                                    f"⭐ **Rating:** {rating}"
                                )

                                st.write(
                                    f"💬 **Reviews:** {reviews}"
                                )

                                if link != "#":

                                    st.link_button(
                                        "🔗 View Deal",
                                        link
                                    )

                                st.divider()

            except Exception as e:

                st.error(
                    f"❌ Something went wrong: {e}"
                )