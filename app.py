import streamlit as st
import requests
import math
import re
from textblob import TextBlob


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Local Price Finder AI",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ============================================================
# SETTINGS
# ============================================================

SERPAPI_API_KEY = st.secrets.get("SERPAPI_API_KEY", "")

# IMPORTANT:
# Keep this TRUE while your SerpApi quota is exhausted.
# Change to FALSE when you want to use live SerpApi.
DEMO_MODE = True


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main page */

    .main {
        padding-top: 1rem;
    }

    .block-container {
        max-width: 850px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }


    /* Main title */

    .main-title {
        font-size: 32px;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 8px;
    }

    .main-subtitle {
        font-size: 13px;
        color: #6b7280;
        line-height: 1.5;
        margin-bottom: 22px;
    }


    /* Section headings */

    .section-title {
        font-size: 18px;
        font-weight: 750;
        margin-top: 22px;
        margin-bottom: 12px;
    }


    /* Product cards */

    .product-card {
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 16px;
        margin: 12px 0;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .product-name {
        font-size: 16px;
        font-weight: 700;
        color: #202124;
        margin-bottom: 8px;
    }

    .product-price {
        font-size: 22px;
        font-weight: 800;
        margin-bottom: 7px;
    }

    .product-info {
        font-size: 12px;
        color: #666;
        line-height: 1.7;
    }


    /* Store cards */

    .store-card {
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 15px;
        margin: 10px 0;
        background: white;
    }

    .store-name {
        font-size: 16px;
        font-weight: 750;
    }

    .store-info {
        font-size: 12px;
        color: #666;
        line-height: 1.7;
    }


    /* Review cards */

    .review-card {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 14px;
        margin: 10px 0;
        background: #fafafa;
    }

    .review-text {
        font-size: 13px;
        line-height: 1.6;
        color: #444;
    }


    /* Metrics */

    .metric-card {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        background: white;
    }

    .metric-title {
        font-size: 11px;
        color: #777;
        margin-bottom: 5px;
    }

    .metric-value {
        font-size: 21px;
        font-weight: 800;
    }


    /* Deal card */

    .deal-card {
        border-radius: 14px;
        padding: 16px;
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        margin: 12px 0;
    }

    .deal-title {
        font-size: 17px;
        font-weight: 800;
    }

    .deal-text {
        font-size: 13px;
        line-height: 1.6;
        color: #374151;
        margin-top: 5px;
    }


    /* Review score */

    .review-score {
        border-radius: 14px;
        padding: 18px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        text-align: center;
        margin: 12px 0;
    }

    .score-number {
        font-size: 30px;
        font-weight: 850;
    }

    .score-label {
        font-size: 12px;
        color: #64748b;
    }


    /* Buttons */

    div.stButton > button {
        border-radius: 9px;
        font-weight: 650;
        min-height: 42px;
    }


    /* Divider */

    hr {
        margin-top: 25px;
        margin-bottom: 25px;
    }


    /* Footer */

    .footer {
        text-align: center;
        color: #9ca3af;
        font-size: 11px;
        margin-top: 35px;
        padding-top: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "priced_results" not in st.session_state:
    st.session_state.priced_results = []

if "store_results" not in st.session_state:
    st.session_state.store_results = []


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):

    try:

        if value is None:
            return default

        if isinstance(value, str):

            value = (
                value.replace("₹", "")
                .replace(",", "")
                .replace("$", "")
                .strip()
            )

        return float(value)

    except:

        return default


def haversine_km(lat1, lon1, lat2, lon2):

    try:

        R = 6371

        lat1 = math.radians(float(lat1))
        lon1 = math.radians(float(lon1))

        lat2 = math.radians(float(lat2))
        lon2 = math.radians(float(lon2))

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1)
            * math.cos(lat2)
            * math.sin(dlon / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    except:

        return None


# ============================================================
# DEMO PRICE DATA
# ============================================================

def demo_price_results(product, location):

    return [

        {
            "title": f"{product} - Amazon",
            "price": "₹74,999",
            "extracted_price": 74999,
            "rating": 4.6,
            "reviews": 1240,
            "source": "Amazon",
            "delivery": "Free Delivery",
            "link": "https://www.amazon.in/"
        },

        {
            "title": f"{product} - Flipkart",
            "price": "₹72,499",
            "extracted_price": 72499,
            "rating": 4.5,
            "reviews": 892,
            "source": "Flipkart",
            "delivery": "Free Delivery",
            "link": "https://www.flipkart.com/"
        },

        {
            "title": f"{product} - Croma",
            "price": "₹76,990",
            "extracted_price": 76990,
            "rating": 4.4,
            "reviews": 621,
            "source": "Croma",
            "delivery": "Delivery Available",
            "link": "https://www.croma.com/"
        },

        {
            "title": f"{product} - Reliance Digital",
            "price": "₹78,499",
            "extracted_price": 78499,
            "rating": 4.3,
            "reviews": 514,
            "source": "Reliance Digital",
            "delivery": "Delivery Available",
            "link": "https://www.reliancedigital.in/"
        }

    ]


# ============================================================
# DEMO REVIEWS
# ============================================================

def demo_reviews(product):

    return {

        "rating": 4.6,

        "review_count": 1240,

        "reviews": [

            {
                "text": "The product quality is excellent and performance is very smooth. Battery life is also impressive.",
                "rating": 5,
                "title": "Excellent product"
            },

            {
                "text": "Good performance and premium build quality. Delivery was quick and the product arrived safely.",
                "rating": 5,
                "title": "Worth the price"
            },

            {
                "text": "The performance is good but the price is slightly high compared to other products.",
                "rating": 4,
                "title": "Good overall"
            },

            {
                "text": "Very satisfied with the purchase. Everything works perfectly and the quality feels premium.",
                "rating": 5,
                "title": "Very satisfied"
            }

        ]
    }


# ============================================================
# DEMO LOCAL STORES
# ============================================================

def demo_stores(product, location):

    return [

        {
            "name": "Yashu Digital World",
            "address": "Giri Nagar, Kukatpally, Hyderabad",
            "distance": 4.8,
            "rating": 5.0,
            "reviews": 792,
            "phone": "091339 1995",
            "link": "https://www.google.com/maps/search/?api=1&query=Yashu+Digital+World+Hyderabad"
        },

        {
            "name": "Croma",
            "address": "Forum Sujana Mall, Kukatpally, Hyderabad",
            "distance": 6.2,
            "rating": 4.4,
            "reviews": 1240,
            "phone": "040 4000 0000",
            "link": "https://www.google.com/maps/search/?api=1&query=Croma+Kukatpally+Hyderabad"
        },

        {
            "name": "Reliance Digital",
            "address": "Manjeera Mall, Kukatpally, Hyderabad",
            "distance": 7.1,
            "rating": 4.3,
            "reviews": 918,
            "phone": "040 4000 1111",
            "link": "https://www.google.com/maps/search/?api=1&query=Reliance+Digital+Kukatpally+Hyderabad"
        }

    ]


# ============================================================
# LIVE SERPAPI - PRODUCT SEARCH
# ============================================================

def search_product_prices(product, location):

    if not SERPAPI_API_KEY:

        return []

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
            "https://serpapi.com/search.json",
            params=params,
            timeout=30
        )

        if response.status_code == 401:

            st.error(
                "🔐 SerpApi authentication failed. "
                "Check your API key."
            )

            return []

        if response.status_code == 429:

            st.warning(
                "⚠️ SerpApi request limit has been reached. "
                "Please use Demo Mode."
            )

            return []

        if response.status_code != 200:

            return []

        data = response.json()

        return data.get("shopping_results", [])

    except Exception as e:

        st.error(f"Search error: {e}")

        return []


