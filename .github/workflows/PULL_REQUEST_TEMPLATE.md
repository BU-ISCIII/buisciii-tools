<!--
# bu-isciii tools pull request

Based on nf-core/viralrecon pull request template

Fill in the appropriate checklist below and delete whatever is not relevant.

PRs should be made against the dev branch, unless you're preparing a pipeline release.
-->

## PR checklist

- [ ] This comment contains a description of changes (with reason).
- [ ] Make sure your code lints (`black and flake8`).
- If a new tamplate was added make sure:
    - [ ] Template's schema is added in `templates/services.json`.
    - [ ] Template's pipeline's documentation in `assets/reports/md/template.md` is added.
    - [ ] Results Documentation in `assets/reports/results/template.md` is updated.
- [ ] `CHANGELOG.md` is updated.
- [ ] `README.md` is updated (including new tool citations and authors/contributors).
- [ ] If you know a new user was added to the SFTP, make sure you added it to `templates/sftp_user.json`
