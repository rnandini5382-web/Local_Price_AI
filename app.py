import streamlit as st
import requests
import math
import re
from textblob import TextBlob

# ============================================================
# LOCAL PRICE FINDER AI
# SerpApi-powered price comparison + local stores +
# customer review analysis + demo fallback
# ============================================================

st.set_page_config(
    page_title="Local Price Finder AI",
    page_icon="🛍️",
    layout="wide"
)

# ------------------------------------------------------------
# API KEY
# ------------------------------------------------------------
SERPAPI_API_KEY = st.secrets.get("SERPAPI_API_KEY", "")

# ------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------
if "priced_results" not in st.session_state:
    st.session_state.priced_results = []

if "search_mode" not in st.session_state:
    st.session_state.search_mode = "🎭 Demo Mode"

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def safe_float(value):
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = re.sub(r"[^\d.]", "", str(value))
        return float(cleaned) if cleaned else None
    except Exception:
        return None


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1)
        * math.cos(p2)
        * math.sin(dl / 2) ** 2
    )

    return radius * 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )


def get_secret_status():
    return bool(
        isinstance(SERPAPI_API_KEY, str)
        and SERPAPI_API_KEY.strip()
    )


# ------------------------------------------------------------
# DEMO DATA
# ------------------------------------------------------------
def demo_price_results(product, location):
    product_name = product.strip() or "Smartphone"

    return [
        {
            "position": 1,
            "title": f"{product_name} - Amazon",
            "source": "Amazon",
            "price": "₹69,999",
            "extracted_price": 69999,
            "old_price": "₹79,999",
            "extracted_old_price": 79999,
            "rating": 4.6,
            "reviews": 1248,
            "delivery": "Free delivery",
            "product_link": "https://www.amazon.in/",
            "website_link": "https://www.amazon.in/",
            "thumbnail": "",
            "product_id": "demo-product-1"
        },
        {
            "position": 2,
            "title": f"{product_name} - Flipkart",
            "source": "Flipkart",
            "price": "₹72,499",
            "extracted_price": 72499,
            "old_price": "₹81,999",
            "extracted_old_price": 81999,
            "rating": 4.5,
            "reviews": 982,
            "delivery": "Free delivery",
            "product_link": "https://www.flipkart.com/",
            "website_link": "https://www.flipkart.com/",
            "thumbnail": "",
            "product_id": "demo-product-2"
        },
        {
            "position": 3,
            "title": f"{product_name} - Croma",
            "source": "Croma",
            "price": "₹74,990",
            "extracted_price": 74990,
            "old_price": "₹79,990",
            "extracted_old_price": 79990,
            "rating": 4.4,
            "reviews": 614,
            "delivery": "Free delivery",
            "product_link": "https://www.croma.com/",
            "website_link": "https://www.croma.com/",
            "thumbnail": "",
            "product_id": "demo-product-3"
        },
        {
            "position": 4,
            "title": f"{product_name} - Reliance Digital",
            "source": "Reliance Digital",
            "price": "₹76,999",
            "extracted_price": 76999,
            "old_price": "₹82,999",
            "extracted_old_price": 82999,
            "rating": 4.3,
            "reviews": 421,
            "delivery": "Free delivery",
            "product_link": "https://www.reliancedigital.in/",
            "website_link": "https://www.reliancedigital.in/",
            "thumbnail": "",
            "product_id": "demo-product-4"
        },
    ]


def demo_reviews(product):
    return {
        "rating": product.get("rating", 4.5),
        "review_count": product.get("reviews", 100),
        "reviews": [
            {
                "user_name": "Verified Customer",
                "rating": 5,
                "title": "Excellent product",
                "text": "The product quality is excellent and the performance is very smooth. Battery life is good and delivery was quick.",
                "date": "2026-10-02"
            },
            {
                "user_name": "Happy Buyer",
                "rating": 5,
                "title": "Worth the price",
                "text": "Very good value for money. The camera and performance are impressive and I am happy with the purchase.",
                "date": "2026-09-28"
            },
            {
                "user_name": "Customer",
                "rating": 4,
                "title": "Good overall",
                "text": "Good phone with useful features. Setup was easy and the display looks great.",
                "date": "2026-09-21"
            },
            {
                "user_name": "Verified Buyer",
                "rating": 3,
                "title": "Some room for improvement",
                "text": "The product is good, but charging could be faster. Overall I am satisfied.",
                "date": "2026-09-17"
            },
            {
                "user_name": "Customer",
                "rating": 5,
                "title": "Highly recommended",
                "text": "Amazing experience. Everything works as expected and the build quality feels premium.",
                "date": "2026-09-10"
            },
        ]
    }


