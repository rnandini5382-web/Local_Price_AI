import streamlit as st
from serpapi import GoogleSearch


# --------------------------------
# Search Online Products
# --------------------------------
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


# --------------------------------
# Search Nearby Local Stores
# --------------------------------
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

    return results.get("local_results", [])


# --------------------------------
# App
# --------------------------------
st.title("🛍️ Local Price Finder AI")

st.write(
    "Compare online prices and discover nearby local stores."
)


# --------------------------------
# Inputs
# --------------------------------
product = st.text_input(
    "What product are you looking for?",
    placeholder="Example: iPhone 15 128GB"
)

location = st.text_input(
    "Enter your location",
    placeholder="Example: Hyderabad"
)


# =================================
# ONLINE PRICE SEARCH
# =================================
if st.button("📍 Find Nearby Stores"):

    if product and location:

        with st.spinner(
            "📍 Searching nearby stores..."
        ):

            stores = search_local_stores(
                product,
                location
            )

        if stores:

            st.success(
                f"Found {len(stores)} nearby stores! 🎉"
            )

            for store in stores:

                st.markdown(
                    f"### 🏪 {store.get('title', 'Unknown Store')}"
                )

                st.write(
                    f"⭐ **Rating:** "
                    f"{store.get('rating', 'N/A')}"
                )

                st.write(
                    f"💬 **Reviews:** "
                    f"{store.get('reviews', 'N/A')}"
                )

                st.write(
                    f"📍 **Address:** "
                    f"{store.get('address', 'N/A')}"
                )

                st.write(
                    f"🏷️ **Type:** "
                    f"{store.get('type', 'N/A')}"
                )

                st.divider()

        else:

            st.warning(
                "No nearby stores were found."
            )

    else:

        st.error(
            "Please enter both product and location."
        )

            # -------------------------
            # Best Deal
            # -------------------------
            if priced_results:

                best_deal = min(
                    priced_results,
                    key=lambda x: x["extracted_price"]
                )

                st.subheader(
                    "🏆 Best Online Price"
                )

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

            # -------------------------
            # All Online Results
            # -------------------------
            st.divider()

            st.subheader(
                "📊 Online Price Comparison"
            )

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
                "No online shopping results found."
            )

    else:

        st.error(
            "Please enter both product and location."
        )


# =================================
# LOCAL STORE SEARCH
# =================================

st.divider()

st.subheader(
    "📍 Nearby Local Stores"
)


if st.button("📍 Find Nearby Stores"):

    if product and location:

        with st.spinner(
            "📍 Finding nearby stores..."
        ):

            stores = search_local_stores(
                product,
                location
            )

        if stores:

            st.success(
                f"Found {len(stores)} local stores! 🎉"
            )

            for store in stores:

                store_name = store.get(
                    "title",
                    "Unknown Store"
                )

                rating = store.get(
                    "rating",
                    "Not available"
                )

                reviews = store.get(
                    "reviews",
                    "Not available"
                )

                address = store.get(
                    "address",
                    "Address unavailable"
                )

                st.markdown(
                    f"### 🏪 {store_name}"
                )

                st.write(
                    f"⭐ **Rating:** {rating}"
                )

                st