+++
title = "Zola tutorial #7: Deploying to gitlab pages | Static site generator | Jamstack"
date = "2025-11-03"
tags = [ "zola", "staticsitegenerator", "gitlab", "jamstack", "deployment",]

[extra]
youtube_id = "R_dKhFDfI4E"
+++

## TL;DR (Quick Summary)

> In this lesson we will learn about deploying zola websites to gitlab pages.

## 🎧 Listen to the Episode

<audio controls style="width: 100%;">
  <source src="./asset.mp3" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>

## 📋 Structured Key Takeaways

## 🔍 Step-by-Step Summary
1. Create a production build of your Zola website using the `zola build` command to generate a static build of your website.
2. Configure a service like GitLab Pages or Netlify to host your website by creating a config file.
3. Set up a GitLab account and create a project with a name that ends in `.gitlab.io` to deploy your website.
4. Push your website code to the GitLab project and let the CI/CD pipeline automatically deploy your website.
5. Verify your website is live by visiting the base URL specified in your config file.
6. Use the `--u` option with `zola build` to specify a base URL for your website.

## 💡 Key Insights
* Zola provides a `build` command to create a static build of your website, which can be deployed to any web server.
* To deploy to GitLab Pages, create a `.gitlab-ci.yml` file in your repository's root directory with the necessary configuration.
* The base URL for your website on GitLab Pages is determined by your project name, which should end in `.gitlab.io`.
* The CI/CD pipeline on GitLab will automatically deploy your website when you push code to your project's master branch.
* You can specify a base URL for your website using the `--u` option with `zola build`.
* Zola's documentation provides deployment guides for various services, including Netlify and GitLab Pages.

---

## 🗒️ Transcript (Auto-Generated)

> Hello friends, how are you doing? In the previous videos, we were building or creating our website using Zola and running a development server to see how the website looks like. But now we have deployed our website to GitLab and it is running live like it's an url itc.gitlab.io. You can even visit that and check the website that is running here. To do this, to get to this point, we just need to have two more steps from our last videos and these two steps are first to check whether your website is building properly so building as in zola provides us a command build which will create a static build of your website which has all the files and folders required for your website to run so zola is not required after that point these files are the static http html and css javascript files which you can just deploy to any web server and it will work so that step is required to just test whether the build works fine and then second is to use a service like gitlab or netlify and to deploy our website there and this is done in an automated fashion like once you set this up just once and after that every commit every push to your master branch in your repository we'll deploy your website like update your website continuously okay so first i'll show you how to do how to run the build or the zola build command and what it will do what it will do so we will go to our website and this is our project structure that you see here and this is our config.toml file so to run our build command you just have to say zola build so if you check our current content for the content of your directory you have content static templates etc and if you run zola build this will it is very fast generally so this will create a public directory which is your final build of your or or final build of your website so it has all the static files required for your website to run so if we check the content of public you see there is an index and then JavaScript CSS files etc Just this directory is enough for your website to work And this step to run build locally is not required but it can be used to check whether your website is properly building or not, if there is any issue or not. Now our website is working as we can do the release build and it works fine. can we just see we can see all the files created etc the next step is to use a service like GitLab or Netlify to host or create a continuous build of our website and host it live in a URL that it provides for free you can even change that URL by by buying a custom domain name and then you setting it up in the service itself now as Naveen showed you how to check or how to create a production build of your website we are left with two things to do which will deploy our website to a service first is to have a config file for whichever service you want to deploy your website to in our case we have deployed our website on gitlab pages so we will use or we will create a config file for gitlab dot for gitlab pages and for that you have to visit zola documentation and go inside the deployment part and you can see different services so we'll go to gitlab pages and you have to create uh as you see here it is mentioned that you have to create a dot gitlab slash sorry dot gitlab dash ci dot yml file in the root directory of your repository and add this content that you see in the black here you just have to copy paste this content in a file named as dot gitlab dash ci.yml in our case we have already copied it and if you see the documentations and our gitlab yml there is just one difference which is the zola build command so if you see here the zola build command is just zola build and in our document in our file we have something extra which is minus u option so what this minus u option does is it gives it gives you an option to specify your base URL in our case we have added HTTPS slash slash itgracy.gitlab.io where this URL comes from we'll show you in a while but just remember that this is how you can specify a base URL and if you have followed our series you must have seen that there is an option to specify a base url inside config file as well but as we are going to deploy our websites on more than one services so what we chose is we will have a base url for each service in its own file so minus you is the option through which you can specify base url and now we'll come to the second part which is having an account on gitlab so to deploy on gitlab you first need an account on gitlab and once you create account you also need a project where you will push your code or a repository on gitlab where you will push all your website code and the name of that project can be in one of the two ways so first way is you can straight away give the name as username.gitlab.io here in our case it is itc.gitlab.io username or group whatever you prefer so or you can give something else as well so it should be .gitlab.io so username.gitlab.io so in our case itc.gitlab.io it is just possible it is only username or the organization name so it's our repository is under an organization itc so it should be itc and if it's under your username so for example my username is now in carcara so it should be now in carcara.gitlab.io only these two project names will work other than that you can just have a random user random project name so you can have a random as navin mentioned you can have a random project as well so let's say if we add some other project name or such as website or xyz so what happens is you will have your website on itc.gitlab.io which is a username dot or project name dot sorry not project name group name username or group name dot gitlab.io slash the project name so in our case if you see our website it is directly hosted on itgrc.gitlab.io because that's the project name that we specified our group name was itgrc so itgrc.gitlab.io if let's say navin deploys on his profile with some other name so the name for the website will be navin.gitlab.io slash the name of the repository and yes that it so once you have these two things that is a config file and an account on GitLab with the project name whenever you push to your project master branch what will happen is GitLab will automatically run a process which is called CI CD pipeline and it will run whatever steps you have mentioned in your config file and create your website or make your website ready for you. you can visit the url that is the base url right itc.gitlab.io in our case and you can see your website live and if you are still confused as to what the url should be or what the url will be you can visit gitlab and go to the settings part of it and you can see that there is a section called as pages so if you go to that pages part what you will see is you will see the exact url that your website will be served on so in our case it is itc.gitlab.io and yep that's it how you can deploy your website on gitlab pages and for any other uh services you can refer to the documentation of get solar and you can go to the deployment part and you can see different services so in this case if you want to deploy on netlify then you can simply follow these steps and they are pretty much similar for each and every service you just have to create a config file for that service and copy paste this content simply and push your or website or code to that service and it will run a process just as gitlab and it will deploy your website there as well okay so this was the final video in our series of zola tutorial and following this series you should be able to at least build a simple website and deploy it in a gitlab service and if you have any doubts or questions regarding how to do some special features or special things in zola please let us know in the comments and we will try to help you also if you want to want us to make videos on specific features of zola which we have not covered in this series do let us know in the comments as well and we will try to make them also for any other services like gitlab pages or netlify if you want some detailed videos do let us know about that as well and we'll try to cover those videos as well okay thank you

