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
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "shopping_results",
            []
        )

        # --------------------------------------------------------
        # FAST FALLBACK LINKS
        # --------------------------------------------------------
        # Give every result a link immediately.
        # Google Product API enrichment is only done for
        # the first 3 results to keep the search fast.

        for item in results:

            item["website_link"] = (
                item.get("product_link")
                or item.get("link")
            )

            item["reviews_results"] = []

        # --------------------------------------------------------
        # ENRICH ONLY TOP 3 RESULTS
        # --------------------------------------------------------

        for item in results[:3]:

            product_id = item.get(
                "product_id"
            )

            page_token = item.get(
                "immersive_product_page_token"
            )

            if not product_id and not page_token:
                continue

            try:

                product_params = {
                    "engine": "google_product",
                    "hl": "en",
                    "gl": "in",
                    "api_key": SERPAPI_API_KEY
                }

                if page_token:

                    product_params[
                        "page_token"
                    ] = page_token

                else:

                    product_params[
                        "product_id"
                    ] = product_id

                    product_params[
                        "offer_view"
                    ] = "true"

                product_response = requests.get(
                    "https://serpapi.com/search.json",
                    params=product_params,
                    timeout=10
                )

                product_response.raise_for_status()

                product_data = (
                    product_response.json()
                )

                product_results = (
                    product_data.get(
                        "product_results",
                        {}
                    )
                )

                stores = product_results.get(
                    "stores",
                    []
                )

                source_name = str(
                    item.get("source", "")
                ).strip().lower()

                matching_store = None

                # Prefer the same store/source.
                for store in stores:

                    store_name = str(
                        store.get("name", "")
                    ).strip().lower()

                    if (
                        source_name
                        and store_name
                        and (
                            source_name
                            in store_name
                            or
                            store_name
                            in source_name
                        )
                    ):

                        matching_store = store
                        break

                # Otherwise choose the store
                # with the closest price.
                if (
                    matching_store is None
                    and stores
                ):

                    target_price = item.get(
                        "extracted_price"
                    )

                    if isinstance(
                        target_price,
                        (int, float)
                    ):

                        priced_stores = []

                        for store in stores:

                            store_price = (
                                store.get(
                                    "extracted_price"
                                )
                            )

                            if isinstance(
                                store_price,
                                (int, float)
                            ):

                                priced_stores.append(
                                    (
                                        abs(
                                            store_price
                                            - target_price
                                        ),
                                        store
                                    )
                                )

                        if priced_stores:

                            priced_stores.sort(
                                key=lambda x: x[0]
                            )

                            matching_store = (
                                priced_stores[0][1]
                            )

                if matching_store:

                    merchant_link = (
                        matching_store.get(
                            "link"
                        )
                    )

                    if merchant_link:

                        item[
                            "website_link"
                        ] = merchant_link

                # Get actual user review text
                # when the Product API provides it.
                user_reviews = (
                    product_results.get(
                        "user_reviews",
                        []
                    )
                )

                if isinstance(
                    user_reviews,
                    list
                ):

                    item[
                        "reviews_results"
                    ] = user_reviews

            except Exception:
                # Keep the already available
                # Shopping product link.
                pass

        return results

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

# ========================================================
# AI CUSTOMER REVIEW ANALYSIS
# ========================================================

st.divider()

st.subheader(
    "⭐ AI Customer Review Analysis"
)

