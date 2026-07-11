
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with child as (
    select listing_id as from_field
    from "hostlens"."main_staging"."stg_reviews"
    where listing_id is not null
),

parent as (
    select listing_id as to_field
    from "hostlens"."main_staging"."stg_listings"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null



  
  
      
    ) dbt_internal_test