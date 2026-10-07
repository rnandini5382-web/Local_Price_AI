import streamlit as st
import requests
from urllib.parse import quote
from textblob import TextBlob
import re


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

        st.error(
            f"❌ Product search failed: {e}"
        )

        return []


# ============================================================
# SEARCH NEARBY LOCAL STORES
# ============================================================

def search_local_stores(product, location):

    if not SERPAPI_API_KEY:
        return []

    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_maps",
        "type": "search",
        "q": product + " stores",
        "location": location,
        "m": 10000,
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

        data = response.json()

        if response.status_code != 200:

            error_message = data.get(
                "error",
                "Unknown SerpApi error"
            )

            st.error(
                f"❌ SerpApi error: {error_message}"
            )

            return []

        return data.get(
            "local_results",
            []
        )

    except Exception as e:

        st.error(
            f"❌ Nearby store search failed: {e}"
        )

        return []


# ============================================================
# DEAL SCORE
# ============================================================

def calculate_deal_score(
    price,
    rating,
    reviews
):

    score = 0

    try:

        if price is not None:
            score += 50

        if rating is not None:
            rating_value = float(rating)
            score += rating_value * 8

        if reviews is not None:

            if isinstance(reviews, str):
                reviews_value = int(
                    reviews.replace(",", "")
                )
            else:
                reviews_value = int(reviews)

            if reviews_value >= 1000:
                score += 10

            elif reviews_value >= 500:
                score += 7

            elif reviews_value >= 100:
                score += 5

    except Exception:
        pass

    return round(score, 2)


# ============================================================
# SESSION STATE
# ============================================================

if "online_results" not in st.session_state:

    st.session_state.online_results = []


if "local_stores" not in st.session_state:

    st.session_state.local_stores = []


if "searched_product" not in st.session_state:

    st.session_state.searched_product = ""


# ============================================================
# INPUT SECTION
# ============================================================

st.subheader("📋 Product Search")


product = st.text_input(
    "🛒 Enter Product Name",
    placeholder="Example: iPhone 15, Laptop, Headphones"
)


location = st.text_input(
    "📍 Enter Your Location",
    placeholder="Example: Hyderabad"
)


# ===========================================================
# BUDGET
# ============================================================

budget = st.number_input(
    "💰 Your Maximum Budget (₹)",
    min_value=0,
    value=50000,
    step=1000
)


# ============================================================
# SEARCH OPTIONS
# ============================================================

col1, col2 = st.columns(2)


with col1:

    radius = st.selectbox(
        "📍 Store Search Radius",
        [
            "5 km",
            "10 km",
            "25 km",
            "50 km"
        ]
    )


with col2:

    condition = st.selectbox(
        "📦 Product Condition",
        [
            "Any",
            "New",
            "Used",
            "Refurbished"
        ]
    )


priority = st.selectbox(
    "🎯 What matters most?",
    [
        "Lowest Price",
        "Best Overall Deal",
        "Nearest Store",
        "Best Rating"
    ]
)


# ============================================================
# 📍 NEARBY LOCAL STORES
# ============================================================

st.divider()

st.subheader("📍 Nearby Local Stores")


if st.button(
    "📍 Find Nearby Stores",
    use_container_width=True
):

    if not product:

        st.warning(
            "⚠️ Please enter a product first."
        )

    elif not location:

        st.warning(
            "⚠️ Please enter your location first."
        )

    else:

        with st.spinner(
            "📍 Finding nearby stores..."
        ):

            stores = search_local_stores(
                product,
                location
            )

        st.session_state.local_stores = stores

        if stores:

            st.success(
                f"Found {len(stores)} nearby stores!"
            )

        else:

            st.info(
                "No nearby stores were found."
            )


# ============================================================
# DISPLAY NEARBY STORES
# ============================================================

if st.session_state.local_stores:

    st.markdown("### 🏪 Nearby Stores")

    for store in st.session_state.local_stores:

        store_name = store.get(
            "title",
            "Local Store"
        )

        address = store.get(
            "address",
            "Address unavailable"
        )

        rating = store.get(
            "rating",
            "N/A"
        )

        reviews = store.get(
            "reviews",
            "N/A"
        )

        phone = store.get(
            "phone",
            "Not available"
        )

        website = store.get(
            "website",
            ""
        )

        latitude = store.get(
            "gps_coordinates",
            {}
        ).get(
            "latitude"
        )

        longitude = store.get(
            "gps_coordinates",
            {}
        ).get(
            "longitude"
        )


        st.markdown(
            f"""
            ### 🏪 {store_name}

            📍 **Address:** {address}

            ⭐ **Rating:** {rating}

            💬 **Reviews:** {reviews}

            📞 **Phone:** {phone}
            """
        )


        # Directions

        if latitude and longitude:

            maps_url = (
                "https://www.google.com/maps/dir/?api=1"
                f"&destination={latitude},{longitude}"
            )

            st.link_button(
                "🧭 Get Directions",
                maps_url
            )

        elif address:

            maps_url = (
                "https://www.google.com/maps/search/?api=1"
                f"&query={quote(address)}"
            )

            st.link_button(
                "🧭 View on Google Maps",
                maps_url
            )


        if website:

            st.link_button(
                "🌐 Visit Store Website",
                website
            )


        st.divider()


