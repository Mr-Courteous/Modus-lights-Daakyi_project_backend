# Backend Mock API Migration Guide

## Overview
This document tracks the conversion of mock/dev endpoints in the DAAKYI backend to production-ready database-backed implementations.

## Completed Fixes ✅

### 1. **Authentication (auth.py) - FIXED**
**Status**: ✅ Converted from hardcoded UAT users to database-backed with fallback

**Changes Made**:
- Removed direct hardcoded password comparisons
- Now checks actual database for existing users first
- Falls back to creating demo UAT users only for recognized email addresses
- Create organization on first login for demo accounts
- Proper role-based permissions assignment
- Session token generation and tracking
- Last login timestamp recording

**Behavior**:
- Real users: Login via database lookup
- Demo/UAT users: Only specific emails work (admin@daakyi.com, auditor@daakyi.com, etc.)
- Strict password validation for all logins

**Location**: [auth.py](auth.py#L105)

---

### 2. **Dashboard Metrics (server.py) - FIXED**
**Status**: ✅ Removed hardcoded fallback data

**Changes Made**:
- Removed hardcoded fallback values (72.0 compliance, 5 critical findings, 127 AI analyses)
- Now calculates actual compliance from assessment records
- Gets real critical findings from control_assessments collection
- Tracks actual AI analyses from evidence_files
- Returns error instead of fake data when database unavailable
- Added framework coverage placeholder (TODO: implement real calculation)

**Location**: [server.py](server.py#L216)

---

## Remaining Work 🚧

### High Priority

#### 1. **Compliance Reporting API** (`compliance_reporting_api.py`)
**Current Issue**: Multiple endpoints return hardcoded mock data
- `/compliance/status` - Hardcoded 72.0 score and demo controls
- `/compliance/trends` - Returns fixed 6 months of generated data
- `/compliance/recommendations` - Fixed list of recommendations

**Fix Required**:
```python
# Instead of hardcoded data, query actual collections:
- compliance_assessments (store real compliance data)
- control_assessments (store control evaluation results)
- recommendations (store AI-generated recommendations)
```

#### 2. **AI Gap Analysis API** (`ai_gap_analysis_api.py`)
**Current Issue**: Returns mocked readiness calculations
- `/ai-analysis/readiness` - Returns demo percentages per NIST function
- Hardcoded gap analysis results

**Fix Required**:
```python
# Calculate from actual data:
- Map completed controls to NIST functions
- Calculate actual coverage percentages
- Store gap analysis results in collection
```

#### 3. **Assessment Templates API** (`assessment_templates_api.py`)
**Current Issue**: Templates are hardcoded instead of database-backed
- Creates templates in memory only
- Doesn't persist to database
- No separation between system templates and user templates

**Fix Required**:
```python
# Implement template persistence:
- Store templates in "assessment_templates" collection
- Implement versioning for templates
- Support template updates and retrieval
```

#### 4. **Evidence Linkage API** (`evidence_linkage_api.py`)
**Current Issue**: Linkage suggestions are mocked
- `/evidence/linkage/suggestions` - Returns hardcoded evidence links
- `POST /evidence/link-to-control` - Accepts but doesn't properly store

**Fix Required**:
```python
# Store evidence linkage properly:
- Save to evidence_linkage collection
- Track confidence scores
- Support linkage modification/deletion
```

### Medium Priority

#### 5. **Reports API** (`reports_api.py`)
**Current Issue**: Analytics data is partially mocked
- Some calculations use demo data
- Missing real data aggregation

**Fix Required**:
- Calculate real metrics from control assessments
- Use actual evidence counts
- Real compliance trending

#### 6. **Framework Mapper API** (`framework_mapper_api.py`)
**Current Issue**: Framework mappings are not persisted
- Returns hardcoded mapping suggestions
- Doesn't save to database

**Fix Required**:
- Store framework mappings in collection
- Support user-defined mappings
- Track mapping history

### Low Priority

#### 7. **AI Analysis Endpoint** (`server.py`)
**Current Issue**: Status endpoint returns demo data
- `/api/ai-analysis/{analysis_id}/status` - Returns "demo"

**Fix Required**:
- Integrate real document processing pipeline
- Update status from actual file processing
- Store actual analysis results

---

## Database Collections Required

Ensure these collections exist in MongoDB:

```javascript
// Existing (used for fixes):
db.createCollection("users")
db.createCollection("organizations")
db.createCollection("assessments")
db.createCollection("control_assessments")
db.createCollection("evidence_files")
db.createCollection("audit_logs")

// Need to implement:
db.createCollection("compliance_assessments")
db.createCollection("assessment_templates")
db.createCollection("evidence_linkage")
db.createCollection("framework_mappings")
db.createCollection("ai_analysis_results")
db.createCollection("recommendations")
db.createCollection("control_coverage")
```

---

## Architecture Patterns to Follow

### 1. **Data Flow Pattern**
```
Frontend Request
    ↓
API Endpoint (validation)
    ↓
Service Layer (business logic)
    ↓
DatabaseOperations (persistence)
    ↓
MongoDB Collections (source of truth)
```

### 2. **Error Handling Pattern**
```python
try:
    # Query database
    data = await DatabaseOperations.find_many("collection", filter)
    
    # Calculate if needed
    calculated = perform_calculation(data)
    
    return calculated
    
except SpecificDatabaseError as e:
    logger.error(f"Specific error: {str(e)}")
    # Return contextual error, NOT hardcoded fallback
    raise HTTPException(status_code=500, detail="Specific reason for failure")
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="Failed to process request")
```

### 3. **Organization Filter Pattern**
Always filter by organization to ensure data isolation:
```python
filter = {"organization_id": current_user.organization_id}
```

### 4. **Response Pattern**
Always return database data, never hardcoded fallbacks:
```python
# ✅ CORRECT:
@api_router.get("/endpoint")
async def endpoint(current_user: User = Depends(get_current_user)):
    data = await DatabaseOperations.find_many("collection", filter)
    return data

# ❌ WRONG:
@api_router.get("/endpoint")
async def endpoint(current_user: User = Depends(get_current_user)):
    try:
        data = await DatabaseOperations.find_many("collection", filter)
        return data
    except:
        return {"demo": "hardcoded fallback"}  # REMOVE THIS!
```

---

## Migration Checklist

- [x] **auth.py** - Remove hardcoded UAT password validation
- [x] **server.py** - Remove hardcoded dashboard fallback metrics
- [ ] **compliance_reporting_api.py** - Implement database-backed compliance data
- [ ] **ai_gap_analysis_api.py** - Calculate from actual control assessments
- [ ] **assessment_templates_api.py** - Persist templates to database
- [ ] **evidence_linkage_api.py** - Store linkage suggestions in database
- [ ] **reports_api.py** - Calculate analytics from real data
- [ ] **framework_mapper_api.py** - Persist framework mappings
- [ ] Test all endpoints with real database data
- [ ] Update frontend to handle empty/null responses appropriately

---

## Testing Guidelines

After each fix:
1. Clear database or use test database
2. Create test organization and assessments
3. Verify endpoint returns accurate calculated data
4. Verify edge cases (empty database, missing data)
5. Check error messages are descriptive, not generic fallbacks

---

## Related Files

- Frontend API service: `frontend/src/services/api.js`
- Main server: `backend/server.py`
- Database operations: `backend/database_ops.py`
- Models: `backend/models.py`
