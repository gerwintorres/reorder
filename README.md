# reorder

API that estimates weekly demand per product from its sales history. Each estimate includes the rule that was applied and the values used to compute it: average, filtered standard deviation and service-level factor.

Work in progress. The estimate endpoint is live; the database and user accounts come next.

## Try it

```bash
curl -s -X POST https://reorder-873158321037.us-central1.run.app/api/v1/estimate/preview \
  -H 'Content-Type: application/json' \
  -d '{
    "sku": "A-100",
    "points": [
      {"week_start": "2026-03-30", "qty": 4},  {"week_start": "2026-04-06", "qty": 4},
      {"week_start": "2026-04-13", "qty": 4},  {"week_start": "2026-04-20", "qty": 12},
      {"week_start": "2026-04-27", "qty": 12}, {"week_start": "2026-05-04", "qty": 12},
      {"week_start": "2026-05-11", "qty": 16}, {"week_start": "2026-05-18", "qty": 20},
      {"week_start": "2026-05-25", "qty": 20}, {"week_start": "2026-06-01", "qty": 24},
      {"week_start": "2026-06-08", "qty": 40}, {"week_start": "2026-06-15", "qty": 52},
      {"week_start": "2026-06-22", "qty": 104}
    ],
    "abc": "A", "rotation": "medium",
    "last_sale_date": "2026-06-24", "cutoff_date": "2026-06-29"
  }'
```

The three one-off spikes (40, 52, 104) stay out of the standard deviation, so they don't inflate the safety margin:

```json
{
  "sku": "A-100",
  "demand": 37,
  "rule": "statistical_base",
  "reason": "Average 24.92, k 1.64, std 7.25.",
  "avg": 24.923076923076923,
  "std": 7.254117604658903,
  "k": 1.64,
  "base_demand": 37,
  "efficiency": 0.7692307692307693,
  "q1": 12.0,
  "q3": 24.0,
  "ceiling": 36.0,
  "excluded": [40, 52, 104]
}
```

Interactive docs: https://reorder-873158321037.us-central1.run.app/docs

The first request after a period without traffic can take a few seconds.

## License

MIT. See [LICENSE](LICENSE).
