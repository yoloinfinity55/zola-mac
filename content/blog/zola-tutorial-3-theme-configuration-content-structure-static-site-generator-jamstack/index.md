+++
title = "Zola tutorial #3: Theme configuration & content structure | Static site generator | Jamstack"
date = "2025-11-03"
tags = [ "jamstack", "zola", "website", "staticsitegenerator", "theme",]

[extra]
youtube_id = "GUQt52IXwXQ"
+++
![Zola tutorial #3: Theme configuration & content structure | Static site generator | Jamstack](./asset.jpg)

## TL;DR (Quick Summary)

> In this lesson we will learn about configuring theme and also have a look at default content structure provided by Zola.

## 🎧 Listen to the Episode

<audio controls style="width: 100%;">
  <source src="./asset.mp3" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>

## 📋 Structured Key Takeaways

## 🔍 Step-by-Step Summary
1. Configure the theme by copying the theme's `config.toml` file into the project directory.
2. Edit the `config.toml` file to change variables such as the website title and URL.
3. Specify the theme to use in the `config.toml` file by adding the `theme` variable.
4. Create content for the website by adding Markdown files to the `content` directory.
5. Understand the content structure provided by Zola, where folders inside the `content` directory determine the website's URL structure.
6. Create a `_index.md` file to define a section page, such as a blog or landing page.

## 💡 Key Insights
* Each theme in Zola has its own `config.toml` file that can be used to configure the website.
* The `config.toml` file can be edited to change variables such as the website title, URL, and theme.
* Zola uses a content structure where folders inside the `content` directory determine the website's URL structure.
* A `_index.md` file can be used to define a section page, such as a blog or landing page.
* Markdown is a simple language used to generate structured documents, and is used to write content in Zola.
* Templates can be used to customize the layout and design of the website, and will be covered in future videos.

---

## 🗒️ Transcript (Auto-Generated)

> Hello friends, how are you doing? In the previous parts, we learned about how Jamstack architecture works and we took a look at Zola, which is the static site generator that we are using to build this website for our ITCresy. We created a project structure using the zolas init command and you can see the structure right here then we added a theme which was deep thought and the process of adding theme was very simple it was just cloning the deep thought repository from github inside themes directory you can also manually download the deep thought repository from github and then put the contents in this way like put the deep thought folder inside themes directory then you we also changed the config.toml file to say that we want to use this theme so we added a theme variable and then we were missing some variables in config.toml which were required for deep thought to work so it was not working then we copied these variables from the github page of the deep thought and it looks something like this right now very fresh is looking like this um it is possible when you try to read from the readme and try to add a variables one by one it is possible that you can miss few so we have found a nice way to get all the configurations from the theme and change whatever what we want so what we will do is copy the themes config.toml. So each theme is also a Zola website. So it has the same structure as the website that you have. So it has a config.toml. It has a content directory. It has few extra files, which you can also add. It has sass, like we have, it has static, templates, etc. The only special thing about theme that it might have a theme, it should have a theme.toml. we will not worry about it right now all we want to want is write this file config.toml we want this file inside our directory that is we want to overwrite our config.toml by the config.toml present inside deep thought or the theme whichever theme that you add so we can just this command will do that it will overwrite the config.toml that we have and then we now have all the variables that deep thought uses to configure the website and we can change the parts that we want to change by the way if you have not seen the previous parts and if you are not getting what is happening please check that videos out will you can can find the links above and you can also find the links in the description okay let's continue we will add the url of our website which is itcresi in our case sorry not commenting itcresi the title we can change to itcresi then we leave others as it is Change whatever you want to change and keep the others Now let's try what happens if we run this code. So we'll do zola serve and refresh. The theme is not coming up. Why was that? The reason is, previously also we did the same thing. we missed we are not telling Zola to use the theme how will it know which theme to use you can have multiple themes by the way inside themes directory but you have to say which theme you want to use so we will say theme equals to deep thought this is the folder name that you have inside themes directory and if I restart this the development server and refresh you can see it is working now and we have the title etc we have some navbar items it's an easy fix to change them if you want to this is the list that you have to change as you can see it's the list that we see here home posts tags categories home post tags categories etc you can change them like we don't want these two we just want about then about okay and now if any changes to config.toml you have to re rerun the development server and changes to content or any static files and templates it will be automatically reflected you won't have to restart it so just if you change any configuration inside the config.toml you have to refresh restart the browser restart the development server and we can see that we now have a different um navbar items sorry you can click on one of them and as there was there is no content right we have not added any content if we go in our project structure if you check the content is empty there's nothing inside content or anything we just have configured the uh website to use the deep thought theme now let's create content inside our website and for that we have to look at the structure that zola provides us with if you go to this documentation we can see that uh inside our content directory the basically the content directory is a directory where we add all our content so if you see the structure here that is there is a folder called as blogs blog then there is a folder called as landing so whatever structure you define or you make inside your content directory there is the main content directory is how your website will be structured or is how the urls will be structured so in this case you will see that your url is the base url that is http slash my website dot com slash blog then there is also base url slash landing so what happens is whatever folders you have inside your main content directory gets added after your base URL. That is your main website's URL. And the files that you create inside these folders that is if you see the cli file which is created inside the blog folder the this file name gets added after the slash blog url so the entire url becomes the base url that is website my website.com slash the folder name that is the blog and slash the cli usage name that is the file name but if you look at some if you look at a file which is underscore index.md and if we check the url that we have it is just slash block and it does not have slash underscore index.md sorry slash underscore index and why this is because underscore index.md is a special file what this does is whichever folder you want to make as a section that is you want to convert the folder as a section in this case the blog folder inside that folder we have to add a file that is underscore index.md now what a section is to understand in simple terms if we take the example of blog so the main page of blog where we'll have all our posts listed if we just see even the deep thought website we can see that there is a page called as posts and inside that post space we have different single posts listed is 11th post 10th post 9th post so this entire posts page p-o-s-d-s this url you can see this entire page is a section page and a single files or single pages inside that there is 11th post 10 post etc are the pages inside the file so even if we see the url here we can see that it is slash posts slash post dash 11. so the structure if we look at the structure of this deep thought inside our own themes directory we'll find that inside the content directory we'll have a folder named as posts therefore the URL will have base URL slash posts and if you look inside this posts directory we'll see there is an underscore index MD file but there are also other pages called as post 0 dot MD 1 dot MD 11 9 dot MD 8 dot MD and etc so the URL you saw was slash posts slash post-0 or slash posts slash post dot post-11 and if you look inside this post inside one of the MD files you will see there are different variables and inside the index file we will have something called as title description and the same is been used when you look at the main theme if you go to the posts section you will see that these variables are used here that is posts and the blog post accumulated over time so generally what happens is inside this section page that is the index underscore index or template you just use some variables which are listed in your theme that is listed in your template and apart from that what the template of this page does is it lists all the other pages that it has and it displays to you on the screen so what a template is and how to use it we'll see we'll be seeing in the upcoming videos of this series but for now just understand that a single folder is a section folder is a section and all the pages inside that are called as pages now similarly we create a page for our own integracy website but if you see the deep thoughts index page or the main page it has something written as deep thought then there's a text below that and even below the image there are some texts so if you look at our own website we don't have anything apart from the image and now we are going to add that and to add the text what we will do is we create our main content folder or we will create our base page as a section page and to do that to is create a underscore index.md file inside the main content folder and this is just a md file inside that we will have to enclose with three pluses includes inside these three pluses something of a toml structure and a toml structure is nothing but what we saw when we created or edited our config.toml file so similarly for this the toml structure has some variables these are predefined variables which zola provides us and these very set of variables are called as front matter and what happens is there are different types of font matters that Zola provides us with we will be using some of them in this index.md that is title and description we will be using and whatever you write apart from this section that is apart from the font matter section is your content part and that is to be written as MD and MD is nothing but a simple language that is used to generate structured documents and it is almost similar to plain text so what we'll do is we'll just add some text and you can see that it is appearing that is the title that we added and the description that we added are all appearing in our main that is index page and also the content that we added is appearing below our image now how this is appearing at a particular place that is how the title and uh the content are appearing above and below the image that is what we're going to what we are going to see when we create templates and when we use or edit the templates now just to look at what markdown is it is a simple language and we will be adding the description inside i will be adding a link in our description which through which you can uh look at how to write markdowns okay now we'll just add some markdown and we'll see how it looks you can see it has created a a heading a subheading paragraphs and some spaces and etc so it's a language which is used to create structured documents it's very simple you can have a look at the description that way you can have a look at the link in our description so that's it for this part in this part we saw how to configure our web theme and how to add content to our website and how the exact directory structure is and in the next part we'll be looking at how to add more content and also take a look at how the how and what are the templates and how to add edit them thank you

---

## 📝 Full Article Narrative

Introduction

In the world of web development, static site generators have become increasingly popular due to their speed, security, and ease of use. One such static site generator is Zola, which is built on the Jamstack architecture and written in Rust. In this article, we will explore the process of configuring a theme and creating content structure in Zola. We will be building a professional website for ITcracy using Zola, and this tutorial is part of a series that covers the entire process.

As we dive into the world of Zola, it's essential to understand the basics of Jamstack architecture and how Zola fits into it. In our previous tutorials, we covered the fundamentals of Jamstack and created a project structure using Zola's init command. We also added a theme called Deep Thought, which we will be using throughout this tutorial. Now, it's time to configure the theme and create content for our website.

The process of configuring a theme in Zola is relatively straightforward. Each theme has its own config.toml file, which can be used to configure the website. To configure the theme, we need to copy the theme's config.toml file into our project directory and edit it to change variables such as the website title and URL. We also need to specify the theme to use in the config.toml file by adding the theme variable. In our case, we will be using the Deep Thought theme, so we need to add the theme = "deepthought" variable to our config.toml file.

### Configuring the Theme

To configure the theme, we start by copying the theme's config.toml file into our project directory. This file contains all the variables that the theme uses to configure the website. We can then edit this file to change variables such as the website title and URL. For example, we can change the title to "ITcracy" and the URL to "https://itcracy.com". We can also change other variables such as the navbar items and the footer text.

### Creating Content Structure

Once we have configured the theme, we can start creating content for our website. Zola uses a content structure where folders inside the content directory determine the website's URL structure. For example, if we create a folder called "blog" inside the content directory, the URL for this folder will be "https://itcracy.com/blog". We can then create Markdown files inside this folder to create individual blog posts. The URL for each blog post will be "https://itcracy.com/blog/post-title".

To create a section page, such as a blog or landing page, we need to create a _index.md file inside the folder. This file will contain the content for the section page, and it will also list all the other pages inside the folder. For example, if we create a _index.md file inside the blog folder, it will contain the content for the blog section page, and it will also list all the individual blog posts.

### Writing Content with Markdown

Markdown is a simple language used to generate structured documents. It is almost similar to plain text, and it is easy to learn and use. To write content with Markdown, we simply need to create a Markdown file and start writing. We can use headers, paragraphs, lists, and other formatting options to create structured content. For example, we can create a header by using the # symbol, and we can create a paragraph by simply typing text.

In conclusion, configuring a theme and creating content structure in Zola is a relatively straightforward process. By copying the theme's config.toml file and editing it to change variables, we can configure the theme to our liking. By creating folders and Markdown files inside the content directory, we can create content for our website and determine the URL structure. With Markdown, we can write structured content that is easy to read and understand. In our next tutorial, we will cover the process of creating templates and customizing the layout and design of our website.

---

## ▶️ Watch the Video

* **Author:** ITcracy
* **Duration:** 13m

<div class="youtube-embed">
<iframe width="560" height="315" src="https://www.youtube.com/embed/GUQt52IXwXQ" frameborder="0" allowfullscreen></iframe>
</div>

[Watch on YouTube](https://www.youtube.com/watch?v=GUQt52IXwXQ)

---

## 🐦 Social Media Post (X/Twitter)

**Copy and Paste for Promotion (280 Character Limit):**

"Build a pro website with Zola! 🚀 Learn theme configuration & content structure in our latest tutorial 📄. Read now and take your Jamstack skills to the next level! 👉 https://x.com #jamstack #zola #website #staticsitegenerator"

