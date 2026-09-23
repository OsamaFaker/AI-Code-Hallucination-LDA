# Lemmatization Audit -- Full text (Analysis B)

- Documents: 66
- Distinct surface forms (post-filter, pre-correction): 12070
- Distinct lemmas after correction: 9377
- Surface forms with raw (pre-correction) lemmatization inconsistency: 829

## Applied deterministic corrections (plan SS7)

Fixed overrides (spaCy lemmatizer errors / non-standard-usage normalization):

- `cod` -> `code`
- `datum` -> `data`

Plural-merge map, derived from this representation's own HF-A/unigram baseline vocabulary (lemma `X` -> `Xs` merged into `X` when both occur): **337 mappings**.

| plural | -> singular |
|---|---|
| abcdef_classes | abcdef_classe |
| actions | action |
| agents | agent |
| agreements | agreement |
| aids | aid |
| algorithms | algorithm |
| alternatives | alternative |
| amounts | amount |
| analytics | analytic |
| annotations | annotation |
| apirefs | apiref |
| apis | api |
| applications | application |
| apps | app |
| areas | area |
| arrays | array |
| assignments | assignment |
| assistants | assistant |
| assumptions | assumption |
| attacks | attack |
| attempts | attempt |
| attributes | attribute |
| authors | author |
| aws | aw |
| backgrounds | background |
| baselines | baseline |
| behaviors | behavior |
| benchmarks | benchmark |
| bins | bin |
| birds | bird |
| biswas | biswa |
| bugs | bug |
| candidates | candidate |
| cases | case |
| causes | cause |
| chains | chain |
| challenges | challenge |
| changes | change |
| characteristics | characteristic |
| chatbots | chatbot |
| chatgpts | chatgpt |
| cis | ci |
| cls | cl |
| cms | cm |
| codecontests | codecontest |
| codeforces | codeforce |
| codewars | codewar |
| cohens | cohen |
| collections | collection |
| combinations | combination |
| comments | comment |
| commits | commit |
| commons | common |
| comparisons | comparison |
| components | component |
| concepts | concept |
| conclusions | conclusion |
| conditions | condition |
| configs | config |
| configurations | configuration |
| conflicts | conflict |
| considerations | consideration |
| constraints | constraint |
| contexts | context |
| contributions | contribution |
| conventions | convention |
| courses | course |
| css | cs |
| cwes | cwe |
| cycles | cycle |
| datasets | dataset |
| declarations | declaration |
| definitions | definition |
| demographics | demographic |
| dependencies | dependencie |
| designs | design |
| details | detail |
| developers | developer |
| dfs | df |
| diagrams | diagram |
| dis | di |
| documents | document |
| domains | domain |
| dos | do |
| edges | edge |
| elements | element |
| emailutils | emailutil |
| endpoints | endpoint |
| ends | end |
| engineers | engineer |
| enumerations | enumeration |
| environments | environment |
| errors | error |
| ethics | ethic |
| examples | example |
| expectations | expectation |
| experiences | experience |
| experiments | experiment |
| experts | expert |
| explanations | explanation |
| expressions | expression |
| factors | factor |
| failures | failure |
| feathers | feather |
| features | feature |
| feeds | feed |
| fields | field |
| figs | fig |
| figures | figure |
| files | file |
| findings | finding |
| fis | fi |
| fms | fm |
| forms | form |
| fsms | fsm |
| funcs | func |
| functions | function |
| games | game |
| generates | generate |
| generations | generation |
| generators | generator |
| generics | generic |
| ghosts | ghost |
| giservices | giservice |
| gpt4hints | gpt4hint |
| gpus | gpu |
| graders | grader |
| grades | grade |
| graphics | graphic |
| groups | group |
| guidelines | guideline |
| hallucinations | hallucination |
| handles | handle |
| hendrycks | hendryck |
| heuristics | heuristic |
| hits | hit |
| holes | hole |
| https | http |
| humans | human |
| hyperparameters | hyperparameter |
| ides | ide |
| ids | id |
| impacts | impact |
| implications | implication |
| improvements | improvement |
| indicators | indicator |
| inputs | input |
| insertions | insertion |
| inspections | inspection |
| institutes | institute |
| instructors | instructor |
| interactions | interaction |
| interfaces | interface |
| invariants | invariant |
| involves | involve |
| ios | io |
| issues | issue |
| items | item |
| johns | john |
| judges | judge |
| katas | kata |
| keystrokes | keystroke |
| languages | language |
| lecturers | lecturer |
| lens | len |
| lessons | lesson |
| levels | level |
| librarians | librarian |
| limitations | limitation |
| lines | line |
| linters | linter |
| livestreams | livestream |
| llms | llm |
| lmms | lmm |
| lms | lm |
| locs | loc |
| logistics | logistic |
| logits | logit |
| logs | log |
| manybugs | manybug |
| mathematics | mathematic |
| means | mean |
| measures | measure |
| medians | median |
| messages | message |
| methods | method |
| metrics | metric |
| metricss | metrics |
| misinterpretations | misinterpretation |
| miss | mis |
| mistakes | mistake |
| mistakess | mistakes |
| mitigations | mitigation |
| models | model |
| modes | mode |
| names | name |
| negatives | negative |
| networks | network |
| news | new |
| nis | ni |
| num_less | num_les |
| numbers | number |
| objectives | objective |
| objects | object |
| obstacles | obstacle |
| occurrences | occurrence |
| operands | operand |
| operations | operation |
| opinions | opinion |
| options | option |
| oss | os |
| outcomes | outcome |
| outputs | output |
| overlooks | overlook |
| packages | package |
| pages | page |
| pairs | pair |
| pandas | panda |
| papers | paper |
| parameters | parameter |
| params | param |
| participants | participant |
| pas | pa |
| pass | pas |
| patterns | pattern |
| perspectives | perspective |
| phrs | phr |
| pointers | pointer |
| points | point |
| poles | pole |
| positives | positive |
| practices | practice |
| practitioners | practitioner |
| presentations | presentation |
| problems | problem |
| programmers | programmer |
| projects | project |
| prompts | prompt |
| proofs | proof |
| publications | publication |
| questions | question |
| quixbugs | quixbug |
| rates | rate |
| recommendations | recommendation |
| remarks | remark |
| removes | remove |
| repositories | repositorie |
| requirements | requirement |
| res | re |
| researchers | researcher |
| resources | resource |
| respondents | respondent |
| responses | response |
| results | result |
| retrievals | retrieval |
| reviewers | reviewer |
| reviews | review |
| rnns | rnn |
| rqs | rq |
| rules | rule |
| sales | sale |
| samples | sample |
| scenarios | scenario |
| sciences | science |
| scores | score |
| seconds | second |
| sections | section |
| sects | sect |
| segments | segment |
| sequences | sequence |
| services | service |
| settings | setting |
| signatures | signature |
| sis | si |
| skills | skill |
| slides | slide |
| snippets | snippet |
| sns | sn |
| solutions | solution |
| sources | source |
| spaces | space |
| sstubs | sstub |
| stacks | stack |
| stakes | stake |
| standards | standard |
| starts | start |
| statements | statement |
| states | state |
| statistics | statistic |
| steps | step |
| streamers | streamer |
| strengths | strength |
| strings | string |
| structures | structure |
| students | student |
| subjects | subject |
| submissions | submission |
| suggestions | suggestion |
| sums | sum |
| supports | support |
| surveys | survey |
| systems | system |
| tables | table |
| tags | tag |
| tasks | task |
| techniques | technique |
| teos | teo |
| tests | test |
| themes | theme |
| thoughts | thought |
| threats | threat |
| times | time |
| tokens | token |
| tools | tool |
| topics | topic |
| transformers | transformer |
| treatments | treatment |
| trees | tree |
| trends | trend |
| trials | trial |
| ttbs | ttb |
| types | type |
| units | unit |
| urls | url |
| users | user |
| variables | variable |
| variants | variant |
| verbs | verb |
| vms | vm |
| walkthroughs | walkthrough |
| weights | weight |
| windows | window |
| works | work |
| workshops | workshop |
| xss | xs |
| years | year |
| zybooks | zybook |

