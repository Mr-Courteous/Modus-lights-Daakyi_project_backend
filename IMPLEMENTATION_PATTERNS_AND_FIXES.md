# Backend API Implementation Patterns & Fixes

## Critical Implementation Guidelines

### Pattern 1: Replace Mock Data with Database Queries

**❌ WRONG - Current Mock Pattern:**
```python
@router.get("/endpoint")
async def endpoint(current_user: User = Depends(get_current_user)):
    # Mock data hardcoded
    mock_data = [
        {"id": 1, "name": "Demo Item 1"},
        {"id": 2, "name": "Demo Item 2"}
    ]
    return {"items": mock_data}
```

**✅ CORRECT - Database Pattern:**
```python
@router.get("/endpoint")
async def endpoint(current_user: User = Depends(get_current_user)):
    from database_ops import DatabaseOperations
    
    # Query real database
    items = await DatabaseOperations.find_many(
        "collection_name",
        {"organization_id": current_user.organization_id},
        sort=[("created_at", -1)]
    ) or []
    
    return {"items": items}
```

---

## Files That Need Fixes

### 1. **compliance_reporting_api.py** (Partially Fixed)
**What Was Fixed:**
- ✅ executive_summary endpoint - Now queries control_assessments
- ✅ get_report_templates endpoint - Now queries report_templates collection

**Still Needs Fixes:**
- [ ] `@router.get("/compliance-scoring/{assessment_id}")`
  - Lines ~430: Returns hardcoded mock_scorecard
  - **Fix**: Query control_assessments and calculate actual scores

- [ ] `@router.get("/audit-trail")`
  - Lines ~630: Returns mock_audit_trail
  - **Fix**: Query audit_logs collection

- [ ] `@router.get("/reports/{report_id}/export")`
  - Lines ~888: Mock export status
  - **Fix**: Query export_jobs collection

- [ ] `@router.get("/schedules")`
  - Lines ~950: Returns mock_schedules
  - **Fix**: Query report_schedules collection

- [ ] `@router.get("/stakeholder-views")`
  - Lines ~1153: Returns mock_views
  - **Fix**: Query stakeholder_views collection

### 2. **ai_gap_analysis_api.py**
**Issues:**
- Lines ~100: Hardcoded readiness percentages
- Lines ~200: Fixed gap analysis results
- Lines ~300: Demo recommendations

**Required Changes:**
```python
# Instead of:
readiness_scores = {"Identify": 78.5, "Protect": 82.3, ...}

# Do:
controls = await DatabaseOperations.find_many(
    "control_assessments",
    {"assessment_id": assessment_id, "organization_id": org_id}
)
readiness_scores = calculate_readiness_from_controls(controls)
```

### 3. **assessment_templates_api.py**
**Issues:**
- No database persistence for created templates
- Templates only exist in memory
- No versioning

**Required Implementation:**
```python
@router.post("/templates")
async def create_template(request, current_user):
    from database_ops import DatabaseOperations
    
    template_data = {
        "id": str(uuid.uuid4()),
        "name": request.name,
        "organization_id": current_user.organization_id,
        "sections": request.sections,
        "created_at": datetime.utcnow(),
        "created_by": current_user.id
    }
    
    # Save to database
    await DatabaseOperations.insert_one("assessment_templates", template_data)
    return template_data
```

### 4. **evidence_linkage_api.py**
**Issues:**
- Linkage suggestions are mocked
- Confidence scores are hardcoded
- Suggestions not persisted

**Required Implementation:**
```python
@router.get("/suggestions/{assessment_id}")
async def get_linkage_suggestions(assessment_id, current_user):
    from database_ops import DatabaseOperations
    
    # Get actual evidence files
    evidence = await DatabaseOperations.find_many(
        "evidence_files",
        {"assessment_id": assessment_id}
    )
    
    # Query or generate actual suggestions
    suggestions = await DatabaseOperations.find_many(
        "evidence_linkage_suggestions",
        {"assessment_id": assessment_id}
    )
    
    return {"suggestions": suggestions}
```

### 5. **framework_mapper_api.py**
**Issues:**
- Framework mappings not persisted
- Returns hardcoded mapping suggestions
- No user customization support

**Required Implementation:**
- Store mappings in "framework_mappings" collection
- Support create/update/delete operations
- Track mapping history

### 6. **reports_api.py**
**Issues:**
- Analytics data partially mocked
- Some metrics use demo values
- Trend data generated instead of calculated

**Required Implementation:**
- Query actual assessment data
- Calculate metrics from control assessments
- Track historical data for trends

---

## Database Collections - Implementation Order

### Phase 1 - Already Exist (Use Immediately)
```javascript
users
organizations  
assessments
control_assessments
evidence_files
audit_logs
```

