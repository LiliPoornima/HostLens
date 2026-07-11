-- mart_host_performance.sql
-- Business mart: computes host-level performance metrics by joining the
-- staging host profile with aggregated listing performance stats.
-- Used for host segmentation, Superhost analysis, and partnership scoring.
--
-- Upstream: stg_listings, stg_hosts
-- Materialization: table (refreshed on dbt run)



with listings as (
    select * from "hostlens"."main_staging"."stg_listings"
),

hosts as (
    select * from "hostlens"."main_staging"."stg_hosts"
),

-- Aggregate listing-level metrics per host
host_listing_agg as (

    select
        host_id,

        -- Portfolio size
        count(*)                                    as total_active_listings,
        count(distinct borough)                     as boroughs_active_in,

        -- Pricing
        round(avg(price_usd), 2)                    as avg_listing_price_usd,
        round(median(price_usd), 2)                 as median_listing_price_usd,
        round(min(price_usd), 2)                    as min_listing_price_usd,
        round(max(price_usd), 2)                    as max_listing_price_usd,

        -- Demand
        sum(review_count)                           as total_reviews_received,
        round(avg(review_count), 1)                 as avg_reviews_per_listing,
        round(avg(review_scores_rating), 3)         as avg_rating,

        -- Occupancy (may be null pre-ML)
        round(avg(occupancy_rate), 4)               as avg_occupancy_rate,
        round(sum(estimated_annual_revenue_usd), 2) as total_estimated_revenue_usd,

        -- Property mix
        count(case when room_type = 'Entire home/apt' then 1 end)
                                                    as entire_home_listings,
        count(case when room_type = 'Private room' then 1 end)
                                                    as private_room_listings,

        -- Availability
        round(avg(availability_365), 1)             as avg_availability_days,

        -- Min stay policy (shorter = more demand-flexible)
        round(avg(minimum_nights), 1)               as avg_minimum_nights

    from listings
    group by host_id

),

-- Join host profile with aggregated listing metrics
joined as (

    select
        h.host_id,
        h.is_superhost,
        h.is_identity_verified,
        h.host_tenure_days,
        h.total_listings as declared_listing_count,
        h.host_response_rate,
        h.host_acceptance_rate,
        h.host_response_time,

        la.total_active_listings,
        la.boroughs_active_in,
        la.avg_listing_price_usd,
        la.median_listing_price_usd,
        la.min_listing_price_usd,
        la.max_listing_price_usd,
        la.total_reviews_received,
        la.avg_reviews_per_listing,
        la.avg_rating,
        la.avg_occupancy_rate,
        la.total_estimated_revenue_usd,
        la.entire_home_listings,
        la.private_room_listings,
        la.avg_availability_days,
        la.avg_minimum_nights,

        -- Derived host tier
        case
            when la.total_active_listings >= 10 then 'Enterprise Host'
            when la.total_active_listings >= 3  then 'Professional Host'
            when la.total_active_listings = 1   then 'Individual Host'
            else 'Multi-unit Host'
        end as host_tier,

        -- Performance score (0–100, composite metric)
        round(
            (
                coalesce(la.avg_rating / 5.0 * 40, 0)                  -- 40% weight: rating
                + coalesce(la.avg_occupancy_rate * 30, 0)               -- 30% weight: occupancy
                + case when h.is_superhost then 20 else 0 end           -- 20% weight: Superhost
                + coalesce(
                    (1 - la.avg_minimum_nights / 30.0) * 10, 0         -- 10% weight: flexibility
                  )
            ), 2
        ) as performance_score_100

    from host_listing_agg la
    left join hosts h using (host_id)

)

select *
from joined
order by total_estimated_revenue_usd desc nulls last