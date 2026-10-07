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

       