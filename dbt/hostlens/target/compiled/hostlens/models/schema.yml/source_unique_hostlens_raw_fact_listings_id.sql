
    
    

select
    id as unique_field,
    count(*) as n_records

from "hostlens"."hostlens_raw"."fact_listings"
where id is not null
group by id
having count(*) > 1


