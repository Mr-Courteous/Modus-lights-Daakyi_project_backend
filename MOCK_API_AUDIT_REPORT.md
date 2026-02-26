# Complete Backend Mock API Audit Report

Generated: January 26, 2026  
Status: 2/50+ endpoints fixed, 48+ remaining

---

## Summary Statistics

| Category | Count | Fixed | Remaining |
|----------|-------|-------|-----------|
| API Files | 25+ | 2 | 23+ |
| Mock Endpoints | 50+ | 2 | 48+ |
| Lines of Mock Code | ~2000 | 200 | ~1800 |

---

## File-by-File Breakdown

### ✅ FIXED

#### 1. **auth.py** (1 fix)
- ✅ Line 115: `mock_login()` - Now queries database, creates demo users only for known emails
- **Impact**: Real user login now working with organization creation

#### 2. **server.py** (1 fix)  
- ✅ Line 216: `/dashboard/metrics` - Removed hardcoded fallback metrics, calculates from real data
- **Impact**: Dashboard shows actual assessment metrics, not hardcoded values

---

### 🚧 HIGH PRIORITY - REMAINING

#### 3. **compliance_reporting_api.py** (8 mock sections)
**File Size**: 1413 lines | **Mock Data**: ~400 lines

**Remaining Issues:**

1. **Line 386-544**: `@router.get("/compliance-scoring/{assessment_id}")`
   - Returns: Hardcoded mock_scorecard
   - Fix: Query `control_assessments` collection
   - Impact: Compliance scores not calculated from real controls

2. **Line 586-728**: `@router.get("/audit-trail")`  
   - Returns: Hardcoded mock_audit_trail with 20 fake entries
   - Fix: Query `audit_logs` collection
   - Impact: Audit trail shows demo data, not real actions

3. **Line 844-900**: `@router.get("/reports/{report_id}/export")`
   - Returns: Mock export_status
   - Fix: Query `export_jobs` collection
   - Impact: Export requests not tracked in database

4. **Line 906-1050**: `@router.get("/schedules")`
   - Returns: Hardcoded mock_schedules (5 fake entries)
   - Fix: Query `report_schedules` collection
   - Impact: Scheduled reports not persisted

5. **Line 1109-1217**: `@router.get("/stakeholder-views")`
   - Returns: Hardcoded mock_views
   - Fix: Query `stakeholder_views` collection
   - Impact: Role-based views showing demo data

6. **Line 1242-1300**: Role-specific dashboard endpoints
   - Return: Hardcoded role-specific metrics
   - Fix: Calculate from real assessment data
   - Impact: Executive dashboard shows fake numbers

---

#### 4. **auditor_analytics_api.py** (8 mock sections)
**File Size**: Unknown | **Mock Data**: ~500+ lines

**Issues** (Lines):
- 92: `# Mock audit progress data`
- 170: `# Mock risk assessment data`
- 206: `# Mock evidence quality data`
- 254: `# Mock compliance gaps data`
- 338: `# Mock review timeline data`
- 372: `# Mock validation metrics`
- 438: `# Mock audit findings data`
- 472: `# Mock performance summary`

**Fix Pattern**: Replace all with database queries from:
- `audit_logs` collection
- `control_assessments` collection
- `evidence_files` collection

---

#### 5. **framework_mapper_api.py** (2-3 mock sections)
**File Size**: Unknown | **Mock Data**: ~200 lines

**Issues**:
- Line 190-279: `# Mock data for development` - mock_controls hardcoded
- Line 284-285: TODO comment about LlmChat integration
- Storage: All mappings in memory, not persisted

**Fix**: 
- Store frameworks in `framework_mappings` collection
- Implement real LLM integration or remove TODO
- Query from database instead of mock_controls dict

---

#### 6. **evidence_lifecycle_api.py** (6-7 mock sections)
**File Size**: Unknown | **Mock Data**: ~300 lines

**Issues**:
- 38: Mock lifecycle state
- 175: Mock reviews for development
- 254: Mock AI quality analysis
- 407: Mock processing results
- 439: Mock bulk operations
- 491: Mock operation status
- 620: Mock pending reviews

