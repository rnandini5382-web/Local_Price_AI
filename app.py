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
# SERPAPI - ONLINE PRODUCT SEARCH
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
# SERPAPI - LOCAL STORE SEARCH
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
# APP TITLE
# =========================================================

st.title(
    "🛍️ Local Price Finder AI"
)

st.write(
    "Compare online prices and discover "
    "nearby local stores."
)


# =========================================================
# USER INPUTS
# =========================================================

product = st.text_input(
    "What product are you looking for?",
    placeholder="Example: iPhone 15 128GB"
)

location = st.text_input(
    "Enter your location",
    placeholder="Example: Hyderabad"
)


# =========================================================
# INITIALIZE SESSION STATE
# =========================================================

if "online_results" not in st.session_state:

    st.session_state.online_results = []


if "local_stores" not in st.session_state:

    st.session_state.local_stores = []


# =========================================================
# ONLINE PRICE SEARCH BUTTON
# =========================================================

if st.button(
    "🔎 Find Best Prices"
):

    if product and location:

        with st.spinner(
            "🔎 Searching for the best prices..."
        ):

            st.session_state.online_results = (
                search_products(
                    product,
                    location
                )
            )

    else:

        st.error(
            "Please enter both product "
            "and location."
        )


# =========================================================
# DISPLAY ONLINE RESULTS
# =========================================================

results = st.session_state.online_results


if results:

    st.success(
        f"Found {len(results)} online results! 🎉"
    )


    # =====================================================
    # FIND PRODUCTS WITH NUMERICAL PRICES
    # =====================================================

    priced_results = [

        item

        for item in results

        if isinstance(
            item.get("extracted_price"),
            (int, float)
        )
    ]


    # =====================================================
    # BEST ONLINE PRICE
    # =====================================================

    if priced_results:

        best_deal = min(
            priced_results,
            key=lambda x: x[
                "extracted_price"
            ]
        )


        st.subheader(
            "🏆 Best Online Price"
        )


        st.success(
            f"💰 {best_deal.get(
                'price',
                'Price unavailable'
            )}"
        )


        st.write(
            f"🛍️ **Product:** "
            f"{best_deal.get(
                'title',
                'Unknown Product'
            )}"
        )


        st.write(
            f"🏪 **Store:** "
            f"{best_deal.get(
                'source',
                'Unknown Store'
            )}"
        )


        best_link = (
            best_deal.get("link")
            or
            best_deal.get("product_link")
        )


        if best_link:

            st.link_button(
                "🛒 View Best Deal",
                best_link
            )


    # =====================================================
    # PRICE COMPARISON
    # =====================================================

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
            or
            item.get("product_link")
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


    # =====================================================
    # SMART DEAL RECOMMENDATION
    # =====================================================

    st.subheader(
        "🤖 Smart Deal Recommendation"
    )


    if priced_results:

        best_item = min(
            priced_results,
            key=lambda x: x[
                "extracted_price"
            ]
        )


        best_price = best_item.get(
            "extracted_price"
        )


        best_product = best_item.get(
            "title",
            "Unknown Product"
        )


        best_store = best_item.get(
            "source",
            "Unknown Store"
        )


        rating = best_item.get(
            "rating"
        )


        reviews = best_item.get(
            "reviews"
        )


        try:

            rating = float(
                rating
            )

        except:

            rating = None


        try:

            reviews = int(
                reviews
            )

        except:

            reviews = None


        deal_score = calculate_deal_score(
            best_price,
            rating,
            reviews
        )


        st.success(
            "🏆 Best Deal Found!"
        )


        st.write(
            f"🛍️ **Product:** "
            f"{best_product}"
        )


        st.write(
            f"💰 **Price:** "
            f"₹{best_price:,.2f}"
        )


        st.write(
            f"🏪 **Store:** "
            f"{best_store}"
        )


        st.metric(
            "🏆 Deal Score",
            f"{deal_score}/100"
        )


        if rating is not None:

            st.write(
                f"⭐ **Rating:** "
                f"{rating}/5"
            )


        if reviews is not None:

            st.write(
                f"💬 **Reviews:** "
                f"{reviews:,}"
            )


        if deal_score >= 80:

            st.success(
                "🔥 Excellent deal!"
            )

        elif deal_score >= 60:

            st.info(
                "👍 Good deal."
            )

        else:

            st.warning(
                "⚠️ Consider comparing "
                "more options."
            )


        st.info(
            "🤖 Recommendation: This listing "
            "currently offers the best combination "
            "of available price information."
        )


    else:

        st.warning(
            "No numerical prices were available "
            "to calculate a recommendation."
        )


# =========================================================
# NEARBY LOCAL STORES
# =========================================================

st.divider()

st.subheader(
    "📍 Nearby Local Stores"
)


if st.button(
    "📍 Find Nearby Stores"
):

    if product and location:

        with st.spinner(
            "📍 Finding nearby stores..."
        ):

            st.session_state.local_stores = (
                search_local_stores(
                    product,
                    location
                )
            )

    else:

        st.error(
            "Please enter both product "
            "and location first."
        )


# =========================================================
# DISPLAY LOCAL STORES
# =========================================================

stores = st.session_state.local_stores


if stores:

    st.success(
        f"Found {len(stores)} nearby stores! 🎉"
    )


    for store in stores:

        store_name = store.get(
            "title",
            "Unknown Store"
        )


        rating = store.get(
            "rating",
            "N/A"
        )


        reviews = store.get(
            "reviews",
            "N/A"
        )


        address = store.get(
            "address",
            "Address unavailable"
        )


        store_type = store.get(
            "type",
            "N/A"
        )


        st.markdown(
            f"### 🏪 {store_name}"
        )


        st.write(
            f"⭐ **Rating:** {rating}"
        )


        st.write(
            f"💬 **Reviews:** {reviews}"
        )


        st.write(
            f"📍 **Address:** {address}"
        )


        st.write(
            f"🏷️ **Type:** {store_type}"
        )


        # Store links
        links = store.get(
            "links",
            {}
        )


        if isinstance(
            links,
            dict
        ):

            directions = links.get(
                "directions"
            )


            if directions:

                st.link_button(
                    "🗺️ Get Directions",
                    directions
                )


        st.divider()


elif product and location:

    st.info(
        "Click 📍 Find Nearby Stores "
        "to search local businesses."
    )