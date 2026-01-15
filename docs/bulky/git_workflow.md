<!-- @meta
version: 1.0
created: 2025-12-02
last_polished: 2025-12-30
status: active
-->

# Git Workflow Rules

**Purpose:** Define standard Git workflow for all projects to maintain code quality and prevent accidental damage.

**Applies to:** All projects in the workspace

---

## Branch Protection

### Public Repositories
- **Branch protection enabled** via GitHub (strict mode)
- Requires pull request with 1 approval
- Prevents force pushes and branch deletion
- Enforced for all users including admins

### Private Repositories
- **No automatic enforcement** (GitHub Pro required)
- Follow workflow rules manually (honor system)
- Use PR-based workflow even without enforcement

---

## Standard Workflow

### Rule 1: NEVER Push Directly to Main

**CRITICAL:** Always use feature branches and pull requests. This rule applies regardless of branch protection status.

**Always use feature branches:**

```bash
# Create feature branch
git checkout -b feature/add-flashcards
# or
git checkout -b fix/audio-bug
# or
git checkout -b docs/update-readme

# Work on changes
git add .
git commit -m "Add new vocabulary flashcards"

# Push feature branch
git push -u origin feature/add-flashcards
```

<!-- @assertion id="rule1_branch_naming" type="constraint" priority="high" -->
**Branch naming conventions:**
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions
<!-- @/assertion -->

### Rule 2: Use Pull Requests

**Create PR for all changes:**

```bash
# After pushing feature branch
gh pr create --title "Add new vocabulary flashcards" --body "$(cat <<'EOF'
## Changes
- Added 15 new vocabulary words
- Updated word tracking
- Regenerated Anki deck

## Testing
- [x] Generated deck successfully
- [x] Imported to Anki
- [x] Verified audio files

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**PR checklist:**
- [ ] Clear title describing the change
- [ ] Description with bullet points
- [ ] Self-review completed
- [ ] All tests pass (if applicable)
- [ ] No sensitive data included

### Rule 3: Review Before Merge

**Self-review process:**

```bash
# Review changes in PR
gh pr view --web

# Check diff
gh pr diff

# If changes needed
git checkout feature/add-flashcards
# Make changes
git add .
git commit -m "Address review feedback"
git push

# When ready, merge with rebase (default strategy)
gh pr merge --rebase --delete-branch

# Or squash for very small changes
gh pr merge --squash --delete-branch
```

<!-- @assertion id="rule3_merge_strategy" type="constraint" priority="critical" -->
**Merge strategies:**
- **Rebase and squash** (default) - Linear history, logically grouped commits
- **Squash merge** - Alternative: single commit per PR (use for small changes)
- **Rebase merge** - Rare: preserve individual commits (use for large, well-structured PRs)
- **Merge commit** - Avoid: creates non-linear history
<!-- @/assertion -->

<!-- @assertion id="rule3_merge_authorization" type="requirement" priority="critical" -->
**Merge authorization:**
- **ONLY the user can merge PRs** - Claude Code must NOT execute merge commands
- Claude can create PRs, review code, suggest changes, but merge requires explicit user action
- User executes: `gh pr merge --rebase --delete-branch` (or equivalent)
<!-- @/assertion -->

### Rule 4: Keep Main Clean and Linear

**Main branch should always be:**
- ✓ Working and tested
- ✓ Deployable at any time
- ✓ Free of WIP commits
- ✓ Linear history (no merge commits)
- ✓ Never force-pushed

<!-- @assertion id="rule4_accidental_commit" type="sequence" priority="high" -->
**If you accidentally commit to main:**

```bash
# DON'T force push - it's blocked anyway
# Instead, revert the commit
git revert HEAD
git push origin main

# Or if not pushed yet
git reset --soft HEAD~1
git stash
git checkout -b feature/fix-mistake
git stash pop
git add .
git commit -m "Proper commit message"
git push -u origin feature/fix-mistake
# Then create PR
```
<!-- @/assertion -->

---

## Emergency Procedures

### Hotfix Workflow

<!-- @assertion id="hotfix_workflow" type="sequence" priority="high" -->
**For critical fixes that need immediate merge:**

```bash
# Create hotfix branch from main
git checkout main
git pull
git checkout -b hotfix/critical-bug

# Make minimal fix
git add .
git commit -m "Fix critical bug in flashcard generation"
git push -u origin hotfix/critical-bug

# Create PR with [HOTFIX] prefix
gh pr create --title "[HOTFIX] Fix critical bug" --body "Critical fix, needs immediate merge"

# Merge immediately after self-review (use rebase to maintain linear history)
gh pr merge --rebase --delete-branch
```
<!-- @/assertion -->

### Undoing Changes

**Revert a merged PR:**

```bash
# Find the merge commit
git log --oneline main

# Revert it
git revert <merge-commit-sha>
git push origin main
```

**Undo local commits (not pushed):**

```bash
# Soft reset (keeps changes)
git reset --soft HEAD~1

# Hard reset (discards changes)
git reset --hard HEAD~1
```

---

## Submodule-Specific Workflow

**When working in submodules after meta-repo conversion:**

```bash
# Work in submodule (e.g., german/)
cd projects/german
git checkout -b feature/new-cards
# Make changes
git add .
git commit -m "Add vocabulary cards"
git push -u origin feature/new-cards
gh pr create
gh pr merge --squash --delete-branch

