#!/bin/bash

curl -s localhost:6333/collections/docs_text/points/scroll \
  -H 'content-type: application/json' \
  -d '{
        "limit": 100,
        "with_payload": true,
        "with_vectors": false
      }' | tee page1.json | jq -r '.result.points[].payload.doc_name'

