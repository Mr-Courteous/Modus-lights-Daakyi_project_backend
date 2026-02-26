# Backend Migration Action Plan & Summary

**Date**: January 26, 2026  
**Status**: Backend audit complete, critical fixes in progress

---

## 🎯 Mission

Convert DAAKYI backend from mock/test APIs to production-ready database-backed implementations that comply with the app architecture and provide real data integration.

---

## ✅ Completed Work

### 1. Authentication Fix (auth.py)
**What**: Converted mock login from hardcoded UAT users to database-backed
**Status**: ✅ COMPLETE

**Changes**:
- Checks database for existing users first
- Creates demo users only for recognized email addresses
- Generates session tokens and tracks last_login
- Creates organization on first demo user login

**Impact**: 
- Real users can now login properly
- Demo UAT accounts work with password validation
- Organization isolation enforced

**Files Modified**: 
- [auth.py](auth.py#L105) - mock_login function
- [server.py](server.py#L163) - mock_login endpoint updated

---

### 2. Dashboard Metrics Fix (server.py)
**What**: Removed hardcoded fallback metrics, now calculates from real data
**Status**: ✅ COMPLETE

**Changes**:
- Calculates compliance score from actual assessments
- Gets real critical findings from control_assessments
- Fetches actual AI analysis count
- Returns database calculation errors instead of fake data

**Impact**:
- Dashboard shows real metrics
- No more hardcoded values like "72.0" compliance
- Errors propagate properly instead of being hidden

**Files Modified**:
- [server.py](server.py#L216) - get_dashboard_metrics function

---

### 3. Report Templates Fix (compliance_reporting_api.py)
**What**: Converted template retrieval from hardcoded list to database query
**Status**: ✅ COMPLETE

**Changes**:
- Queries report_templates collection
- Filters by organization and template type
- Falls back to system defaults if no templates exist
- Supports custom organization templates

**Impact**:
- Templates now user-configurable
- Organization-specific customization possible
- Scalable template management

**Files Modified**:
- [compliance_reporting_api.py](compliance_reporting_api.py#L226) - get_report_templates function
- [compliance_reporting_api.py](compliance_reporting_api.py#L56) - executive_summary endpoint updated

---

### 4. Documentation Created

| Document | Purpose | Location |
|----------|---------|----------|
| BACKEND_MOCK_API_MIGRATION_GUIDE.md | Overview of all fixes and patterns | [backend/](backend/BACKEND_MOCK_API_MIGRATION_GUIDE.md) |
| IMPLEMENTATION_PATTERNS_AND_FIXES.md | Code patterns and implementation guidelines | [backend/](backend/IMPLEMENTATION_PATTERNS_AND_FIXES.md) |
| MOCK_API_AUDIT_REPORT.md | Complete audit of all mock implementations | [backend/](backend/MOCK_API_AUDIT_REPORT.md) |

---

## 🚧 Remaining Work (Priority Order)

### HIGH PRIORITY (Must Fix for MVP)

#### 1. **compliance_reporting_api.py** - 5 Endpoints (Est. 6 hrs)
**Status**: 40% complete (2/7 endpoints fixed)

**Still Need Fixing**:
- [ ] Line 386: `@router.get("/compliance-scoring/{assessment_id}")` 
  - Replace mock_scorecard with real scores from control_assessments
- [ ] Line 586: `@router.get("/audit-trail")`
  - Query audit_logs collection
- [ ] Line 844: `@router.get("/reports/{report_id}/export")`
  - Query export_jobs collection
- [ ] Line 906: `@router.get("/schedules")`
  - Query report_schedules collection
- [ ] Line 1109: `@router.get("/stakeholder-views")`
  - Query stakeholder_views collection

**Quick Fix**: Use template from IMPLEMENTATION_PATTERNS_AND_FIXES.md

**Collections Needed**:
- compliance_assessments
- report_schedules
- export_jobs
- stakeholder_views
- audit_logs

---

#### 2. **auditor_analytics_api.py** - 8 Endpoints (Est. 7 hrs)
**Status**: 0% complete (All mock)

**Issues**: Every analytics endpoint returns hardcoded mock data

**Quick Wins**:
- All need same pattern: query real collections instead of mocks
- Use audit_logs, control_assessments, evidence_files

**Collections Needed**:
- audit_logs (already exists)
- control_assessments (already exists)
- evidence_quality_scores

---

#### 3. **framework_mapper_api.py** - Framework Data (Est. 4 hrs)
**Status**: 0% complete (All mock)

**Current Issue**: 
- Line 190-279: mock_controls hardcoded dictionary
- All mappings in memory, not persisted

**Fix**:
- Create framework_mappings collection
- Store user's framework mappings
- Query instead of mock_controls dict

---

### MEDIUM PRIORITY (Can Follow Later)

#### 4. **reports_api.py** - 2-3 Endpoints (Est. 3 hrs)
#### 5. **evidence_lifecycle_api.py** - 6-7 Endpoints (Est. 4 hrs)
#### 6. **mvp1_auditor_workflow.py** - 7 Endpoints (Est. 5 hrs)
#### 7. **mvp1_analyst_workflow.py** - Multiple (Est. 4 hrs)
#### 8. **task_workflow_api.py** - 2 Endpoints (Est. 3 hrs)
#### 9. **mvp1_leadership_workflow.py** - 4+ Endpoints (Est. 4 hrs)
#### 10. **mvp1_cross_role_sync.py** - 5+ Endpoints (Est. 3 hrs)

---

## 🗄️ Database Setup Required

### Create Collections (MongoDB)

Run these commands in MongoDB:

```javascript
// Core Collections (Phase 1)
db.createCollection("compliance_assessments");
db.createCollection("report_schedules");
db.createCollection("export_jobs");
db.createCollection("stakeholder_views");
db.createCollection("framework_mappings");
db.createCollection("evidence_quality_scores");
db.createCollection("evidence_processing_jobs");

// Create Indexes for Performance
db.compliance_assessments.createIndex({assessment_id: 1, organization_id: 1});
db.report_schedules.createIndex({organization_id: 1, is_active: 1});
db.framework_mappings.createIndex({assessment_id: 1});
db.export_jobs.createIndex({user_id: 1, created_at: -1});
db.audit_logs.createIndex({organization_id: 1, timestamp: -1});
```

---

## 📋 Implementation Checklist

### For Next Session (compliance_reporting_api.py fixes)

- [ ] Read IMPLEMENTATION_PATTERNS_AND_FIXES.md
- [ ] Read MOCK_API_AUDIT_REPORT.md
- [ ] Create required MongoDB collections
- [ ] Fix compliance-scoring endpoint (Line 386)
  - [ ] Query control_assessments
  - [ ] Calculate real compliance scores
  - [ ] Test with existing assessments
- [ ] Fix audit-trail endpoint (Line 586)
  - [ ] Query audit_logs
  - [ ] Test filtering
- [ ] Fix export endpoint (Line 844)
  - [ ] Create export_jobs collection
  - [ ] Track exports
- [ ] Fix schedules endpoint (Line 906)
  - [ ] Create report_schedules collection
  - [ ] Support active/inactive filtering
- [ ] Fix stakeholder-views endpoint (Line 1109)
  - [ ] Create stakeholder_views collection
  - [ ] Support role-based filtering

### Testing After Each Fix
- [ ] Endpoint returns real database data
- [ ] Organization isolation enforced
- [ ] Error handling works (no fake fallbacks)
- [ ] Empty database handled gracefully
- [ ] Frontend tests still pass

---

## 🔄 Integration Testing (After MVP Fixes)

```bash
# 1. Start backend
cd daakyi/backend
python server.py

# 2. In another terminal, run tests
# All endpoints should return real data now:
python -m pytest tests/ -v

# 3. Verify no mock data in any response
grep -r "demo\|mock" responses.json  # Should be empty
```

---

## 📊 Progress Tracking

**Overall Completion**: ~4% (2/50+ endpoints)

| Phase | Status | Endpoints | % Complete |
|-------|--------|-----------|-----------|
| Authentication | ✅ DONE | 1/1 | 100% |
| Dashboard | ✅ DONE | 1/1 | 100% |
| Compliance Reporting | 🔄 IN PROGRESS | 2/7 | 29% |
| Auditor Analytics | ⏳ PENDING | 0/8 | 0% |
| Framework Mapping | ⏳ PENDING | 0/1 | 0% |
| Reports API | ⏳ PENDING | 0/3 | 0% |
| Evidence Lifecycle | ⏳ PENDING | 0/7 | 0% |
| MVP1 Workflows | ⏳ PENDING | 0/15 | 0% |
| **Total** | | 2/50+ | ~4% |

---

## 💡 Key Principles (Remember These!)

1. **No Hardcoded Fallback Data**
   - If database fails, throw error instead of returning fake data
   - Frontend should handle errors gracefully

2. **Organization Isolation**
   - Every query must filter by `organization_id`
   - Users can only see their org's data

3. **Real Data Only**
   - Remove every `mock_`, `demo_`, hardcoded number
   - All metrics must be calculated from data in database

4. **Proper Error Handling**
   - Log errors properly
   - Return meaningful error messages
   - Never silently return fake data

5. **Database-First Architecture**
   - Query data → Calculate metrics → Return results
   - Not: Check cache → Use mock → Then check database

---

## 🎓 Pattern Reference

### When You See This (WRONG)
```python
try:
    data = await fetch_real_data()
except:
    data = [{"id": "demo", "name": "Demo Data"}]  # ❌ WRONG
```

### Do This Instead (RIGHT)
```python
try:
    data = await fetch_real_data()
except Exception as e:
    logger.error(f"Failed to fetch: {str(e)}")
    raise HTTPException(status_code=500, detail="Failed to fetch data")
```

---

## 📞 Support Resources

- **Audit Report**: See MOCK_API_AUDIT_REPORT.md for complete list of issues
- **Implementation Guide**: See IMPLEMENTATION_PATTERNS_AND_FIXES.md for code patterns
- **Migration Guide**: See BACKEND_MOCK_API_MIGRATION_GUIDE.md for overview

---

## ⏱️ Time Estimate Summary

| Task | Est. Hours | Difficulty |
|------|-----------|------------|
| compliance_reporting API | 6 | Medium |
| auditor_analytics API | 7 | Medium |
| framework_mapper API | 4 | Easy |
| reports API | 3 | Easy |
| evidence_lifecycle API | 4 | Medium |
| mvp1_auditor_workflow | 5 | Medium |
| mvp1_analyst_workflow | 4 | Medium |
| task_workflow API | 3 | Easy |
| mvp1_leadership_workflow | 4 | Medium |
| mvp1_cross_role_sync | 3 | Easy |
| Testing & QA | 8 | High |
| **TOTAL** | **~51 hours** | |

---

## 🚀 Next Immediate Actions

1. **Review** the three documentation files created
2. **Understand** common mock patterns from IMPLEMENTATION_PATTERNS_AND_FIXES.md
3. **Create** the MongoDB collections listed above
4. **Fix** compliance_reporting_api.py starting with compliance-scoring endpoint
5. **Test** each fix immediately after implementation

---

## 📌 Remember

The goal is to make the **entire backend real and production-ready**. No more mock data, no more hardcoded values. Every endpoint should query the database and return actual organization data.

The frontend and backend are now connected. The backend must provide *real* data for the frontend to display.

**You've got this! Let's build a real product.** 💪

---

*Last Updated*: January 26, 2026  
*Next Review*: After compliance_reporting_api.py is complete  
*Status*: On track for MVP delivery
