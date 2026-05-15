-- Highest value customers.
SELECT
    customer_id,
    name,
    segment,
    country,
    total_orders,
    ROUND(lifetime_value, 2) AS lifetime_value,
    first_order_date,
    last_order_date
FROM mart_customer_lifetime_value
ORDER BY lifetime_value DESC;

-- Segment performance.
SELECT
    segment,
    orders,
    customers,
    ROUND(net_revenue, 2) AS net_revenue,
    ROUND(average_order_value, 2) AS average_order_value
FROM mart_segment_performance
ORDER BY net_revenue DESC;