# Update meta-repo to track new commit
cd ..  # back to projects/
git add german
git commit -m "Update german submodule to latest"
git push origin main
```

**Important:** Submodule commits must be pushed BEFORE updating meta-repo.

---

## Commit Message Standards

### Format

```
<type>: <subject>

<body>

<footer>
```

### Types
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

### Examples

**Good:**
```
feat: Add 15 Konjunktiv II flashcards

- Added conditional mood examples
- Updated word tracking
- Regenerated Anki deck

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

**Bad:**
```
update stuff
```

---

## GitHub CLI Commands Reference

```bash
# Create branch and PR
git checkout -b feature/my-feature
gh pr create

# View PR
gh pr view
gh pr view --web

# Check PR status
gh pr status

# Merge PR (default: rebase for linear history)
gh pr merge --rebase --delete-branch

# Alternative: squash for small changes
gh pr merge --squash --delete-branch

# List PRs
gh pr list

# Close PR without merging
gh pr close <number>
```

**Pro tip:** Before merging with rebase, clean up your commits:
```bash
# Interactive rebase to squash/reorder commits
git checkout feature/my-feature
git rebase -i main

# Mark commits to squash (change 'pick' to 'squash' or 's')
# Save and exit, then force-push the cleaned branch
git push --force-with-lease
```

---

## Exceptions

<!-- @assertion id="exceptions_direct_commits" type="requirement" priority="critical" -->
**When direct commits to main are acceptable:**
- Initial repository setup
- Emergency hotfixes (with immediate notification)
- Automated bot commits (CI/CD)
- Meta-repo submodule updates
<!-- @/assertion -->

<!-- @assertion id="exceptions_skip_review" type="requirement" priority="critical" -->
**When to skip PR review:**
- Typo fixes in documentation
- README updates with no code changes
- Updating .gitignore
- Emergency security patches
<!-- @/assertion -->

---

## Enforcement

### Public Repos (german-learning, document-polishing)
- GitHub enforces these rules automatically
- Force push blocked
- Direct commits to main blocked
- PR required for all changes

### Private Repos (english-learning, obsidian_vault)
- No automatic enforcement
- Follow workflow manually
- Use PR process for discipline
- Future: Upgrade to GitHub Pro for enforcement

---

## Gitignore Best Practices

### Pattern Syntax

**CRITICAL:** Comments in `.gitignore` MUST be on separate lines, NOT inline with patterns.

**Why this matters:**
- In `.gitignore`, the `#` character **only starts a comment at the beginning of a line**
- When placed mid-line, everything after the pattern (including spaces and `#`) becomes part of the literal pattern match
- This causes patterns to silently fail without warning

**Bad (will NOT work):**
```gitignore
SESSION_LOG.md      # User session tracking
**/workspace/**     # Generated outputs
temp/               # Temporary files
```

In the above example:
- Git looks for a file literally named `SESSION_LOG.md      # User session tracking` (with spaces and comment)
- The actual file `SESSION_LOG.md` will NOT match and will NOT be ignored
- `git check-ignore` will return exit code 1 (not ignored)
- Files will show as `??` (untracked) instead of being ignored

**Good (correct syntax):**
```gitignore
# User session tracking
SESSION_LOG.md

# Generated outputs
**/workspace/**

# Temporary files
temp/
```

### Testing Patterns

**Always verify gitignore patterns work:**
```bash
# Test if a file/directory is ignored (exit 0 = ignored, exit 1 = not ignored)
git check-ignore -v SESSION_LOG.md
git check-ignore -v scripts/workspace/

# Expected output when working:
# .gitignore:57:SESSION_LOG.md	SESSION_LOG.md

# Show all ignored files in directory
git status --ignored
```

### Common Mistakes

1. **Inline comments** (see above) - Most common, silently breaks patterns
2. **Already tracked files** - `.gitignore` doesn't apply to already-tracked files:
   ```bash
   # Remove from git tracking first
   git rm --cached SESSION_LOG.md
   git commit -m "Remove SESSION_LOG.md from tracking"
   ```
3. **Explicit git add bypasses gitignore** - `git add <specific-file>` overrides `.gitignore`:
   ```bash
   # BAD: Bypasses gitignore
   git add SESSION_LOG.md workspace/ TODO.md

   # GOOD: Respects gitignore
   git add .
   ```

### Verification After Changes

After modifying `.gitignore`:
```bash
# Test critical patterns
git check-ignore -v SESSION_LOG.md
git check-ignore -v scripts/workspace/
git check-ignore -v temp/

# Verify files are actually ignored
git status --porcelain
# Ignored files should not appear (or show as !!)
```

**Reference:** See document_polishing PR #21 (2025-12-26) for real-world example of inline comment issue.

---

## Summary Checklist

Before every change:
- [ ] Create feature branch
- [ ] Make changes and commit
- [ ] Clean up commits (interactive rebase if needed)
- [ ] Push to feature branch
- [ ] Create pull request
- [ ] Self-review changes
- [ ] Merge with rebase (or squash for small changes)
- [ ] Delete feature branch
- [ ] Verify main has linear history: `git log --oneline --graph`

---

**Last Updated:** 2025-12-02
**Applies to:** All projects (german, english, document_polishing, obsidian_vault, meta-repo)
