-- Campaign attribution based on matching segment and campaign date windows.
SELECT
    campaign_id,
    campaign_name,
    segment,
    channel,
    ROUND(spend, 2) AS spend,
    attributed_orders,
    ROUND(attributed_revenue, 2) AS attributed_revenue,
    ROUND(roi, 4) AS roi
FROM mart_campaign_performance
ORDER BY attributed_revenue DESC;
