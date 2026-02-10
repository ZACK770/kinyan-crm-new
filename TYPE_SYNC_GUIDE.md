# Type Synchronization Guide

This guide explains how to keep TypeScript (frontend) and Python (backend) types in sync.

## The Problem

When frontend sends `full_name` but backend expects `name`, you get silent failures or 500 errors.
Manual synchronization is error-prone.

## Solutions Implemented

### 1. Shared Schema File (`api/schemas.py`)

All Pydantic models are defined in one place:

```python
# api/schemas.py
from pydantic import BaseModel, Field

class LeadCreate(BaseModel):
    full_name: str = Field(default="", description="שם פרטי")
    phone: str = Field(..., description="טלפון")
    # ... all fields with descriptions
```

**Usage in API endpoints:**
```python
from .schemas import LeadCreate, LeadUpdate

@router.post("/")
async def create_lead(data: LeadCreate): ...
```

### 2. Auto-Generated TypeScript Types

FastAPI automatically generates OpenAPI schema at `/openapi.json`.
We use `openapi-typescript` to convert it to TypeScript:

```bash
# Generate types
npm run types:sync

# Or manually
python scripts/generate_types.py
```

This creates `frontend/src/types/api.generated.ts` with all API types.

### 3. Type Checking

```bash
# Check all TypeScript types (without building)
npm run types:check
```

## Workflow

### When Adding/Changing an API Endpoint:

1. **Update `api/schemas.py`** - Define or modify the Pydantic model
2. **Run type generation** - `npm run types:sync` in frontend/
3. **Update frontend code** - Use the generated types
4. **Test** - TypeScript will catch mismatches at compile time

### Example: Adding a New Field

```python
# 1. Update api/schemas.py
class LeadCreate(BaseModel):
    full_name: str = ""
    phone: str
    new_field: str | None = None  # ← Add here
```

```bash
# 2. Generate types
cd frontend && npm run types:sync
```

```typescript
// 3. TypeScript now knows about new_field
const lead: components["schemas"]["LeadCreate"] = {
  phone: "0501234567",
  new_field: "value"  // ← TypeScript validates this
};
```

## File Structure

```
api/
├── schemas.py          # Source of truth for all schemas
├── leads_api.py        # Uses schemas from schemas.py
└── ...

frontend/src/types/
├── index.ts            # Manual types (for non-API types)
├── auth.ts             # Auth-specific types
└── api.generated.ts    # Auto-generated from OpenAPI ← DON'T EDIT!
```

## Best Practices

1. **Never define schemas inline** - Always use `api/schemas.py`
2. **Run `types:sync` in CI/CD** - Catch mismatches before deployment
3. **Use Field() with descriptions** - Better docs and OpenAPI schema
4. **Don't edit `api.generated.ts`** - It gets overwritten

## Alternative: Runtime Validation with Zod

For additional frontend validation, you can use Zod:

```typescript
import { z } from 'zod';

const LeadCreateSchema = z.object({
  full_name: z.string(),
  phone: z.string().min(9),
  email: z.string().email().optional(),
});

// Validates at runtime
const result = LeadCreateSchema.safeParse(formData);
if (!result.success) {
  showError(result.error.message);
}
```

## Troubleshooting

### "Property X does not exist on type Y"
- Run `npm run types:sync` to regenerate types
- Check that `api/schemas.py` has the field

### 422 Unprocessable Entity
- Frontend sending wrong field names
- Check network tab for the actual request body
- Compare with OpenAPI schema at `/docs`

### 500 Internal Server Error
- Check uvicorn logs for Python traceback
- Usually a backend bug, not a type mismatch