# ============================================================
# LIVE SERPAPI - LOCAL STORES
# ============================================================

def search_local_stores_live(product, location, radius_km):

    if not SERPAPI_API_KEY:

        return []

    params = {

        "engine": "google_maps",

        "q": product,

        "location": location,

        "type": "search",

        "m": int(radius_km * 1000),

        "hl": "en",

        "gl": "in",

        "api_key": SERPAPI_API_KEY
    }

    try:

        response = requests.get(
            "https://serpapi.com/search.json",
            params=params,
            timeout=30
        )

        if response.status_code == 401:

            st.error("🔐 SerpApi authentication failed.")

            return []

        if response.status_code == 429:

            st.warning(
                "⚠️ SerpApi request limit reached. "
                "Please use Demo Mode."
            )

            return []

        if response.status_code != 200:

            return []

        data = response.json()

        results = []

        for place in data.get("local_results", []):

            gps = place.get("gps_coordinates", {})

            results.append(
                {
                    "name": place.get("title", "Unknown Store"),

                    "address": place.get(
                        "address",
                        "Address unavailable"
                    ),

                    "distance": place.get(
                        "distance",
                        "N/A"
                    ),

                    "rating": place.get(
                        "rating",
                        0
                    ),

                    "reviews": place.get(
                        "reviews",
                        0
                    ),

                    "phone": place.get(
                        "phone",
                        "N/A"
                    ),

                    "link": place.get(
                        "links",
                        {}
                    ).get(
                        "directions",
                        place.get("link", "")
                    ),

                    "gps": gps
                }
            )

        return results

    except Exception as e:

        st.error(f"Store search error: {e}")

        return []