def demo_stores(product, location):
    return [
        {
            "title": f"{product} Store - Banjara Hills",
            "address": "Banjara Hills, Hyderabad",
            "distance_km": 2.1,
            "rating": 4.5,
            "reviews": 820,
            "gps": {"latitude": 17.4156, "longitude": 78.4480},
            "link": "https://www.google.com/maps/"
        },
        {
            "title": f"{product} Store - Jubilee Hills",
            "address": "Jubilee Hills, Hyderabad",
            "distance_km": 3.8,
            "rating": 4.4,
            "reviews": 610,
            "gps": {"latitude": 17.4325, "longitude": 78.4071},
            "link": "https://www.google.com/maps/"
        },
        {
            "title": f"{product} Store - Madhapur",
            "address": "Madhapur, Hyderabad",
            "distance_km": 4.6,
            "rating": 4.3,
            "reviews": 540,
            "gps": {"latitude": 17.4483, "longitude": 78.3915},
            "link": "https://www.google.com/maps/"
        },
    ]


# ------------------------------------------------------------
# SERPAPI: GOOGLE SHOPPING
# ------------------------------------------------------------
def search_product_prices(product, location):
    if not get_secret_status():
        st.error(
            "❌ SerpApi key is missing. "
            "Add SERPAPI_API_KEY in Streamlit Secrets."
        )
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
            timeout=15
        )

        if response.status_code == 401:
            st.error(
                "❌ SerpApi authentication failed (HTTP 401). "
                "Check SERPAPI_API_KEY in Streamlit Secrets."
            )
            return []

        if response.status_code == 429:
            st.error(
                "⚠️ SerpApi request limit reached (HTTP 429). "
                "Use Demo Mode or wait for your quota/rate limit to reset."
            )
            return []

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "shopping_results",
            []
        )

        for item in results:
            item["website_link"] = (
                item.get("product_link")
                or item.get("link")
            )

        return results

    except requests.exceptions.Timeout:
        st.error(
            "⏱️ Price search timed out. Please try again."
        )
        return []

    except requests.exceptions.RequestException:
        st.error(
            "❌ Unable to fetch live shopping results right now."
        )
        return []

    except Exception:
        st.error(
            "❌ Unexpected error while searching prices."
        )
        return []


# ------------------------------------------------------------
# SERPAPI: GOOGLE PRODUCT REVIEWS
# ------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_product_reviews_cached(product_id, page_token):
    if not get_secret_status():
        return None

    if not product_id and not page_token:
        return None

    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_product",
        "hl": "en",
        "gl": "in",
        "api_key": SERPAPI_API_KEY
    }

    if page_token:
        params["page_token"] = page_token
    else:
        params["product_id"] = product_id
        params["offer_view"] = "true"

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        if response.status_code in (401, 429):
            return None

        response.raise_for_status()

        data = response.json()

        product_results = data.get(
            "product_results",
            {}
        )

        user_reviews = product_results.get(
            "user_reviews",
            []
        )

        real_reviews = []

        for review in user_reviews:
            if not isinstance(review, dict):
                continue

            text = review.get("text", "")

            if (
                isinstance(text, str)
                and text.strip()
            ):
                real_reviews.append(review)

        if not real_reviews:
            return None

        return {
            "rating": product_results.get("rating"),
            "review_count": product_results.get("reviews"),
            "reviews": real_reviews
        }

    except Exception:
        return None


def fetch_product_reviews(product):
    product_id = product.get("product_id")

    page_token = product.get(
        "immersive_product_page_token"
    )

    return fetch_product_reviews_cached(
        product_id,
        page_token
    )


