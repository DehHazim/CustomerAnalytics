-- Monthly revenue and order trends.
SELECT
    order_month,
    orders,
    customers,
    ROUND(gross_revenue, 2) AS gross_revenue,
    ROUND(discounts, 2) AS discounts,
    ROUND(net_revenue, 2) AS net_revenue,
    ROUND(net_revenue / NULLIF(orders, 0), 2) AS average_order_value
FROM mart_monthly_revenue
ORDER BY order_month;

-- Revenue by product category.
SELECT
    product_category,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(net_amount), 2) AS net_revenue
FROM fact_orders
WHERE is_completed_paid = 1
GROUP BY product_category
ORDER BY net_revenue DESC;
