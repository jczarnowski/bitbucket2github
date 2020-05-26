# bitbucket2github
A quick python script I have hacked in few hours to migrate my git repos from bitbucket to github. It uses python wrappers for the BitBucket and GitHub public API to list all repositories, lets the user select which ones to copy and pushes them to github.

```diff
-This comes with no warranty, use on your own responsibility!
```

## Dependencies
  * pybitbucket
  * PyGithub
  * tabulate
  * pygit
  
I have only ran the script with python 2.7 due to pybitbucket throwing errors with python3. Couldn't be bothered fixing this.

## Usage

Create your own credentials file `my_credentials.json` following the schema in `credentials.json`:

```
{
        "bitbucket": {
                "user": "bitbucket_username",
                "mail": "user@mail",
                "auth_token": ""
        },
        "github": {
                "auth_token": ""
        }
}
```

The GitHub auth token can be generated by going into `Settings->Developer Settings->Personal Access Tokens`. You only need to give it privileges to access your repos.

The bitbucket token is an app password generated in `Personal Settings->App Passwords`. This one only needs read access to your repos.

Once you're set, run the script with:
```
python2 migrate.py --authfile my_credentials.json
```
