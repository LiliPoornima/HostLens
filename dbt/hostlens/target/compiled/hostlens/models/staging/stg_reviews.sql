

with source as (
    select
        cast(listing_id as bigint) as review_id,
        listing_id,
        cast(null as bigint) as reviewer_id,
        try_cast(last_review as date) as review_date,
        cast(50 as integer) as comment_length_chars,
        cast('Mock review comments' as varchar) as comment_preview
    from dim_reviews
    where listing_id is not null
)

select * from source