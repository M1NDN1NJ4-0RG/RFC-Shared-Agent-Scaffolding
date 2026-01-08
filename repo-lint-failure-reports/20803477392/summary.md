2026-01-08T02:42:35.4978493Z ##[debug]Starting: Vector Tests: Conformance
2026-01-08T02:42:35.4999218Z ##[debug]Cleaning runner temp folder: /home/runner/work/_temp
2026-01-08T02:42:35.5100240Z ##[debug]Starting: Set up job
2026-01-08T02:42:35.5101352Z Current runner version: '2.330.0'
2026-01-08T02:42:35.5144605Z ##[group]Runner Image Provisioner
2026-01-08T02:42:35.5145252Z Hosted Compute Agent
2026-01-08T02:42:35.5145811Z Version: 20251211.462
2026-01-08T02:42:35.5146358Z Commit: 6cbad8c2bb55d58165063d031ccabf57e2d2db61
2026-01-08T02:42:35.5146958Z Build Date: 2025-12-11T16:28:49Z
2026-01-08T02:42:35.5147597Z Worker ID: {8c807647-7ea1-4a05-ad02-02ecad8c0364}
2026-01-08T02:42:35.5148154Z ##[endgroup]
2026-01-08T02:42:35.5148609Z ##[group]Operating System
2026-01-08T02:42:35.5149068Z Ubuntu
2026-01-08T02:42:35.5149495Z 24.04.3
2026-01-08T02:42:35.5149872Z LTS
2026-01-08T02:42:35.5150296Z ##[endgroup]
2026-01-08T02:42:35.5150731Z ##[group]Runner Image
2026-01-08T02:42:35.5151430Z Image: ubuntu-24.04
2026-01-08T02:42:35.5151909Z Version: 20251215.174.1
2026-01-08T02:42:35.5153040Z Included Software: https://github.com/actions/runner-images/blob/ubuntu24/20251215.174/images/ubuntu/Ubuntu2404-Readme.md
2026-01-08T02:42:35.5154216Z Image Release: https://github.com/actions/runner-images/releases/tag/ubuntu24%2F20251215.174
2026-01-08T02:42:35.5155049Z ##[endgroup]
2026-01-08T02:42:35.5156019Z ##[group]GITHUB_TOKEN Permissions
2026-01-08T02:42:35.5157817Z Contents: write
2026-01-08T02:42:35.5158257Z Metadata: read
2026-01-08T02:42:35.5158712Z PullRequests: write
2026-01-08T02:42:35.5159230Z ##[endgroup]
2026-01-08T02:42:35.5161341Z Secret source: Actions
2026-01-08T02:42:35.5162268Z ##[debug]Primary repository: M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding
2026-01-08T02:42:35.5163059Z Prepare workflow directory
2026-01-08T02:42:35.5227491Z ##[debug]Creating pipeline directory: '/home/runner/work/RFC-Shared-Agent-Scaffolding'
2026-01-08T02:42:35.5230485Z ##[debug]Creating workspace directory: '/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding'
2026-01-08T02:42:35.5232055Z ##[debug]Update context data
2026-01-08T02:42:35.5235000Z ##[debug]Evaluating job-level environment variables
2026-01-08T02:42:35.5442183Z ##[debug]Evaluating job container
2026-01-08T02:42:35.5445517Z ##[debug]Evaluating job service containers
2026-01-08T02:42:35.5448161Z ##[debug]Evaluating job defaults
2026-01-08T02:42:35.5474762Z Prepare all required actions
2026-01-08T02:42:35.5514628Z Getting action download info
2026-01-08T02:42:35.9104890Z Download action repository 'actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683' (SHA:11bd71901bbe5b1630ceea73d27597364c9af683)
2026-01-08T02:42:35.9149598Z ##[debug]Copied action archive '/opt/actionarchivecache/actions_checkout/11bd71901bbe5b1630ceea73d27597364c9af683.tar.gz' to '/home/runner/work/_actions/_temp_3e41a8b4-e5ee-42ae-ab26-9a1ffc8cba77/d9d82dc8-bc78-4b3f-94f9-ee30e479ab54.tar.gz'
2026-01-08T02:42:35.9844853Z ##[debug]Unwrap 'actions-checkout-11bd719' to '/home/runner/work/_actions/actions/checkout/11bd71901bbe5b1630ceea73d27597364c9af683'
2026-01-08T02:42:35.9909062Z ##[debug]Archive '/home/runner/work/_actions/_temp_3e41a8b4-e5ee-42ae-ab26-9a1ffc8cba77/d9d82dc8-bc78-4b3f-94f9-ee30e479ab54.tar.gz' has been unzipped into '/home/runner/work/_actions/actions/checkout/11bd71901bbe5b1630ceea73d27597364c9af683'.
2026-01-08T02:42:36.0006279Z Download action repository 'actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2b' (SHA:0b93645e9fea7318ecaed2b359559ac225c90a2b)
2026-01-08T02:42:36.0368507Z ##[debug]Copied action archive '/opt/actionarchivecache/actions_setup-python/0b93645e9fea7318ecaed2b359559ac225c90a2b.tar.gz' to '/home/runner/work/_actions/_temp_7c43e521-c42b-4d26-a013-9c0272af9765/8bddab63-500c-4901-bdac-7f4605d5d175.tar.gz'
2026-01-08T02:42:36.0809800Z ##[debug]Unwrap 'actions-setup-python-0b93645' to '/home/runner/work/_actions/actions/setup-python/0b93645e9fea7318ecaed2b359559ac225c90a2b'
2026-01-08T02:42:36.0922071Z ##[debug]Archive '/home/runner/work/_actions/_temp_7c43e521-c42b-4d26-a013-9c0272af9765/8bddab63-500c-4901-bdac-7f4605d5d175.tar.gz' has been unzipped into '/home/runner/work/_actions/actions/setup-python/0b93645e9fea7318ecaed2b359559ac225c90a2b'.
2026-01-08T02:42:36.0967976Z ##[debug]action.yml for action: '/home/runner/work/_actions/actions/checkout/11bd71901bbe5b1630ceea73d27597364c9af683/action.yml'.
2026-01-08T02:42:36.1681359Z ##[debug]action.yml for action: '/home/runner/work/_actions/actions/setup-python/0b93645e9fea7318ecaed2b359559ac225c90a2b/action.yml'.
2026-01-08T02:42:36.1806171Z ##[debug]Set step '__actions_checkout' display name to: 'Checkout repository'
2026-01-08T02:42:36.1809850Z ##[debug]Set step '__actions_setup-python' display name to: 'Set up Python'
2026-01-08T02:42:36.1811951Z ##[debug]Set step '__run' display name to: 'Install pytest'
2026-01-08T02:42:36.1813753Z ##[debug]Set step '__run_2' display name to: 'Run vector tests'
2026-01-08T02:42:36.1814497Z Complete job name: Vector Tests: Conformance
2026-01-08T02:42:36.1837021Z ##[debug]Collect running processes for tracking orphan processes.
2026-01-08T02:42:36.1979788Z ##[debug]Finishing: Set up job
2026-01-08T02:42:36.2090514Z ##[debug]Evaluating condition for step: 'Checkout repository'
2026-01-08T02:42:36.2124696Z ##[debug]Evaluating: success()
2026-01-08T02:42:36.2129552Z ##[debug]Evaluating success:
2026-01-08T02:42:36.2143729Z ##[debug]=> true
2026-01-08T02:42:36.2149531Z ##[debug]Result: true
2026-01-08T02:42:36.2172187Z ##[debug]Starting: Checkout repository
2026-01-08T02:42:36.2243317Z ##[debug]Register post job cleanup for action: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
2026-01-08T02:42:36.2375634Z ##[debug]Loading inputs
2026-01-08T02:42:36.2387929Z ##[debug]Evaluating: github.repository
2026-01-08T02:42:36.2388970Z ##[debug]Evaluating Index:
2026-01-08T02:42:36.2390853Z ##[debug]..Evaluating github:
2026-01-08T02:42:36.2392261Z ##[debug]..=> Object
2026-01-08T02:42:36.2397801Z ##[debug]..Evaluating String:
2026-01-08T02:42:36.2398735Z ##[debug]..=> 'repository'
2026-01-08T02:42:36.2402763Z ##[debug]=> 'M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding'
2026-01-08T02:42:36.2404446Z ##[debug]Result: 'M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding'
2026-01-08T02:42:36.2408448Z ##[debug]Evaluating: github.token
2026-01-08T02:42:36.2408995Z ##[debug]Evaluating Index:
2026-01-08T02:42:36.2409438Z ##[debug]..Evaluating github:
2026-01-08T02:42:36.2410031Z ##[debug]..=> Object
2026-01-08T02:42:36.2410501Z ##[debug]..Evaluating String:
2026-01-08T02:42:36.2410954Z ##[debug]..=> 'token'
2026-01-08T02:42:36.2411928Z ##[debug]=> '***'
2026-01-08T02:42:36.2412509Z ##[debug]Result: '***'
2026-01-08T02:42:36.2430470Z ##[debug]Loading env
2026-01-08T02:42:36.2615032Z ##[group]Run actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
2026-01-08T02:42:36.2615827Z with:
2026-01-08T02:42:36.2616265Z   repository: M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding
2026-01-08T02:42:36.2616999Z   token: ***
2026-01-08T02:42:36.2617335Z   ssh-strict: true
2026-01-08T02:42:36.2617680Z   ssh-user: git
2026-01-08T02:42:36.2618051Z   persist-credentials: true
2026-01-08T02:42:36.2618440Z   clean: true
2026-01-08T02:42:36.2618809Z   sparse-checkout-cone-mode: true
2026-01-08T02:42:36.2619236Z   fetch-depth: 1
2026-01-08T02:42:36.2619582Z   fetch-tags: false
2026-01-08T02:42:36.2619932Z   show-progress: true
2026-01-08T02:42:36.2620296Z   lfs: false
2026-01-08T02:42:36.2620621Z   submodules: false
2026-01-08T02:42:36.2620982Z   set-safe-directory: true
2026-01-08T02:42:36.2621934Z ##[endgroup]
2026-01-08T02:42:36.3554627Z ##[debug]GITHUB_WORKSPACE = '/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding'
2026-01-08T02:42:36.3556173Z ##[debug]qualified repository = 'M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding'
2026-01-08T02:42:36.3557060Z ##[debug]ref = 'refs/pull/288/merge'
2026-01-08T02:42:36.3557798Z ##[debug]commit = 'f1babcc31e4e9b36c5a0468e414b1fc73121a9ba'
2026-01-08T02:42:36.3558524Z ##[debug]clean = true
2026-01-08T02:42:36.3559095Z ##[debug]filter = undefined
2026-01-08T02:42:36.3559696Z ##[debug]fetch depth = 1
2026-01-08T02:42:36.3560592Z ##[debug]fetch tags = false
2026-01-08T02:42:36.3561470Z ##[debug]show progress = true
2026-01-08T02:42:36.3562296Z ##[debug]lfs = false
2026-01-08T02:42:36.3563299Z ##[debug]submodules = false
2026-01-08T02:42:36.3564360Z ##[debug]recursive submodules = false
2026-01-08T02:42:36.3565538Z ##[debug]GitHub Host URL =
2026-01-08T02:42:36.3567879Z ::add-matcher::/home/runner/work/_actions/actions/checkout/11bd71901bbe5b1630ceea73d27597364c9af683/dist/problem-matcher.json
2026-01-08T02:42:36.3639023Z ##[debug]Added matchers: 'checkout-git'. Problem matchers scan action output for known warning or error strings and report these inline.
2026-01-08T02:42:36.3643967Z Syncing repository: M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding
2026-01-08T02:42:36.3645309Z ::group::Getting Git version info
2026-01-08T02:42:36.3646357Z ##[group]Getting Git version info
2026-01-08T02:42:36.3647256Z Working directory is '/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding'
2026-01-08T02:42:36.3648370Z ##[debug]Getting git version
2026-01-08T02:42:36.3649071Z [command]/usr/bin/git version
2026-01-08T02:42:36.3695836Z git version 2.52.0
2026-01-08T02:42:36.3715638Z ##[debug]0
2026-01-08T02:42:36.3716614Z ##[debug]git version 2.52.0
2026-01-08T02:42:36.3717276Z ##[debug]
2026-01-08T02:42:36.3718433Z ##[debug]Set git useragent to: git/2.52.0 (github-actions-checkout)
2026-01-08T02:42:36.3719873Z ::endgroup::
2026-01-08T02:42:36.3720475Z ##[endgroup]
2026-01-08T02:42:36.3725001Z ::add-mask::***
2026-01-08T02:42:36.3731713Z Temporarily overriding HOME='/home/runner/work/_temp/6861b06c-8111-4f02-9682-4d1eca730d76' before making global git config changes
2026-01-08T02:42:36.3733260Z Adding repository directory to the temporary git global config as a safe directory
2026-01-08T02:42:36.3736401Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding
2026-01-08T02:42:36.3764599Z ##[debug]0
2026-01-08T02:42:36.3765232Z ##[debug]
2026-01-08T02:42:36.3769394Z Deleting the contents of '/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding'
2026-01-08T02:42:36.3773237Z ::group::Initializing the repository
2026-01-08T02:42:36.3774159Z ##[group]Initializing the repository
2026-01-08T02:42:36.3778072Z [command]/usr/bin/git init /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding
2026-01-08T02:42:36.3860768Z hint: Using 'master' as the name for the initial branch. This default branch name
2026-01-08T02:42:36.3862085Z hint: will change to "main" in Git 3.0. To configure the initial branch name
2026-01-08T02:42:36.3863438Z hint: to use in all of your new repositories, which will suppress this warning,
2026-01-08T02:42:36.3864527Z hint: call:
2026-01-08T02:42:36.3865087Z hint:
2026-01-08T02:42:36.3865796Z hint: 	git config --global init.defaultBranch <name>
2026-01-08T02:42:36.3866664Z hint:
2026-01-08T02:42:36.3867448Z hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
2026-01-08T02:42:36.3868811Z hint: 'development'. The just-created branch can be renamed via this command:
2026-01-08T02:42:36.3869911Z hint:
2026-01-08T02:42:36.3870465Z hint: 	git branch -m <name>
2026-01-08T02:42:36.3871285Z hint:
2026-01-08T02:42:36.3872201Z hint: Disable this message with "git config set advice.defaultBranchName false"
2026-01-08T02:42:36.3874109Z Initialized empty Git repository in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/.git/
2026-01-08T02:42:36.3876097Z ##[debug]0
2026-01-08T02:42:36.3877798Z ##[debug]Initialized empty Git repository in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/.git/
2026-01-08T02:42:36.3879309Z ##[debug]
2026-01-08T02:42:36.3880402Z [command]/usr/bin/git remote add origin https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding
2026-01-08T02:42:36.3903620Z ##[debug]0
2026-01-08T02:42:36.3904646Z ##[debug]
2026-01-08T02:42:36.3905717Z ::endgroup::
2026-01-08T02:42:36.3906280Z ##[endgroup]
2026-01-08T02:42:36.3907615Z ::group::Disabling automatic garbage collection
2026-01-08T02:42:36.3908503Z ##[group]Disabling automatic garbage collection
2026-01-08T02:42:36.3909457Z [command]/usr/bin/git config --local gc.auto 0
2026-01-08T02:42:36.3931756Z ##[debug]0
2026-01-08T02:42:36.3932773Z ##[debug]
2026-01-08T02:42:36.3933799Z ::endgroup::
2026-01-08T02:42:36.3934308Z ##[endgroup]
2026-01-08T02:42:36.3935269Z ::group::Setting up auth
2026-01-08T02:42:36.3935934Z ##[group]Setting up auth
2026-01-08T02:42:36.3940789Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-01-08T02:42:36.3959757Z ##[debug]1
2026-01-08T02:42:36.3960759Z ##[debug]
2026-01-08T02:42:36.3966553Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-01-08T02:42:36.4221051Z ##[debug]0
2026-01-08T02:42:36.4222271Z ##[debug]
2026-01-08T02:42:36.4226745Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-01-08T02:42:36.4252325Z ##[debug]1
2026-01-08T02:42:36.4252954Z ##[debug]
2026-01-08T02:42:36.4258203Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-01-08T02:42:36.4422397Z ##[debug]0
2026-01-08T02:42:36.4423003Z ##[debug]
2026-01-08T02:42:36.4429693Z [command]/usr/bin/git config --local http.https://github.com/.extraheader AUTHORIZATION: basic ***
2026-01-08T02:42:36.4450501Z ##[debug]0
2026-01-08T02:42:36.4457878Z ##[debug]
2026-01-08T02:42:36.4458533Z ::endgroup::
2026-01-08T02:42:36.4458858Z ##[endgroup]
2026-01-08T02:42:36.4459453Z ::group::Fetching the repository
2026-01-08T02:42:36.4459889Z ##[group]Fetching the repository
2026-01-08T02:42:36.4466324Z [command]/usr/bin/git -c protocol.version=2 fetch --no-tags --prune --no-recurse-submodules --depth=1 origin +f1babcc31e4e9b36c5a0468e414b1fc73121a9ba:refs/remotes/pull/288/merge
2026-01-08T02:42:37.1450821Z From https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding
2026-01-08T02:42:37.1452588Z  * [new ref]         f1babcc31e4e9b36c5a0468e414b1fc73121a9ba -> pull/288/merge
2026-01-08T02:42:37.1479343Z ##[debug]0
2026-01-08T02:42:37.1480408Z ##[debug]
2026-01-08T02:42:37.1481686Z ::endgroup::
2026-01-08T02:42:37.1482311Z ##[endgroup]
2026-01-08T02:42:37.1483439Z ::group::Determining the checkout info
2026-01-08T02:42:37.1484312Z ##[group]Determining the checkout info
2026-01-08T02:42:37.1485631Z ::endgroup::
2026-01-08T02:42:37.1486152Z ##[endgroup]
2026-01-08T02:42:37.1488709Z [command]/usr/bin/git sparse-checkout disable
2026-01-08T02:42:37.1518414Z ##[debug]0
2026-01-08T02:42:37.1519551Z ##[debug]
2026-01-08T02:42:37.1523846Z [command]/usr/bin/git config --local --unset-all extensions.worktreeConfig
2026-01-08T02:42:37.1547136Z ##[debug]0
2026-01-08T02:42:37.1548343Z ##[debug]
2026-01-08T02:42:37.1549435Z ::group::Checking out the ref
2026-01-08T02:42:37.1550247Z ##[group]Checking out the ref
2026-01-08T02:42:37.1552774Z [command]/usr/bin/git checkout --progress --force refs/remotes/pull/288/merge
2026-01-08T02:42:37.2234041Z Note: switching to 'refs/remotes/pull/288/merge'.
2026-01-08T02:42:37.2235005Z
2026-01-08T02:42:37.2235627Z You are in 'detached HEAD' state. You can look around, make experimental
2026-01-08T02:42:37.2237289Z changes and commit them, and you can discard any commits you make in this
2026-01-08T02:42:37.2239517Z state without impacting any branches by switching back to a branch.
2026-01-08T02:42:37.2240428Z
2026-01-08T02:42:37.2241035Z If you want to create a new branch to retain commits you create, you may
2026-01-08T02:42:37.2242726Z do so (now or later) by using -c with the switch command. Example:
2026-01-08T02:42:37.2243561Z
2026-01-08T02:42:37.2243911Z   git switch -c <new-branch-name>
2026-01-08T02:42:37.2244497Z
2026-01-08T02:42:37.2245188Z Or undo this operation with:
2026-01-08T02:42:37.2245714Z
2026-01-08T02:42:37.2246034Z   git switch -
2026-01-08T02:42:37.2246480Z
2026-01-08T02:42:37.2247216Z Turn off this advice by setting config variable advice.detachedHead to false
2026-01-08T02:42:37.2248204Z
2026-01-08T02:42:37.2249379Z HEAD is now at f1babcc Merge cd9b384aa0c015b074e2ba168e3b7d3464af8a63 into c243618685d70d49119e6e4bcb143fab8bb2eaa2
2026-01-08T02:42:37.2252217Z ##[debug]0
2026-01-08T02:42:37.2253360Z ##[debug]
2026-01-08T02:42:37.2254525Z ::endgroup::
2026-01-08T02:42:37.2255219Z ##[endgroup]
2026-01-08T02:42:37.2269565Z ##[debug]0
2026-01-08T02:42:37.2271226Z ##[debug]commit f1babcc31e4e9b36c5a0468e414b1fc73121a9ba
2026-01-08T02:42:37.2273082Z ##[debug]Author: Copilot <198982749+Copilot@users.noreply.github.com>
2026-01-08T02:42:37.2274342Z ##[debug]Date:   Thu Jan 8 02:40:09 2026 +0000
2026-01-08T02:42:37.2275234Z ##[debug]
2026-01-08T02:42:37.2276635Z ##[debug]    Merge cd9b384aa0c015b074e2ba168e3b7d3464af8a63 into c243618685d70d49119e6e4bcb143fab8bb2eaa2
2026-01-08T02:42:37.2278357Z ##[debug]
2026-01-08T02:42:37.2279397Z [command]/usr/bin/git log -1 --format=%H
2026-01-08T02:42:37.2291950Z f1babcc31e4e9b36c5a0468e414b1fc73121a9ba
2026-01-08T02:42:37.2298283Z ##[debug]0
2026-01-08T02:42:37.2300888Z ##[debug]f1babcc31e4e9b36c5a0468e414b1fc73121a9ba
2026-01-08T02:42:37.2302904Z ##[debug]
2026-01-08T02:42:37.2305465Z ##[debug]Unsetting HOME override
2026-01-08T02:42:37.2315109Z ::remove-matcher owner=checkout-git::
2026-01-08T02:42:37.2331069Z ##[debug]Removed matchers: 'checkout-git'
2026-01-08T02:42:37.2368356Z ##[debug]Node Action run completed with exit code 0
2026-01-08T02:42:37.2403452Z ##[debug]Save intra-action state isPost = true
2026-01-08T02:42:37.2405190Z ##[debug]Save intra-action state setSafeDirectory = true
2026-01-08T02:42:37.2407839Z ##[debug]Save intra-action state repositoryPath = /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding
2026-01-08T02:42:37.2414021Z ##[debug]Set output commit = f1babcc31e4e9b36c5a0468e414b1fc73121a9ba
2026-01-08T02:42:37.2416118Z ##[debug]Set output ref = refs/pull/288/merge
2026-01-08T02:42:37.2422903Z ##[debug]Finishing: Checkout repository
2026-01-08T02:42:37.2448677Z ##[debug]Evaluating condition for step: 'Set up Python'
2026-01-08T02:42:37.2453741Z ##[debug]Evaluating: success()
2026-01-08T02:42:37.2455301Z ##[debug]Evaluating success:
2026-01-08T02:42:37.2456840Z ##[debug]=> true
2026-01-08T02:42:37.2458116Z ##[debug]Result: true
2026-01-08T02:42:37.2459820Z ##[debug]Starting: Set up Python
2026-01-08T02:42:37.2516273Z ##[debug]Register post job cleanup for action: actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2b
2026-01-08T02:42:37.2547856Z ##[debug]Loading inputs
2026-01-08T02:42:37.2576907Z ##[debug]Evaluating: (((github.server_url == 'https://github.com') && github.token) || '')
2026-01-08T02:42:37.2578562Z ##[debug]Evaluating Or:
2026-01-08T02:42:37.2580990Z ##[debug]..Evaluating And:
2026-01-08T02:42:37.2584034Z ##[debug]....Evaluating Equal:
2026-01-08T02:42:37.2585933Z ##[debug]......Evaluating Index:
2026-01-08T02:42:37.2586965Z ##[debug]........Evaluating github:
2026-01-08T02:42:37.2588099Z ##[debug]........=> Object
2026-01-08T02:42:37.2589105Z ##[debug]........Evaluating String:
2026-01-08T02:42:37.2590122Z ##[debug]........=> 'server_url'
2026-01-08T02:42:37.2591376Z ##[debug]......=> 'https://github.com'
2026-01-08T02:42:37.2592432Z ##[debug]......Evaluating String:
2026-01-08T02:42:37.2593411Z ##[debug]......=> 'https://github.com'
2026-01-08T02:42:37.2597256Z ##[debug]....=> true
2026-01-08T02:42:37.2598282Z ##[debug]....Evaluating Index:
2026-01-08T02:42:37.2599218Z ##[debug]......Evaluating github:
2026-01-08T02:42:37.2600169Z ##[debug]......=> Object
2026-01-08T02:42:37.2601061Z ##[debug]......Evaluating String:
2026-01-08T02:42:37.2602198Z ##[debug]......=> 'token'
2026-01-08T02:42:37.2603595Z ##[debug]....=> '***'
2026-01-08T02:42:37.2604706Z ##[debug]..=> '***'
2026-01-08T02:42:37.2606004Z ##[debug]=> '***'
2026-01-08T02:42:37.2611983Z ##[debug]Expanded: ((('https://github.com' == 'https://github.com') && '***') || '')
2026-01-08T02:42:37.2613655Z ##[debug]Result: '***'
2026-01-08T02:42:37.2622063Z ##[debug]Loading env
2026-01-08T02:42:37.2635148Z ##[group]Run actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2b
2026-01-08T02:42:37.2636400Z with:
2026-01-08T02:42:37.2637101Z   python-version: 3.11
2026-01-08T02:42:37.2637906Z   check-latest: false
2026-01-08T02:42:37.2638945Z   token: ***
2026-01-08T02:42:37.2639684Z   update-environment: true
2026-01-08T02:42:37.2640543Z   allow-prereleases: false
2026-01-08T02:42:37.2641539Z ##[endgroup]
2026-01-08T02:42:37.4137311Z ##[debug]Python is expected to be installed into /opt/hostedtoolcache
2026-01-08T02:42:37.4140549Z ::group::Installed versions
2026-01-08T02:42:37.4142184Z ##[group]Installed versions
2026-01-08T02:42:37.4144778Z ##[debug]Semantic version spec of 3.11 is 3.11
2026-01-08T02:42:37.4147153Z ##[debug]isExplicit:
2026-01-08T02:42:37.4148513Z ##[debug]explicit? false
2026-01-08T02:42:37.4161817Z ##[debug]isExplicit: 3.10.19
2026-01-08T02:42:37.4163437Z ##[debug]explicit? true
2026-01-08T02:42:37.4168023Z ##[debug]isExplicit: 3.11.14
2026-01-08T02:42:37.4169657Z ##[debug]explicit? true
2026-01-08T02:42:37.4175185Z ##[debug]isExplicit: 3.12.12
2026-01-08T02:42:37.4176712Z ##[debug]explicit? true
2026-01-08T02:42:37.4183108Z ##[debug]isExplicit: 3.13.11
2026-01-08T02:42:37.4184825Z ##[debug]explicit? true
2026-01-08T02:42:37.4190613Z ##[debug]isExplicit: 3.14.2
2026-01-08T02:42:37.4192233Z ##[debug]explicit? true
2026-01-08T02:42:37.4196505Z ##[debug]isExplicit: 3.9.25
2026-01-08T02:42:37.4197969Z ##[debug]explicit? true
2026-01-08T02:42:37.4201550Z ##[debug]evaluating 6 versions
2026-01-08T02:42:37.4225454Z ##[debug]matched: 3.11.14
2026-01-08T02:42:37.4228193Z ##[debug]checking cache: /opt/hostedtoolcache/Python/3.11.14/x64
2026-01-08T02:42:37.4231330Z ##[debug]Found tool in cache Python 3.11.14 x64
2026-01-08T02:42:37.4255876Z Successfully set up CPython (3.11.14)
2026-01-08T02:42:37.4257530Z ::endgroup::
2026-01-08T02:42:37.4258215Z ##[endgroup]
2026-01-08T02:42:37.4266165Z ##[add-matcher]/home/runner/work/_actions/actions/setup-python/0b93645e9fea7318ecaed2b359559ac225c90a2b/.github/python.json
2026-01-08T02:42:37.4280494Z ##[debug]Added matchers: 'python'. Problem matchers scan action output for known warning or error strings and report these inline.
2026-01-08T02:42:37.4298226Z ##[debug]Node Action run completed with exit code 0
2026-01-08T02:42:37.4306443Z ##[debug]pythonLocation='/opt/hostedtoolcache/Python/3.11.14/x64'
2026-01-08T02:42:37.4308145Z ##[debug]PKG_CONFIG_PATH='/opt/hostedtoolcache/Python/3.11.14/x64/lib/pkgconfig'
2026-01-08T02:42:37.4309711Z ##[debug]pythonLocation='/opt/hostedtoolcache/Python/3.11.14/x64'
2026-01-08T02:42:37.4311310Z ##[debug]Python_ROOT_DIR='/opt/hostedtoolcache/Python/3.11.14/x64'
2026-01-08T02:42:37.4312775Z ##[debug]Python2_ROOT_DIR='/opt/hostedtoolcache/Python/3.11.14/x64'
2026-01-08T02:42:37.4314192Z ##[debug]Python3_ROOT_DIR='/opt/hostedtoolcache/Python/3.11.14/x64'
2026-01-08T02:42:37.4315736Z ##[debug]PKG_CONFIG_PATH='/opt/hostedtoolcache/Python/3.11.14/x64/lib/pkgconfig'
2026-01-08T02:42:37.4317306Z ##[debug]LD_LIBRARY_PATH='/opt/hostedtoolcache/Python/3.11.14/x64/lib'
2026-01-08T02:42:37.4320803Z ##[debug]Set output python-version = 3.11.14
2026-01-08T02:42:37.4322326Z ##[debug]Set output python-path = /opt/hostedtoolcache/Python/3.11.14/x64/bin/python
2026-01-08T02:42:37.4324345Z ##[debug]Finishing: Set up Python
2026-01-08T02:42:37.4340950Z ##[debug]Evaluating condition for step: 'Install pytest'
2026-01-08T02:42:37.4344218Z ##[debug]Evaluating: success()
2026-01-08T02:42:37.4345339Z ##[debug]Evaluating success:
2026-01-08T02:42:37.4346447Z ##[debug]=> true
2026-01-08T02:42:37.4347432Z ##[debug]Result: true
2026-01-08T02:42:37.4348716Z ##[debug]Starting: Install pytest
2026-01-08T02:42:37.4370943Z ##[debug]Loading inputs
2026-01-08T02:42:37.4373703Z ##[debug]Loading env
2026-01-08T02:42:37.4397344Z ##[group]Run python3 -m pip install --upgrade pip
2026-01-08T02:42:37.4398841Z [36;1mpython3 -m pip install --upgrade pip[0m
2026-01-08T02:42:37.4399909Z [36;1mpython3 -m pip install pytest[0m
2026-01-08T02:42:37.4435210Z shell: /usr/bin/bash -e {0}
2026-01-08T02:42:37.4436019Z env:
2026-01-08T02:42:37.4436847Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.14/x64
2026-01-08T02:42:37.4438188Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.14/x64/lib/pkgconfig
2026-01-08T02:42:37.4439606Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.14/x64
2026-01-08T02:42:37.4440834Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.14/x64
2026-01-08T02:42:37.4442353Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.14/x64
2026-01-08T02:42:37.4443618Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.14/x64/lib
2026-01-08T02:42:37.4444668Z ##[endgroup]
2026-01-08T02:42:37.4494284Z ##[debug]/usr/bin/bash -e /home/runner/work/_temp/037a56fa-62c3-4432-a4d2-afd92ca1c79b.sh
2026-01-08T02:42:39.5009595Z Requirement already satisfied: pip in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (25.3)
2026-01-08T02:42:40.2745316Z Collecting pytest
2026-01-08T02:42:40.3787423Z   Downloading pytest-9.0.2-py3-none-any.whl.metadata (7.6 kB)
2026-01-08T02:42:40.4070223Z Collecting iniconfig>=1.0.1 (from pytest)
2026-01-08T02:42:40.4260671Z   Downloading iniconfig-2.3.0-py3-none-any.whl.metadata (2.5 kB)
2026-01-08T02:42:40.4593724Z Collecting packaging>=22 (from pytest)
2026-01-08T02:42:40.4792852Z   Downloading packaging-25.0-py3-none-any.whl.metadata (3.3 kB)
2026-01-08T02:42:40.5082371Z Collecting pluggy<2,>=1.5 (from pytest)
2026-01-08T02:42:40.5275947Z   Downloading pluggy-1.6.0-py3-none-any.whl.metadata (4.8 kB)
2026-01-08T02:42:40.5670438Z Collecting pygments>=2.7.2 (from pytest)
2026-01-08T02:42:40.5860740Z   Downloading pygments-2.19.2-py3-none-any.whl.metadata (2.5 kB)
2026-01-08T02:42:40.6096633Z Downloading pytest-9.0.2-py3-none-any.whl (374 kB)
2026-01-08T02:42:40.6868910Z Downloading pluggy-1.6.0-py3-none-any.whl (20 kB)
2026-01-08T02:42:40.7074668Z Downloading iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
2026-01-08T02:42:40.7285872Z Downloading packaging-25.0-py3-none-any.whl (66 kB)
2026-01-08T02:42:40.7499718Z Downloading pygments-2.19.2-py3-none-any.whl (1.2 MB)
2026-01-08T02:42:40.7811295Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.2/1.2 MB 39.0 MB/s  0:00:00
2026-01-08T02:42:40.8032153Z Installing collected packages: pygments, pluggy, packaging, iniconfig, pytest
2026-01-08T02:42:41.6141812Z
2026-01-08T02:42:41.6151737Z Successfully installed iniconfig-2.3.0 packaging-25.0 pluggy-1.6.0 pygments-2.19.2 pytest-9.0.2
2026-01-08T02:42:41.6591373Z ##[debug]Finishing: Install pytest
2026-01-08T02:42:41.6598912Z ##[debug]Evaluating condition for step: 'Run vector tests'
2026-01-08T02:42:41.6601669Z ##[debug]Evaluating: success()
2026-01-08T02:42:41.6602017Z ##[debug]Evaluating success:
2026-01-08T02:42:41.6602403Z ##[debug]=> true
2026-01-08T02:42:41.6602757Z ##[debug]Result: true
2026-01-08T02:42:41.6603816Z ##[debug]Starting: Run vector tests
2026-01-08T02:42:41.6623714Z ##[debug]Loading inputs
2026-01-08T02:42:41.6625184Z ##[debug]Loading env
2026-01-08T02:42:41.6629089Z ##[group]Run python3 -m pytest tools/repo_lint/tests/test_vectors.py -v
2026-01-08T02:42:41.6629556Z [36;1mpython3 -m pytest tools/repo_lint/tests/test_vectors.py -v[0m
2026-01-08T02:42:41.6651875Z shell: /usr/bin/bash -e {0}
2026-01-08T02:42:41.6652107Z env:
2026-01-08T02:42:41.6652357Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.14/x64
2026-01-08T02:42:41.6652751Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.14/x64/lib/pkgconfig
2026-01-08T02:42:41.6653247Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.14/x64
2026-01-08T02:42:41.6653587Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.14/x64
2026-01-08T02:42:41.6653927Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.14/x64
2026-01-08T02:42:41.6654284Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.14/x64/lib
2026-01-08T02:42:41.6654568Z ##[endgroup]
2026-01-08T02:42:41.6678313Z ##[debug]/usr/bin/bash -e /home/runner/work/_temp/60b26040-b8df-45db-92ff-b118bf5b405b.sh
2026-01-08T02:42:42.0306776Z ============================= test session starts ==============================
2026-01-08T02:42:42.0307430Z platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /opt/hostedtoolcache/Python/3.11.14/x64/bin/python3
2026-01-08T02:42:42.0307873Z cachedir: .pytest_cache
2026-01-08T02:42:42.0488690Z rootdir: /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding
2026-01-08T02:42:42.0489268Z configfile: pyproject.toml
2026-01-08T02:42:42.0489508Z collecting ... collected 6 items
2026-01-08T02:42:42.0489765Z
2026-01-08T02:42:42.1116760Z tools/repo_lint/tests/test_vectors.py::test_python_docstring_vectors FAILED [ 16%]
2026-01-08T02:42:42.1123423Z tools/repo_lint/tests/test_vectors.py::test_bash_docstring_vectors SKIPPED [ 33%]
2026-01-08T02:42:42.1130058Z tools/repo_lint/tests/test_vectors.py::test_powershell_docstring_vectors SKIPPED [ 50%]
2026-01-08T02:42:42.1136539Z tools/repo_lint/tests/test_vectors.py::test_perl_docstring_vectors SKIPPED [ 66%]
2026-01-08T02:42:42.1145419Z tools/repo_lint/tests/test_vectors.py::test_vector_fixtures_exist PASSED [ 83%]
2026-01-08T02:42:42.1374578Z tools/repo_lint/tests/test_vectors.py::test_vector_schema_validation PASSED [100%]
2026-01-08T02:42:42.1375325Z
2026-01-08T02:42:42.1375599Z =================================== FAILURES ===================================
2026-01-08T02:42:42.1376277Z ________________________ test_python_docstring_vectors _________________________
2026-01-08T02:42:42.1376742Z
2026-01-08T02:42:42.1376919Z     def test_python_docstring_vectors():
2026-01-08T02:42:42.1377436Z         """Test Python docstring validation vectors.
2026-01-08T02:42:42.1377948Z
2026-01-08T02:42:42.1378193Z         :Purpose:
2026-01-08T02:42:42.1378720Z             Validates that Python docstring enforcement produces expected violations
2026-01-08T02:42:42.1379494Z             for missing docstrings, pragma exemptions, and edge cases.
2026-01-08T02:42:42.1380032Z
2026-01-08T02:42:42.1380377Z         :note: Loads and runs all Python docstring vectors from:
2026-01-08T02:42:42.1381029Z             conformance/repo-lint/vectors/docstrings/python-docstring-*.json
2026-01-08T02:42:42.1381809Z         """
2026-01-08T02:42:42.1382126Z         # Find all Python docstring vectors
2026-01-08T02:42:42.1382709Z         vector_files = list(DOCSTRINGS_DIR.glob("python-docstring-*.json"))
2026-01-08T02:42:42.1383375Z         assert vector_files, "No Python docstring vectors found"
2026-01-08T02:42:42.1383867Z
2026-01-08T02:42:42.1384151Z         for vector_file in vector_files:
2026-01-08T02:42:42.1385039Z             vector = load_vector(vector_file)
2026-01-08T02:42:42.1385512Z             fixture_path = REPO_ROOT / vector["fixture"]
2026-01-08T02:42:42.1385887Z
2026-01-08T02:42:42.1386170Z             # Run docstring validator on fixture
2026-01-08T02:42:42.1386688Z             actual_violations = run_docstring_validator(fixture_path)
2026-01-08T02:42:42.1387178Z
2026-01-08T02:42:42.1387469Z             # Compare with expected violations
2026-01-08T02:42:42.1388203Z >           compare_violations(actual_violations, vector["expected_violations"], vector["id"])
2026-01-08T02:42:42.1388734Z
2026-01-08T02:42:42.1388916Z tools/repo_lint/tests/test_vectors.py:323:
2026-01-08T02:42:42.1389419Z _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
2026-01-08T02:42:42.1389794Z
2026-01-08T02:42:42.1389901Z actual = []
2026-01-08T02:42:42.1391534Z expected = [{'line': 27, 'message': "Function 'no_doc' is missing a docstring", 'path': 'conformance/repo-lint/vectors/fixtures/p...ring", 'path': 'conformance/repo-lint/vectors/fixtures/python/docstring_test.py', 'rule_id': 'DOCSTRING.MISSING', ...}]
2026-01-08T02:42:42.1393207Z vector_id = 'python-docstring-001'
2026-01-08T02:42:42.1393491Z
2026-01-08T02:42:42.1393925Z     def compare_violations(actual: List[Dict], expected: List[Dict], vector_id: str) -> None:
2026-01-08T02:42:42.1395021Z         """Compare actual vs expected violations and assert match.
2026-01-08T02:42:42.1395521Z
2026-01-08T02:42:42.1395942Z         :param actual: List of actual violations from running validator
2026-01-08T02:42:42.1396615Z             expected: List of expected violations from vector file
2026-01-08T02:42:42.1397215Z             vector_id: ID of test vector (for error messages)
2026-01-08T02:42:42.1397675Z
2026-01-08T02:42:42.1398060Z         :raises AssertionError: If violations don't match expected
2026-01-08T02:42:42.1398564Z
2026-01-08T02:42:42.1398939Z         :note: Compares violations by normalized fields:
2026-01-08T02:42:42.1399408Z             - rule_id
2026-01-08T02:42:42.1399750Z             - symbol
2026-01-08T02:42:42.1400039Z             - symbol_kind
2026-01-08T02:42:42.1400318Z             - line
2026-01-08T02:42:42.1400596Z             - severity
2026-01-08T02:42:42.1400864Z
2026-01-08T02:42:42.1401539Z             Path matching is relaxed (basename only) to handle absolute vs relative paths.
2026-01-08T02:42:42.1402287Z             Message matching uses substring match to handle variation in error text.
2026-01-08T02:42:42.1402870Z         """
2026-01-08T02:42:42.1403241Z         # Sort both lists by symbol and line for stable comparison
2026-01-08T02:42:42.1403942Z         actual_sorted = sorted(actual, key=lambda v: (v.get("symbol", ""), v.get("line", 0)))
2026-01-08T02:42:42.1404859Z         expected_sorted = sorted(expected, key=lambda v: (v.get("symbol", ""), v.get("line", 0)))
2026-01-08T02:42:42.1405487Z
2026-01-08T02:42:42.1405771Z         # Build diagnostic message
2026-01-08T02:42:42.1406207Z         if len(actual_sorted) != len(expected_sorted):
2026-01-08T02:42:42.1406740Z             msg = f"\n{vector_id}: Violation count mismatch\n"
2026-01-08T02:42:42.1407437Z             msg += f"Expected {len(expected_sorted)} violations, got {len(actual_sorted)}\n\n"
2026-01-08T02:42:42.1408092Z             msg += "Expected violations:\n"
2026-01-08T02:42:42.1408534Z             for v in expected_sorted:
2026-01-08T02:42:42.1409076Z                 msg += f"  - {v.get('symbol')} (line {v.get('line')}): {v.get('rule_id')}\n"
2026-01-08T02:42:42.1409631Z             msg += "\nActual violations:\n"
2026-01-08T02:42:42.1410036Z             for v in actual_sorted:
2026-01-08T02:42:42.1410601Z                 msg += f"  - {v.get('symbol')} (line {v.get('line')}): {v.get('rule_id')}\n"
2026-01-08T02:42:42.1411337Z >           pytest.fail(msg)
2026-01-08T02:42:42.1411706Z E           Failed:
2026-01-08T02:42:42.1412112Z E           python-docstring-001: Violation count mismatch
2026-01-08T02:42:42.1412881Z E           Expected 3 violations, got 0
2026-01-08T02:42:42.1413316Z E
2026-01-08T02:42:42.1413618Z E           Expected violations:
2026-01-08T02:42:42.1414102Z E             - MissingClassDoc (line 31): DOCSTRING.MISSING
2026-01-08T02:42:42.1414672Z E             - method_without_doc (line 36): DOCSTRING.MISSING
2026-01-08T02:42:42.1415208Z E             - no_doc (line 27): DOCSTRING.MISSING
2026-01-08T02:42:42.1415627Z E
2026-01-08T02:42:42.1415930Z E           Actual violations:
2026-01-08T02:42:42.1416177Z
2026-01-08T02:42:42.1416378Z tools/repo_lint/tests/test_vectors.py:260: Failed
2026-01-08T02:42:42.1416927Z =========================== short test summary info ============================
2026-01-08T02:42:42.1417734Z FAILED tools/repo_lint/tests/test_vectors.py::test_python_docstring_vectors - Failed:
2026-01-08T02:42:42.1418480Z python-docstring-001: Violation count mismatch
2026-01-08T02:42:42.1418952Z Expected 3 violations, got 0
2026-01-08T02:42:42.1419207Z
2026-01-08T02:42:42.1419350Z Expected violations:
2026-01-08T02:42:42.1419738Z   - MissingClassDoc (line 31): DOCSTRING.MISSING
2026-01-08T02:42:42.1420263Z   - method_without_doc (line 36): DOCSTRING.MISSING
2026-01-08T02:42:42.1420748Z   - no_doc (line 27): DOCSTRING.MISSING
2026-01-08T02:42:42.1421049Z
2026-01-08T02:42:42.1421334Z Actual violations:
2026-01-08T02:42:42.1422037Z ==================== 1 failed, 2 passed, 3 skipped in 0.09s ====================
2026-01-08T02:42:42.1576199Z ##[error]Process completed with exit code 1.
2026-01-08T02:42:42.1587661Z ##[debug]Finishing: Run vector tests
2026-01-08T02:42:42.1604899Z ##[debug]Evaluating condition for step: 'Post Set up Python'
2026-01-08T02:42:42.1606453Z ##[debug]Evaluating: success()
2026-01-08T02:42:42.1606767Z ##[debug]Evaluating success:
2026-01-08T02:42:42.1607108Z ##[debug]=> false
2026-01-08T02:42:42.1607401Z ##[debug]Result: false
2026-01-08T02:42:42.1612436Z ##[debug]Evaluating condition for step: 'Post Checkout repository'
2026-01-08T02:42:42.1614591Z ##[debug]Evaluating: always()
2026-01-08T02:42:42.1614906Z ##[debug]Evaluating always:
2026-01-08T02:42:42.1615627Z ##[debug]=> true
2026-01-08T02:42:42.1615928Z ##[debug]Result: true
2026-01-08T02:42:42.1616412Z ##[debug]Starting: Post Checkout repository
2026-01-08T02:42:42.1669136Z ##[debug]Loading inputs
2026-01-08T02:42:42.1670639Z ##[debug]Evaluating: github.repository
2026-01-08T02:42:42.1670941Z ##[debug]Evaluating Index:
2026-01-08T02:42:42.1671451Z ##[debug]..Evaluating github:
2026-01-08T02:42:42.1671803Z ##[debug]..=> Object
2026-01-08T02:42:42.1672033Z ##[debug]..Evaluating String:
2026-01-08T02:42:42.1672281Z ##[debug]..=> 'repository'
2026-01-08T02:42:42.1672656Z ##[debug]=> 'M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding'
2026-01-08T02:42:42.1673087Z ##[debug]Result: 'M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding'
2026-01-08T02:42:42.1675366Z ##[debug]Evaluating: github.token
2026-01-08T02:42:42.1675654Z ##[debug]Evaluating Index:
2026-01-08T02:42:42.1675861Z ##[debug]..Evaluating github:
2026-01-08T02:42:42.1676084Z ##[debug]..=> Object
2026-01-08T02:42:42.1676288Z ##[debug]..Evaluating String:
2026-01-08T02:42:42.1676498Z ##[debug]..=> 'token'
2026-01-08T02:42:42.1676957Z ##[debug]=> '***'
2026-01-08T02:42:42.1677259Z ##[debug]Result: '***'
2026-01-08T02:42:42.1687650Z ##[debug]Loading env
2026-01-08T02:42:42.1691257Z Post job cleanup.
2026-01-08T02:42:42.2551195Z ##[debug]Getting git version
2026-01-08T02:42:42.2571239Z [command]/usr/bin/git version
2026-01-08T02:42:42.2603855Z git version 2.52.0
2026-01-08T02:42:42.2623872Z ##[debug]0
2026-01-08T02:42:42.2624531Z ##[debug]git version 2.52.0
2026-01-08T02:42:42.2624860Z ##[debug]
2026-01-08T02:42:42.2625508Z ##[debug]Set git useragent to: git/2.52.0 (github-actions-checkout)
2026-01-08T02:42:42.2628039Z ::add-mask::***
2026-01-08T02:42:42.2642027Z Temporarily overriding HOME='/home/runner/work/_temp/ed5450ad-4827-46be-b0d8-e8df4a347930' before making global git config changes
2026-01-08T02:42:42.2642908Z Adding repository directory to the temporary git global config as a safe directory
2026-01-08T02:42:42.2647218Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding
2026-01-08T02:42:42.2669328Z ##[debug]0
2026-01-08T02:42:42.2669728Z ##[debug]
2026-01-08T02:42:42.2676423Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-01-08T02:42:42.2697463Z ##[debug]1
2026-01-08T02:42:42.2697915Z ##[debug]
2026-01-08T02:42:42.2703147Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-01-08T02:42:42.2882428Z ##[debug]0
2026-01-08T02:42:42.2882987Z ##[debug]
2026-01-08T02:42:42.2889082Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-01-08T02:42:42.2907130Z http.https://github.com/.extraheader
2026-01-08T02:42:42.2911532Z ##[debug]0
2026-01-08T02:42:42.2912072Z ##[debug]http.https://github.com/.extraheader
2026-01-08T02:42:42.2912324Z ##[debug]
2026-01-08T02:42:42.2917411Z [command]/usr/bin/git config --local --unset-all http.https://github.com/.extraheader
2026-01-08T02:42:42.2937010Z ##[debug]0
2026-01-08T02:42:42.2937407Z ##[debug]
2026-01-08T02:42:42.2940974Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-01-08T02:42:42.3107788Z ##[debug]0
2026-01-08T02:42:42.3108299Z ##[debug]
2026-01-08T02:42:42.3108798Z ##[debug]Unsetting HOME override
2026-01-08T02:42:42.3157672Z ##[debug]Node Action run completed with exit code 0
2026-01-08T02:42:42.3159642Z ##[debug]Finishing: Post Checkout repository
2026-01-08T02:42:42.3203531Z ##[debug]Starting: Complete job
2026-01-08T02:42:42.3205205Z Uploading runner diagnostic logs
2026-01-08T02:42:42.3216664Z ##[debug]Starting diagnostic file upload.
2026-01-08T02:42:42.3217014Z ##[debug]Setting up diagnostic log folders.
2026-01-08T02:42:42.3218796Z ##[debug]Creating diagnostic log files folder.
2026-01-08T02:42:42.3228163Z ##[debug]Copying 1 worker diagnostic logs.
2026-01-08T02:42:42.3236468Z ##[debug]Copying 1 runner diagnostic logs.
2026-01-08T02:42:42.3237369Z ##[debug]Zipping diagnostic files.
2026-01-08T02:42:42.3314816Z ##[debug]Uploading diagnostic metadata file.
2026-01-08T02:42:42.3342401Z ##[debug]Diagnostic file upload complete.
2026-01-08T02:42:42.3342862Z Completed runner diagnostic log upload
2026-01-08T02:42:42.3343115Z Cleaning up orphan processes
2026-01-08T02:42:42.3626862Z ##[debug]Finishing: Complete job
2026-01-08T02:42:42.3657720Z ##[debug]Finishing: Vector Tests: Conformance
