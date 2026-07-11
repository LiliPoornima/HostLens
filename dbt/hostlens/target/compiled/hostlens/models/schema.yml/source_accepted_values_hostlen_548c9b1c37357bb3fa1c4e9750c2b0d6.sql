
    
    

with all_values as (

    select
        neighbourhood_group_cleansed as value_field,
        count(*) as n_records

    from "hostlens"."hostlens_raw"."fact_listings"
    group by neighbourhood_group_cleansed

)

select *
from all_values
where value_field not in (
    'Manhattan','Brooklyn','Queens','Bronx','Staten Island'
)


