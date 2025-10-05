# Copilot Plan: Add `name` to `/auth/me` Response

## Goal
Ensure the backend `/auth/me` endpoint returns the user's `name` field so the frontend can display it in the Navbar.

## Steps

1. **Identify Backend Stack and Auth Implementation**
   - Confirm backend framework (likely FastAPI or Flask based on structure).
   - Locate authentication logic and `/auth/me` route.

2. **Read Key Files for Context**
   - `backend/app/routes.py` (likely contains route definitions)
   - `backend/app/models.py` (user model definition)
   - `backend/app/services/` (auth/user service logic)
   - `backend/app/database.py` (DB session/ORM setup)

3. **Update `/auth/me` Endpoint**
   - Ensure the endpoint fetches and returns the user's `name`.
   - Update response schema if needed.

4. **Test the Endpoint**
   - Use curl or test client to verify `name` is present in response.

5. **Confirm Frontend Integration**
   - Ensure frontend displays the name once backend is fixed.

## Next Actions
- Read the files listed above to gather implementation details.
- Update this plan with findings and implementation steps.
