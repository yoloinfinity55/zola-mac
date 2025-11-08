+++
title = "Zola tutorial #1: Build modern website using static site generator | Jamstack"
date = "2025-11-03"
tags = [ "website", "zola", "staticsitegenerator", "jamstack",]

[extra]
youtube_id = "rLcziFHhpPI"
+++

## TL;DR (Summary)

> In this series we will build a professional website for ITcracy using Zola, a static site generator in rust based on jamstack architecture.

## 🎧 Listen to the Episode

<audio controls style="width: 100%;">
  <source src="./asset.mp3" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>

## 🧭 Introduction
Are you tired of traditional website technologies that are slow, costly, and difficult to customize? Look no further! In this article, we'll explore the world of static site generators, specifically Zola, and how it can help you build a modern, fast, and cost-effective website. With the rise of Jamstack architecture, static site generators have become a popular choice for developers and non-developers alike. In this series, we'll build a professional website for ITcracy using Zola, and in this first lesson, we'll learn about the advantages of Jamstack-based static site generators over traditional website technologies.

The traditional approach to building websites involves using technologies like WordPress or Django, which can be slow, expensive, and require a lot of processing power. On the other hand, Jamstack-based static site generators like Zola offer a faster, more cost-effective, and easily customizable solution. With Zola, you can build a website that meets your conditions: fast, static pages, low hosting costs, easy customization, and the ability to add content without writing HTML or CSS code.

In this article, we'll break down the main steps and concepts covered in the video and provide key insights into the benefits of using Zola and Jamstack architecture. Whether you're a developer or a non-technical person, this article will provide you with a comprehensive understanding of how to build a modern website using Zola.

这段视频讲解了什么是 Zola 静态网站生成器，以及它相比传统网站技术（比如 WordPress 或 Django）的优势。以下是对初学者的简明中文梳理：



视频里提到：
- 传统网站（如 WordPress、Django）每次用户访问网页，服务器都要即时处理请求并生成 HTML。这种方式速度比较慢，且服务器成本高，需要一直在线运行。
- 静态网站生成器（如 Zola）是先把所有页面预先生成好，保存为纯静态 HTML 文件。用户访问时直接获取这些文件，因此速度更快、成本更低，可以免费托管在 Github、Gitlab 或 Netlify 等平台。

Zola 的特点有：
- 只需下载一个可执行文件，无需复杂安装
- 支持语法高亮、短代码、内部链接等功能
- 使用类似 Jinja 或 Django 的模板语言，适合有 Python 基础的人
- 内容可以用 Markdown 编写，不需要写 HTML 或 CSS

使用流程：
1. 选择一个 Zola 主题（不必自己写 HTML）
2. 马上用 Markdown 添加内容
3. 可以随时自定义和修改网站

适合哪些人？
- 想要速度快、成本低、易自定义的网站
- 不懂 HTML/CSS，只会写 Markdown
- 喜欢简单易用，而且可自由托管的建站方式

结论：Zola 帮助你用 Markdown 轻松建站，无需复杂代码与服务器运维，适合初学者和追求高效、低成本解决方案的人。


## 🔍 Step-by-Step Summary
Here's a step-by-step summary of the main concepts covered in the video:
1. **Introduction to traditional website technologies**: The video starts by explaining the traditional approach to building websites using technologies like WordPress or Django.
2. **Introduction to Jamstack architecture**: The video then introduces Jamstack architecture and how it differs from traditional website technologies.
3. **Advantages of Jamstack-based static site generators**: The video highlights the advantages of using Jamstack-based static site generators, including faster page loads, lower hosting costs, and easy customization.
4. **Introduction to Zola**: The video introduces Zola, a static site generator built in Rust, and explains why it was chosen for this project.
5. **Overview of the next lesson**: The video concludes by providing an overview of the next lesson, where we'll create a website using Zola and customize it to our liking.

