import streamlit as st
from serpapi import GoogleSearch


# -----------------------------
# SerpApi Product Search
# -----------------------------
def search_products(product, location):
def search_local_stores(product, location):

    params = {
        "engine": "google_maps",
        "q": f"{product} stores",
        "location": location,
        "type": "search",
        "api_key": st.secrets["SERPAPI_API_KEY"],
        "hl": "en",
        "gl": "in"
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    return results.get("local_results", [])

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


# -----------------------------
# App Title
# -----------------------------
st.title("🛍️ Local Price Finder AI")

st.write(
    "Find and compare product prices from online shopping results."
)


# -----------------------------
# User Inputs
# -----------------------------
product = st.text_input(
    "What product are you looking for?",
    placeholder="Example: iPhone 15 128GB"
)

location = st.text_input(
    "Enter your location",
    placeholder="Example: Hyderabad"
)


# -----------------------------
# Search Button
# -----------------------------
if st.button("🔎 Find Best Prices"):

    if product and location:

        with st.spinner("🔎 Searching for prices..."):

            results = search_products(
                product,
                location
            )


        # -----------------------------
        # Results
        # -----------------------------
        if results:

            st.success(
                f"Found {len(results)} results! 🎉"
            )

            # Find results that have numerical prices
            priced_results = [
                item
                for item in results
                if isinstance(
                    item.get("extracted_price"),
                    (int, float)
                )
            ]


            # -----------------------------
            # Best Deal
            # -----------------------------
            if priced_results:

                best_deal = min(
                    priced_results,
                    key=lambda x: x["extracted_price"]
                )

                st.subheader("🏆 Best Price Found")

                st.success(
                    f"💰 {best_deal.get('price', 'Price unavailable')}"
                )

                st.write(
                    f"🛍️ **Product:** "
                    f"{best_deal.get('title', 'Unknown Product')}"
                )

                st.write(
                    f"🏪 **Store:** "
                    f"{best_deal.get('source', 'Unknown Store')}"
                )

                best_link = (
                    best_deal.get("link")
                    or best_deal.get("product_link")
                )

                if best_link:
                    st.link_button(
                        "🛒 View Best Deal",
                        best_link
                    )


            # -----------------------------
            # All Results
            # -----------------------------
            st.divider()

            st.subheader("📊 Price Comparison")

            for item in results:

                title = item.get(
                    "title",
                    "Unknown Product"
                )

                price = item.get(
                    "price",
                    "Not available"
                )

                source = item.get(
                    "source",
                    "Unknown Store"
                )

                link = (
                    item.get("link")
                    or item.get("product_link")
                )

                st.markdown(
                    f"### 🛍️ {title}"
                )

                st.write(
                    f"💰 **Price:** {price}"
                )

                st.write(
                    f"🏪 **Store:** {source}"
                )

                if link:
                    st.link_button(
                        "🛒 View Product",
                        link
                    )

                st.divider()


        else:

            st.warning(
                "No shopping results found."
            )


    else:

        st.error(
            "Please enter both product and location."
        )