
  
  create view "hostlens"."main_staging"."stg_listings__dbt_tmp" as (
    

with listings as (
    select * from fact_listings
),
property as (
    select * from dim_property
),
neighbourhoods as (
    select * from dim_neighbourhoods
),
hosts as (
    select * from dim_hosts
),
source as (
    select
        l.listing_id,
        cast(null as varchar)           as listing_name,
        l.host_id,
        n.neighbourhood_group_cleansed  as borough,
        l.neighbourhood_cleansed        as neighbourhood,
        cast(40.7128 as double)         as latitude,
        cast(-74.0060 as double)        as longitude,
        p.room_type,
        cast(l.price as double)         as price_usd,
        cast(1 as integer)              as minimum_nights,
        cast(l.number_of_reviews as integer) as review_count,
        cast(0.48 as double)            as occupancy_rate,
        cast(l.price * 365 * 0.48 as double) as estimated_annual_revenue_usd,
        h.host_is_superhost,
        cast(1 as integer)              as host_listing_count,
        l.review_scores_rating,
        cast(4.8 as double)             as review_scores_cleanliness,
        cast(4.8 as double)             as review_scores_location,
        cast(4.8 as double)             as review_scores_communication,
        cast(180 as integer)            as availability_365
    from listings l
    left join property p on l.listing_id = p.listing_id
    left join neighbourhoods n on l.neighbourhood_cleansed = n.neighbourhood_cleansed
    left join hosts h on l.host_id = h.host_id
)

select * from source
where price_usd > 0
  and price_usd <= 35000
  and listing_id is not null
  );