# ============================================================
# 🔎 FIND BEST PRICES
# ============================================================

st.subheader("🔎 Find Best Prices")


if st.button(
    "🔎 Find Best Prices",
    use_container_width=True
):

    if not product:

        st.warning(
            "⚠️ Please enter a product first."
        )

    elif not location:

        st.warning(
            "⚠️ Please enter your location first."
        )

    else:

        with st.spinner(
            "🔎 Searching for the best prices..."
        ):

            results = search_products(
                product,
                location
            )


# ----------------------------------------------------
        # FILTER BY CONDITION
# ----------------------------------------------------

        if condition != "Any":

            filtered_results = []

            for item in results:

                title = item.get(
                    "title",
                    ""
                ).lower()

                if condition.lower() in title:

                    filtered_results.append(
                        item
                    )

            if filtered_results:

                results = filtered_results


# ----------------------------------------------------
        # STORE RESULTS
# ----------------------------------------------------

        st.session_state.online_results = results

        st.session_state.searched_product = product


# ============================================================
# PRICE RESULTS
# ============================================================

priced_results = []


if st.session_state.online_results:

    st.subheader("🛒 Price Results")


    for item in st.session_state.online_results:

        title = item.get(
            "title",
            "Product"
        )

        price = item.get(
            "price",
            "Price unavailable"
        )

        source = item.get(
            "source",
            "Unknown Store"
        )

        link = item.get(
            "link",
            ""
        )

        rating = item.get(
            "rating",
            "N/A"
        )

        reviews = item.get(
            "reviews",
            "N/A"
        )

        extracted_price = item.get(
            "extracted_price"
        )


        if extracted_price is not None:

            priced_results.append(
                item
            )


        st.markdown(
            f"""
            ### 🛍️ {title}

            🏪 **Store:** {source}

            💰 **Price:** {price}

            ⭐ **Rating:** {rating}

            💬 **Reviews:** {reviews}
            """
        )


        if link:

            st.link_button(
                "🛒 View Product",
                link
            )


        st.divider()


# ============================================================
# BEST ONLINE PRICE
# ============================================================

if priced_results:

    st.subheader("💰 Best Online Price")


    cheapest_item = min(
        priced_results,
        key=lambda x: x.get(
            "extracted_price",
            float("inf")
        )
    )


    cheapest_price = cheapest_item.get(
        "extracted_price"
    )

    cheapest_title = cheapest_item.get(
        "title",
        "Best Price"
    )

    cheapest_source = cheapest_item.get(
        "source",
        "Unknown Store"
    )


    st.success(
        f"""
        🏆 **Lowest Price Found**

        **Product:** {cheapest_title}

        **Store:** {cheapest_source}

        **Price:** ₹{cheapest_price:,.0f}
        """
    )


    cheapest_link = cheapest_item.get(
        "link"
    )


    if cheapest_link:

        st.link_button(
            "🛒 Buy at Lowest Price",
            cheapest_link,
            use_container_width=True
        )


# ============================================================
# SAVINGS ANALYSIS
# ============================================================

if len(priced_results) >= 2:

    prices = [
        item.get("extracted_price")
        for item in priced_results
        if item.get("extracted_price") is not None
    ]


    if prices:

        lowest_price = min(prices)

        highest_price = max(prices)

        potential_savings = (
            highest_price -
            lowest_price
        )


        st.subheader("💸 Savings Analysis")


        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(
                "Lowest Price",
                f"₹{lowest_price:,.0f}"
            )


        with col2:

            st.metric(
                "Highest Price",
                f"₹{highest_price:,.0f}"
            )


        with col3:

            st.metric(
                "Potential Savings",
                f"₹{potential_savings:,.0f}"
            )


## ============================================================
# ⭐ AI CUSTOMER REVIEW ANALYSIS
# ============================================================