---

## 📝 Full Article Narrative

Introduction

In the world of web development, static site generators have become increasingly popular due to their ease of use, flexibility, and performance. One such static site generator is Zola, which is built on the Jamstack architecture and offers a range of features that make it an attractive choice for developers. In this article, we will explore how to deploy a Zola website to GitLab Pages, a popular platform for hosting static websites. We will walk through the steps involved in creating a production build of your website, configuring GitLab Pages, and deploying your website.

As we continue our series on building a professional website using Zola, we will dive into the details of deploying our website to a live environment. In previous videos, we have covered the basics of creating a website using Zola and running a development server to test our website. Now, we will take the next step and deploy our website to GitLab Pages, which offers a free and easy-to-use platform for hosting static websites. By the end of this article, you will have a clear understanding of how to deploy your Zola website to GitLab Pages and make it available to the world.

To deploy a Zola website to GitLab Pages, we need to follow a few simple steps. First, we need to create a production build of our website using the `zola build` command. This command generates a static build of our website, which can be deployed to any web server. The resulting build includes all the necessary files and folders required for our website to run, including HTML, CSS, and JavaScript files. We can then use this build to deploy our website to GitLab Pages.

### Creating a Production Build

To create a production build of our website, we use the `zola build` command. This command is fast and efficient, and it generates a `public` directory that contains all the necessary files and folders required for our website to run. We can verify that the build is successful by checking the contents of the `public` directory, which should include an `index.html` file, as well as CSS and JavaScript files. If we encounter any issues during the build process, we can use this step to troubleshoot and resolve them.

### Configuring GitLab Pages

To deploy our website to GitLab Pages, we need to configure a few settings. First, we need to create a `.gitlab-ci.yml` file in the root directory of our repository. This file contains the necessary configuration for GitLab Pages to deploy our website. We can find the required configuration in the Zola documentation, which provides a sample `.gitlab-ci.yml` file that we can use as a starting point. We simply need to copy and paste the contents of this file into our own `.gitlab-ci.yml` file and modify it as needed.

One important setting that we need to configure is the base URL for our website. We can specify the base URL using the `--u` option with the `zola build` command. For example, if we want to deploy our website to `itcracy.gitlab.io`, we can use the following command: `zola build --u https://itcracy.gitlab.io`. This sets the base URL for our website and ensures that all links and assets are correctly referenced.

### Deploying to GitLab Pages

To deploy our website to GitLab Pages, we need to create a GitLab account and a project with a name that ends in `.gitlab.io`. We can then push our website code to the GitLab project and let the CI/CD pipeline automatically deploy our website. The CI/CD pipeline will run the necessary steps to build and deploy our website, including running the `zola build` command and configuring the necessary settings.

Once our website is deployed, we can verify that it is live by visiting the base URL that we specified. We can also use the GitLab Pages settings to verify the URL that our website will be served on. By following these simple steps, we can deploy our Zola website to GitLab Pages and make it available to the world.

In conclusion, deploying a Zola website to GitLab Pages is a straightforward process that requires just a few simple steps. By creating a production build of our website, configuring GitLab Pages, and deploying our website, we can make our website available to the world. Whether you are a seasoned developer or just starting out, Zola and GitLab Pages offer a powerful and flexible platform for building and deploying static websites. With this knowledge, you can now deploy your own Zola website to GitLab Pages and share it with the world.

---

## ▶️ Watch the Video

* **Author:** ITcracy
* **Duration:** 9m

<div class="youtube-embed">
<iframe width="560" height="315" src="https://www.youtube.com/embed/R_dKhFDfI4E" frameborder="0" allowfullscreen></iframe>
</div>

[Watch on YouTube](https://www.youtube.com/watch?v=R_dKhFDfI4E)
