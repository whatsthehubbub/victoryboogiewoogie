# Your Daily Victory Boogie Woogie

The collaborative writing game we made for [De Gids](http://www.de-gids.nl/home).

(c) 2012-2013 All rights reserved.

# How to set up a fresh project (on OS X)

1. Install homebrew, by getting the commandline tools: https://developer.apple.com/downloads and then do the install homebrew here: http://mxcl.github.com/homebrew/
2. Open Terminal.app
3. Check python is installed by typing `python`
4. Install pip if you don't have it `sudo easy_install pip`
5. Use pip to install virtualenv (don't ask me why): `sudo pip install virtualenv`
6. Find a fresh place to checkout the project: git@github.com:whatsthehubbub/victoryboogiewoogie.git use the Mac client: http://mac.github.com/
7. In the terminal `cd` to where you just checked out the project, for instance: `cd ~/Documents/projects/sake/victorycheckout`
8. Create a virtual environment if you don't have one yet: `virtualenv venv --distribute`
9. Start a virtual environment: `source venv/bin/activate`
10. Install all the necessary packages: `pip install -r requirements.txt`
11. If you have never done so, setup the database: `python manage.py syncdb`, follow the instructions you get and note down the username and password that give you /admin access to the django site
12. Because we use *south* to create the tables for the application (and to update after model changes) you need to run: `python manage.py migrate`
13. Start the server with `python manage.py runserver` and go to your django at http://127.0.0.1:8000/admin

To restart the server simply repeat steps 9 and 13.
To be up to date again always do: 9, 10, 12, 13.


# How to front-end
1. Get accustomed to Less: http://lesscss.org
2. Download CodeKit: http://incident57.com/codekit/
3. Concatenate + minify  Styles and Scripts (and set output path to same folder)
4. Optimise images before uploading



# Deploy a branch

git push heroku develop:master


# Do a release (develop is our release branch)

1. git pull
1. git checkout master
2. git merge --no-ff develop
3. git tag -a tagname (optional)
4. git push
5. git push heroku master
6. heroku run python manage.py migrate boogie
5. git checkout develop

# Do an update to staging

1. git push staging master
2. heroku run --app dry-earth-9852 python manage.py collectstatic --noinput
2. Visit: http://dry-earth-9852.herokuapp.com/