## 💡 Key Insights
Here are the key insights and takeaways from the video:
* **Faster page loads**: Jamstack-based static site generators like Zola offer faster page loads since the pages are pre-rendered and pre-built.
* **Lower hosting costs**: With Jamstack-based static site generators, you can host your website for almost free on platforms like GitHub or GitLab Pages, or Netlify.
* **Easy customization**: Zola allows you to customize your website easily using markdown, without requiring any HTML or CSS code.
* **Security benefits**: Jamstack-based static site generators reduce the risk of attacks since there's no processing involved on the server-side.
* **Scalability**: Static site generators like Zola make it easy to scale your website, as you can simply put the static pages on a CDN or any server you want.
* ** Templating language**: Zola's templating language is similar to Jinja or Django templates, making it easier to develop websites, especially for those familiar with Python and Jinja.

## 🗒️ Transcript (Auto-Generated)

> Hello friends, how are you doing? We are planning to build a new website for itagrassi. And before starting, we have few conditions with what we want, right? So we want the website to be really fast. The output should be in static pages. So that should not be any processing involved on each request. Second, the hosting cost should be almost nil. third would be that it should be easily customizable we should be able to customize any part of it fourth would be we need to add content to it without having to write any html or css code okay so going by these conditions we have couple of options with us one or the first can be like WordPress, Django sites, etc, which are traditional web technologies. And what happens in these traditional web technologies is you send a request to web server that is you type www and then some processing happens on the server the HTML page is generated on the fly and you get back the result So let see if these steps or if this traditional web technologies fulfill our conditions And you can straight away see that as there is some processing on the fly involved, so it is losing speed and also as it requires some processing, it is not purely static. So you will need some or the other web server to host it. And obviously it won't be cost effective as well because you will have to spend for web servers cost as well. So what we have decided is to go to our other option, which is a static site generator. And static site generators are based on Jamstack architecture. What happens in Jamstack architecture is the pages are pre-rendered, pre-built HTML pages. And when you request for a website, that is, again, When you type www.xyz.com, you straight away get the pre-rendered pages. So how these match our conditions, how these Jamstack or the static site generators match our conditions are. They are static pages. So they are obviously fast. No processing is involved So obviously the threats or the attacks are reduced to greater extent as compared to traditional web technologies then being static pages they can be hosted almost free of cost on github or gitlab pages and netlify and many other hosting options they can also be scaled easily because they are just static pages again so you can put them in CDNs or any servers you want, you can shift them, shift the servers. If you're not happy with your service performance and you won't have to do much for seeing as well. Then what we have decided is we'll go ahead with these Jamstack based static site generators. Yeah. And the static site generators take markdown as input to create new content. So we don't have to write HTML, which was our last condition. And so in static site generators, also, you have many options. One of them is Zola. There are others like you go cats, we view press etc. But we have decided to go with Zola. As it has few advantages you can say it is just a single executable So there no installation process as such you just have to download a single executable and then you can use it It has other features like syntax highlighting short course internal links Don worry if you not getting what these are When we will be building the website you will understand it easily But the main reason for us to choose Zola is the templating language. So the templating language is similar to Jinja or Django templates. And these are used in Python applications. And since we are familiar with Python and Jinja, it will be much easier for us to develop these websites using Zola. and yeah so in the next part we will create the website by using a theme from zola we will choose one of the themes so that we don't have to write any html and just add our contents using markdown we will also show you how you can customize them to your liking and then build your own website so if you follow along it will be very easy for you guys to also create your website which you can update easily by using markdown only. Thank you.

## ▶️ Watch the Video

* **Author:** ITcracy
* **Duration:** 4m

<div class="youtube-embed">
<iframe width="560" height="315" src="https://www.youtube.com/embed/rLcziFHhpPI" frameborder="0" allowfullscreen></iframe>
</div>

[Watch on YouTube](https://www.youtube.com/watch?v=rLcziFHhpPI)
