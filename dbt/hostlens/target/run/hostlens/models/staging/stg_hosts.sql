
  
  create view "hostlens"."main_staging"."stg_hosts__dbt_tmp" as (
    

with source as (
    select
        host_id,
        host_name,
        case
            when lower(cast(host_is_superhost as varchar)) in ('t', 'true', '1') then true
            else false
        end as is_superhost,
        true as is_identity_verified,
        cast(1000 as integer) as host_tenure_days,
        cast(1 as integer) as total_listings,
        cast(null as varchar) as host_response_rate,
        cast(null as varchar) as host_acceptance_rate,
        cast(null as varchar) as host_response_time
    from dim_hosts
    where host_id is not null
)

select * from source
  );
