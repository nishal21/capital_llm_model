---
name: fix-contribution
description: >
  Fix common issues in geographic data contributions to the CSC database.
  Use this skill whenever you need to fix, correct, repair, patch, or resolve
  issues in a data contribution or PR. Trigger on: "@copilot fix this",
  "auto-fix" label on issues, "can you fix", "please correct", "help me fix",
  "what's wrong with my PR", removing auto-managed fields, correcting country
  codes, fixing mismatched foreign keys, or formatting JSON. Also use when
  a PR has validation errors and you need to commit fixes directly.
  Read common-fixes.md in this directory for fix patterns and examples.
---

## When to Use This Skill

- A PR has validation errors and you are asked to fix them
- An issue is assigned to you with the `auto-fix` or `copilot` label
- A maintainer comments "@copilot fix this" on a PR

Before starting, read `common-fixes.md` in this skill's directory for detailed fix patterns with before/after examples.

## Fix Process

### Step 1: Identify the Issues

Read the validation report comment on the PR (posted by the PR Validator workflow). It will list specific errors and warnings categorised as:
- Schema errors (missing/invalid fields)
- Cross-reference errors (invalid state_id, country_id, mismatched codes)
- Coordinate warnings (out of bounds)
- Duplicate warnings

### Step 2: Apply Fixes

#### Missing Required Fields

For cities missing fields, look up the correct values:
- `state_id` / `state_code`: Search `states.json` by state name and country
- `country_id` / `country_code`: Search `countries.json` by country name
- `latitude` / `longitude`: If missing, leave a comment asking the contributor rather than guessing

#### Wrong Field Formats

- `country_code` not 2 chars: Look up the correct ISO2 code from `countries.json`
- Latitude/longitude out of range: Check if values are swapped or have extra digits
- Empty name: Cannot fix - ask the contributor

#### Auto-Managed Fields Present

Remove these fields from the contribution:
- `id`
- `created_at`
- `updated_at`
- `flag`

#### Mismatched References

- If `country_code` does not match `country_id`: Look up the correct code from `countries.json`
- If `state_code` does not match `state_id`: Look up the correct code from `states.json`
- If `state_id` belongs to a different country: Flag for contributor clarification

### Step 3: Commit the Fix

If you have write access to the contributor's branch:
1. Make the corrections directly in the contribution file
2. Commit with message: `fix: correct [description] in [filename]`
3. Comment on the PR explaining what was fixed and why

If you do NOT have write access:
1. Create a new branch from the PR's base branch
2. Apply the fixes
3. Open a new PR referencing the original: `fix: corrections for PR #[number]`
4. Comment on the original PR linking to your fix PR

### Step 4: Explain Changes

Always comment on the PR explaining:
- What was wrong
- What was fixed
- Source of the correct data (if applicable)
- Any items that need contributor input (cannot auto-fix)

## Common Fix Patterns

### Pattern: Country Code Lookup
```
1. Read the country_id from the record
2. Find the country in countries.json by id
3. Use its iso2 field as the correct country_code
```

### Pattern: State Code Lookup
```
1. Read the state_id from the record
2. Find the state in states.json by id
3. Use its state_code or iso2 field as the correct state_code
4. Verify the state's country_id matches the record's country_id
```

### Pattern: Remove Auto-Managed Fields
```
For each record in the contribution:
  Remove: id, created_at, updated_at, flag
  Keep everything else unchanged
```

## Important Rules

- Never modify coordinate values without a verified source
- Never change the `name` field without contributor confirmation
- Always explain what you changed and why
- If unsure about correct data, ask rather than guess
- Preserve the original JSON formatting style of the file
