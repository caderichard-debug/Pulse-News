# Deployment Strategy

## You Need TWO Separate Deployments

**Why?** Render deploys the latest commit on the branch. If you remove FORCE_REBUILD before merging, the rebuild won't happen.

---

## Deployment 1: Force Rebuild (⚠️ WIPES DATABASE)

This merges your current branch to main with `FORCE_REBUILD=true`, triggering a complete database reset.

```bash
# Make sure you're on fix/enum-fix branch
git checkout fix/enum-fix

# Merge to main and push
git checkout main
git merge fix/enum-fix
git push origin main

# ⏳ Wait for Render to deploy (check logs for "🔥 FORCE_REBUILD=true detected")
```

---

## Deployment 2: Remove FORCE_REBUILD (REQUIRED!)

**⚠️ DO THIS IMMEDIATELY** after Deployment 1 succeeds, or every future deployment will wipe your database!

### Step 1: Remove the flag from render.yaml

Edit [render.yaml](render.yaml) and **delete** these lines:

```yaml
      - key: FORCE_REBUILD
        value: "true"
```

### Step 2: Commit directly to main

```bash
# On main branch
git add render.yaml
git commit -m "Remove FORCE_REBUILD flag after successful rebuild"
git push origin main

# ✅ This triggers Deployment 2 with normal migrations
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
