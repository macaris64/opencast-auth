# GitHub Branch Protection Setup Guide

This guide explains how to set up branch protection rules for the OpenCast Auth Platform repository to ensure code quality and prevent direct pushes to the main branch.

## Prerequisites

- Repository admin access
- CI/CD pipeline configured (GitHub Actions)
- Development team ready to use PR workflow

## Step 1: Access Branch Protection Settings

1. Go to your GitHub repository
2. Click on **Settings** tab
3. Select **Branches** from the left sidebar
4. Click **Add rule** button

## Step 2: Configure Branch Protection Rule

### Basic Settings

- **Branch name pattern**: `main` (or `master` if using master branch)
- ✅ **Restrict pushes that create files larger than 100 MB**

### Branch Protection Rules

- ✅ **Require a pull request before merging**

  - ✅ **Require approvals**: 1 (minimum)
  - ✅ **Dismiss stale PR approvals when new commits are pushed**
  - ✅ **Require review from code owners** (if using CODEOWNERS file)

- ✅ **Require status checks to pass before merging**

  - ✅ **Require branches to be up to date before merging**
  - **Required status checks**:
    - `lint` (Code quality checks)
    - `test` (Unit tests)
    - `security` (Security scans)
    - `build` (Build verification)
    - `cli-test` (CLI functionality tests)

- ✅ **Require conversation resolution before merging**
- ✅ **Require signed commits** (optional but recommended)
- ✅ **Require linear history** (optional, prevents merge commits)

### Additional Settings

- ✅ **Include administrators** (applies rules to admins too)
- ✅ **Allow force pushes** → **Disable** (prevents force pushes)
- ✅ **Allow deletions** → **Disable** (prevents branch deletion)

## Step 3: Verify Configuration

After setting up the rules:

1. Try to push directly to main branch (should be blocked)
2. Create a test PR to verify:
   - Status checks run automatically
   - PR requires approval
   - All checks must pass before merge

## Step 4: Team Communication

Inform your development team about the new workflow:

1. **No direct pushes** to main branch
2. **All changes** must go through Pull Requests
3. **Code review** is mandatory
4. **All CI checks** must pass
5. Use **feature branches** for development

## Development Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: your feature description"

# Push to GitHub
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# Wait for reviews and CI checks
# Merge after approval
```

## Troubleshooting

### Common Issues

1. **Status checks not appearing**

   - Ensure GitHub Actions workflow is properly configured
   - Check workflow file syntax
   - Verify workflow has run at least once

2. **Can't merge despite passing checks**

   - Check if all required status checks are listed
   - Ensure branch is up to date with main
   - Verify all conversations are resolved

3. **Administrators can't push**
   - This is expected if "Include administrators" is enabled
   - Use PR workflow even for admin changes

### Emergency Procedures

In case of urgent fixes:

1. Temporarily disable branch protection
2. Make necessary changes
3. Re-enable protection immediately
4. Document the emergency change

## Benefits

- **Code Quality**: All code is reviewed before merging
- **Stability**: Prevents broken code from reaching main branch
- **Collaboration**: Encourages team discussion and knowledge sharing
- **Compliance**: Maintains audit trail of all changes
- **Automation**: CI/CD pipeline ensures consistent quality checks

## Next Steps

1. Set up the branch protection rules as described
2. Train team members on the new workflow
3. Monitor PR process and adjust rules if needed
4. Consider additional tools like automated dependency updates
