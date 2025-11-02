+++
title = "Getting Started with Zola on macOS"
date = 2025-11-02
description = "A complete guide to installing and setting up Zola static site generator on your Mac."
+++

# Getting Started with Zola on macOS

Welcome to the world of static site generation! Zola is a fast, secure, and flexible static site generator written in Rust. In this guide, we'll walk through installing Zola on your macOS machine and creating your first site.

## Why Zola?

Before we dive in, let's quickly discuss why Zola is an excellent choice for your static site:

- **Blazing Fast**: Written in Rust, Zola compiles sites incredibly quickly
- **Secure**: No runtime dependencies or database means fewer security concerns
- **Flexible**: Uses the powerful Tera templating engine
- **Modern**: Supports Sass compilation, syntax highlighting, and search indexing out of the box

## Installing Zola

### Method 1: Using Homebrew (Recommended)

The easiest way to install Zola on macOS is through Homebrew:

```bash
brew install zola
```

Verify the installation:

```bash
zola --version
```

### Method 2: Download Binary

If you prefer not to use Homebrew, you can download the latest binary from the [official Zola releases page](https://github.com/getzola/zola/releases).

1. Download the macOS binary (usually `zola-vX.X.X-x86_64-apple-darwin.tar.gz`)
2. Extract the archive
3. Move the `zola` binary to `/usr/local/bin/` or add it to your PATH

## Creating Your First Site

Once Zola is installed, let's create your first site:

```bash
# Create a new directory for your site
mkdir my-zola-site
cd my-zola-site

# Initialize a new Zola site
zola init
```

Zola will ask you a few questions:
- **Base URL**: Enter your site's URL (e.g., `https://example.com` or `http://localhost:1111` for development)
- **Sass compilation**: Yes (enables CSS preprocessing)
- **Syntax highlighting**: Yes (adds code syntax highlighting)
- **Search index**: Yes (enables built-in search functionality)

## Understanding the Directory Structure

After initialization, you'll see this structure:

```
my-zola-site/
├── config.toml          # Site configuration
├── content/             # Your Markdown content
├── static/              # Static assets (images, CSS, JS)
├── templates/           # HTML templates
└── themes/              # Zola themes (optional)
```

## Your First Post

Let's create a simple blog post. Create a new file at `content/blog/hello-world.md`:

```markdown
+++
title = "Hello, World!"
date = 2025-11-02
description = "My first post with Zola"
+++

# Hello, World!

This is my first blog post created with Zola on macOS. Welcome to the future of static sites!

## What makes Zola special?

- **Speed**: Compiles in milliseconds
- **Security**: No server-side processing
- **Simplicity**: Focus on content, not configuration
```

## Running the Development Server

To see your site in action:

```bash
zola serve
```

Open your browser to `http://127.0.0.1:1111` and you'll see your site running locally!

## Building for Production

When you're ready to deploy:

```bash
zola build
```

This creates a `public/` directory with your compiled site, ready for deployment to any static hosting service.

## Next Steps

Now that you have Zola up and running, you might want to:

1. [Explore Zola themes](https://www.getzola.org/themes/)
2. Learn about [content organization](https://www.getzola.org/documentation/content/overview/)
3. Set up [deployment to GitHub Pages](https://www.getzola.org/documentation/deployment/github-pages/)

Happy blogging with Zola!