# ------------------------------------------------------------
# REVIEW SENTIMENT ANALYSIS
# ------------------------------------------------------------
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
    polarities = []

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

            polarities.append(polarity)

            if polarity > 0.10:
                positive += 1

            elif polarity < -0.10:
                negative += 1

            else:
                neutral += 1

        except Exception:
            neutral += 1

    total = (
        positive
        + negative
        + neutral
    )

    if total == 0:
        return {
            "score": None,
            "sentiment": "No usable review text",
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "total": 0
        }

    average_polarity = (
        sum(polarities) / len(polarities)
        if polarities
        else 0
    )

    score = round(
        ((average_polarity + 1) / 2) * 100
    )

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
        "score": score,
        "sentiment": sentiment,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "total": total
    }


# ------------------------------------------------------------
# SERPAPI: GOOGLE MAPS
# ------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def search_local_stores_live(product, location, radius_km):
    if not get_secret_status():
        return []

    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_maps",
        "q": product,
        "location": location,
        "type": "search",
        "hl": "en",
        "gl": "in",
        "m": int(radius_km * 1000),
        "api_key": SERPAPI_API_KEY
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        if response.status_code in (401, 429):
            return []

        response.raise_for_status()

        data = response.json()

        local_results = data.get(
            "local_results",
            []
        )

        stores = []

        for item in local_results:

            gps = item.get(
                "gps_coordinates",
                {}
            )

            lat = gps.get("latitude")
            lon = gps.get("longitude")

            store = {
                "title": item.get(
                    "title",
                    "Local Store"
                ),
                "address": item.get(
                    "address",
                    "Address unavailable"
                ),
                "rating": item.get("rating"),
                "reviews": item.get("reviews"),
                "link": item.get("link"),
                "gps": gps
            }

            if lat is not None and lon is not None:
                store["distance_km"] = None

            stores.append(store)

        return stores

    except Exception:
        return []


# ------------------------------------------------------------
# DISPLAY HELPERS
# ------------------------------------------------------------
def sort_results(results, priority):
    if not results:
        return results

    if priority == "Lowest Price":
        return sorted(
            results,
            key=lambda x: (
                safe_float(
                    x.get("extracted_price")
                )
                if safe_float(
                    x.get("extracted_price")
                ) is not None
                else float("inf")
            )
        )

    if priority == "Best Rating":
        return sorted(
            results,
            key=lambda x: (
                safe_float(x.get("rating"))
                if safe_float(x.get("rating")) is not None
                else 0
            ),
            reverse=True
        )

    if priority == "Best Overall Deal":
        def deal_score(item):
            price = safe_float(
                item.get("extracted_price")
            )
            rating = safe_float(
                item.get("rating")
            )

            if price is None:
                price = 999999999

            if rating is None:
                rating = 0

            return (
                (rating * 20)
                - (price / 10000)
            )

        return sorted(
            results,
            key=deal_score,
            reverse=True
        )

    return results


# ============================================================
# HEADER
# ============================================================
st.title("🛍️ Local Price Finder AI")

st.markdown(
    """
### Find better prices, nearby stores and trustworthy customer insights.

Compare online prices, discover local stores, and analyze real customer
review text before making a purchase.
"""
)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:

    st.header("⚙️ Search Settings")

    product = st.text_input(
        "🛍️ Product",
        placeholder="e.g. iPhone 16"
    )

    location = st.text_input(
        "📍 Location",
        value="Hyderabad"
    )

    budget = st.number_input(
        "💰 Maximum Budget (₹)",
        min_value=0,
        value=100000,
        step=1000
    )

    radius_km = st.selectbox(
        "📍 Store Search Radius",
        [5, 10, 25, 50],
        index=0
    )

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
        "🎯 Priority",
        [
            "Lowest Price",
            "Best Overall Deal",
            "Nearest Store",
            "Best Rating"
        ]
    )

    st.divider()

    st.subheader("🔌 Data Mode")

    search_mode = st.radio(
        "Choose data source:",
        [
            "🎭 Demo Mode",
            "🌐 Live SerpApi"
        ],
        index=0
    )

    st.session_state.search_mode = search_mode

    if search_mode == "🌐 Live SerpApi":

        if get_secret_status():
            st.success(
                "🔐 SerpApi key detected."
            )
        else:
            st.warning(
                "⚠️ SERPAPI_API_KEY is missing."
            )

    else:

        st.info(
            "🎭 Demo Mode uses built-in sample "
            "data and does not consume SerpApi quota."
        )

