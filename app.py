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
            st.success(f"Found {len(results)} results! 🎉")

            st.subheader("💰 Price Comparison")

            for item in results:
                title = item.get("title", "Unknown Product")
                price = item.get("price", "Not available")
                source = item.get("source", "Unknown Store")
                link = item.get("link", "")

                st.markdown(f"### 🛍️ {title}")
                st.write(f"💰 **Price:** {price}")
                st.write(f"🏪 **Store:** {source}")

                if link:
                    st.link_button("🛒 View Product", link)

                st.divider()

        else:
            st.warning("No shopping results found.")

    else:
        st.error("Please enter both product and location.")