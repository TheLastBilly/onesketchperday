# OneSketchADay
This is the source code for the [onesketchaday.art](onesketchaday.art) website run by me and a couple other friends. This repostitory contains the code for both the website's stack as well as the Discord bot we use to upload content into that website. This repository was written only for the purpose of transparency and to allow others who would like to contribute to the project to do so without having to request access to the code. It was not, however, created with the intention of making it easier for others to create websites similar to [onesketchaday.art](onesketchaday.art).

While you absolutely have my permission to do so (not that you'd need it given the license I used), I wrote this site with the intention of deploying it in a way that makes sense to me, and not necessarily someone else wanting to launch a similar site. I will describe the steps I used to deploy this website bellow, althought it is absolutely possible (and very easy too honestly) to do this without many of the tools I will be listing in the next section of this README.

## Requirements
This project was designed to be run on Ubuntu (so Linux) and it has not been tested with the Docker implementation used in Windows. You are free to try it in other operating systems however.

Once you get an Ubuntu box running, you'll need to install the following programs:
- git
- docker
- docker-compose
- vim/nano
- nginx

## Setup
### Getting the souce code
Copy and paste this command on your terminal
```bash
git clone https://github.com/TheLastBilly/onesketchaday
```

It will download all the contents of this repository into a folder called `onesketchaday`. From the same terminal window, enter that folder using the following command:
```bash
cd onesketchaday
```

### Configuring the environment
Open the [variables.env](/variables.env) file in a text editor. You can also do it from the terminal by using `vim`/`nano`
```bash
nano variables.env
```

Change all of the fields that end with `_PASSWORD` to something random. you don't need to worry too much about remembering what the new passwords are, just make sure that they are not trivial to figure out. I would also recommend you change the `ADMIN_PAGE` variable to something other than `admin` for security reasons. And of course, you need to change the `SITE_URL` and `DOMAIN` variables to your own url and domain respectively.

You will also need to create your own django key for the site, and store it in a file called `django-token`, located at the root of this repository. It is important that this key is unique, so please google how to safely create one yourself, but avoid using sites to get it if possible.

***Note: you can generate a random password on linux by using the following command:***
```bash
tr -dc A-Za-z0-9 </dev/urandom | head -c 13 ; echo ''
```

### Getting a Discord Bot API key
In order to upload content to your website, you will need to generate a Discord Bot API key. The steps on how to do this are detailed in a lot of websites, but I would recommend you use the [official discordpy documentation](https://discordpy.readthedocs.io/en/stable/discord.html).

Once you get your key you will need to paste it into a file named `discord-token` located in the same directory as the `django-token` file.

### Running the server
Once all the preparations are completed, just use the following command to start the server:
```bash
docker-compose up
```

This will start the web server and the discord bot. A directory called `sockets` will be created with the unix sockets required to connect your application to your web server. Check the output from the commands for any errors.