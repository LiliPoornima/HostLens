
  
    
    

    create  table
      "hostlens"."main_marts"."mart_borough_pricing__dbt_tmp"
  
    as (
      -- mart_borough_pricing.sql
-- Business mart: computes per-borough pricing, availability, and demand
-- statistics. This is the primary output consumed by BI tools and the
-- Streamlit Market Overview tab.
--
-- Upstream: stg_listings (staging view)
-- Materialization: table (refreshed on dbt run)



with listings as (
    select * from "hostlens"."main_staging"."stg_listings"
),

borough_stats as (

    select
        borough,
        room_type,

        -- Volume
        count(*)                            as listing_count,
        count(distinct host_id)             as unique_host_count,

        -- Pricing
        round(avg(price_usd), 2)            as avg_price_usd,
        round(median(price_usd), 2)         as median_price_usd,
        round(percentile_cont(0.25) within group (order by price_usd), 2)
                                            as p25_price_usd,
        round(percentile_cont(0.75) within group (order by price_usd), 2)
                                            as p75_price_usd,
        round(min(price_usd), 2)            as min_price_usd,
        round(max(price_usd), 2)            as max_price_usd,
        round(stddev(price_usd), 2)         as stddev_price_usd,

        -- Occupancy & Revenue (nulls if ML pipeline hasn't run)
        round(avg(occupancy_rate), 4)       as avg_occupancy_rate,
        round(avg(estimated_annual_revenue_usd), 2)
                                            as avg_annual_revenue_usd,
        round(sum(estimated_annual_revenue_usd), 2)
                                            as total_market_revenue_usd,

        -- Demand signal (reviews as proxy)
        round(avg(review_count), 1)         as avg_reviews_per_listing,

        -- Availability
        round(avg(availability_365), 1)     as avg_availability_days,

        -- Rating quality
        round(avg(review_scores_rating), 3) as avg_rating

    from listings
    group by borough, room_type

),

ranked as (
    select
        *,
        rank() over (partition by borough order by listing_count desc)
            as room_type_rank_in_borough,
        rank() over (order by avg_price_usd desc)
            as global_price_rank
    from borough_stats
)

select * from ranked
order by borough, room_type_rank_in_borough
    );
  
  