# Screenshots Guide

Save the following PNG files into this folder after running the stack:

1) FastAPI Docs
   - Open: http://localhost:8000/docs
   - Save as: fastapi_docs.png

2) Upload response (terminal)
   - Run: curl -F "file=@docs/samples/receipt1.png" http://localhost:8000/api/v1/receipts/upload | jq .
   - Save as: upload_response.png

3) Analytics summary (terminal)
   - Run: curl http://localhost:8000/api/v1/analytics/summary | jq .
   - Save as: analytics_summary.png

4) Postman requests
   - Import docs/postman_collection.json
   - Save screenshot as: postman_requests.png
