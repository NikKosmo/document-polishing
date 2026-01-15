<!-- @meta
version: 2.0
created: 2026-01-10
last_polished: never
status: active
source: Industry research + user workflow interview
-->

# Git Workflow Rules

**For AI Agents (Claude Code, etc.)**

This document defines git/GitHub workflow rules for AI coding assistants working in this repository. These rules are based on industry best practices (2025) and project-specific preferences.

---

## Rule 1: Branch Workflow

### Branch Creation

<!-- @assertion id="rule1_branch_creation" type="requirement" priority="high" -->
**All work must be done on feature branches, never directly on main.**

- Create feature branch from main before making changes
- Branch naming conventions:
  - `feature/description` - New features
  - `fix/description` - Bug fixes
  - `docs/description` - Documentation updates
  - `refactor/description` - Code refactoring
  - `test/description` - Test additions
  - `hotfix/description` - Emergency fixes (still uses PR workflow)
<!-- @/assertion -->

**Example:**
```bash
git checkout main
git pull
git checkout -b feature/add-user-auth
```

---

## Rule 2: Commit Practices

### Commit Frequency

<!-- @assertion id="rule2_commit_frequency" type="requirement" priority="medium" -->
**Commit early and often with small, logical changes.**

- Prefer multiple small commits over large batches
- Each commit should represent one logical change
- Write descriptive commit messages (what and why)
- Easier to review, easier to revert, better for debugging
<!-- @/assertion -->

**Example:**
```bash
# Good: Small, logical commits
git commit -m "Add user model with email validation"
git commit -m "Add login endpoint with JWT generation"
git commit -m "Add tests for authentication flow"

# Avoid: Large, multi-purpose commit
git commit -m "Add authentication system" # (50 files changed)
```

---

## Rule 3: Pull Request (PR) Workflow

### PR Creation

<!-- @assertion id="rule3_pr_creation" type="requirement" priority="high" -->
**All changes must go through Pull Request workflow - no direct commits to main.**

Steps:
1. Push feature branch to remote: `git push -u origin feature/your-feature`
2. Create PR: `gh pr create --title "Title" --body "Description"`
3. PR must include:
   - Clear title describing the change
   - Description explaining what and why
   - Reference to related issues (if applicable)
<!-- @/assertion -->

### PR Review Requirements

<!-- @assertion id="rule3_pr_review_required" type="requirement" priority="critical" -->
**Every PR must be reviewed before merge - no exceptions.**

- ALL changes require human review, including:
  - Typo fixes in documentation
  - README formatting changes
  - .gitignore updates
  - Emergency security patches
- Review may be fast (30 seconds for typos), but must happen
- "Emergency" means fast review (minutes), NOT no review
<!-- @/assertion -->

**Review Checklist:**
- Scope: Does diff match stated goal? Any unexpected changes?
- Tests: New/updated tests? All tests passing?
- Security: Inputs validated? No hardcoded secrets?
- Quality: Follows project conventions? Readable?

### Merge Strategy

<!-- @assertion id="rule3_merge_strategy" type="constraint" priority="critical" -->
**Default merge strategy: Rebase and squash**

- Creates one logical commit per PR
- Linear history, clean for debugging and git bisect
- All PRs use rebase+squash unless user explicitly chooses alternative

Alternative strategies (require user decision):
- **Squash merge** - Single commit, no granularity (use for tiny changes)
- **Rebase merge** - Preserve individual commits (rare, only if commits are well-structured)
- **Merge commit** - AVOID: creates non-linear history

The default is always rebase+squash. Agent should not make judgment calls about when to use alternatives.
<!-- @/assertion -->

### Merge Authorization

<!-- @assertion id="rule3_merge_authorization" type="requirement" priority="critical" -->
**ONLY the user can execute merge commands.**

- Agent creates PRs but NEVER executes merge
- User must manually approve and merge
- Even with all approvals + passing CI, agent cannot merge
- Agent can create PRs, review code, suggest changes
- User executes: `gh pr merge --rebase --delete-branch`

**Prohibited commands for agents:**
- `gh pr merge` (any variant)
- `git merge`
- Any command that integrates branches
<!-- @/assertion -->

---

## Rule 4: Direct Commits to Main

### General Rule

<!-- @assertion id="rule4_no_direct_commits" type="requirement" priority="critical" -->
**NEVER commit directly to main - use PR workflow for all changes.**

- No exceptions for "trivial" changes
- No exceptions for emergencies (use expedited PR workflow instead)
- No exceptions for automated processes (configure PRs with auto-approval if needed)
<!-- @/assertion -->

### If You Accidentally Commit to Main