if priced_results:

    for item in priced_results:

        title = item.get(
            "title",
            "Product"
        )

        # ------------------------------------------------
        # GET RATING
        # ------------------------------------------------

        rating = item.get(
            "rating"
        )

        review_count = item.get(
            "reviews"
        )

        # ------------------------------------------------
        # TRY ALTERNATIVE RATING FIELDS
        # ------------------------------------------------

        if rating is None:
            rating = item.get(
                "rating_score"
            )

        if review_count is None:
            review_count = item.get(
                "reviews_count"
            )

        st.markdown(
            f"### 🛍️ {title}"
        )

        # ------------------------------------------------
        # CHECK FOR ACTUAL REVIEW TEXT
        # ------------------------------------------------

        reviews_results = item.get(
            "reviews_results",
            []
        )

        review_texts = []

        if isinstance(
            reviews_results,
            list
        ):

            for review in reviews_results:

                if isinstance(
                    review,
                    dict
                ):

                    text = (
                        review.get("text")
                        or
                        review.get("content")
                        or
                        review.get("snippet")
                        or
                        review.get("review")
                    )

                    if text:
                        review_texts.append(
                            str(text)
                        )

                elif isinstance(
                    review,
                    str
                ):

                    if review.strip():
                        review_texts.append(
                            review.strip()
                        )

        # =================================================
        # LEVEL 1 — ACTUAL CUSTOMER REVIEWS
        # =================================================

        if review_texts:

            analysis = (
                analyze_customer_reviews(
                    review_texts
                )
            )

            if analysis["score"] is not None:

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "🤖 AI Review Score",
                        f'{analysis["score"]}/100'
                    )

                with col2:

                    st.metric(
                        "📊 Reviews Analyzed",
                        analysis["total"]
                    )

                st.write(
                    f'**Overall Sentiment:** '
                    f'{analysis["sentiment"]}'
                )

                col1, col2, col3 = (
                    st.columns(3)
                )

                with col1:

                    st.metric(
                        "😊 Positive",
                        analysis["positive"]
                    )

                with col2:

                    st.metric(
                        "😐 Neutral",
                        analysis["neutral"]
                    )

                with col3:

                    st.metric(
                        "👎 Negative",
                        analysis["negative"]
                    )

        # =================================================
        # LEVEL 2 — RATING BASED AI ANALYSIS
        # =================================================

        elif rating is not None:

            try:

                rating_value = float(
                    rating
                )

                # Keep rating within valid range
                rating_value = max(
                    0,
                    min(
                        rating_value,
                        5
                    )
                )

                satisfaction_score = round(
                    (
                        rating_value
                        /
                        5
                    )
                    * 100
                )

                col1, col2 = (
                    st.columns(2)
                )

                with col1:

                    st.metric(
                        "⭐ Customer Rating",
                        f"{rating_value:.1f}/5"
                    )

                with col2:

                    st.metric(
                        "🤖 AI Satisfaction Score",
                        f"{satisfaction_score}/100"
                    )

                if review_count:

                    st.write(
                        f"💬 **Based on:** "
                        f"{review_count} "
                        f"customer reviews"
                    )

                # -----------------------------------------
                # SENTIMENT
                # -----------------------------------------

                if rating_value >= 4.5:

                    sentiment = (
                        "Very Positive 😊"
                    )

                    message = (
                        "Customers appear highly "
                        "satisfied with this product."
                    )

                    st.success(
                        f"😊 **{sentiment}** — "
                        f"{message}"
                    )

                elif rating_value >= 4.0:

                    sentiment = (
                        "Positive 👍"
                    )

                    message = (
                        "Customers generally "
                        "appear satisfied with this product."
                    )

                    st.success(
                        f"👍 **{sentiment}** — "
                        f"{message}"
                    )

                elif rating_value >= 3.0:

                    sentiment = (
                        "Mixed 😐"
                    )

                    message = (
                        "Customer satisfaction "
                        "appears moderate."
                    )

                    st.warning(
                        f"😐 **{sentiment}** — "
                        f"{message}"
                    )

                else:

                    sentiment = (
                        "Negative 👎"
                    )

                    message = (
                        "The available rating "
                        "indicates lower customer satisfaction."
                    )

                    st.error(
                        f"👎 **{sentiment}** — "
                        f"{message}"
                    )

                st.info(
                    "🤖 AI Insight: "
                    "The satisfaction score is calculated "
                    "from the available customer rating. "
                    "Individual review text was not returned "
                    "by the current product data source."
                )

            except Exception:

                st.info(
                    "ℹ️ Customer rating data "
                    "could not be analyzed."
                )

        # =================================================
        # LEVEL 3 — NO REVIEW DATA
        # =================================================

        else:

            st.info(
                "ℹ️ No customer rating or review "
                "information was returned for this product."
            )

else:

    st.info(
        "🔎 Search for a product first to see "
        "customer review analysis."
    )


# ========================================================
# SMART DEAL RECOMMENDATION
# ========================================================

    # ========================================================
    # SMART DEAL RECOMMENDATION
    # ========================================================

    st.divider()

    st.subheader(
        "🤖 Smart Deal Recommendation"
    )

    if priced_results:

        best_item = priced_results[0]

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

        best_title = best_item.get(
            "title",
            "Product"
        )

        st.success(
            f"🏆 Recommended Deal: "
            f"{best_title}"
        )

        if best_price is not None:

            st.write(
                f"💰 **Price:** "
                f"₹{best_price:,.0f}"
            )

        if best_rating:

            st.write(
                f"⭐ **Rating:** "
                f"{best_rating}/5"
            )

        if best_reviews:

            st.write(
                f"💬 **Reviews:** "
                f"{best_reviews}"
            )

        st.write(
            f"🏪 **Seller:** "
            f"{best_source}"
        )

        reasons = []

        if best_price is not None:
            reasons.append(
                "competitive price"
            )

        if best_rating:

            try:

                if float(best_rating) >= 4:
                    reasons.append(
                        "strong customer rating"
                    )

            except Exception:
                pass

        if best_reviews:

            try:

                if int(best_reviews) >= 100:
                    reasons.append(
                        "good review volume"
                    )

            except Exception:
                pass

        if reasons:

            st.info(
                "💡 Recommended because of "
                + ", ".join(reasons)
                + "."
            )

        best_item_link = (
            best_item.get("website_link")
            or best_item.get("product_link")
            or best_item.get("link")
        )

        if best_item_link:

            st.link_button(
                "🛒 Buy / Visit Best Deal",
                best_item_link
            )

# FOOTER
# ============================================================

st.divider()

st.caption(
    "🛍️ Local Price Finder AI | "
    "Powered by SerpApi"
)
