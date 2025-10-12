# Post-Deployment Checklist

## After Next Deployment (with FORCE_REBUILD=true)

**IMPORTANT**: Once the next deployment completes successfully, you MUST remove the FORCE_REBUILD flag:

### Step 1: Remove FORCE_REBUILD from render.yaml

Edit [render.yaml](render.yaml) and **delete** these lines:

```yaml
      - key: FORCE_REBUILD
        value: "true"
```

### Step 2: Commit and Push

```bash
git add render.yaml
git commit -m "Remove FORCE_REBUILD flag after successful deployment"
git push
```

### Why This Matters

- `FORCE_REBUILD=true` drops ALL tables and rebuilds the database from scratch
- This should **ONLY** happen once to clean up the production database
- If left enabled, every deployment will wipe your production data!
- After the first rebuild, all future deployments will use normal migrations

### Verification

After removing the flag, the next deployment should show:
```
Alembic version tracking exists (current: ...)
Running normal migration upgrade...
```

Instead of:
```
🔥 FORCE_REBUILD=true detected - This will drop all tables!
```

---

## Normal Deployment Process (After Initial Rebuild)

Once FORCE_REBUILD is removed, deployments will:

1. ✅ Check existing Alembic version
2. ✅ Run only new migrations (incremental updates)
3. ✅ Preserve all existing data
4. ✅ Seed any missing reference data (sources, topics, frameworks)
5. ✅ Start the server
6. ✅ Trigger initial jobs only if database is empty

This is the standard, safe deployment process you'll use going forward.
