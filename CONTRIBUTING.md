# Contributing

This is a learning-oriented research repository. Small, explainable changes are preferred.

1. State the question and the simplest relevant baseline.
2. Change one major research assumption at a time; record the data window, timing and costs.
3. Run `python -m unittest discover -s tests -v`. Add meaningful tests when accounting, data timing or optimization behavior changes.
4. Keep claims proportionate: historical improvement is not validated alpha; solver convergence is not profitability.
5. Selectively maintain `docs/learning_qa.md` by topic: preserve useful concepts, key misconceptions and research decisions; rewrite concisely, merge repetition and omit routine exchanges. Do not transcribe each question and answer. Link to lessons for detailed calculations and distinguish observed numbers from general principles.
6. Do not commit raw market datasets, personal account exports, credentials, local environments or runtime logs.
7. Keep source notebooks and their authoring helpers consistent. Only refresh curated reports after reviewing executed outputs.

Report bugs with the Python version, command, expected behavior and a small synthetic example where possible. Do not post credentials or private portfolio information in issues.

## Lesson completion and publication

After each completed lesson, publish its reviewed code, curated report and learning Q&A to GitHub. Update project documentation when its scope or assumptions change, run the applicable checks, inspect the final diff, then commit and push to `JerryCuZ/market-portfolio-lab`. Check GitHub Actions and report publication and validation status to the learner. Documentation-only edits may use `git diff --check`; code and research behavior changes require the tests above and relevant lesson execution.

This is the user's standing project-maintenance instruction. The agent workflow is recorded in `AGENTS.md`.
