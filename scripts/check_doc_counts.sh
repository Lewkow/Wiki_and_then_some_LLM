#!/bin/bash

curl -s localhost:6333/collections/docs_text/points/count \
  -H 'content-type: application/json' \
  -d '{"exact": true}' | jq .

