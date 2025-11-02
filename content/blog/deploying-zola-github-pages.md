+++
title = "Deploying Zola Sites to GitHub Pages on macOS"
date = 2025-11-02
description = "Step-by-step guide to deploying your Zola static site to GitHub Pages using GitHub Actions."
+++

# Deploying Zola Sites to GitHub Pages on macOS

GitHub Pages provides free hosting for static websites, making it the perfect platform for Zola sites. In this guide, we'll set up automated deployment using GitHub Actions, so your site updates every time you push changes.

## Prerequisites

Before we start, ensure you have:

- A GitHub account
- A Zola site ready to deploy
- Git installed on your macOS machine

## Step 1: Create a GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" icon → "New repository"
3. Name your repository (e.g., `yourusername.github.io` for a user site, or `zola-site` for a project site)
4. Make it public (required for GitHub Pages)
5. Don't initialize with README, .gitignore, or license (we'll add our Zola site)

## Step 2: Push Your Zola Site to GitHub

```bash
# Initialize git in your Zola project (if not already done)
git init

# Add all your files
git add .

# Commit your changes
git commit -m "Initial Zola site"

# Add your GitHub repository as remote
git remote add origin https://github.com/yourusername/yourrepo.git

# Push to GitHub
git push -u origin main
```

## Step 3: Configure GitHub Pages

### For User/Organization Sites (yourusername.github.io)

1. Go to your repository on GitHub
2. Click "Settings" tab
3. Scroll down to "Pages" section
4. Under "Source", select "GitHub Actions"

### For Project Sites (yourusername.github.io/project-name)

1. Follow the same steps above
2. Your site will be available at `https://yourusername.github.io/project-name`

## Step 4: Create GitHub Actions Workflow

Create the workflow file for automated deployment:

```bash
mkdir -p .github/workflows
touch .github/workflows/deploy.yml
```

Add this content to `.github/workflows/deploy.yml`:

```yaml
name: Deploy Zola site to Pages

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Install Zola
        run: |
          wget -q -O - \
            "https://github.com/getzola/zola/releases/download/v0.18.0/zola-v0.18.0-x86_64-unknown-linux-gnu.tar.gz" \
            | tar xzf - -C /usr/local/bin

      - name: Build with Zola
        run: zola build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

## Step 5: Update Your Zola Configuration

Update your `config.toml` to use the correct base URL:

```toml
# For user sites
base_url = "https://yourusername.github.io"

# For project sites
base_url = "https://yourusername.github.io/repository-name"
```

## Step 6: Commit and Push

```bash
# Add the workflow file
git add .github/workflows/deploy.yml

# Update config if needed
git add config.toml

# Commit changes
git commit -m "Add GitHub Pages deployment workflow"

# Push to trigger deployment
git push
```

## Step 7: Monitor Deployment

1. Go to your repository on GitHub
2. Click the "Actions" tab
3. You should see a workflow running
4. Once complete, go to "Settings" → "Pages" to find your site URL

## Troubleshooting Common Issues

### Build Failures

If your build fails, check the Actions logs for errors. Common issues:

- **Missing base_url**: Ensure `base_url` is set correctly in `config.toml`
- **Broken links**: Run `zola check` locally to find broken internal links
- **Theme issues**: Verify your theme is properly configured

### Site Not Updating

- Wait a few minutes after deployment
- Check that you're pushing to the `main` branch
- Clear your browser cache (Ctrl+F5 or Cmd+Shift+R)

### Custom Domain

To use a custom domain:

1. Go to repository Settings → Pages
2. Add your custom domain
3. Create a `CNAME` file in your `static` directory with your domain
4. Update your `config.toml` base_url to use your custom domain

## Advanced Configuration

### Deploying from a Different Branch

Modify the workflow to deploy from a `deploy` branch:

```yaml
on:
  push:
    branches: ["deploy"]
```

### Using Different Zola Versions

Update the Zola installation step:

```yaml
- name: Install Zola
  run: |
    wget -q -O - \
      "https://github.com/getzola/zola/releases/download/v0.19.0/zola-v0.19.0-x86_64-unknown-linux-gnu.tar.gz" \
      | tar xzf - -C /usr/local/bin
```

### Adding Build Arguments

Pass additional arguments to `zola build`:

```yaml
- name: Build with Zola
  run: zola build --drafts
```

## Local Testing

Before pushing, test your build locally:

```bash
# Build the site
zola build

# Serve locally to test
zola serve

# Check for broken links
zola check
```

## Performance Tips

- Enable `minify_html = true` in your `config.toml` for smaller HTML files
- Use `hard_link_static = true` for faster builds on macOS
- Optimize images before adding them to your site

## Next Steps

With GitHub Pages deployment set up, your Zola site will automatically update whenever you push changes. Consider:

1. Setting up a custom domain
2. Adding Google Analytics
3. Implementing comments with services like utterances or giscus
4. Setting up a CDN for better performance

Your Zola site is now live and automatically deployed! 🎉