**Collections Needed**:
- `evidence_lifecycle_events`
- `evidence_quality_scores`
- `evidence_processing_jobs`

---

#### 7. **reports_api.py** (2-3 mock sections)
**File Size**: Unknown | **Mock Data**: ~200 lines

**Issues**:
- 117: Mock data note
- 276-326: `mock_reports` - hardcoded report list
- 401-450: `# Mock analytics data`

**Fix**: 
- Query `reports` collection
- Calculate analytics from `control_assessments`
- Implement real trending over time

---

#### 8. **tokuro_ai_engine.py** (3 sections)
**Issues**:
- 136: `_create_mock_analysis()` 
- 241-247: `_create_fallback_analysis()`
- Falls back to mock when LLM fails

**Fix**: Remove fallback or implement real logic

---

#### 9. **task_workflow_api.py** (2 mock sections)
**Issues**:
- 995: Mock integration with Phase 3A
- 1099: Mock playbook template

**Fix**: Query actual data instead of mock

---

#### 10. **mvp1_leadership_workflow.py** (4 mock sections)
**Issues**:
- 369: Mock compliance insights
- 478: Mock framework status
- 601: Mock risk heatmap
- 755: Mock report list

---

#### 11. **mvp1_auditor_workflow.py** (7 mock sections)
**Issues**:
- 115-126: Fallback to demo data (5, 12)
- 134: Mock pending reviews
- 168: Mock recent feedback
- 190: Mock analyst submissions
- 214: Mock engagement insights
- Multiple more lines with mock- prefix

---

#### 12. **mvp1_analyst_workflow.py** (mock_results)
**Issues**:
- 777-801: Returns mock_results instead of real AI results

---

#### 13. **mvp1_api.py** (multiple TODO/mock)
**Issues**:
- 660-662: TODOs for form counting, evidence counting
- 685-687: TODO for reviews, feedback, approval
- 710-712: TODO for compliance calculation

---

#### 14. **mvp1_cross_role_sync.py** (5 mock sections)
**Issues**:
- 309: Mock activity feed
- 429: Mock notifications
- 530: Mock discussion threads
- 598: Mock workflow state sync
- 635: Mock collaboration indicators

---

#### 15. **mvp1_leadership_workflow.py**

Many mock data sections replacing real calculations

---

### 📋 OTHER FILES WITH MOCK DATA

- **mvp1_admin_portal_api.py**: Lines 176, 188-190 (TODO comments for real uptime/storage)
- **mvp1_auth.py**: Line 376, 381 (Fallback organization)
- **mvp1_analyst_workflow.py**: Mock results
- **risk_intelligence_api.py**: Line 1107 (Fallback method)
- **tokuro_ai_api.py**: Line 93 (Fallback for single framework)
- **database.py**: Lines 23-25 (Fallback connection)

---

## Priority Order for Fixes

### Tier 1 (Most Critical - Affect Core Workflow)
1. **compliance_reporting_api.py** - All compliance endpoints
2. **auditor_analytics_api.py** - Audit data integrity
3. **framework_mapper_api.py** - Framework coverage calculation

### Tier 2 (High Priority - Affect Reporting)
4. **reports_api.py** - Report generation
5. **evidence_lifecycle_api.py** - Evidence tracking
6. **tokuro_ai_engine.py** - AI analysis

### Tier 3 (Medium Priority - Affect Features)
7. **mvp1_auditor_workflow.py** - Auditor workflow
8. **mvp1_analyst_workflow.py** - Analyst workflow
9. **task_workflow_api.py** - Task management

### Tier 4 (Lower Priority - Enhancement)
10. **mvp1_leadership_workflow.py** - Executive dashboard
11. **mvp1_cross_role_sync.py** - Collaboration features
12. **mvp1_api.py** - Legacy MVP APIs

---

## Required Database Collections (Full List)

### Phase 1 - Already Exist
```
users
organizations
assessments
control_assessments
evidence_files
audit_logs
```

### Phase 2 - Must Create
```
compliance_assessments
report_templates
evidence_linkage
report_schedules
export_jobs
stakeholder_views
recommendations
framework_mappings
audit_progress
compliance_gaps
evidence_quality_scores
evidence_processing_jobs
```

