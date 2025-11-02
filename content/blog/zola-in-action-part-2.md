+++
title = "Zola in Action: Setting Up Your First Project and Theme"
date = 2025-11-01
description = ""
+++

# Zola in Action: Setting Up Your First Project and Theme

Hey friends, how are you doing? This is a series on how to build a website using Zola. In the previous part, we discussed our goals for building a website and why we chose Zola, a static site generator, over traditional web technologies like WordPress or Django. In this part, we're actually going to see Zola in action! We'll initialize a project, integrate a theme, and understand how Zola fits into the process.

## 1. Installing Zola

To start, we first need to install Zola. The best way to do this is by visiting the official documentation at [zola.getzola.org](https://www.getzola.org/). You'll find installation instructions tailored to your operating system and distribution. The simplest method we recommend is to go to the GitHub releases page and download the binary specific to your system.

If you encounter any issues or have questions about the installation process, please mention them in the comments, and we'll get back to you as soon as possible.

Once downloaded, you can add the Zola binary to your system's PATH. This allows you to run Zola commands directly from your terminal by simply typing `zola` followed by the command. For example, to check the version, you'd type `zola --version`.

## 2. Starting a New Zola Project

Now that Zola is installed, let's start a new project. Navigate to your desired project directory in the terminal and run:

```bash
zola init .
```

When you run `zola init`, it will ask you a few questions:

*   **What is the URL of your site (base_url)?** This can be anything, for example, `https://yourwebsite.com` or `http://localhost:1111` for local development.
*   **Do you want Sass compilation?** (We can leave this to default: `yes`)
*   **Do you want syntax highlighting?** (Leave to default)
*   **Do you want a search index?** (Leave to default)

All these questions and their answers are customizable and can be changed later in your `config.toml` file.

After initialization, Zola creates a basic directory structure for you, including a `config.toml` file and various folders like `content/`, `templates/`, and `static/`.

## 3. Exploring the Default Structure

To see what the default Zola structure looks like, you can run the development server:

```bash
zola serve
```

This command builds your website, compiles it, and serves it on `http://localhost:1111`. This is incredibly helpful for live development, as you can see your changes instantly. Since we haven't added any custom templates yet, Zola will display a default template page, indicating that it couldn't find a specific template to render.

## 4. Installing a Zola Theme

Now, let's enhance our site by installing a theme. Zola has a vibrant theme ecosystem. You can find themes on the official Zola website or by searching GitHub.

To install a theme:

1.  **Choose a theme:** For this example, let's say we choose a theme called "DeepThought" (you can choose any theme you like).
2.  **Clone the theme:** Navigate into your project's `themes/` directory (if it doesn't exist, create it) and clone the theme's GitHub repository:

    ```bash
    cd themes
    git clone https://github.com/your-theme-repo/deepthought.git
    ```

3.  **Configure `config.toml`:** Go back to your project's root directory and open `config.toml`. Add or update the `theme` variable to the name of the theme's directory (which is usually the repository name):

    ```toml
    theme = "deepthought"
    ```

## 5. Theme-Specific Configuration

Many themes require additional configuration options in your `config.toml` to function correctly. These are specific to each theme. For example, the "DeepThought" theme might require `navbar_items` and `default_language` settings.

If you encounter errors after setting the theme, check the theme's documentation (usually in its GitHub repository's `README.md`) for required configuration. You might need to add sections like this to your `config.toml`:

```toml
[extra]
navbar_items = [
    { url = "/", name = "Home" },
    { url = "/blog", name = "Blog" },
]

[translations]
en = { title = "My Blog", base_url = "https://example.com" }
# fr = { title = "Mon Blog", base_url = "https://example.com/fr" }
```

After adding the necessary configuration, run `zola serve` again. If everything is set up correctly, your theme should now be applied, and you'll see its default layout. You might not have any content yet, but the theme's structure will be visible.

In the next part of this series, we'll delve into configuring these theme options further and adding content to make our website truly shine. Thank you for reading!
+++
