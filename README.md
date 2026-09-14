## Candidate Configuration

This project uses local JSON configuration files to store candidate information and reusable job application answers.

For privacy reasons, the real configuration files are excluded from Git and should **not** be committed to a public repository.

### 1. Create your candidate profile

Copy the example profile:

```bash
cp candidate/profile.example.json candidate/profile.json
```

Then edit:

```text
candidate/profile.json
```

with your own information, including:

* Name and contact information
* Target job titles
* Preferred locations
* Salary preferences
* Years of experience
* Technical skills
* Work authorization and sponsorship requirements
* Seniority preferences
* Application behavior

The matching engine uses this file when evaluating job postings.

### 2. Create your application answer memory

Copy the example file:

```bash
cp candidate/application_answers.example.json candidate/application_answers.json
```

This file stores reusable answers to application questions encountered while processing job applications.

For example, differently worded questions such as:

```text
Have you worked at Anduril before?
Have you ever been employed by Anduril?
Have you had prior employment with Anduril?
```

can all be mapped internally to the same canonical question:

```text
previously_employed_by_company
```

Answers may be stored globally or per company depending on the type of question.

The agent can reuse previously saved answers so that the same question does not need to be answered repeatedly.

### Privacy

The following files are intentionally ignored by Git:

```text
candidate/profile.json
candidate/application_answers.json
```

They may contain personal information such as contact details, work authorization information, employment history, and application answers.

Do not remove these files from `.gitignore` unless you understand the privacy implications.

Only the example files should normally be committed:

```text
candidate/profile.example.json
candidate/application_answers.example.json
```