## Raw (pre-correction) inconsistent lemmatization, for reference

| surface form | lemma : count |
|---|---|
| generated | generate:1899, generated:29 |
| llms | llms:1144, llm:411 |
| programming | programming:1340, program:33 |
| models | model:1010, models:52 |
| tasks | task:953, tasks:16 |
| participants | participant:912, participants:10 |
| based | base:890, based:1 |
| data | datum:657, data:232 |
| tools | tool:844, tools:38 |
| results | result:872, results:2 |
| students | student:837, students:2 |
| coding | cod:591, coding:168 |
| problems | problem:690, problems:18 |
| cases | case:660, cases:23 |
| developers | developer:609, developers:2 |
| hallucinations | hallucination:557, hallucinations:37 |
| tests | test:479, tests:19 |
| prompts | prompt:465, prompts:15 |
| solutions | solution:448, solutions:12 |
| errors | error:418, errors:4 |
| generating | generate:398, generating:23 |
| learning | learning:278, learn:142 |
| questions | question:399, questions:20 |
| snippets | snippet:401, snippets:7 |
| types | type:361, types:15 |
| related | relate:287, related:64 |
| patterns | pattern:328, patterns:17 |
| following | follow:247, following:93 |
| users | user:312, users:1 |
| suggestions | suggestion:306, suggestions:6 |
| languages | language:301, languages:8 |
| training | training:275, train:28 |
| issues | issue:271, issues:14 |
| methods | method:276, methods:4 |
| understanding | understanding:189, understand:83 |
| scenarios | scenario:262, scenarios:2 |
| findings | finding:245, findings:6 |
| responses | response:247, responses:1 |
| capabilities | capability:243, capabilities:4 |
| challenges | challenge:239, challenges:4 |