st.divider()

st.subheader("⭐ AI Customer Review Analysis")

if priced_results:

    for item in priced_results[:5]:

        title = item.get(
            "title",
            "Product"
        )

        rating = item.get(
            "rating"
        )

        review_count = item.get(
            "reviews"
        )

# ----------------------------------------------------
        # Try to obtain review text
# ----------------------------------------------------

        review_texts = []

        possible_reviews = item.get(
            "reviews_results",
            []
        )

        if isinstance(
            possible_reviews,
            list
        ):

            for review in possible_reviews:

                if isinstance(
                    review,
                    dict
                ):

                    text = review.get(
                        "snippet"
                    ) or review.get(
                        "text"
                    )

                    if text:

                        review_texts.append(
                            text
                        )

                elif isinstance(
                    review,
                    str
                ):

                    review_texts.append(
                        review
                    )

# ----------------------------------------------------
        # Analyze reviews
# ----------------------------------------------------

        analysis = analyze_customer_reviews(
            review_texts
        )

        st.markdown(
            f"### 🛍️ {title}"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            if rating:

                st.metric(
                    "⭐ Product Rating",
                    f"{rating}/5"
                )

            else:

                st.metric(
                    "⭐ Product Rating",
                    "N/A"
                )

        with col2:

            st.metric(
                "💬 Review Count",
                str(
                    review_count
                    if review_count
                    else "N/A"
                )
            )

        with col3:

            if analysis["score"] is not None:

                st.metric(
                    "🧠 Review Score",
                    f"{analysis['score']}/100"
                )

            else:

                st.metric(
                    "🧠 Review Score",
                    "N/A"
                )

# ----------------------------------------------------
        # Detailed analysis
# ----------------------------------------------------

        if analysis["score"] is not None:

            st.markdown(
                f"""
                **Overall Customer Sentiment:**  
                {analysis['sentiment']}

                👍 **Positive Reviews:** {analysis['positive']}

                😐 **Neutral Reviews:** {analysis['neutral']}

                👎 **Negative Reviews:** {analysis['negative']}
                """
            )

            # Progress bar

            st.progress(
                analysis["score"] / 100
            )

            # Verdict

            if analysis["score"] >= 80:

                st.success(
                    "🏆 Customers are highly satisfied with this product."
                )

            elif analysis["score"] >= 65:

                st.info(
                    "👍 Customers generally have a positive experience."
                )

            elif analysis["score"] >= 50:

                st.warning(
                    "😐 Customer opinions are mixed."
                )

            else:

                st.error(
                    "⚠️ Customer sentiment is mostly negative."
                )

        else:

            st.info(
                "ℹ️ Detailed review text was not returned "
                "for this product. The available rating and "
                "review count can still be used."
            )

        st.divider()

else:

    st.info(
        "🔎 Search for products first to analyze customer reviews."
    )
# ============================================================
# 🤖 SMART DEAL RECOMMENDATION
# ============================================================

st.divider()

st.subheader("🤖 Smart Deal Recommendation")


if priced_results:

# --------------------------------------------------------
    # Calculate scores
# --------------------------------------------------------

    scored_results = []


    for item in priced_results:

        price = item.get(
            "extracted_price"
        )

        rating = item.get(
            "rating"
        )

        reviews = item.get(
            "reviews"
        )


        score = calculate_deal_score(
            price,
            rating,
            reviews
        )


        item_copy = item.copy()

        item_copy["deal_score"] = score

        scored_results.append(
            item_copy
        )

# --------------------------------------------------------
    # Select recommendation
# --------------------------------------------------------

    if priority == "Lowest Price":

        best_item = min(
            scored_results,
            key=lambda x: x.get(
                "extracted_price",
                float("inf")
            )
        )


    elif priority == "Best Rating":

        best_item = max(
            scored_results,
            key=lambda x: float(
                x.get(
                    "rating",
                    0
                ) or 0
            )
        )


    else:

        best_item = max(
            scored_results,
            key=lambda x: x.get(
                "deal_score",
                0
            )
        )


    best_title = best_item.get(
        "title",
        "Best Deal"
    )

    best_price = best_item.get(
        "extracted_price"
    )

    best_rating = best_item.get(
        "rating"
    )

    best_reviews = best_item.get(
        "reviews"
    )

    best_source = best_item.get(
        "source",
        "Unknown Store"
    )

    best_link = best_item.get(
        "link"
    )


# --------------------------------------------------------
    # Budget analysis
# --------------------------------------------------------

    within_budget = []


    for item in scored_results:

        item_price = item.get(
            "extracted_price"
        )

        if (
            item_price is not None
            and item_price <= budget
        ):

            within_budget.append(
                item
            )


# --------------------------------------------------------
    # Show recommendation
# --------------------------------------------------------

    st.success(
        "🏆 Smart Deal Recommendation"
    )


    st.markdown(
        f"""
        ### 🏆 {best_title}

        🏪 **Store:** {best_source}

        💰 **Price:** ₹{best_price:,.0f}
        
        ⭐ **Rating:** {best_rating if best_rating else "N/A"}

        💬 **Reviews:** {best_reviews if best_reviews else "N/A"}

        🎯 **Deal Score:** {best_item.get("deal_score", 0)}
        """
    )


# --------------------------------------------------------
    # Budget result
# --------------------------------------------------------

    if best_price is not None:

        if best_price <= budget:

            remaining = budget - best_price

            st.success(
                f"""
                ✅ **Within Your Budget**

                Your budget: ₹{budget:,.0f}

                Deal price: ₹{best_price:,.0f}

                💰 You have ₹{remaining:,.0f} remaining.
                """
            )

        else:

            extra = best_price - budget

            st.warning(
                f"""
                ⚠️ **Above Your Budget**

                Your budget: ₹{budget:,.0f}

                Deal price: ₹{best_price:,.0f}

                You need ₹{extra:,.0f} more.
                """
            )


# --------------------------------------------------------
    # Best option within budget
# --------------------------------------------------------

    if within_budget:

        budget_best = min(
            within_budget,
            key=lambda x: x.get(
                "extracted_price",
                float("inf")
            )
        )


        budget_price = budget_best.get(
            "extracted_price"
        )

        budget_title = budget_best.get(
            "title",
            "Budget Deal"
        )

        budget_source = budget_best.get(
            "source",
            "Unknown Store"
        )

        budget_link = budget_best.get(
            "link"
        )


        st.info(
            f"""
            💡 **Best Option Within Your Budget**

            🛍️ {budget_title}

            🏪 {budget_source}

            💰 ₹{budget_price:,.0f}
            """
        )


        if budget_link:

            st.link_button(
                "🛒 View Budget-Friendly Deal",
                budget_link,
                use_container_width=True
            )


# --------------------------------------------------------
    # Open recommended deal
# --------------------------------------------------------

    if best_link:

        st.link_button(
            "🛍️ Open Recommended Deal",
            best_link,
            use_container_width=True
        )


else:

    st.info(
        "🔎 Search for product prices above to generate a Smart Deal Recommendation."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center">

    🛍️ **Local Price Finder AI**

    Powered by **SERPAPI**

    🔎 Compare • 📍 Discover • 💰 Save • 🤖 Recommend

    </div>
    """,
    unsafe_allow_html=True
)
# ============================================================
# ⭐ CUSTOMER REVIEW ANALYZER
# ============================================================

def analyze_customer_reviews(reviews):

    if not reviews:

        return {
            "score": None,
            "sentiment": "No review text available",
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "total": 0
        }

    positive = 0
    negative = 0
    neutral = 0

    sentiments = []

    for review in reviews:

        if not isinstance(review, str):
            continue

        review = review.strip()

        if not review:
            continue

        try:

            polarity = TextBlob(
                review
            ).sentiment.polarity

            sentiments.append(
                polarity
            )

            if polarity > 0.10:

                positive += 1

            elif polarity < -0.10:

                negative += 1

            else:

                neutral += 1

        except Exception:

            neutral += 1

    total = (
        positive +
        negative +
        neutral
    )

    if total == 0:

        return {
            "score": None,
            "sentiment": "No usable reviews",
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "total": 0
        }

# --------------------------------------------------------
    # SENTIMENT SCORE
# --------------------------------------------------------

    average_polarity = sum(
        sentiments
    ) / len(sentiments)

    sentiment_score = (
        (average_polarity + 1) / 2
    ) * 100

    sentiment_score = round(
        sentiment_score
    )

# --------------------------------------------------------
    # OVERALL SENTIMENT
# --------------------------------------------------------

    positive_percentage = (
        positive / total
    ) * 100

    negative_percentage = (
        negative / total
    ) * 100

    if positive_percentage >= 70:

        sentiment = "Very Positive 😊"

    elif positive_percentage >= 50:

        sentiment = "Positive 👍"

    elif negative_percentage >= 50:

        sentiment = "Negative 👎"

    else:

        sentiment = "Mixed 😐"

    return {
        "score": sentiment_score,
        "sentiment": sentiment,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "total": total
    }