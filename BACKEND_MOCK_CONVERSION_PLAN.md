# Backend API Mock-to-Real Conversion Plan

## Overview
This document outlines the plan to convert mock/hardcoded implementations in the DAAKYI backend to real database-backed operations while maintaining the app's multi-tenant, role-based architecture.

## Critical Issues Identified

### 1. **Mock Login Endpoint** (CRITICAL)
- **File**: `server.py` line 162, `auth.py` line 115
- **Issue**: Hardcoded UAT users instead of querying actual database
- **Impact**: Cannot authenticate real users created in database
- **Fix**: Query database for users, validate credentials properly
- **Files to modify**: `auth.py`, `server.py`

### 2. **Hardcoded Dashboard Metrics** (HIGH)
- **File**: `server.py` lines 239-304
- **Issue**: Fallback metrics returning fixed demo data instead of actual counts
- **Impact**: Dashboard shows fake data even when real data exists in database
- **Fix**: Calculate metrics from actual assessments, controls, evidence data
- **Files to modify**: `server.py`

### 3. **Mock Compliance Reporting Data** (HIGH)
- **File**: `compliance_reporting_api.py` multiple endpoints
- **Issue**: Multiple endpoints returning hardcoded demo data
- **Impact**: Reports don't reflect actual compliance status
- **Files to modify**: `compliance_reporting_api.py`

### 4. **Mock Assessment Templates** (MEDIUM)
- **File**: `assessment_templates_api.py` line 41, 211, 469, 588
- **Issue**: Template data hardcoded instead of fetched from database
- **Impact**: Cannot create/manage custom templates
- **Files to modify**: `assessment_templates_api.py`

### 5. **Mock Evidence Linkage** (MEDIUM)
- **File**: `evidence_linkage_api.py` lines 379, 394, 595, 633
- **Issue**: Evidence validation and suggestions are mocked
- **Impact**: Evidence linking doesn't use actual data
- **Files to modify**: `evidence_linkage_api.py`

### 6. **Mock Framework Mapper Data** (MEDIUM)
- **File**: `framework_mapper_api.py` line 190
- **Issue**: Framework mapping suggestions are hardcoded
- **Impact**: Control-to-control mappings don't use actual data
- **Files to modify**: `framework_mapper_api.py`

### 7. **Mock AI Gap Analysis** (MEDIUM)
- **File**: `ai_gap_analysis_api.py` line 388
- **Issue**: Readiness calculations use placeholder logic
- **Impact**: Gap analysis doesn't reflect actual state
- **Files to modify**: `ai_gap_analysis_api.py`

### 8. **Mock Reports Analytics** (MEDIUM)
- **File**: `reports_api.py` line 117, 401
- **Issue**: Analytics data is hardcoded demo data
- **Impact**: Report statistics are fake
- **Files to modify**: `reports_api.py`

## Architecture Principles

All conversions must follow these principles:

### 1. **Multi-Tenancy**
- All queries filter by `current_user.organization_id`
- No cross-organization data leaks
- Example: `{"organization_id": current_user.organization_id}`

### 2. **Role-Based Access Control**
- Check `current_user.role` and `current_user.permissions` before returning data
- Audit-log sensitive operations
- Example: Only admins can see other users' data

### 3. **Database-First Approach**
- Query MongoDB for actual data
- Remove all hardcoded demo data
- Provide fallback only for system-level statuses, not data

### 4. **Error Handling**
- Return proper HTTP status codes
- Log errors for debugging
- Don't expose sensitive information in error messages

### 5. **Performance**
- Use efficient queries with proper indexing
- Count documents instead of fetching all for statistics
- Cache results when appropriate (not in MVP phase)

## Implementation Order

Priority order (do these first):

1. **Fix Mock Login** - Without this, nobody can login
2. **Fix Dashboard Metrics** - Users see data on first visit
3. **Fix User Management** - Admins need to manage users
4. **Fix Assessment APIs** - Core functionality
5. **Other Endpoints** - As needed

