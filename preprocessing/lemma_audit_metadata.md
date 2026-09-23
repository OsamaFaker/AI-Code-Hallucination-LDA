# Lemmatization Audit -- Metadata (Analysis A)

- Documents: 66
- Distinct surface forms (post-filter, pre-correction): 2319
- Distinct lemmas after correction: 1820
- Surface forms with raw (pre-correction) lemmatization inconsistency: 89

## Applied deterministic corrections (plan SS7)

Fixed overrides (spaCy lemmatizer errors / non-standard-usage normalization):

- `cod` -> `code`
- `datum` -> `data`

Plural-merge map, derived from this representation's own HF-A/unigram baseline vocabulary (lemma `X` -> `Xs` merged into `X` when both occur): **35 mappings**.

| plural | -> singular |
|---|---|
| algorithms | algorithm |
| apis | api |
| applications | application |
| apps | app |
| assignments | assignment |
| challenges | challenge |
| chatbots | chatbot |
| commons | common |
| contexts | context |
| courses | course |
| engineers | engineer |
| examples | example |
| exercises | exercise |
| expectations | expectation |
| experiences | experience |
| explanations | explanation |
| factors | factor |
| hallucinations | hallucination |
| hands | hand |
| humans | human |
| instructors | instructor |
| interfaces | interface |
| issues | issue |
| languages | language |
| levels | level |
| llms | llm |
| models | model |
| outcomes | outcome |
| practices | practice |
| problems | problem |
| states | state |
| students | student |
| suggestions | suggestion |
| tasks | task |
| tools | tool |

## Raw (pre-correction) inconsistent lemmatization, for reference

| surface form | lemma : count |
|---|---|
| llms | llms:108, llm:37 |
| programming | programming:125, program:2 |
| models | model:80, models:34 |
| generated | generate:64, generated:3 |
| hallucinations | hallucination:55, hallucinations:6 |
| based | base:58, based:1 |
| engineering | engineering:45, engineer:1 |
| students | student:44, students:2 |
| tasks | task:43, tasks:1 |
| tools | tool:40, tools:4 |
| coding | cod:26, coding:5 |
| problems | problem:29, problems:1 |
| learning | learning:18, learn:10 |
| generating | generate:21, generating:3 |
| languages | language:20, languages:1 |
| challenges | challenge:14, challenges:3 |
| issues | issue:16, issues:1 |
| data | datum:11, data:5 |
| capabilities | capability:14, capabilities:1 |
| vulnerabilities | vulnerability:12, vulnerabilitie:1 |
| automated | automate:10, automated:3 |
| assignments | assignment:10, assignments:3 |
| debugging | debugging:7, debug:4 |
| apis | api:10, apis:1 |
| experiences | experience:10, experiences:1 |
| promising | promising:8, promise:2 |
| grading | grade:6, grading:4 |
| uses | use:6, us:3 |
| solving | solve:8, solving:1 |
| testing | testing:6, test:3 |
| examples | example:7, examples:2 |
| proposed | propose:8, proposed:1 |
| analyzed | analyze:7, analyzed:1 |
| applications | application:6, applications:1 |
| mitigating | mitigate:6, mitigating:1 |
| understanding | understand:4, understanding:3 |
| limited | limit:4, limited:3 |
| chatbots | chatbot:6, chatbots:1 |
| advanced | advanced:6, advance:1 |
| driven | drive:4, driven:3 |

The plural-merge map above resolves the great majority of these (e.g. llms/llm, models/model, tools/tool). Remaining residual cases are genuine part-of-speech-dependent inflections (a word used as both noun and verb across different documents, or an irregular plural the +s suffix rule does not cover) rather than lemmatizer errors, and are left uncorrected.

## Top 60 terms by frequency, after correction (manual eyeball review)

| lemma | count |
|---|---|
| code | 443 |
| llm | 215 |
| generation | 187 |
| chatgpt | 171 |
| model | 158 |
| language | 138 |
| programming | 125 |
| generate | 124 |
| hallucination | 103 |
| large | 99 |
| ai | 90 |
| study | 88 |
| software | 88 |
| tool | 66 |
| base | 61 |
| task | 58 |
| student | 57 |
| development | 54 |
| prompt | 45 |
| engineering | 45 |
| result | 44 |
| problem | 41 |
| provide | 37 |
| performance | 36 |
| work | 36 |
| paper | 35 |
| user | 35 |
| developer | 35 |
| use | 34 |
| research | 34 |
| api | 34 |
| demonstrate | 32 |
| potential | 31 |
| process | 31 |
| human | 31 |
| improve | 31 |
| test | 30 |
| feedback | 29 |
| solution | 29 |
| include | 29 |
| finding | 28 |
| propose | 28 |
| design | 28 |
| different | 28 |
| explore | 28 |
| challenge | 27 |
| dataset | 27 |
| evaluate | 27 |
| case | 26 |
| evaluation | 26 |
| class | 26 |
| issue | 26 |
| quality | 25 |
| education | 25 |
| empirical | 24 |
| gpt-4 | 24 |
| level | 24 |
| benchmark | 24 |
| program | 23 |
| requirement | 23 |
