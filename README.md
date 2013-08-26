Civic Ninjas Butsudan
=====================
Discovering and showcasing civic ninjas.

Forked from [Mozilla
webdev-contributors](https://github.com/mozilla/webdev-contributors)

Install requirements
--------------------
Install requirements:

    pip install -r requirements.txt

Set up GitHub App
-----------------
GitHub limits API calls for un-authenticated apps. You should [register an
app](http://developer.github.com/guides/basics-of-authentication/#registering-your-app)
because this script makes potentially thousands of API requests.

Then, set the following environment variables to use your App's id & secret:

    export GITHUB_CLIENT_ID=
    export GITHUB_CLIENT_SECRET=

Run it
------
Run:

    python get_contributors.py