## Key Database Collections

```
Users: mvp1_users (for MVP1) or users (for Phase 1)
- Fields: id, email, password_hash, role, permissions, status, organization_id, ...

Organizations: organizations or mvp1_organizations
- Fields: id, name, industry, size, ...

Assessments: assessments
- Fields: id, organization_id, title, status, created_by, assigned_team, due_date, ...

Evidence: evidence_files
- Fields: id, assessment_id, file_name, status, processing_status, ...

Controls: controls or nist_controls
- Fields: id, framework, control_id, description, status, ...

Compliance Data: compliance_scores, gaps, remediation_tasks
- Fields: organization_id, framework, score, gaps, ...
```

## Implementation Checklist

- [ ] Fix mock login (auth.py, server.py)
- [ ] Fix dashboard metrics (server.py)
- [ ] Fix user management endpoints (mvp1_user_management_api.py)
- [ ] Fix assessment endpoints (server.py, assessment_api.py)
- [ ] Fix evidence endpoints (server.py, evidence_service.py)
- [ ] Fix compliance reporting (compliance_reporting_api.py)
- [ ] Fix assessment templates (assessment_templates_api.py)
- [ ] Fix evidence linkage (evidence_linkage_api.py)
- [ ] Fix framework mapper (framework_mapper_api.py)
- [ ] Fix AI gap analysis (ai_gap_analysis_api.py)
- [ ] Fix reports analytics (reports_api.py)
- [ ] Test all endpoints with real data
- [ ] Update frontend to use new real endpoints
- [ ] Load testing with realistic data volumes

## Testing Strategy

### Unit Tests
- Test each converted endpoint with mock database
- Verify multi-tenant isolation
- Verify role-based access

### Integration Tests
- Test with real MongoDB connection
- Create test data
- Verify data filtering and isolation

### UAT Testing
- Create test organizations
- Create users with different roles
- Verify workflows end-to-end
- Verify data doesn't leak across orgs

### UAT Credentials (For Reference)
```
Admin: admin@daakyi.com / admin123
Analyst: analyst@daakyi.com / analyst123
Auditor: auditor@daakyi.com / auditor123
Leadership: leadership@daakyi.com / leadership123
```

## Database Initialization

Before testing, ensure database has:
1. Test organizations created
2. Test users with proper roles and permissions
3. Sample assessments
4. Sample evidence files
5. Sample controls and compliance data

See `create_mvp1_org_and_admin.py` and `insert_demo_user.py` for examples.

## Notes for Implementation

1. **Session Token**: Current implementation uses session_token in localStorage. Ensure backend validates these properly.

2. **Permissions**: Check if user has needed permissions before allowing actions. Audit-log all changes.

3. **Data Validation**: Validate all input data against models using Pydantic.

4. **Async Operations**: Keep all database operations async for performance.

5. **Logging**: Log all authentication attempts, data access, and modifications for compliance.

6. **Error Messages**: Don't expose database errors to frontend; log them internally and return generic messages.

## Success Criteria

- All endpoints return real data from database
- No hardcoded demo/mock values in production paths
- Multi-tenant isolation verified
- Role-based access control enforced
- All authenticated endpoints require valid session
- Audit logging captures all important actions
- Performance acceptable with test data

## Timeline

- **Phase 1 (Critical)**: Mock login, dashboard, user management - 2-3 days
- **Phase 2 (Core)**: Assessments, evidence, frameworks - 3-4 days
- **Phase 3 (Features)**: Reports, analytics, linkage - 2-3 days
- **Phase 4 (Polish)**: Testing, optimization, documentation - 2-3 days

**Total Estimated Time**: 10-15 days

---

See specific implementation files for detailed changes:
- `BACKEND_MOCK_FIX_AUTH.md` - Authentication fixes
- `BACKEND_MOCK_FIX_DASHBOARD.md` - Dashboard metrics fixes
- `BACKEND_MOCK_FIX_OTHER.md` - Other endpoint fixes
