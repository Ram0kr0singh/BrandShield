# Frontend manual checks

## Old scan-response compatibility

1. In browser developer tools, intercept `POST /api/monitoring/scan` and return a normal scan payload with `source_warnings` omitted.
2. On the dashboard, select a protected brand and choose **Scan now**.
3. Confirm the dashboard reloads normally, no degraded-source warning is shown, and the source-status strip remains independent.

Also block `GET /api/sources/status`: the strip should show **Source status unavailable** with Retry, while the dashboard remains usable.
