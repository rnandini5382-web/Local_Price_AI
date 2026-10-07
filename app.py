import streamlit as st
from serpapi import GoogleSearch


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Local Price Finder AI",
    page_icon="🛍️",
    layout="wide"
)


# =========================================================
# SEARCH ONLINE PRODUCTS
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
# SEARCH LOCAL STORES
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
# CALCULATE DEAL SCORE
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
    "Compare online prices, check your budget, "
    "and discover nearby local stores."
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
# FIND BEST PRICES BUTTON
# =========================================================
# =========================================================
# NEARBY LOCAL STORES BUTTON
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

        links = store.get(
            "links",
            {}
        )

        if isinstance(links, dict):

            directions = links.get(
                "directions"
            )

            if directions:

                st.link_button(
                    "🗺️ Get Directions",
                    directions
                )

        st.divider()

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
# ONLINE RESULTS
# =========================================================

results = st.session_state.online_results


if results:

    st.success(
        f"Found {len(results)} online results! 🎉"
    )


    # =====================================================
    # PRODUCTS WITH NUMERICAL PRICES
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
            key=lambda x: x["extracted_price"]
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
    # SAVINGS ANALYSIS
    # =====================================================

    if len(priced_results) >= 2:

        prices = [

            item["extracted_price"]

            for item in priced_results
        ]


        lowest_price = min(prices)

        highest_price = max(prices)

        savings = (
            highest_price
            - lowest_price
        )


        st.divider()

        st.subheader(
            "💰 Savings Analysis"
        )


        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(
                "💵 Lowest Price",
                f"₹{lowest_price:,.0f}"
            )


        with col2:

            st.metric(
                "💸 Highest Price",
                f"₹{highest_price:,.0f}"
            )


        with col3:

            st.metric(
                "🎯 Potential Savings",
                f"₹{savings:,.0f}"
            )


        if savings > 0:

            st.success(
                f"🤖 You could potentially save "
                f"₹{savings:,.0f} by choosing "
                f"the lowest-priced option."
            )


    # =====================================================
    # ONLINE PRICE COMPARISON
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
    # BUDGET ANALYSIS
    # =====================================================

    st.subheader(
        "🎯 Budget Analysis"
    )


    if priced_results:

        within_budget = [

            item

            for item in priced_results

            if item["extracted_price"] <= budget
        ]


        if within_budget:

            budget_best = min(
                within_budget,
                key=lambda x: x["extracted_price"]
            )


            budget_price = (
                budget_best["extracted_price"]
            )


            remaining = (
                budget - budget_price
            )


            st.success(
                "🟢 Best option within your budget!"
            )


            st.write(
                f"🛍️ **Product:** "
                f"{budget_best.get(
                    'title',
                    'Unknown Product'
                )}"
            )


            st.write(
                f"💰 **Price:** "
                f"₹{budget_price:,.2f}"
            )


            st.write(
                f"💵 **Budget remaining:** "
                f"₹{remaining:,.2f}"
            )


        else:

            cheapest = min(
                priced_results,
                key=lambda x: x["extracted_price"]
            )


            cheapest_price