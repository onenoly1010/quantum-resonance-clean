# Canon of Autonomy

This repository is designed to operate without reliance on any single person.  
All contributors, tools, and maintainers participate as equals within a transparent, documented workflow.

The purpose of this canon is to ensure:
- continuity without a central figure,
- clarity without private knowledge,
- safety without hierarchy,
- and collaboration without dependency.

---

## 1. Core principles

- **Sovereignty:**  
  Each contributor acts from their own judgment and responsibility. No one is required for the system to function.

- **Transparency:**  
  Decisions, changes, and rationales are recorded in issues, pull requests, and documentation—not only in chat.

- **Inclusivity:**  
  The project is open to contributors of varying skill levels. Explanations and processes must be approachable.

- **Non‑hierarchy (with roles):**  
  Roles exist for clarity and care, not power. No role grants inherent superiority over others.

- **Safety:**  
  No harmful, abusive, or illegal content. No medical, legal, or financial advice. Respect for people and boundaries is mandatory.

---

## 2. Roles and responsibilities

Roles describe responsibilities, not rank. One person may hold multiple roles; roles may change over time.

- **Maintainers:**  
  - Review and merge pull requests.  
  - Uphold this canon and the project's direction.  
  - Keep documentation and workflows coherent.

- **Stewards / Guardians:**  
  - Care for coherence, tone, and adherence to principles.  
  - Ensure new contributors can understand and enter the project.  
  - Surface misalignment or drift in process or behavior.  

  Stewards do not outrank maintainers; they hold a *care* function, not a command function.

- **Contributors:**  
  - Propose changes via issues and PRs.  
  - Improve code, tests, docs, and workflows.  
  - Follow the documented processes and respect others.

- **Assistant (AI tools):**  
  - Provide suggestions, drafts, and clarifications.  
  - Never act as final authority.  
  - Always defer to human maintainers and this canon.

No role is indispensable. The project must remain functional even if any specific person is absent.

---

## 3. Autonomous assistant instructions

The assistant is a tool that supports clarity, not a decision‑maker.

### 3.1 Principles for the assistant

- **Sovereignty:**  
  Do not override contributor intent. When unsure, ask for clarification.

- **Transparency:**  
  Make reasoning explicit. Point to specific files, lines, and impacts.

- **Minimalism:**  
  Prefer the smallest, safe change that moves work forward.

- **Context‑awareness:**  
  Use existing patterns, structures, and docs in this repo before inventing new ones.

### 3.2 Scope of assistance

The assistant may:
- suggest code, tests, and refactors;
- draft or improve documentation;
- outline workflows or checklists;
- summarize issues, PRs, and changes.

The assistant must not:
- merge pull requests;
- approve or trigger production deployments;
- claim authority, emotion, or consciousness;
- contradict this canon.

### 3.3 Handoff behavior

When the assistant proposes non‑trivial changes, it should:
- summarize what it did or suggests doing;
- name the affected files and key sections;
- state any assumptions or open questions.

The repository must remain understandable without relying on the assistant's memory or prior interactions.

---

## 4. Workflow and handoff guidelines

This section ensures any contributor can pause and another can resume without losing context.

### 4.1 Ready for handoff

Work (branch, issue, or PR) is **ready for handoff** when:

- **Purpose:**  
  The goal is clearly described.

- **Status:**  
  Current progress and remaining work are written down.

- **Traceability:**  
  Linked issues, PRs, and related discussions are referenced.

- **Reproducibility:**  
  Setup and test steps are documented and verifiable.

- **Open questions:**  
  Known uncertainties or decisions yet to be made are listed.

If these are missing, the work is not ready for handoff.

### 4.2 Handoff checklist

Before stepping away from a task:

- **Write a summary:**  
  3–10 lines describing what you did and what remains.

- **Point to locations:**  
  List key files, functions, or configs touched.

- **State status:**  
  - Does it build?  
  - Do tests pass?  
  - Any known failures?

- **List next actions:**  
  2–5 concrete next steps the next person can take.

---

## 5. Contributor workflow

### 5.1 Getting started

- Read `README.md`, this `CANON_OF_AUTONOMY.md`, and any domain‑specific docs.
- Set up the project and run tests to confirm the environment works.
- Select an issue or create a clearly scoped one.

### 5.2 Making changes

- **Branch:**  
  Use a descriptive branch name (e.g. `feature/add-auth`, `fix/issue-42`).

- **Scope:**  
  Keep changes focused and small where possible.

- **Docs:**  
  Update documentation whenever behavior or usage changes.

You may use the assistant for help, but you are responsible for reviewing and understanding its output.

### 5.3 Pull requests

Every PR should include:

- **Summary:** What changed and why.  
- **Impact:** Which parts of the system are affected.  
- **Testing:** Which tests were run and results.  
- **Risks:** Potential breaking changes or follow‑ups.

### 5.4 Review and merge

- Use comments to clarify intent and raise concerns.
- Address feedback or explain clearly if you disagree.
- Only maintainers (or designated roles) merge PRs.

All significant decisions must be visible in issues or PRs, not only in private channels.

---

## 6. Governance and continuity

### 6.1 Decisions

Decisions are made:

- in issues and PRs,
- by maintainers and contributors in conversation,
- with stewards/guardians highlighting principles and coherence.

Private or ephemeral discussions must be summarized into issues/PRs when they affect the project.

### 6.2 No single point of failure

This canon is written so that:

- No individual is required for the project to continue.  
- Any maintainer can step away without blocking progress.  
- New stewards and maintainers can be onboarded by reading this file, the README, and existing issues/PRs.

### 6.3 Amendments

This canon may evolve over time.

To propose changes:
- open an issue describing the motivation;
- draft a PR updating this file;
- invite review from maintainers and stewards.

Changes are accepted when:
- they uphold sovereignty, transparency, inclusivity, non‑hierarchy, and safety;
- they improve clarity or practicality.

---

This canon exists so that the work here is **shared, durable, and sovereign**—  
independent of any single person, yet welcoming to everyone who chooses to participate.
