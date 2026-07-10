-- Section 3.4: Data Modeling
-- Task: Create dimension tables

CREATE TABLE dim_hosts (
    host_id BIGINT PRIMARY KEY,
    host_name VARCHAR(255),
    host_is_superhost VARCHAR(10),
    host_location VARCHAR(255)
);

CREATE TABLE dim_neighbourhoods (
    neighbourhood_cleansed VARCHAR(255) PRIMARY KEY,
    neighbourhood_group_cleansed VARCHAR(255)
);

CREATE TABLE dim_property (
    listing_id BIGINT PRIMARY KEY,
    property_type VARCHAR(255),
    room_type VARCHAR(255),
    bedrooms FLOAT,
    beds FLOAT
);

CREATE TABLE dim_reviews (
    listing_id BIGINT PRIMARY KEY,
    first_review DATE,
    last_review DATE
);

CREATE TABLE fact_listings (
    listing_id BIGINT PRIMARY KEY,
    host_id BIGINT,
    neighbourhood_cleansed VARCHAR(255),
    price FLOAT,
    number_of_reviews INT,
    review_scores_rating FLOAT,
    reviews_per_month FLOAT,
    total_reviews INT,

    FOREIGN KEY (host_id)
        REFERENCES dim_hosts(host_id),

    FOREIGN KEY (neighbourhood_cleansed)
        REFERENCES dim_neighbourhoods(neighbourhood_cleansed)
);