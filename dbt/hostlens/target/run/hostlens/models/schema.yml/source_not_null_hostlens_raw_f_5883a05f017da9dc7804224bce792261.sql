
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select neighbourhood_group_cleansed
from "hostlens"."hostlens_raw"."fact_listings"
where neighbourhood_group_cleansed is null



  
  
      
    ) dbt_internal_test