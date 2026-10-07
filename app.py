import streamlit as st
import requests
import math
from textblob import TextBlob


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Local Price Finder AI",
    page_icon="🛍️",
    layout="wide"
)


# ============================================================
# SERPAPI API KEY
# ============================================================

try:
    SERPAPI_API_KEY = st.secrets["SERPAPI_API_KEY"]
except Exception:
    st.error(
        "❌ SERPAPI_API_KEY is missing. "
        "Please add it to Streamlit Secrets."
    )
    st.stop()


# ============================================================
# SEARCH PRODUCT PRICES
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

        response.raise_for_status()

        data = response.json()

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
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            return None

        location_data = data[0]

        gps = location_data.get("gps")

        if gps and len(gps) >= 2:

            longitude = float(gps[0])
            latitude = float(gps[1])

            return latitude, longitude

    except Exception:
        pass

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
    lat2 = math.radians(lat2)

    delta_lat = math.radians(
        lat2 - lat1
    )

    delta_lon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


# ============================================================
# SEARCH LOCAL STORES
# ============================================================

def search_local_stores(
    product,
    location,
    radius_km=10
):

    user_coordinates = (
        get_location_coordinates(location)
    )

    if not user_coordinates:

        st.warning(
            "⚠️ Could not determine the coordinates "
            "for this location."
        )

        return []

    user_lat, user_lon = user_coordinates

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

        response.raise_for_status()

        data = response.json()

        local_results = data.get(
            "local_results",
            []
        )

        filtered_stores = []

        for store in local_results:

            gps = store.get(
                "gps_coordinates"
            )

            if not gps:
                continue

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

            try:

                distance = calculate_distance(
                    user_lat,
                    user_lon,
                    float(store_lat),
                    float(store_lon)
                )

            except Exception:
                continue

            # HARD RADIUS FILTER
            if distance <= radius_km:

                store["distance_km"] = round(
                    distance,
                    2
                )

                filtered_stores.append(
                    store
                )

        filtered_stores.sort(
            key=lambda x: x.get(
                "distance_km",
                999999
            )
        )

        return filtered_stores

    except Exception as e:

        st.error(
            f"❌ Nearby store search failed: {e}"
        )

        return []


# ============================================================
# DEAL SCORE
# ============================================================

def calculate_deal_score(item):

    price = item.get(
        "extracted_price"
    )

    rating = item.get(
        "rating"
    )

    reviews = item.get(
        "reviews"
    )

    try:
        price = float(price)
    except Exception:
        price = None

    try:
        rating = float(rating)
    except Exception:
        rating = 0

    try:
        reviews = int(reviews)
    except Exception:
        reviews = 0

    if price is None:

        return 0

    rating_score = (
        rating / 5
    ) * 50

    review_score = min(
        math.log10(
            reviews + 1
        ) * 10,
        30
    )

    price_score = 20

    return round(
        rating_score
        +
        review_score
        +
        price_score,
        2
    )


# ============================================================
# AI CUSTOMER REVIEW ANALYSIS
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
        +
        negative
        +
        neutral
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
        /
        len(polarities)
    )

    score = round(
        (
            (average_polarity + 1)
            /
            2
        )
        * 100
    )

    positive_percentage = (
        positive / total
    ) * 100

    negative_percentage = (
        negative / total
    ) * 100

    if positive_percentage >= 70:

        sentiment = (
            "Very Positive 😊"
        )

    elif positive_percentage >= 50:

        sentiment = (
            "Positive 👍"
        )

    elif negative_percentage >= 50:

        sentiment = (
            "Negative 👎"
        )

    else:

        sentiment = (
            "Mixed 😐"
        )

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

if "priced_results" not in st.session_state:

    st.session_state.priced_results = []


if "stores" not in st.session_state:

    st.session_state.stores = []


# ============================================================
# TITLE
# ============================================================

st.title(
    "🛍️ Local Price Finder AI"
)

st.write(
    "Find the best prices, nearby stores, "
    "customer satisfaction and smart deals "
    "using SerpApi."
)


# ============================================================
# INPUT SECTION
# ============================================================

st.subheader(
    "🔎 Search Product"
)

product = st.text_input(
    "🛍️ Product Name",
    placeholder="Example: iPhone 16"
)

location = st.text_input(
    "📍 Your Location",
    placeholder="Example: Hyderabad"
)


col1, col2 = st.columns(2)


with col1:

    budget = st.number_input(
        "💰 Maximum Budget (₹)",
        min_value=0,
        value=0,
        step=1000
    )


with col2:

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

    if product and location:

        with st.spinner(
            "📍 Finding nearby stores..."
        ):

            stores = search_local_stores(
                product,
                location,
                radius_km
            )

        st.session_state.stores = stores

        if stores:

            st.success(
                f"Found {len(stores)} "
                f"store(s) within "
                f"{radius_km} km."
            )

        else:

            st.warning(
                f"⚠️ No stores found within "
                f"{radius_km} km."
            )

    else:

        st.warning(
            "⚠️ Please enter both product "
            "and location."
        )


# ============================================================
# DISPLAY NEARBY STORES
# ============================================================

