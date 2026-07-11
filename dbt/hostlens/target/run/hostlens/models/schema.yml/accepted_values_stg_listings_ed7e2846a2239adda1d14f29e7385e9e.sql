
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        borough as value_field,
        count(*) as n_records

    from "hostlens"."main_staging"."stg_listings"
    group by borough

)

select *
from all_values
where value_field not in (
    'Manhattan','Brooklyn','Queens','Bronx','Staten Island'
)



  
  
      
    ) dbt_internal_test