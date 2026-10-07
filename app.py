import streamlit as st
import os
import streamlit as st
from serpapi import GoogleSearch

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

    # Get products that have a usable numeric price
    priced_results = [
        item for item in results
        if isinstance(item.get("extracted_price"), (int, float))
    ]

    if priced_results:
        # Find the cheapest product
        best_deal = min(
            priced_results,
            key=lambda x: x["extracted_price"]
        )

        st.subheader("🏆 Best Price Found")

        st.success(
            f"💰 {best_deal.get('price', 'Price unavailable')} "
            f"at 🏪 {best_deal.get('source', 'Unknown Store')}"
        )

        st.write(
            f"**Product:** {best_deal.get('title', 'Unknown Product')}"
        )

        best_link = best_deal.get("link") or best_deal.get("product_link")

        if best_link:
            st.link_button("🛒 View Best Deal", best_link)

    st.divider()

    st.subheader("📊 All Price Comparisons")

    for item in priced_results:
        title = item.get("title", "Unknown Product")
        price = item.get("price", "Not available")
        source = item.get("source", "Unknown Store")
        link = item.get("link") or item.get("product_link")

        st.markdown(f"### 🛍️ {title}")
        st.write(f"💰 **Price:** {price}")
        st.write(f"🏪 **Store:** {source}")

        if link:
            st.link_button("🛒 View Product", link)

        st.divider()

else:
    st.warning("No shopping results found.")