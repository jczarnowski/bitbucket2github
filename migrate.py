import os
import argparse
import json

import git
from tabulate import tabulate
from github import Github, GithubException
from pybitbucket.bitbucket import Client 
from pybitbucket.repository import Repository
from pybitbucket.auth import BasicAuthenticator

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clone_dir', default='/tmp')
    parser.add_argument('--authfile', default='credentials.json')
    args = parser.parse_args()

    with open(args.authfile, 'r') as f:
        creds = json.load(f)

    # log into bitbucket and github
    github = Github(creds['github']['auth_token'])
    github_user = github.get_user()

    # verify github credentials by running a dummy command
    try:
        data = [(s.name, s.name) for s in github.get_user().get_repos()]
    except:
        print('Invalid GitHub token!')
        exit(1)

    bitbucket = Client(BasicAuthenticator(creds['bitbucket']['user'], creds['bitbucket']['auth_token'], creds['bitbucket']['mail']))

    # update the git command shell environment with SSH agent stuff
    global_git = git.Git()
    global_git.update_environment(**{ k: os.environ[k] for k in os.environ if k.startswith('SSH') })

    # list bitbucket repos
    repos = list()
    failed=list()
    for repo in Repository.find_repositories_by_owner_and_role(role='owner', client=bitbucket):
        item = {'name': repo.name, 
                'description': repo.description, 
                'private': repo.is_private, 
                'link': repo.links['clone'][1]['href'], 
                'copy': False}
        if repo.scm != 'git':
            print('Warning: repository {} will be ignored as it does not use git as SCM'.format(repo.name))
            item['reason'] = 'Non-git SCM: {}'.format(repo.scm)
            failed.append(item)
            continue
        repos.append(item)

    # ask the user which repos to copy
    proceed = False
    while not proceed:
        print('BitBucket Repositories to copy:')
        print(tabulate(repos, headers="keys"))
        print('Type a name of a repo to toggle it, "all" to toggle all or "go" to proceed with the current selection')

        while True:
            choice = raw_input('Choice [go|all]: ')
            if choice == 'go':
                proceed = True
                break
            elif choice == 'all':
                for r in repos:
                    r['copy'] = not r['copy']
                break

            item = next((item for item in repos if choice == item["name"]), None)
            if item is not None:
                item['copy'] = not item['copy']
                break
            print('{} not found!'.format(choice))

    # fliter repos with copy=False
    copy_repos = [it for it in repos if it['copy']]

    print('Final list to copy:')
    print(tabulate(copy_repos, headers="keys"))

    # do the copying
    for repo in copy_repos:
        print('[{}]'.format(repo['name']))

        # fetch or clone the bitbucket repository
        destdir=os.path.join(args.clone_dir, repo['name'])
        if os.path.exists(destdir):
            local_repo = git.Repo(destdir)
            print('{} exists and is a valid repo, fetching updates'.format(destdir))
            local_repo.remotes.origin.fetch()
        else:
            print('-- Cloning {}'.format(repo['link']))
            try:
                local_repo = git.Repo.clone_from(repo['link'], destdir)
            except:
                print('Clone failed')
                repo['reason'] = 'Clone failed'
                failed.append(repo)
                continue

        # try to create the repo on github
        try:
            print('-- Creating a GitHub repo')
            github_user.create_repo(repo['name'], description=repo['description'], private=repo['private'])
        except GithubException as e:
            print(e.data['message'])
            repo['reason'] = e.data['message']
            failed.append(repo)
            continue
        github_repo = github_user.get_repo(repo['name'])

        # push to github repo
        print('-- Pushing')
        try:
            if not 'github' in local_repo.remotes:
                remote = local_repo.create_remote('github', github_repo.ssh_url)
            else:
                remote = local_repo.remotes.github
            remote.push()
        except git.exc.GitCommandError as e:
            print('Failed to push')
            print(e)
            repo['reason'] = 'Push failed'
            failed.append(repo)
            continue

    if len(failed) > 0:
        print('Migration failed for: ')
        print(tabulate(failed, headers="keys"))


if __name__ == '__main__':
    main()
