-- HostLens SQL Analytics Queries
-- These queries run against the star schema populated in DuckDB

-- 1. Average price by neighbourhood (Top 15 most expensive)
SELECT
    neighbourhood_cleansed,
    ROUND(AVG(price), 2) AS average_price,
    COUNT(*) AS listing_count
FROM fact_listings
GROUP BY neighbourhood_cleansed
HAVING COUNT(*) >= 5
ORDER BY average_price DESC
LIMIT 15;


-- 2. Top 10 hosts by number of listings
SELECT
    f.host_id,
    h.host_name,
    h.host_is_superhost,
    COUNT(*) AS listing_count
FROM fact_listings f
JOIN dim_hosts h ON f.host_id = h.host_id
GROUP BY f.host_id, h.host_name, h.host_is_superhost
ORDER BY listing_count DESC
LIMIT 10;


-- 3. Average rating by room type
SELECT
    p.room_type,
    ROUND(AVG(f.review_scores_rating), 2) AS average_rating,
    COUNT(*) AS listing_count
FROM fact_listings f
JOIN dim_property p ON f.listing_id = p.listing_id
GROUP BY p.room_type
ORDER BY average_rating DESC;


-- 4. Most reviewed neighbourhoods (Top 10)
SELECT
    neighbourhood_cleansed,
    SUM(number_of_reviews) AS total_reviews,
    ROUND(AVG(review_scores_rating), 2) AS average_rating
FROM fact_listings
GROUP BY neighbourhood_cleansed
ORDER BY total_reviews DESC
LIMIT 10;


-- 5. Estimated annual revenue and listing density by neighbourhood group (borough)
SELECT
    n.neighbourhood_group_cleansed AS borough,
    COUNT(*) AS listing_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_listings), 2) AS percent_of_listings,
    ROUND(AVG(f.price), 2) AS average_price,
    ROUND(SUM(f.price * f.reviews_per_month * 12 * 0.7), 2) AS estimated_annual_revenue_millions
FROM fact_listings f
JOIN dim_neighbourhoods n ON f.neighbourhood_cleansed = n.neighbourhood_cleansed
GROUP BY n.neighbourhood_group_cleansed
ORDER BY listing_count DESC;