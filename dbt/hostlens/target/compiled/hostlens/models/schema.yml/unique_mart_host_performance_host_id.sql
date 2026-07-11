
    
    

select
    host_id as unique_field,
    count(*) as n_records

from "hostlens"."main_marts"."mart_host_performance"
where host_id is not null
group by host_id
having count(*) > 1