<!-- @assertion id="rule4_accidental_commit_recovery" type="sequence" priority="high" -->
**Recovery procedure if you commit to main by mistake:**

If NOT pushed yet:
```bash
git reset --soft HEAD~1  # Undo commit, keep changes
git stash                # Save changes
git checkout -b feature/fix-mistake  # Create proper branch
git stash pop            # Restore changes
git add .
git commit -m "Proper commit message"
git push -u origin feature/fix-mistake
gh pr create
```

If ALREADY pushed to main:
```bash
# NEVER use git push --force on main
git revert HEAD          # Creates new commit undoing changes
git push origin main
# Then follow proper branch workflow for fix
```
<!-- @/assertion -->

---

## Rule 5: Emergency Hotfix Workflow

### When Production is Down

<!-- @assertion id="rule5_hotfix_workflow" type="sequence" priority="critical" -->
**Even in emergencies, follow PR workflow with expedited review.**

Emergencies include:
- Production system completely down
- Security vulnerability actively exploited
- Data corruption or loss risk

**Hotfix procedure:**
1. Create hotfix branch from main:
```bash
git checkout main
git pull
git checkout -b hotfix/critical-bug
```

2. Make minimal fix and commit:
```bash
git add .
git commit -m "hotfix: Fix critical bug in authentication"
```

3. Push and create PR with `[HOTFIX]` prefix:
```bash
git push -u origin hotfix/critical-bug
gh pr create --title "[HOTFIX] Fix critical bug" --body "Critical fix, needs immediate merge"
```

4. Notify team for expedited review:
   - Slack/Discord: "Production down, need immediate PR review"
   - Tag on-call engineer

5. Get fast-tracked review (minutes, not hours)

6. User merges after approval:
```bash
gh pr merge --rebase --delete-branch
```

**Key principle:** Emergency = fast review, NOT no review.
<!-- @/assertion -->

---

## Rule 6: Branch Protection

### Required Settings

<!-- @assertion id="rule6_branch_protection" type="requirement" priority="high" -->
**Main branch must have protection enabled:**

- Require PR reviews (at least 1 approval)
- Require status checks to pass (all CI tests)
- Restrict direct push to main (enforce PR workflow)
- Require linear history (no merge commits)

These protections prevent accidents and enforce workflow consistency.
<!-- @/assertion -->

---

## Rule 7: Agent Boundaries

### What Agents CAN Do

<!-- @assertion id="rule7_agent_permissions" type="constraint" priority="high" -->
**Permitted operations for AI agents:**

- Create feature branches: `git checkout -b feature/*`
- Commit to feature branches: `git commit`
- Push to feature branches: `git push origin feature/*`
- Create PRs: `gh pr create`
- Review code and suggest changes
- Respond to PR feedback with new commits

**Prohibited operations for AI agents:**
- Execute merge commands (any variant)
- Commit directly to main
- Push to main branch: `git push origin main`
- Skip PR workflow for any reason
- Make decisions about review exceptions
<!-- @/assertion -->

---

## Rule 8: Co-Authorship

### Commit Attribution

<!-- @assertion id="rule8_coauthorship" type="requirement" priority="medium" -->
**All AI-generated commits must include co-author attribution.**

Format:
```bash
git commit -m "$(cat <<'EOF'
Add user authentication system

Implements JWT-based auth with refresh tokens.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

This maintains transparency about which code was AI-assisted.
<!-- @/assertion -->

---

## Summary: Key Principles

1. **Human-in-the-Loop** - Agents propose, humans execute merges
2. **Review is Non-Negotiable** - Every change gets reviewed (fast or slow)
3. **Linear History Priority** - Default to rebase+squash for clean history
4. **Process Over Speed** - Expedite the process, don't bypass it
5. **No Direct Commits** - All work through PR workflow, no exceptions
6. **Agent Boundaries** - Clear separation of agent vs human actions

---

## Sources

- Industry research: temp/agentic_git_research.md (2025 best practices)
- User workflow interview: temp/user_workflow_profile.md
- Key sources:
  - [Anthropic - Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
  - [AWS - Agentic AI Security Scoping Matrix](https://aws.amazon.com/blogs/security/the-agentic-ai-security-scoping-matrix-a-framework-for-securing-autonomous-ai-systems/)
  - [Addy Osmani - LLM Coding Workflow 2026](https://addyosmani.com/blog/ai-coding-workflow/)
  - [GitHub - Building Reliable AI Workflows](https://github.blog/ai-and-ml/github-copilot/how-to-build-reliable-ai-workflows-with-agentic-primitives-and-context-engineering/)