if st.session_state.stores:

    for store in (
        st.session_state.stores
    ):

        st.markdown("---")

        st.subheader(
            f"🏪 {store.get('title', 'Store')}"
        )

        address = store.get(
            "address"
        )

        if address:

            st.write(
                f"📍 **Address:** {address}"
            )

        rating = store.get(
            "rating"
        )

        if rating:

            st.write(
                f"⭐ **Rating:** {rating}"
            )

        reviews = store.get(
            "reviews"
        )

        if reviews:

            st.write(
                f"💬 **Reviews:** {reviews}"
            )

        phone = store.get(
            "phone"
        )

        if phone:

            st.write(
                f"📞 **Phone:** {phone}"
            )

        distance = store.get(
            "distance_km"
        )

        if distance is not None:

            st.write(
                f"📏 **Distance:** "
                f"{distance} km"
            )

        place_id = store.get(
            "place_id"
        )

        if place_id:

            maps_url = (
                "https://www.google.com/maps/"
                f"search/?api=1&query="
                f"{store.get('title', '')}"
                f"&query_place_id="
                f"{place_id}"
            )

        else:

            maps_url = (
                "https://www.google.com/maps/"
                "search/?api=1&query="
                f"{store.get('title', '')}"
            )

        st.link_button(
            "🗺️ Get Directions",
            maps_url
        )


# ============================================================
# FIND BEST PRICES
# ============================================================

st.divider()

if st.button(
    "🔎 Find Best Prices",
    use_container_width=True
):

    if product and location:

        with st.spinner(
            "🔎 Searching prices..."
        ):

            results = search_product_prices(
                product,
                location
            )

        # ----------------------------------------------------
        # CONDITION FILTER
        # ----------------------------------------------------

        if condition != "Any":

            filtered_results = []

            for item in results:

                title = str(
                    item.get(
                        "title",
                        ""
                    )
                ).lower()

                if condition.lower() in title:

                    filtered_results.append(
                        item
                    )

            # Keep original results if filter
            # would otherwise remove everything
            if filtered_results:

                results = filtered_results


        # ----------------------------------------------------
        # BUDGET FILTER
        # ----------------------------------------------------

        if budget > 0:

            budget_results = []

            for item in results:

                price = item.get(
                    "extracted_price"
                )

                try:

                    price = float(price)

                    if price <= budget:

                        budget_results.append(
                            item
                        )

                except Exception:

                    pass

            if budget_results:

                results = budget_results


        # ----------------------------------------------------
        # DEAL SCORE
        # ----------------------------------------------------

        for item in results:

            item["deal_score"] = (
                calculate_deal_score(item)
            )


        # ----------------------------------------------------
        # PRIORITY SORTING
        # ----------------------------------------------------

        if priority == "Lowest Price":

            results.sort(
                key=lambda x:
                x.get(
                    "extracted_price",
                    float("inf")
                )
                if isinstance(
                    x.get("extracted_price"),
                    (int, float)
                )
                else float("inf")
            )

        elif priority == "Best Overall Deal":

            results.sort(
                key=lambda x:
                x.get(
                    "deal_score",
                    0
                ),
                reverse=True
            )

        elif priority == "Best Rating":

            results.sort(
                key=lambda x:
                x.get(
                    "rating",
                    0
                )
                if isinstance(
                    x.get("rating"),
                    (int, float)
                )
                else 0,
                reverse=True
            )

        elif priority == "Nearest Store":

            # Online shopping results don't
            # necessarily have distance.
            # Keep results in SerpApi order.
            pass


        st.session_state.priced_results = (
            results
        )

    else:

        st.warning(
            "⚠️ Please enter both product "
            "and location."
        )


# ============================================================
# PRICE RESULTS
# ============================================================

priced_results = (
    st.session_state.priced_results
)


if priced_results:

    st.divider()

    st.subheader(
        "💰 Best Price Results"
    )

    # --------------------------------------------------------
    # DISPLAY PRODUCTS
    # --------------------------------------------------------

    for item in priced_results:

        st.markdown("---")

        title = item.get(
            "title",
            "Product"
        )

        st.subheader(
            f"🛍️ {title}"
        )

        source = item.get(
            "source"
        )

        if source:

            st.write(
                f"🏪 **Store:** {source}"
            )

        price = item.get(
            "price"
        )

        extracted_price = item.get(
            "extracted_price"
        )

        if price:

            st.write(
                f"💰 **Price:** {price}"
            )

        elif extracted_price is not None:

            st.write(
                f"💰 **Price:** "
                f"₹{extracted_price:,.0f}"
            )

        rating = item.get(
            "rating"
        )

        if rating:

            st.write(
                f"⭐ **Rating:** {rating}/5"
            )

        review_count = item.get(
            "reviews"
        )

        if review_count:

            st.write(
                f"💬 **Reviews:** "
                f"{review_count}"
            )

        deal_score = item.get(
            "deal_score"
        )

        if deal_score:

            st.write(
                f"🎯 **Deal Score:** "
                f"{deal_score}/100"
            )

        # ----------------------------------------------------
        # VISIT WEBSITE BUTTON
        # ----------------------------------------------------

        product_link = item.get(
            "link"
        )

        if product_link:

            st.link_button(
                "🌐 Visit Website",
                product_link
            )

        else:

            st.info(
                "🌐 Website link is not "
                "available for this result."
            )


    # ========================================================
    # BEST ONLINE PRICE
    # ========================================================

    st.divider()

    st.subheader(
        "🏆 Best Online Price"
    )

    valid_prices = []

    for item in priced_results:

        price = item.get(
            "extracted_price"
        )

        try:

            price = float(price)

            valid_prices.append(
                (price, item)
            )

        except Exception:

            pass


    if valid_prices:

        valid_prices.sort(
            key=lambda x: x[0]
        )

        best_price, best_item = (
            valid_prices[0]
        )

        st.success(
            f"🏆 Best Price: "
            f"₹{best_price:,.0f}"
        )

        if best_item.get(
            "source"
        ):

            st.write(
                f"?