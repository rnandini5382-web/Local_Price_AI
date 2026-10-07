import streamlit as st
from serpapi import GoogleSearch


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
        st.error(f"SerpApi error: {results['error']}")
        return []

    return results.get("local_results", [])

def calculate_deal_score(price, rating, reviews):
    score = 0

    if price is not None:
        score += 50

    if rating is not None:
        score += (rating / 5) * 30

    if reviews is not None:
        if reviews >= 1000:
            score += 20
        elif reviews >= 500:
            score += 15
        elif reviews >= 100:
            score += 10
        else:
            score += 5

    return round(score, 2)

st.title("🛍️ Local Price Finder AI")

st.write(
    "Compare online prices and discover nearby local stores."
)


product = st.text_input(
    "What product are you looking for?",
    placeholder="Example: iPhone 15 128GB"
)

location = st.text_input(
    "Enter your location",
    placeholder="Example: Hyderabad"
)


if st.button("🔎 Find Best Prices"):

    if product and location:

        with st.spinner("🔎 Searching for prices..."):

            results = search_products(
                product,
                location
            )

        if results:

            st.success(
                f"Found {len(results)} online results! 🎉"
            )

            priced_results = [
                item
                for item in results
                if isinstance(
                    item.get("extracted_price"),
                    (int, float)
                )
            ]

            if priced_results:

                best_deal = min(
                    priced_results,
                    key=lambda x: x["extracted_price"]
                )

                st.subheader("🏆 Best Online Price")

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

            st.divider()

            st.subheader("📊 Online Price Comparison")

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


st.divider()

st.subheader("📍 Nearby Local Stores")
st.subheader("🤖 Smart Deal Recommendation")

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

    try:
        best_rating = float(best_rating)
    except:
        best_rating = None

    try:
        best_reviews = int(best_reviews)
    except:
        best_reviews = None

    deal_score = calculate_deal_score(
        best_price,
        best_rating,
        best_reviews
    )

    st.success(
        "🏆 Best Deal Recommendation"
    )

    st.write(
        f"🛍️ **Product:** "
        f"{best_item.get('title', 'Unknown Product')}"
    )

    st.write(
        f"💰 **Price:** "
        f"{best_item.get('price', 'N/A')}"
    )

    st.write(
        f"🏪 **Store:** "
        f"{best_item.get('source', 'Unknown Store')}"
    )

    st.metric(
        "🏆 Deal Score",
        f"{deal_score}/100"
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
            "⚠️ Consider comparing more options."
        )

else:

    st.info(
        "🤖 Not enough price information "
        "to calculate a deal score."
    )


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