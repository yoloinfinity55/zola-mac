+++
title = "Overview"
date = 2025-10-31
+++

[Generated from https://www.getzola.org/documentation/content/overview/]

## Beginner's Explanation
[Generated beginner-friendly explanation for: 
        
    Overview
    Zola uses the directory structure to determine the site structure.
Each child directory in the content directory represents a section
that contains pages (your .md files).
.
└── content
    ├── content
    │   └── something.md // -> https://mywebsite.com/content/something/
    ├── blog
    │   ├── cli-usage.md // -> https://mywebsite.com/blog/cli-usage/
    │   ├── configuration.md // -> https://mywebsite.com/blog/configuration/
    │   ├── directory-structure.md // -> https://mywebsite.com/blog/directory-structure/
    │   ├── _index.md // -> https://mywebsite.com/blog/
    │   └── installation.md // -> https://mywebsite.com/blog/installation/
    └── landing
        └── _index.md // -> https://mywebsite.com/landing/

Each page path (the part after base_url, for example blog/cli-usage/) can be customised by changing the path or
slug attribute of the page front-matter.
You might have noticed a file named _index.md in the example above.
This file is used to store both the metadata and content of the section itself and is not considered a page.
To ensure that the terminology used in the rest of the documentation is understood, let's go over the example above.
The content directory in this case has three sections: content, blog and landing. The content section has only
one page (something.md), the landing section has no pages and the blog section has 4 pages (cli-usage.md,
configuration.md, directory-structure.md and installation.md).
Sections can be nested indefinitely.
🔗Asset colocation
The content directory is not limited to markup files. It's natural to want to co-locate a page and some related
assets, such as images or spreadsheets. Zola supports this pattern out of the box for both sections and pages.
All non-Markdown files you add in a page/section directory will be copied alongside the generated page when the site is
built, which allows us to use a relative path to access them.
Pages with co-located assets should not be placed directly in their section directory (such as latest-experiment.md), but
as an index.md file in a dedicated directory (latest-experiment/index.md), like so:
└── research
    ├── latest-experiment
    │   ├── index.md
    │   └── javascript.js
    ├── _index.md
    └── research.jpg

With this setup, you may access research.jpg from your 'research' section
and javascript.js from your 'latest-experiment' page directly within the Markdown:
Check out the complete program [here](javascript.js). It's **really cool free-software**!

By default, this page's slug will be the directory name and thus its permalink will be https://example.com/research/latest-experiment/.
🔗Excluding files from assets
It is possible to ignore selected asset files using the
ignored_content setting in the config file.
For example, say that you have several code files which you are linking to on your website.
For maintainability, you want to keep your code in the same directory as the Markdown file,
but you don't want to copy the build folders to the public web site. You can achieve this by setting ignored_content in the config file:
(Note of caution: {Cargo.lock,target} is not the same as {Cargo.lock, target})
ignored_content = ["code_articles/**/{Cargo.lock,target}, *.rs"]

🔗Static assets
In addition to placing content files in the content directory, you may also place content
files in the static directory.  Any files/directories that you place in the static directory
will be copied, without modification, to the public directory.
Typically, you might put site-wide assets (such as a CSS file, the site favicon, site logos or site-wide
JavaScript) in the root of the static directory. You can also place any HTML or other files that
you wish to be included without modification (that is, without being parsed as Markdown files)
into the static directory.
Note that the static directory provides an alternative to co-location.  For example, imagine that you
had the following directory structure (a simplified version of the structure presented above):
.
└── content
    └── blog
        ├── configuration
        │    └── index.md // -> https://mywebsite.com/blog/configuration/
        └── _index.md // -> https://mywebsite.com/blog/

To add an image to the https://mywebsite.com/blog/configuration page, you have three options:

You could save the image to the content/blog/configuration directory and then link to it with a
relative path from the index.md page.  This is the approach described under co-location
above.
You could save the image to a static/blog/configuration directory and link to it in exactly the
same way as if you had co-located it. If you do this, the generated files will be identical to those
obtained if you had co-located the image; the only difference will be that all static files will be saved in the
static directory rather than in the content directory. The choice depends on your organizational needs.
Or you could save the image to some arbitrary directory within the static directory. For example,
you could save all images to static/images.  Using this approach, you can no longer use relative links. Instead,
you must use an absolute link to images/[filename] to access your
image. This might be preferable for small sites or for sites that associate images with
multiple pages (e.g., logo images that appear on every page).



    ]

## Step-by-Step Guide
[Generated step-by-step guide for: 
        
    Overview
    Zola uses the directory structure to determine the site structure.
Each child directory in the content directory represents a section
that contains pages (your .md files).
.
└── content
    ├── content
    │   └── something.md // -> https://mywebsite.com/content/something/
    ├── blog
    │   ├── cli-usage.md // -> https://mywebsite.com/blog/cli-usage/
    │   ├── configuration.md // -> https://mywebsite.com/blog/configuration/
    │   ├── directory-structure.md // -> https://mywebsite.com/blog/directory-structure/
    │   ├── _index.md // -> https://mywebsite.com/blog/
    │   └── installation.md // -> https://mywebsite.com/blog/installation/
    └── landing
        └── _index.md // -> https://mywebsite.com/landing/

Each page path (the part after base_url, for example blog/cli-usage/) can be customised by changing the path or
slug attribute of the page front-matter.
You might have noticed a file named _index.md in the example above.
This file is used to store both the metadata and content of the section itself and is not considered a page.
To ensure that the terminology used in the rest of the documentation is understood, let's go over the example above.
The content directory in this case has three sections: content, blog and landing. The content section has only
one page (something.md), the landing section has no pages and the blog section has 4 pages (cli-usage.md,
configuration.md, directory-structure.md and installation.md).
Sections can be nested indefinitely.
🔗Asset colocation
The content directory is not limited to markup files. It's natural to want to co-locate a page and some related
assets, such as images or spreadsheets. Zola supports this pattern out of the box for both sections and pages.
All non-Markdown files you add in a page/section directory will be copied alongside the generated page when the site is
built, which allows us to use a relative path to access them.
Pages with co-located assets should not be placed directly in their section directory (such as latest-experiment.md), but
as an index.md file in a dedicated directory (latest-experiment/index.md), like so:
└── research
    ├── latest-experiment
    │   ├── index.md
    │   └── javascript.js
    ├── _index.md
    └── research.jpg

With this setup, you may access research.jpg from your 'research' section
and javascript.js from your 'latest-experiment' page directly within the Markdown:
Check out the complete program [here](javascript.js). It's **really cool free-software**!

By default, this page's slug will be the directory name and thus its permalink will be https://example.com/research/latest-experiment/.
🔗Excluding files from assets
It is possible to ignore selected asset files using the
ignored_content setting in the config file.
For example, say that you have several code files which you are linking to on your website.
For maintainability, you want to keep your code in the same directory as the Markdown file,
but you don't want to copy the build folders to the public web site. You can achieve this by setting ignored_content in the config file:
(Note of caution: {Cargo.lock,target} is not the same as {Cargo.lock, target})
ignored_content = ["code_articles/**/{Cargo.lock,target}, *.rs"]

🔗Static assets
In addition to placing content files in the content directory, you may also place content
files in the static directory.  Any files/directories that you place in the static directory
will be copied, without modification, to the public directory.
Typically, you might put site-wide assets (such as a CSS file, the site favicon, site logos or site-wide
JavaScript) in the root of the static directory. You can also place any HTML or other files that
you wish to be included without modification (that is, without being parsed as Markdown files)
into the static directory.
Note that the static directory provides an alternative to co-location.  For example, imagine that you
had the following directory structure (a simplified version of the structure presented above):
.
└── content
    └── blog
        ├── configuration
        │    └── index.md // -> https://mywebsite.com/blog/configuration/
        └── _index.md // -> https://mywebsite.com/blog/

To add an image to the https://mywebsite.com/blog/configuration page, you have three options:

You could save the image to the content/blog/configuration directory and then link to it with a
relative path from the index.md page.  This is the approach described under co-location
above.
You could save the image to a static/blog/configuration directory and link to it in exactly the
same way as if you had co-located it. If you do this, the generated files will be identical to those
obtained if you had co-located the image; the only difference will be that all static files will be saved in the
static directory rather than in the content directory. The choice depends on your organizational needs.
Or you could save the image to some arbitrary directory within the static directory. For example,
you could save all images to static/images.  Using this approach, you can no longer use relative links. Instead,
you must use an absolute link to images/[filename] to access your
image. This might be preferable for small sites or for sites that associate images with
multiple pages (e.g., logo images that appear on every page).



    ]

## Audio Version
<audio controls><source src="/static/audio/overview.mp3" type="audio/mpeg"></audio>
