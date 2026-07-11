
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select id
from "hostlens"."hostlens_raw"."fact_listings"
where id is null



  
  
      
    ) dbt_internal_test