The plural-merge map above resolves the great majority of these (e.g. llms/llm, models/model, tools/tool). Remaining residual cases are genuine part-of-speech-dependent inflections (a word used as both noun and verb across different documents, or an irregular plural the +s suffix rule does not cover) rather than lemmatizer errors, and are left uncorrected.

## Top 60 terms by frequency, after correction (manual eyeball review)

| lemma | count |
|---|---|
| code | 8504 |
| generate | 3122 |
| chatgpt | 2692 |
| llm | 2430 |
| model | 2359 |
| task | 1817 |
| prompt | 1814 |
| generation | 1746 |
| test | 1694 |
| problem | 1378 |
| tool | 1356 |
| programming | 1340 |
| hallucination | 1305 |
| al | 1304 |
| ai | 1294 |
| result | 1290 |
| study | 1236 |
| et | 1212 |
| language | 1209 |
| participant | 1144 |
| student | 1123 |
| case | 1067 |
| provide | 1055 |
| base | 1040 |
| use | 1024 |
| user | 953 |
| solution | 939 |
| example | 936 |
| data | 890 |
| question | 822 |
| error | 812 |
| work | 808 |
| developer | 806 |
| dataset | 788 |
| api | 785 |
| different | 756 |
| software | 745 |
| function | 721 |
| method | 707 |
| level | 703 |
| type | 699 |
| time | 699 |
| performance | 693 |
| output | 685 |
| show | 680 |
| process | 650 |
| include | 640 |
| high | 632 |
| correct | 628 |
| program | 615 |
| copilot | 596 |
| figure | 589 |
| snippet | 584 |
| table | 581 |
| number | 581 |
| python | 580 |
| input | 578 |
| analysis | 563 |
| project | 545 |
| design | 542 |