# ============================================================
# FIND BEST PRICES
# ============================================================
st.divider()

if st.button(
    "🔎 Find Best Prices",
    use_container_width=True
):

    if not product.strip():

        st.warning(
            "⚠️ Please enter a product name."
        )

    elif not location.strip():

        st.warning(
            "⚠️ Please enter a location."
        )

    else:

        with st.spinner(
            "🔍 Finding the best prices..."
        ):

            if search_mode == "🎭 Demo Mode":

                results = demo_price_results(
                    product,
                    location
                )

            else:

                results = search_product_prices(
                    product,
                    location
                )

        # Condition filtering
        if condition != "Any":

            filtered = []

            for item in results:

                item_condition = str(
                    item.get(
                        "second_hand_condition",
                        ""
                    )
                ).lower()

                if condition == "New":

                    if not item_condition:
                        filtered.append(item)

                elif condition.lower() in item_condition:

                    filtered.append(item)

            if filtered:
                results = filtered

        # Budget filtering
        if budget > 0:

            budget_results = []

            for item in results:

                price = safe_float(
                    item.get(
                        "extracted_price"
                    )
                )

                if price is not None and price <= budget:
                    budget_results.append(item)

            if budget_results:
                results = budget_results

        results = sort_results(
            results,
            priority
        )

        st.session_state.priced_results = results

# ============================================================
# PRICE RESULTS
# ============================================================
priced_results = st.session_state.priced_results

if priced_results:

    st.subheader("💰 Best Available Prices")

    prices = []

    for item in priced_results:

        price = safe_float(
            item.get("extracted_price")
        )

        if price is not None:
            prices.append(price)

    if prices:

        lowest_price = min(prices)
        highest_price = max(prices)
        savings = highest_price - lowest_price

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "💰 Lowest Price",
                f"₹{lowest_price:,.0f}"
            )

        with col2:
            st.metric(
                "📈 Highest Price",
                f"₹{highest_price:,.0f}"
            )

        with col3:
            st.metric(
                "💸 Potential Savings",
                f"₹{savings:,.0f}"
            )

    st.divider()

    for index, item in enumerate(priced_results):

        title = item.get(
            "title",
            "Unknown Product"
        )

        price = safe_float(
            item.get("extracted_price")
        )

        rating = item.get("rating")
        reviews = item.get("reviews")

        source = item.get(
            "source",
            "Online Store"
        )

        st.markdown(
            f"### {index + 1}. 🛍️ {title}"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Price",
                f"₹{price:,.0f}"
                if price is not None
                else "N/A"
            )

        with col2:
            st.metric(
                "⭐ Rating",
                str(rating)
                if rating is not None
                else "N/A"
            )

        with col3:
            st.metric(
                "💬 Reviews",
                f"{reviews:,}"
                if isinstance(reviews, int)
                else str(reviews or "N/A")
            )

        with col4:
            st.metric(
                "🏪 Store",
                source
            )

        delivery = item.get("delivery")

        if delivery:
            st.caption(
                f"🚚 {delivery}"
            )

        product_link = (
            item.get("website_link")
            or item.get("product_link")
            or item.get("link")
        )

        if product_link:
            st.link_button(
                "🌐 Visit Website",
                product_link
            )

        st.divider()

    # ========================================================
    # SMART DEAL RECOMMENDATION
    # ========================================================
    st.subheader(
        "🤖 Smart Deal Recommendation"
    )

    best_item = priced_results[0]

    best_price = safe_float(
        best_item.get("extracted_price")
    )

    best_rating = safe_float(
        best_item.get("rating")
    )

    best_reviews = best_item.get(
        "reviews"
    )

    best_source = best_item.get(
        "source",
        "Online Store"
    )

    recommendation_parts = []

    if best_price is not None:
        recommendation_parts.append(
            f"₹{best_price:,.0f}"
        )

    if best_rating is not None:
        recommendation_parts.append(
            f"{best_rating:.1f}⭐"
        )

    if best_reviews is not None:
        recommendation_parts.append(
            f"{best_reviews:,} reviews"
        )

    details = ", ".join(
        recommendation_parts
    )

    st.success(
        f"🏆 Recommended deal: "
        f"**{best_item.get('title', 'Best Product')}** "
        f"from **{best_source}**"
        + (f" — {details}" if details else "")
    )

