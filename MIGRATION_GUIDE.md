# Migration Guide for Developers

## When You Merge Main Into Your Branch

If you merge `main` into your feature branch and it includes new migrations, follow these steps:

### Step 1: Pull the latest changes
```bash
git checkout your-branch
git merge main
```

### Step 2: Restart your local Docker environment
```bash
docker-compose restart backend

# Or if you want to be safe, rebuild:
docker-compose up --build backend
```

### Step 3: Verify migrations ran
```bash
docker-compose exec backend alembic current
# Should show: c03e17942bf4 (head)
```

That's it! Alembic automatically detects and runs new migrations.

---

## If You Created Your Own Migration

If you created a custom migration in your branch, you might need to merge migration histories:

### Check for migration conflicts
```bash
docker-compose exec backend alembic heads
# Should show ONE head. If it shows TWO, you have a conflict.
```

### Fix conflict with merge migration
```bash
docker-compose exec backend alembic merge -m "merge migration heads"
docker-compose restart backend
```

---

## Common Issues

### "relation already exists"
Your local database has tables but no alembic_version tracking.

**Fix:**
```bash
# Drop and recreate database
docker-compose down -v
docker-compose up --build
```

### "enum value already exists"
An enum value was manually added to your local DB.

**Fix:**
```bash
# Reset database
docker-compose down -v
docker-compose up --build
```

### "migration XYZ not found"
Your branch is missing a migration that main has.

**Fix:**
```bash
# Merge main into your branch
git merge main
docker-compose restart backend
```

---

## Best Practices

1. ✅ **Always merge main into your branch** before creating new migrations
2. ✅ **Never edit existing migration files** - create new ones instead
3. ✅ **Test migrations locally** before pushing to main
4. ✅ **Use descriptive migration messages**
5. ⚠️ **Avoid manual database changes** - always use migrations

---

## Emergency: Start Fresh

If your local database is completely broken:

```bash
# Nuclear option - wipes everything
docker-compose down -v
docker-compose up --build

# Your database will be rebuilt from scratch using all migrations
```
