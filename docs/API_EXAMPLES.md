# API examples

Start `autorag serve` after installing the project.

```bash
curl -X POST http://127.0.0.1:8000/v1/documents \
  -H 'Content-Type: application/json' \
  -d '{"documents":[{"id":"architecture-1","tenant_id":"demo","title":"Atlas and Beacon","text":"Atlas sends normalized records to Beacon. Beacon indexes these records for search.","entities":["Atlas","Beacon"],"source":"docs://architecture"}]}'

curl -X POST http://127.0.0.1:8000/v1/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"How are Atlas and Beacon connected?","tenant_id":"demo"}'
```

When `AUTORAG_API_KEY` is configured, supply `-H 'x-api-key: YOUR_KEY'`.

The response contains `answer`, `grounded`, `decision`, `hits`, `trace`, `latency_ms` and `request_id`. Run the documented Python tests to verify the exact contract for your deployment.