### Phase 3 - Optional
```
ai_analysis_results
compliance_trends
risk_assessments
activity_feeds
notifications
discussion_threads
```

---

## Database Migration Script Template

```javascript
// Create all required collections
db.createCollection("compliance_assessments");
db.createCollection("report_templates");
db.createCollection("evidence_linkage");
db.createCollection("report_schedules");
db.createCollection("export_jobs");
db.createCollection("stakeholder_views");
db.createCollection("recommendations");
db.createCollection("framework_mappings");
db.createCollection("audit_progress");
db.createCollection("compliance_gaps");
db.createCollection("evidence_quality_scores");

// Create indexes for common queries
db.compliance_assessments.createIndex({assessment_id: 1, organization_id: 1});
db.report_schedules.createIndex({organization_id: 1, is_active: 1});
db.export_jobs.createIndex({user_id: 1, created_at: -1});
db.framework_mappings.createIndex({assessment_id: 1, framework: 1});
```

---

## Implementation Timeline Estimate

| Task | Files | Est. Lines | Est. Hours |
|------|-------|-----------|-----------|
| compliance_reporting_api | 1 | 400 | 6 |
| auditor_analytics_api | 1 | 500 | 7 |
| framework_mapper_api | 1 | 200 | 4 |
| reports_api | 1 | 200 | 3 |
| evidence_lifecycle_api | 1 | 300 | 4 |
| mvp1_auditor_workflow | 1 | 400 | 5 |
| mvp1_analyst_workflow | 1 | 300 | 4 |
| task_workflow_api | 1 | 200 | 3 |
| mvp1_leadership_workflow | 1 | 300 | 4 |
| mvp1_cross_role_sync | 1 | 250 | 3 |
| **Total** | **10** | **~3200** | **~43 hours** |

---

## Recommended Fix Approach

### Phase 1 (This Session)
- [ ] Fix compliance_reporting_api.py compliance-scoring endpoint
- [ ] Fix auditor_analytics_api.py endpoints
- [ ] Fix framework_mapper_api.py mock data

### Phase 2 (Next Session)
- [ ] Fix reports_api.py
- [ ] Fix evidence_lifecycle_api.py
- [ ] Fix mvp1_auditor_workflow.py

### Phase 3 (Continuous)
- [ ] Fix remaining mvp1_*.py files
- [ ] Fix task_workflow_api.py
- [ ] Test full integration

---

## Verification Checklist

For each fix applied:
- [ ] Removed all `mock_` variable names
- [ ] Removed all `# Mock` comments (replace with real queries)
- [ ] Added `DatabaseOperations` query
- [ ] Added organization_id filter
- [ ] Added error handling (no hardcoded fallback)
- [ ] Added logging for debugging
- [ ] Tested with empty database
- [ ] Tested with real data
- [ ] No hardcoded demo numbers remain

---

## Quick Reference: Common Mock Patterns to Fix

```python
# PATTERN 1: Hardcoded Lists
# ❌ BAD:
mock_items = [{"id": "1", "name": "Demo"}]
return mock_items

# ✅ GOOD:
items = await DatabaseOperations.find_many("collection", filter)
return items

# PATTERN 2: Hardcoded Numbers
# ❌ BAD:
return {"score": 78.5, "count": 5}

# ✅ GOOD:
data = await DatabaseOperations.find_many("collection", filter)
score = calculate_score(data)
return {"score": score, "count": len(data)}

# PATTERN 3: Fallback Data
# ❌ BAD:
try:
    data = fetch_from_db()
except:
    return {"demo": "hardcoded fallback"}

# ✅ GOOD:
try:
    data = fetch_from_db()
except:
    raise HTTPException(status_code=500, detail="Failed to fetch")
```

---

## Next Steps

1. **Review** this document to understand scope
2. **Choose** Tier 1 file to start with
3. **Apply** fixes using provided patterns
4. **Test** each endpoint after fixing
5. **Create** collections in MongoDB as needed
6. **Verify** no hardcoded fallback data remains

---

*Note: All mock data locations identified. Ready for systematic migration to production.*