else:

    st.info(
        "🔎 Enter a product and click "
        "**Find Best Prices** to begin."
    )

# ============================================================
# NEARBY LOCAL STORES
# ============================================================
st.divider()

st.subheader(
    "📍 Nearby Local Stores"
)

if st.button(
    "📍 Find Nearby Stores",
    use_container_width=True
):

    if not product.strip():

        st.warning(
            "⚠️ Enter a product first."
        )

    elif not location.strip():

        st.warning(
            "⚠️ Enter a location first."
        )

    else:

        with st.spinner(
            "📍 Finding nearby stores..."
        ):

            if search_mode == "🎭 Demo Mode":

                stores = demo_stores(
                    product,
                    location
                )

            else:

                stores = search_local_stores_live(
                    product,
                    location,
                    radius_km
                )

        if stores:

            st.success(
                f"✅ Found {len(stores)} nearby store(s)."
            )

            for store in stores:

                st.markdown(
                    f"### 📍 {store.get('title', 'Store')}"
                )

                st.write(
                    store.get(
                        "address",
                        "Address unavailable"
                    )
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    distance = store.get(
                        "distance_km"
                    )

                    st.metric(
                        "📏 Distance",
                        f"{distance:.1f} km"
                        if isinstance(distance, (int, float))
                        else "Nearby"
                    )

                with col2:

                    st.metric(
                        "⭐ Rating",
                        str(
                            store.get(
                                "rating",
                                "N/A"
                            )
                        )
                    )

                with col3:

                    store_reviews = store.get(
                        "reviews"
                    )

                    st.metric(
                        "💬 Reviews",
                        str(
                            store_reviews
                            if store_reviews is not None
                            else "N/A"
                        )
                    )

                if store.get("link"):

                    st.link_button(
                        "🗺️ Open in Google Maps",
                        store["link"]
                    )

                st.divider()

        else:

            st.warning(
                f"⚠️ No stores found within "
                f"{radius_km} km."
            )

# ============================================================
# AI CUSTOMER REVIEW ANALYSIS
# ============================================================
st.divider()

st.subheader(
    "⭐ AI Customer Review Analysis"
)

if priced_results:

    reviewed_products = []

    # Demo mode needs no additional API calls.
    if search_mode == "🎭 Demo Mode":

        for product_item in priced_results:

            review_data = demo_reviews(
                product_item
            )

            product_copy = product_item.copy()

            product_copy["customer_rating"] = (
                review_data["rating"]
            )

            product_copy["customer_review_count"] = (
                review_data["review_count"]
            )

            product_copy["actual_reviews"] = (
                review_data["reviews"]
            )

            reviewed_products.append(
                product_copy
            )

    else:

        products_to_check = priced_results[:3]

        with st.spinner(
            "🔍 Checking products for real customer reviews..."
        ):

            for product_item in products_to_check:

                review_data = fetch_product_reviews(
                    product_item
                )

                # IMPORTANT:
                # Product is kept ONLY when actual
                # customer review text exists.
                if review_data and review_data.get(
                    "reviews"
                ):

                    product_copy = product_item.copy()

                    product_copy["customer_rating"] = (
                        review_data.get("rating")
                    )

                    product_copy["customer_review_count"] = (
                        review_data.get("review_count")
                    )

                    product_copy["actual_reviews"] = (
                        review_data.get("reviews")
                    )

                    reviewed_products.append(
                        product_copy
                    )

    # --------------------------------------------------------
    # DISPLAY ONLY PRODUCTS WITH REAL REVIEW TEXT
    # --------------------------------------------------------
    if reviewed_products:

        if search_mode == "🎭 Demo Mode":

            st.info(
                "🎭 Demo review data is being used. "
                "Switch to Live SerpApi mode when live quota is available."
            )

        else:

            st.success(
                f"✅ Found {len(reviewed_products)} "
                f"product(s) with actual customer review text."
            )

        for item in reviewed_products:

            title = item.get(
                "title",
                "Unknown Product"
            )

            customer_rating = item.get(
                "customer_rating"
            )

            customer_review_count = item.get(
                "customer_review_count"
            )

            actual_reviews = item.get(
                "actual_reviews",
                []
            )

            review_texts = []

            for review in actual_reviews:

                if not isinstance(review, dict):
                    continue

                text = review.get(
                    "text",
                    ""
                )

                if (
                    isinstance(text, str)
                    and text.strip()
                ):
                    review_texts.append(
                        text.strip()
                    )

            if not review_texts:
                continue

            analysis = analyze_customer_reviews(
                review_texts
            )

            if analysis["total"] == 0:
                continue

            st.markdown("---")

            st.markdown(
                f"### 🛍️ {title}"
            )

            # ------------------------------------------------
            # TRUST INFORMATION
            # ------------------------------------------------
            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "⭐ Customer Rating",
                    (
                        f"{customer_rating} / 5"
                        if customer_rating is not None
                        else "N/A"
                    )
                )

            with col2:

                count = customer_review_count

                st.metric(
                    "💬 Customer Reviews",
                    (
                        f"{count:,}"
                        if isinstance(count, int)
                        else str(count or "N/A")
                    )
                )

            with col3:

                st.metric(
                    "🤖 Reviews Analyzed",
                    analysis["total"]
                )

            # ------------------------------------------------
            # AI ANALYSIS
            # ------------------------------------------------
            st.markdown(
                "#### 🤖 AI Review Analysis"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "AI Review Score",
                    f"{analysis['score']} / 100"
                )

            with col2:

                st.metric(
                    "Overall Sentiment",
                    analysis["sentiment"]
                )

            # ------------------------------------------------
            # SENTIMENT BREAKDOWN
            # ------------------------------------------------
            st.markdown(
                "#### 📊 Sentiment Breakdown"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.success(
                    f"😊 Positive: "
                    f"{analysis['positive']}"
                )

            with col2:

                st.info(
                    f"😐 Neutral: "
                    f"{analysis['neutral']}"
                )

            with col3:

                st.error(
                    f"👎 Negative: "
                    f"{analysis['negative']}"
                )

            # ------------------------------------------------
            # ACTUAL REVIEWS
            # ------------------------------------------------
            with st.expander(
                "💬 View Customer Reviews"
            ):

                for review in actual_reviews:

                    review_text = review.get(
                        "text",
                        ""
                    )

                    if not review_text:
                        continue

                    reviewer = review.get(
                        "user_name",
                        "Anonymous"
                    )

                    review_rating = review.get(
                        "rating"
                    )

                    review_date = review.get(
                        "date",
                        ""
                    )

                    review_title = review.get(
                        "title",
                        ""
                    )

                    st.markdown(
                        f"**👤 {reviewer}**"
                    )

                    if review_rating is not None:

                        st.write(
                            f"⭐ {review_rating} / 5"
                        )

                    if review_title:

                        st.markdown(
                            f"**{review_title}**"
                        )

                    st.write(
                        review_text
                    )

                    if review_date:

                        st.caption(
                            f"📅 {review_date}"
                        )

                    st.divider()

    else:

        if search_mode == "🌐 Live SerpApi":

            st.info(
                "ℹ️ No products with actual customer "
                "review text were found. Products without "
                "review text are excluded."
            )

        else:

            st.info(
                "ℹ️ No review data available."
            )

else:

    st.info(
        "🔎 Find product prices first to analyze "
        "customer reviews."
    )

# ============================================================
# FOOTER
# ============================================================
st.divider()

st.caption(
    "🛍️ Local Price Finder AI | "
    "Powered by SerpApi + Streamlit + TextBlob"
)
