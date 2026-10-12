# Project working agreement

Read `CONTRIBUTING.md` before making changes. Teach progressively, explain key operations and results in Chinese, and preserve room for future research without adding premature complexity.

## Publish each completed lesson

The user has explicitly requested ongoing GitHub maintenance after every completed lesson. This is a standing instruction for work on this project, not a background schedule.

1. Update the lesson notebook and any corresponding authoring helper. Execute and review the lesson, then refresh the curated report in `docs/reports/` when relevant.
2. Curate new questions, explanations, difficult concepts and important findings in `docs/learning_qa.md`. Summarize useful learning material; do not copy the full conversation or personal information.
3. Update the README, methodology, reproducibility instructions and roadmap when the lesson changes their content. Keep completed work distinct from future plans.
4. Run the applicable checks in `CONTRIBUTING.md`, inspect the diff, and exclude raw datasets, credentials, private information, environments and runtime files.
5. Commit the completed lesson and push to the confirmed public repository, `https://github.com/JerryCuZ/market-portfolio-lab`, using the JerryCuZ account. Routine lesson publication is already authorized; do not ask for the same authorization again. Respect tool permission requirements. Do not use a connector authenticated as another account.
6. Check the resulting GitHub Actions run and tell the user what changed, what was verified, and where to read it. If authentication, permissions, connectivity or CI blocks completion, report the exact remaining step instead of claiming publication or validation succeeded.

Do not force-push, overwrite unrelated work, publish private data, or place live trades as part of this maintenance workflow.