### Phase 2 - Create These (High Priority)
```javascript
// For compliance reporting
db.createCollection("compliance_assessments", {
  validator: {
    $jsonSchema: {
      properties: {
        assessment_id: { bsonType: "string" },
        organization_id: { bsonType: "string" },
        control_id: { bsonType: "string" },
        status: { enum: ["Compliant", "Non-Compliant", "Partial", "Not Tested"] },
        compliance_score: { bsonType: "double" },
        findings: { bsonType: "array" }
      }
    }
  }
})

db.createCollection("report_templates", {
  validator: {
    $jsonSchema: {
      properties: {
        name: { bsonType: "string" },
        template_type: { bsonType: "string" },
        organization_id: { bsonType: "string" },
        sections: { bsonType: "array" },
        is_predefined: { bsonType: "bool" }
      }
    }
  }
})

db.createCollection("evidence_linkage", {
  validator: {
    $jsonSchema: {
      properties: {
        evidence_id: { bsonType: "string" },
        assessment_id: { bsonType: "string" },
        control_ids: { bsonType: "array" },
        confidence_score: { bsonType: "double" }
      }
    }
  }
})

db.createCollection("audit_logs", {
  validator: {
    $jsonSchema: {
      properties: {
        action: { bsonType: "string" },
        user_id: { bsonType: "string" },
        organization_id: { bsonType: "string" },
        timestamp: { bsonType: "date" },
        details: { bsonType: "object" }
      }
    }
  }
})

db.createCollection("report_schedules")
db.createCollection("export_jobs")
db.createCollection("framework_mappings")
db.createCollection("stakeholder_views")
db.createCollection("recommendations")
```

### Phase 3 - Optional (Nice to Have)
```javascript
db.createCollection("ai_analysis_results")
db.createCollection("compliance_trends")
db.createCollection("risk_assessments")
```

---

## Quick Fix Template

Use this template to fix any endpoint:

```python
# BEFORE (Mock Data)
@router.get("/endpoint")
async def endpoint(current_user: User = Depends(get_current_user)):
    mock_data = [{"id": "1", "value": "demo"}]
    return mock_data

# AFTER (Real Data)
@router.get("/endpoint")
async def endpoint(current_user: User = Depends(get_current_user)):
    from database_ops import DatabaseOperations
    
    try:
        data = await DatabaseOperations.find_many(
            "collection_name",
            {"organization_id": current_user.organization_id},
            sort=[("created_at", -1)]
        )
        return data or []
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch data")
```

---

## Validation Checklist

After fixing each endpoint:

- [ ] Removed all hardcoded "demo", "mock_" variables
- [ ] Added DatabaseOperations queries
- [ ] Filtered by organization_id for data isolation
- [ ] Added error handling without hardcoded fallbacks
- [ ] Added logging for debugging
- [ ] Tested with empty database
- [ ] Tested with real data
- [ ] Verified no hardcoded numbers or strings in response

---

## Testing Script

Create this test to verify fixes:

```python
# test_backend_fixes.py
import requests
import json

BASE_URL = "http://localhost:8000/api"

async def test_no_mock_data():
    """Verify all endpoints return real data only"""
    
    # Login
    login_response = requests.post(f"{BASE_URL}/login", json={
        "email": "admin@daakyi.com",
        "password": "admin123"
    })
    token = login_response.json()["session_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test endpoints
    endpoints = [
        "/dashboard/metrics",
        "/compliance-reporting/templates",
        "/ai-analysis/readiness",
        "/assessment/templates",
        "/evidence/linkage/suggestions",
        "/framework/mappings"
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"{endpoint}: {response.status_code}")
        
        data = response.json()
        
        # Verify no hardcoded demo data
        assert "demo" not in json.dumps(data).lower()
        assert "mock" not in json.dumps(data).lower()
        
        print(f"✅ {endpoint} - No mock data found")
```

---

## Summary

**Fixed (2/20+):**
- ✅ auth.py - Mock login
- ✅ server.py - Dashboard metrics  
- ✅ compliance_reporting_api.py - Executive summary & templates

**Remaining (18/20+):**
- [ ] compliance_reporting_api.py - Scoring, audit trail, export, schedules, views
- [ ] ai_gap_analysis_api.py - Readiness, gaps, recommendations
- [ ] assessment_templates_api.py - Template persistence
- [ ] evidence_linkage_api.py - Linkage persistence
- [ ] framework_mapper_api.py - Mapping persistence
- [ ] reports_api.py - Analytics calculation
- [ ] Other files: phase2_api.py, phase3_api.py, etc.

**Next Priority:** compliance_reporting_api.py compliance-scoring endpoint
