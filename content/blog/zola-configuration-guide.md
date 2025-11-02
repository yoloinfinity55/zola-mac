+++
title = "Essential Zola Configuration for macOS Developers"
date = 2025-11-02
description = "Master the config.toml file and optimize your Zola site for macOS development."
+++

# Essential Zola Configuration for macOS Developers

Zola's configuration is stored in the `config.toml` file at your site's root. This powerful file controls everything from basic site information to advanced features. Let's explore the key configuration options that every macOS developer should know.

## Basic Configuration

Every Zola site starts with these fundamental settings:

```toml
# The URL the site will be built for
base_url = "https://yourusername.github.io/zola-mac"

# The site title and description
title = "Zola-mac"
description = "Building beautiful static sites with Zola on macOS"

# Your name
author = "Your Name"
```

## Build Configuration

Control how Zola processes your site:

```toml
# Whether to compile Sass files
compile_sass = true

# Whether to build a search index
build_search_index = true

# Whether to highlight code blocks
highlight_code = true

# Theme to use (if any)
theme = "your-theme-name"
```

## Content Configuration

Manage how your content is processed:

```toml
# Default language for the site
default_language = "en"

# Generate feeds (RSS/Atom)
generate_feed = true

# Number of articles to include in feed
feed_limit = 20

# Whether to render emojis
render_emojis = true
```

## Taxonomies

Organize your content with tags and categories:

```toml
# Enable taxonomies
taxonomies = [
    {name = "tags", feed = true},
    {name = "categories", feed = true},
]

# Pagination for taxonomy pages
paginate_by = 5
```

## Syntax Highlighting

Customize code syntax highlighting:

```toml
[markdown]
# Enable code block highlighting
highlight_code = true

# Syntax highlighting theme
highlight_theme = "base16-ocean-dark"

# Additional languages to highlight
extra_syntaxes = ["rust", "toml", "bash"]
```

## Link Checking

Ensure your links are valid:

```toml
[link_checker]
# Skip link checking for these URL prefixes
skip_prefixes = [
    "http://localhost",
    "https://github.com/yourusername/zola-mac/edit",
]

# Skip anchor checking
skip_anchor_prefixes = [
    "https://github.com",
]
```

## Extra Configuration

Add custom variables for your templates:

```toml
[extra]
# Social media links
social = [
    { name = "GitHub", url = "https://github.com/yourusername" },
    { name = "Twitter", url = "https://twitter.com/yourusername" },
]

# Analytics
google_analytics = "UA-XXXXXXX-X"

# Comments system
utterances_repo = "yourusername/zola-mac"
```

## macOS-Specific Tips

### Using Environment Variables

Keep sensitive information out of your config:

```toml
# In config.toml
google_analytics = "{{ env.GOOGLE_ANALYTICS_ID }}"
```

Set the environment variable in your shell or use a `.env` file.

### Development vs Production

Use different configurations for development and production:

```bash
# Development
zola serve

# Production build
zola build --base-url $PRODUCTION_URL
```

### Performance Optimization

For better performance on macOS:

```toml
# Enable hard links for faster builds (macOS/Linux only)
hard_link_static = true

# Minify HTML output
minify_html = true
```

## Advanced Configuration

### Custom Output Directory

```toml
# Change the output directory
output_dir = "dist"
```

### Ignoring Content

Exclude files from processing:

```toml
ignored_content = [
    "content/drafts/*",
    "*.tmp.md",
]
```

### Internationalization

Support multiple languages:

```toml
languages = [
    { code = "en", name = "English" },
    { code = "es", name = "Español" },
]

# Language-specific configuration
[languages.es]
title = "Zola-mac"
description = "Construyendo sitios estáticos hermosos con Zola en macOS"
```

## Configuration Validation

Always test your configuration:

```bash
# Check for syntax errors
zola check

# Build and verify
zola build
```

## Common macOS Issues

### File Permissions

If you encounter permission issues:

```bash
# Fix permissions on Zola binary
chmod +x /usr/local/bin/zola
```

### Path Issues

Ensure Zola is in your PATH:

```bash
# Add to ~/.zshrc or ~/.bash_profile
export PATH="/usr/local/bin:$PATH"
```

## Next Steps

With these configuration options, you can customize Zola to fit your exact needs. Remember to:

1. Start with the basics and add features incrementally
2. Test your configuration after each change
3. Use version control to track configuration changes
4. Refer to the [official documentation](https://www.getzola.org/documentation/getting-started/configuration/) for the latest options

Happy configuring!
