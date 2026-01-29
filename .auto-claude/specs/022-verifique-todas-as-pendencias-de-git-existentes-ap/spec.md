# Git Cleanup and Merge to Dev

## Overview

Verify all Git pending items, commit changes, merge all work to `dev` branch, and cleanup worktrees. This involves handling uncommitted changes in the main branch and worktree 014, merging 18 auto-claude/* branches to dev, and removing completed worktrees.

## Workflow Type

**Type**: Feature

This is a feature workflow focused on Git operations to consolidate all pending work into the `dev` branch and clean up the repository state.

## Task Scope

### Current State (Discovered)
- **Main branch**: 1 commit ahead of origin, uncommitted config file changes
- **Worktree 014**: Database indexes work with 3 commits, pending changes (needs commit)
- **Local branches**: 18 auto-claude/* branches with completed work
- **No stashes**

### Files/Operations

#### 1. Worktree Cleanup
- `.auto-claude/worktrees/tasks/014-add-database-indexes-for-frequently-filtered-field` - commit pending changes, merge to dev, remove worktree

#### 2. Main Branch Changes (commit or discard)
- `.auto-claude-security.json`
- `.auto-claude/project_index.json`
- `.claude_settings.json`

#### 3. Branch Operations
- Merge important auto-claude/* branches to `dev`
- Push `dev` to origin
- Clean up merged local branches

### Execution Steps

1. **Worktree 014**: Commit pending changes, merge branch to dev
2. **Remove worktree**: `git worktree remove .auto-claude/worktrees/tasks/014-...`
3. **Main branch**: Commit config changes or discard
4. **Checkout dev**: `git checkout dev` or create from origin/dev
5. **Merge branches**: Merge all auto-claude/* branches with real work
6. **Push**: `git push origin dev`
7. **Cleanup**: Delete merged local branches

## Success Criteria

- [ ] `git status` shows clean working tree
- [ ] `git worktree list` shows only main worktree
- [ ] `git branch -a` shows reduced local branches
- [ ] `dev` branch contains all merged work
- [ ] Remote `origin/dev` is up-to-date

## Notes

- Preserve work from branch 014 (database indexes - valuable)
- Config file changes are auto-generated, safe to commit
- Some auto-claude branches may not have meaningful work (just specs)