# ============================================================
# CUSTOMER REVIEW ANALYSIS
# ============================================================

def analyze_customer_reviews(reviews):

    if not reviews:

        return None

    scores = []

    positive = 0
    neutral = 0
    negative = 0

    for review in reviews:

        text = review.get("text", "").strip()

        if not text:

            continue

        polarity = TextBlob(text).sentiment.polarity

        scores.append(polarity)

        if polarity > 0.10:

            positive += 1

        elif polarity < -0.10:

            negative += 1

        else:

            neutral += 1

    if not scores:

        return None

    average = sum(scores) / len(scores)

    ai_score = round(
        max(0, min(100, (average + 1) * 50)),
        1
    )

    if average > 0.25:

        sentiment = "😊 Very Positive"

    elif average > 0.05:

        sentiment = "🙂 Positive"

    elif average < -0.20:

        sentiment = "😞 Negative"

    elif average < -0.05:

        sentiment = "😐 Slightly Negative"

    else:

        sentiment = "😐 Neutral"

    return {

        "score": ai_score,

        "sentiment": sentiment,

        "positive": positive,

        "neutral": neutral,

        "negative": negative,

        "analyzed": len(scores)
    }


# ============================================================
# SORT PRODUCTS
# ============================================================

def sort_results(results, priority):

    if not results:

        return results

    if priority == "Lowest Price":

        return sorted(
            results,
            key=lambda x: safe_float(
                x.get("extracted_price", x.get("price", 999999999)),
                999999999
            )
        )

    if priority == "Best Rating":

        return sorted(
            results,
            key=lambda x: safe_float(
                x.get("rating", 0)
            ),
            reverse=True
        )

    if priority == "Best Overall Deal":

        def deal_score(item):

            price = safe_float(
                item.get(
                    "extracted_price",
                    item.get("price", 999999999)
                ),
                999999999
            )

            rating = safe_float(
                item.get("rating", 0)
            )

            reviews = safe_float(
                item.get("reviews", 0)
            )

            review_factor = min(reviews / 1000, 1)

            return (
                rating * 20
                + review_factor * 20
                - price / 10000
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

st.markdown(
    """
    <div class="main-title">
        🛍️ Local Price Finder AI
    </div>

    <div class="main-subtitle">
        Find the best prices, nearby stores, customer
        satisfaction and smart deals using SerpApi.
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SEARCH SECTION
# ============================================================

st.markdown(
    '<div class="section-title">🔎 Search Product</div>',
    unsafe_allow_html=True
)


product = st.text_input(
    "🛍️ Product Name",
    placeholder="Example: iPhone 16",
    label_visibility="visible"
)


location = st.text_input(
    "📍 Your Location",
    value="Hyderabad",
    placeholder="Example: Hyderabad"
)


col1, col2 = st.columns(2)

with col1:

    max_budget = st.number_input(
        "💰 Maximum Budget (₹)",
        min_value=0,
        value=100000,
        step=1000
    )


with col2:

    radius_km = st.selectbox(
        "📍 Store Search Radius",
        [5, 10, 25, 50],
        index=0,
        format_func=lambda x: f"{x} km"
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
    "⭐ Priority",
    [
        "Best Overall Deal",
        "Lowest Price",
        "Nearest Store",
        "Best Rating"
    ]
)


# ============================================================
# DEMO STATUS
# ============================================================

if DEMO_MODE:

    st.info(
        "🎭 Demo Mode is active — sample data is being used. "
        "No SerpApi requests are consumed."
    )


# ============================================================
# FIND BEST PRICES BUTTON
# ============================================================

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
            "⚠️ Please enter your location."
        )

    else:

        with st.spinner("🔍 Searching for the best prices..."):

            if DEMO_MODE:

                results = demo_price_results(
                    product,
                    location
                )

            else:

                results = search_product_prices(
                    product,
                    location
                )

            # ------------------------------------------------
            # CONDITION FILTER
            # ------------------------------------------------

            if condition != "Any":

                filtered = []

                for item in results:

                    title = item.get(
                        "title",
                        ""
                    ).lower()

                    if condition.lower() in title:

                        filtered.append(item)

                if filtered:

                    results = filtered

            # ------------------------------------------------
            # BUDGET FILTER
            # ------------------------------------------------

            if max_budget > 0:

                budget_results = []

                for item in results:

                    price = safe_float(
                        item.get(
                            "extracted_price",
                            item.get("price", 0)
                        )
                    )

                    if price <= max_budget:

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

    st.markdown("---")

    st.markdown(
        '<div class="section-title">💰 Best Online Price</div>',
        unsafe_allow_html=True
    )

    prices = [

        safe_float(
            item.get(
                "extracted_price",
                item.get("price", 0)
            )
        )

        for item in priced_results

        if safe_float(
            item.get(
                "extracted_price",
                item.get("price", 0)
            )
        ) > 0
    ]

    if prices:

        lowest_price = min(prices)
        highest_price = max(prices)
        savings = highest_price - lowest_price

        c1, c2, c3 = st.columns(3)

        with c1:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">
                        Lowest Price
                    </div>

                    <div class="metric-value">
                        ₹{lowest_price:,.0f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">
                        Highest Price
                    </div>

                    <div class="metric-value">
                        ₹{highest_price:,.0f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c3:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">
                        Potential Savings
                    </div>

                    <div class="metric-value">
                        ₹{savings:,.0f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


    # ========================================================
    # PRODUCT LIST
    # ========================================================

    for item in priced_results:

        title = item.get(
            "title",
            "Product"
        )

        price = safe_float(
            item.get(
                "extracted_price",
                item.get("price", 0)
            )
        )

        rating = item.get(
            "rating",
            "N/A"
        )

        reviews = item.get(
            "reviews",
            0
        )

        source = item.get(
            "source",
            item.get(
                "merchant",
                "Online Store"
            )
        )

        delivery = item.get(
            "delivery",
            "Delivery available"
        )

        link = item.get(
            "link",
            item.get(
                "product_link",
                ""
            )
        )

        st.markdown(
            f"""
            <div class="product-card">

                <div class="product-name">
                    🛍️ {title}
                </div>

                <div class="product-price">
                    ₹{price:,.0f}
                </div>

                <div class="product-info">

                    ⭐ Rating: {rating}

                    &nbsp;&nbsp; | &nbsp;&nbsp;

                    💬 Reviews: {reviews}

                    <br>

                    🏪 Store: {source}

                    <br>

                    🚚 {delivery}

                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        if link:

            st.link_button(
                "🌐 Visit Website",
                link,
                use_container_width=True
            )


    # ========================================================
    # SMART DEAL RECOMMENDATION
    # ========================================================

    st.markdown("---")

    st.markdown(
        '<div class="section-title">🤖 Smart Deal Recommendation</div>',
        unsafe_allow_html=True
    )

    best_item = priced_results[0]

    best_price = safe_float(
        best_item.get(
            "extracted_price",
            best_item.get("price", 0)
        )
    )

    best_rating = safe_float(
        best_item.get(
            "rating",
            0
        )
    )

    best_reviews = safe_float(
        best_item.get(
            "reviews",
            0
        )
    )

    best_source = best_item.get(
        "source",
        best_item.get(
            "merchant",
            "Online Store"
        )
    )

    deal_score = min(
        100,
        round(
            (
                best_rating / 5 * 60
                + min(best_reviews / 1000, 1) * 20
                + 20
            ),
            1
        )
    )

    st.markdown(
        f"""
        <div class="deal-card">

            <div class="deal-title">
                🏆 Recommended Deal
            </div>

            <div class="deal-text">

                <b>{best_item.get("title", product)}</b>

                <br><br>

                💰 Price:
                <b>₹{best_price:,.0f}</b>

                <br>

                ⭐ Rating:
                <b>{best_rating}/5</b>

                <br>

                💬 Reviews:
                <b>{int(best_reviews)}</b>

                <br>

                🏪 Seller:
                <b>{best_source}</b>

                <br>

                🎯 Deal Score:
                <b>{deal_score}/100</b>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# NEARBY LOCAL STORES
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">📍 Nearby Local Stores</div>',
    unsafe_allow_html=True
)


if st.button(
    "📍 Find Nearby Stores",
    use_container_width=True
):

    if not product.strip():

        st.warning(
            "⚠️ Please enter a product first."
        )

    elif not location.strip():

        st.warning(
            "⚠️ Please enter your location."
        )

    else:

        with st.spinner(
            "📍 Finding nearby stores..."
        ):

            if DEMO_MODE:

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

            st.session_state.store_results = stores


# ============================================================
# DISPLAY STORES
# ============================================================

store_results = st.session_state.store_results


if store_results:

    st.success(
        f"Found {len(store_results)} store(s) near {location}."
    )

    for store in store_results:

        store_name = store.get(
            "name",
            "Local Store"
        )

        address = store.get(
            "address",
            "Address unavailable"
        )

        distance = store.get(
            "distance",
            "N/A"
        )

        rating = store.get(
            "rating",
            "N/A"
        )

        reviews = store.get(
            "reviews",
            0
        )

        phone = store.get(
            "phone",
            "N/A"
        )

        link = store.get(
            "link",
            ""
        )

        st.markdown(
            f"""
            <div class="store-card">

                <div class="store-name">
                    🏪 {store_name}
                </div>

                <div class="store-info">

                    📍 {address}

                    <br>

                    📏 Distance:
                    <b>{distance}</b>

                    <br>

                    ⭐ Rating:
                    <b>{rating}</b>

                    &nbsp;&nbsp; | &nbsp;&nbsp;

                    💬 Reviews:
                    <b>{reviews}</b>

                    <br>

                    📞 Phone:
                    {phone}

                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        if link:

            st.link_button(
                "🗺️ Get Directions",
                link,
                use_container_width=True
            )


# ============================================================
# AI CUSTOMER REVIEW ANALYSIS
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">⭐ AI Customer Review Analysis</div>',
    unsafe_allow_html=True
)


if priced_results:

    reviewed_products = []

    with st.spinner(
        "🔍 Checking products for real customer reviews..."
    ):

        # ----------------------------------------------------
        # DEMO MODE
        # ----------------------------------------------------

        if DEMO_MODE:

            # Check only first 3 products
            for product_item in priced_results[:3]:

                product_copy = product_item.copy()

                review_data = demo_reviews(
                    product_item.get(
                        "title",
                        product
                    )
                )

                if (
                    review_data
                    and review_data.get("reviews")
                ):

                    product_copy["review_data"] = review_data

                    reviewed_products.append(
                        product_copy
                    )


        # ----------------------------------------------------
        # LIVE MODE
        # ----------------------------------------------------

        else:

            for product_item in priced_results[:3]:

                product_id = product_item.get(
                    "product_id"
                )

                if not product_id:

                    continue

                params = {

                    "engine": "google_product",

                    "product_id": product_id,

                    "offer_view": "true",

                    "hl": "en",

                    "gl": "in",

                    "api_key": SERPAPI_API_KEY
                }

                try:

                    response = requests.get(
                        "https://serpapi.com/search.json",
                        params=params,
                        timeout=30
                    )

                    if response.status_code != 200:

                        continue

                    data = response.json()

                    reviews_data = data.get(
                        "user_reviews",
                        []
                    )

                    actual_reviews = []

                    for review in reviews_data:

                        review_text = review.get(
                            "text",
                            ""
                        ).strip()

                        if review_text:

                            actual_reviews.append(
                                review
                            )

                    # IMPORTANT:
                    # Product is included ONLY if actual
                    # review text exists.

                    if actual_reviews:

                        product_copy = product_item.copy()

                        product_copy["review_data"] = {

                            "rating": data.get(
                                "rating",
                                product_item.get(
                                    "rating",
                                    0
                                )
                            ),

                            "review_count": data.get(
                                "reviews",
                                product_item.get(
                                    "reviews",
                                    0
                                )
                            ),

                            "reviews": actual_reviews
                        }

                        reviewed_products.append(
                            product_copy
                        )

                except:

                    continue


    # ========================================================
    # DISPLAY REVIEW RESULTS
    # ========================================================

    if reviewed_products:

        for product_item in reviewed_products:

            review_data = product_item[
                "review_data"
            ]

            reviews = review_data.get(
                "reviews",
                []
            )

            analysis = analyze_customer_reviews(
                reviews
            )

            if not analysis:

                continue

            product_title = product_item.get(
                "title",
                product
            )

            customer_rating = review_data.get(
                "rating",
                "N/A"
            )

            review_count = review_data.get(
                "review_count",
                0
            )

            st.markdown(
                f"### 🛍️ {product_title}"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.metric(
                    "Customer Rating",
                    f"{customer_rating}/5"
                )

            with c2:

                st.metric(
                    "Review Count",
                    review_count
                )

            with c3:

                st.metric(
                    "Reviews Analyzed",
                    analysis["analyzed"]
                )


            st.markdown(
                f"""
                <div class="review-score">

                    <div class="score-number">
                        {analysis["score"]}/100
                    </div>

                    <div class="score-label">
                        🤖 AI Review Score
                    </div>

                    <br>

                    <b>{analysis["sentiment"]}</b>

                </div>
                """,
                unsafe_allow_html=True
            )


            r1, r2, r3 = st.columns(3)

            with r1:

                st.success(
                    f"😊 Positive: {analysis['positive']}"
                )

            with r2:

                st.info(
                    f"😐 Neutral: {analysis['neutral']}"
                )

            with r3:

                st.error(
                    f"😞 Negative: {analysis['negative']}"
                )


            st.markdown("#### 💬 Actual Customer Reviews")

            for review in reviews:

                text = review.get(
                    "text",
                    ""
                )

                rating = review.get(
                    "rating",
                    "N/A"
                )

                title = review.get(
                    "title",
                    ""
                )

                st.markdown(
                    f"""
                    <div class="review-card">

                        <b>⭐ {rating}/5</b>

                        &nbsp;&nbsp;

                        <b>{title}</b>

                        <br><br>

                        <div class="review-text">
                            "{text}"
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

    else:

        st.info(
            "No products with actual customer review text "
            "were found."
        )

else:

    st.info(
        "🔎 Search for a product first to analyze customer reviews."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">

        🛍️ Local Price Finder AI

        <br>

        Compare • Discover • Save

        <br><br>

        Powered by AI & SerpApi

    </div>
    """,
    unsafe_allow_html=True
)
