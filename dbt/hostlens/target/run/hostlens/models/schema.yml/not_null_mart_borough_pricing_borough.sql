
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select borough
from "hostlens"."main_marts"."mart_borough_pricing"
where borough is null



  
  
      
    ) dbt_internal_test