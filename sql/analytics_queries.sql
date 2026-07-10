-- Average price by neighbourhood

SELECT
    neighbourhood_cleansed,
    AVG(price) AS average_price
FROM fact_listings
GROUP BY neighbourhood_cleansed
ORDER BY average_price DESC;


-- Top 10 hosts by number of listings

SELECT
    host_id,
    COUNT(*) AS listing_count
FROM fact_listings
GROUP BY host_id
ORDER BY listing_count DESC
LIMIT 10;


-- Average rating by room type

SELECT
    p.room_type,
    AVG(f.review_scores_rating) AS average_rating
FROM fact_listings f
JOIN dim_property p
    ON f.listing_id = p.listing_id
GROUP BY p.room_type
ORDER BY average_rating DESC;


-- Most reviewed neighbourhoods

SELECT
    neighbourhood_cleansed,
    SUM(number_of_reviews) AS total_reviews
FROM fact_listings
GROUP BY neighbourhood_cleansed
ORDER BY total_reviews DESC;