# Admin Panel - Quick Start Guide

**⚡ 30-Second Summary for New Claude Sessions**

## What Is This?
A production-ready admin panel for Pulse that allows administrators to manage the database, monitor jobs, view logs, and manage users.

## Current Status
📋 **Planning Complete** - Full implementation plan in [ADMIN_PANEL_PLAN.md](ADMIN_PANEL_PLAN.md)
⏳ **Awaiting User Decisions** - See questions below
✅ **Ready to Implement** - All code templates prepared

## What You Need to Know

### Architecture Decisions (Already Made)
- ✅ Integrated admin panel within existing Next.js/FastAPI stack
- ✅ Three-layer auth: Admin token (env var) + User JWT + `is_admin` flag
- ✅ 3 new database tables: User extension + JobExecutionHistory + AdminAuditLog
- ✅ 30+ REST API endpoints at `/admin-panel/`
- ✅ Full React admin UI at `/app/admin/`

### User Decisions Required (Section 12 of plan)
Ask the user to decide:
1. **Admin token rotation** - How often? Manual or automated?
2. **Database restrictions** - Allow raw SQL or just table CRUD?
3. **Job scheduling** - Can admins modify schedules permanently?
4. **UI color scheme** - Different colors for admin panel?
5. **Audit retention** - How many days to keep logs?

## How to Start Implementation

### Step 1: Get Decisions
```markdown
Before I start implementing the admin panel, I need your decisions on these questions from the plan:

1. **Admin Token Rotation**: Should we rotate the ADMIN_TOKEN regularly? If so, how often?
2. **Database Operations**: Should admins be able to execute raw SQL queries, or only table-level CRUD?
3. **Job Scheduling**: Should admins be able to permanently modify job schedules, or just trigger one-off runs?
4. **UI Color Scheme**: Should the admin panel have a different color scheme (e.g., darker, more serious)?
5. **Audit Log Retention**: How many days should we keep admin action logs? (Currently planned: 90 days)

These will help me customize the implementation to your needs.
```

### Step 2: Phase 1 (2-3 days) - Database Setup
1. Read [ADMIN_PANEL_PLAN.md Section 3](ADMIN_PANEL_PLAN.md#3-database-schema-changes)
2. Copy code from [Appendix B.1](ADMIN_PANEL_PLAN.md#b1-database-models-add-to-backendappmodelspy) to `backend/app/models.py`
3. Copy code from [Appendix B.2](ADMIN_PANEL_PLAN.md#b2-config-updates-add-to-backendappconfigpy) to `backend/app/config.py`
4. Run migration commands from [Appendix B.7](ADMIN_PANEL_PLAN.md#b7-migration-commands)
5. Create first admin user with [Appendix B.8](ADMIN_PANEL_PLAN.md#b8-create-first-admin-user)

### Step 3: Phase 2 (3-4 days) - Backend API
1. Create `backend/app/utils/admin_auth.py` from [Appendix B.3](ADMIN_PANEL_PLAN.md#b3-admin-authentication-middleware-backendapputilsadmin_authpy)
2. Create `backend/app/routes/admin_panel.py` using [Section 4.2](ADMIN_PANEL_PLAN.md#42-admin-api-routes-structure)
3. Write tests from [Section 8.1](ADMIN_PANEL_PLAN.md#81-backend-tests)

### Step 4: Phase 4-5 (5-7 days) - Frontend UI
1. Update `frontend/src/lib/api.ts` from [Appendix B.5](ADMIN_PANEL_PLAN.md#b5-frontend-api-client-updates-frontendsrclibapits)
2. Create admin UI following [Section 5](ADMIN_PANEL_PLAN.md#5-frontend-implementation)
3. Write tests from [Section 8.2](ADMIN_PANEL_PLAN.md#82-frontend-tests)

## Key Files (Copy-Paste Ready)

All code templates are in **[Appendix B](ADMIN_PANEL_PLAN.md#appendix-b-complete-code-templates)**:
- B.1 - Database models
- B.2 - Config settings
- B.3 - Admin authentication middleware
- B.4 - Create admin script
- B.5 - Frontend API client updates
- B.6 - Environment variables
- B.7 - Migration commands
- B.8 - Create first admin user
- B.9 - Test commands

## Complete Checklist

**Phase 1: Database & Backend Foundation (2-3 days)**
- [ ] Add 3 fields to User model (is_admin, admin_notes, last_admin_action)
- [ ] Add JobExecutionHistory model
- [ ] Add AdminAuditLog model
- [ ] Update config.py with admin settings
- [ ] Create and run migration
- [ ] Create backend/scripts/create_admin.py
- [ ] Create first admin user
- [ ] Write auth tests

**Phase 2: Core Admin API Endpoints (3-4 days)**
- [ ] Create admin_auth.py middleware
- [ ] Create admin_panel.py router
- [ ] Implement dashboard endpoint
- [ ] Implement database CRUD endpoints
- [ ] Implement job management endpoints
- [ ] Implement user management endpoints
- [ ] Add audit logging to all endpoints
- [ ] Write comprehensive API tests

**Phase 3: Job Tracking & Monitoring (2 days)**
- [ ] Update all job tasks to create history records
- [ ] Implement log viewer endpoints
- [ ] System metrics endpoints
- [ ] Write tracking tests

**Phase 4: Frontend Foundation (2-3 days)**
- [ ] Admin layout and navigation
- [ ] Admin auth page
- [ ] Dashboard page
- [ ] Reusable admin components

**Phase 5: Frontend CRUD Pages (3-4 days)**
- [ ] Database browser
- [ ] User management UI
- [ ] Source management UI
- [ ] Article management UI
- [ ] Job management UI
- [ ] Write frontend tests

**Phase 6: Monitoring & Logs (2 days)**
- [ ] Log viewer UI
- [ ] Audit trail UI
- [ ] Job history UI
- [ ] Real-time job monitoring

**Phase 7: Testing & Polish (2-3 days)**
- [ ] Integration tests
- [ ] Security testing
- [ ] UI/UX polish
- [ ] Error handling
- [ ] Performance optimization

**Phase 8: Documentation & Deployment (1-2 days)**
- [ ] Admin user guide
- [ ] API docs updates
- [ ] Deployment instructions
- [ ] Production deployment

**Total: 17-23 days (3-4.5 weeks)**

## Testing Quick Commands

```bash
# Test admin auth
curl -X GET http://localhost:8000/admin-panel/dashboard \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "X-Admin-Token: $ADMIN_TOKEN"

# Run backend tests
docker-compose exec backend pytest tests/routes/test_admin_panel.py -v

# Run frontend tests
npm test -- admin
```

## Reference Links
- **Full Plan**: [ADMIN_PANEL_PLAN.md](ADMIN_PANEL_PLAN.md)
- **Timeline**: [Section 10](ADMIN_PANEL_PLAN.md#10-implementation-timeline)
- **Code Templates**: [Appendix B](ADMIN_PANEL_PLAN.md#appendix-b-complete-code-templates)
- **Open Questions**: [Section 12](ADMIN_PANEL_PLAN.md#12-open-questions--decisions-needed)

---

**Ready to implement?** Start with Phase 1 after getting user decisions!
