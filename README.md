# bitbucket_deploy_key_util

This utility supports the following subcommands:

1. list_repos
2. add_deploy_key
3. list_deploy_keys
4. remove_deploy_key

It is self-documenting, use `./bitbucket_util.py -h` and `./bitbucket_util.py <subcommand> -h` to read the docs.

## Examples

List all repos matching any of `/-android$/` or `/-ios$/` or `/-web$/`:

    ./bitbucket_util list_repos "-android$" "-ios$" "-web$"

Add a key to all repositories matching the regex `/dingus$/`:

    ./bitbucket_util.py add_deploy_key --key "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDMl/FZf9AtrJBth+8swfDfJrRWetHHnew/LTwX86OGdcG4sJWE9QpWzO9K+szpxaFmMF729bKAUBMBWNoPrYApayyalirpe7fjzHqIWoq9CsP/wKDVSyMxVOiBwBnXSukS7i9iOiC2J9PyEQwAq7GJXI3E2UWyymW7rVyaDdYKLH9PdUMNmLfBpsDUyjdGO40pLjr6KCiyOTLI07Qy9iVz44VTRm6IBlxhee0DV3gw4GADHllSRVVOOngO+3493943sgfsfgsgsffgs3349349DFG346qi4WTeECB6JH87FhdCGS6mFyavpvOnrZdR9jGD auserbb" --label "Optional label" $(./bitbucket_util list_repos "dingus$")

Remove a key from all repositories that include it:

    SSH_KEY=ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDMl/FZf9AtrJBth+8swfDfJrRWetHHnew/LTwX86OGdcG4sJWE9QpWzO9K+szpxaFmMF729bKAUBMBWNoPrYApayyalirpe7fjzHqIWoq9CsP/wKDVSyMxVOiBwBnXSukS7i9iOiC2J9PyEQwAq7GJXI3E2UWyymW7rVyaDdYKLH9PdUMNmLfBpsDUyjdGO40pLjr6KCiyOTLI07Qy9iVz44VTRm6IBlxhee0DV3gw4GADHllSRVVOOngO+3493943sgfsfgsgsffgs3349349DFG346qi4WTeECB6JH87FhdCGS6mFyavpvOnrZdR9jGD auserbb
    SSH_FINGERPRINT=$(echo $SSH_KEY | ssh-keygen -E MD5 -lf /dev/stdin)
    REPOS_WITH_KEY=$(./bitbucket_util.py list_deploy_keys $(./bitbucket_util list_repos) | grep $SSH_FINGERPRINT | cut -f 2)
    ./bitbucket_util.py remove_deploy_key --key "$SSH_KEY" $REPOS_WITH_KEY