#!/bin/bash
# Generate TypeScript types from the FastAPI OpenAPI schema
# Run this whenever backend models/schemas change

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Generating TypeScript types from OpenAPI schema..."

# Start backend temporarily to get schema (or use saved schema)
cd "$PROJECT_ROOT/backend"

# Export OpenAPI schema to JSON
python -c "
from app.main import app
import json

openapi_schema = app.openapi()
with open('../frontend/src/types/openapi.json', 'w') as f:
    json.dump(openapi_schema, f, indent=2)
print('OpenAPI schema exported to frontend/src/types/openapi.json')
"

# Generate TypeScript types using openapi-typescript
cd "$PROJECT_ROOT/frontend"
npx openapi-typescript src/types/openapi.json -o src/types/api.generated.ts

echo "TypeScript types generated at frontend/src/types/api.generated.ts"
