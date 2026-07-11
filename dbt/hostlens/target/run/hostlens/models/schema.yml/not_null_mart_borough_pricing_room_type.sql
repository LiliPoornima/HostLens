
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select room_type
from "hostlens"."main_marts"."mart_borough_pricing"
where room_type is null



  
  
      
    ) dbt_internal_test