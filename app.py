import streamlit as st
import requests
import math
from urllib.parse import quote
from textblob import TextBlob


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Local Price Finder AI",
    page_icon="🛍️",
    layout="wide"
)


# ============================================================
# SERPAPI KEY
# ============================================================

try:
    SERPAPI_API_KEY = st.secrets["SERPAPI_API_KEY"]
except Exception:
    SERPAPI_API_KEY = ""


# ============================================================
# TITLE
# ============================================================

st.title("🛍️ Local Price Finder AI")

st.markdown(
    """
    ### 🔎 Find the best deals near you

    Compare prices, discover nearby stores, analyze customer
    feedback, and get an intelligent deal recommendation.
    """
)


if not SERPAPI_API_KEY:

    st.error(
        "❌ SERPAPI_API_KEY is missing from Streamlit Secrets."
    )

    st.stop()


# ============================================================
# GOOGLE SHOPPING SEARCH
# ============================================================

def search_product_prices(product, location):

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

        data = response.json()

        if response.status_code != 200:

            st.error(
                "❌ SerpApi error: "
                + str(
                    data.get(
                        "error",
                        "Unknown error"
                    )
                )
            )

            return []

        return data.get(
            "shopping_results",
            []
        )

    except Exception as e:

        st.error(
            f"❌ Price search failed: {e}"
        )

        return []


# ============================================================
# GET LOCATION COORDINATES
# ============================================================

def get_location_coordinates(location):

    url = "https://serpapi.com/locations.json"

    params = {
        "q": location,
        "limit": 5
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        locations = response.json()

        if not locations:

            return None

        for loc in locations:

            gps = loc.get("gps")

            if gps and len(gps) >= 2:

                longitude = float(
                    gps[0]
                )

                latitude = float(
                    gps[1]
                )

                return latitude, longitude

        return None

    except Exception:

        return None


# ============================================================
# CALCULATE DISTANCE
# ============================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    earth_radius = 6371.0

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


# ============================================================
# SEARCH NEARBY STORES
# ============================================================

def search_local_stores(
    product,
    location,
    radius_km=10
):

    coordinates = get_location_coordinates(
        location
    )

    if not coordinates:

        st.warning(
            "⚠️ Could not determine the coordinates "
            "for this location."
        )

        return []

    user_lat, user_lon = coordinates

    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_maps",
        "type": "search",
        "q": f"{product} stores",
        "location": location,
        "m": int(radius_km * 1000),
        "nearby": "true",
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

            st.error(
                "❌ SerpApi error: "
                + str(
                    data.get(
                        "error",
                        "Unknown error"
                    )
                )
            )

            return []

        raw_stores = data.get(
            "local_results",
            []
        )

        nearby_stores = []

        for store in raw_stores:

            gps = store.get(
                "gps_coordinates",
                {}
            )

            store_lat = gps.get(
                "latitude"
            )

            store_lon = gps.get(
                "longitude"
            )

            if (
                store_lat is None
                or store_lon is None
            ):

                continue

            distance = calculate_distance(
                user_lat,
                user_lon,
                float(store_lat),
                float(store_lon)
            )

            if distance <= radius_km:

                store["distance_km"] = round(
                    distance,
                    2
                )

                nearby_stores.append(
                    store
                )

        nearby_stores.sort(
            key=lambda x: x.get(
                "distance_km",
                999999
            )
        )

        return nearby_stores

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

            rating_value = float(
                rating
            )

            score += rating_value * 8

        if reviews is not None:

            if isinstance(
                reviews,
                str
            ):

                reviews_value = int(
                    reviews.replace(
                        ",",
                        ""
                    )
                )

            else:

                reviews_value = int(
                    reviews
                )

            if reviews_value >= 1000:
                score += 10

            elif reviews_value >= 500:
                score += 7

            elif reviews_value >= 100:
                score += 5

    except Exception:

        pass

    return round(
        score,
        2
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

    polarities = []

    for review in reviews:

        if not isinstance(
            review,
            str
        ):

            continue

        review = review.strip()

        if not review:

            continue

        try:

            polarity = TextBlob(
                review
            ).sentiment.polarity

            polarities.append(
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
        sum(polarities)
        / len(polarities)
    )

    score = (
        (average_polarity + 1)
        / 2
    ) * 100

    score = round(
        score
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


# ============================================================
# SESSION STATE
# ============================================================

if "online_results" not in st.session_state:

    st.session_state.online_results = []


if "local_stores" not in st.session_state:

    st.session_state.local_stores = []


# ============================================================
# INPUT SECTION
# ============================================================

st.subheader("📋 Product Search")


product = st.text_input(
    "🛒 Enter Product Name",
    placeholder="Example: Laptop"
)


location = st.text_input(
    "📍 Enter Your Location",
    placeholder="Example: Hyderabad"
)


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

    radius_km = int(
        radius.replace(
            " km",
            ""
        )
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

st.subheader(
    "📍 Nearby Local Stores"
)


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
                location,
                radius_km
            )

        st.session_state.local_stores = stores


        if stores:

            st.success(
                f"Found {len(stores)} stores "
                f"within {radius_km} km."
            )

        else:

            st.info(
                f"No {product} stores found "
                f"within {radius_km} km."
            )


# ============================================================
# DISPLAY NEARBY STORES
# ============================================================

if st.session_state.local_stores:

    st.markdown(
        "### 🏪 Nearby Stores"
    )

    for store in st.session_state.local_stores:

        store_name = store.get(
            "title",
            "Local Store"
        )

        address = store.get(
            "address",
            "Address unavailable"
        )

        distance = store.get(
            "distance_km"
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

        st.markdown(
            f"""
            ### 🏪 {store_name}

            📍 **Address:** {address}

            ⭐ **Rating:** {rating}

            💬 **Reviews:** {reviews}

            📞 **Phone:** {phone}
            """
        )

        if distance is not None:

            st.markdown(
                f"📏 **Distance:** {distance} km away"
            )

        gps = store.get(
            "gps_coordinates",
            {}
        )

        latitude = gps.get(
            "latitude"
        )

        longitude = gps.get(
            "longitude"
        )

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

        st.divider()


# ============================================================
# 🔎 FIND BEST PRICES
# ============================================================

st.subheader(
    "🔎 Find Best Prices"
)


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

            results = search_product_prices(
                product,
                location
            )


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


        st.session_state.online_results = results


# ============================================================
# PRICE RESULTS
# ============================================================

priced_results = []


if st.session_state.online_results:

    st.subheader(
        "🛒 Price Results"
    )

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
# 💰 BEST ONLINE PRICE
# ============================================================

if priced_results:

    st.subheader(
        "💰 Best Online Price"
    )

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
# 💸 SAVINGS ANALYSIS
# ============================================================

if len(priced_results) >= 2:

    prices = [
        item.get(
            "extracted_price"
        )
        for item in priced_results
        if item.get(
            "extracted_price"
        ) is not None
    ]

    if prices:

        lowest_price = min(
            prices
        )

        highest_price = max(
            prices
        )

        savings = (
            highest_price
            - lowest_price
        )

        st.subheader(
            "💸 Savings Analysis"
        )

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
                f"₹{savings:,.0f}"
            )


# ============================================================
# ⭐ AI CUSTOMER REVIEW ANALYSIS
# ============================================================

st.divider()

st.subheader(
    "⭐ AI Customer Review Analysis"
)


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

        source = item.get(
            "source",
            "Unknown Store"
        )

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

                    text = (
                        review.get("snippet")
                        or review.get("text")
                        or review.get("content")
          