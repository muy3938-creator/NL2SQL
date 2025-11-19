DeepEye-SQL: A Software-Engineering-Inspired Text-to-SQL
Framework
Chong Chen
Huawei Cloud BU
Beijing, China
chenchong55@huawei.com

Boyan Li
HKUST(GZ)
Guangzhou, China
bli303@connect.hkust-gz.edu.cn

Zhujun Xue
Huawei Cloud BU
Beijing, China
xuezhujun@huawei.com

5
2
0
2

t
c
O
1
2

]

B
D
.
s
c
[

2
v
6
8
5
7
1
.
0
1
5
2
:
v
i
X
r
a

Yinan Mei
Huawei Cloud BU
Beijing, China
yinan.mei@huawei.com

Yuyu Luo∗
HKUST(GZ)
Guangzhou, China
yuyuluo@hkust-gz.edu.cn

Abstract

Large language models (LLMs) have advanced Text-to-SQL, yet
existing solutions still fall short of system-level reliability. The
limitation is not merely in individual modules – e.g., schema link-
ing, reasoning, and verification – but more critically in the lack
of structured orchestration that enforces correctness across the
entire workflow. This gap motivates a paradigm shift: treating Text-
to-SQL not as free-form language generation but as a software-
engineering problem that demands structured, verifiable orchestra-
tion. We present DeepEye-SQL, a software-engineering-inspired
framework that reframes Text-to-SQL as the development of a small
software program, executed through a verifiable process guided
by the Software Development Life Cycle (SDLC). DeepEye-SQL
integrates four synergistic stages: it grounds ambiguous user intent
through semantic value retrieval and robust schema linking; en-
hances fault tolerance with N-version SQL generation using diverse
reasoning paradigms; ensures deterministic verification via a tool-
chain of unit tests and targeted LLM-guided revision; and introduces
confidence-aware selection that clusters execution results to esti-
mate confidence and then takes a high-confidence shortcut or runs
unbalanced pairwise adjudication in low-confidence cases, yielding
a calibrated, quality-gated output. This SDLC-aligned workflow
transforms ad hoc query generation into a disciplined engineering
process. Using ∼30B open-source LLMs without any fine-tuning,
DeepEye-SQL achieves 73.5% execution accuracy on BIRD-Dev and
89.8% on Spider-Test, outperforming state-of-the-art solutions. This
highlights that principled orchestration, rather than LLM scaling
alone, is key to achieving system-level reliability in Text-to-SQL.

1 Introduction

Text-to-SQL is a task that converts natural-language questions into
SQL queries over a database [2, 19, 22–26]. Large language models

∗The Corresponding Author.

Permission to make digital or hard copies of all or part of this work for personal or
classroom use is granted without fee provided that copies are not made or distributed
for profit or commercial advantage and that copies bear this notice and the full citation
on the first page. Copyrights for components of this work owned by others than the
author(s) must be honored. Abstracting with credit is permitted. To copy otherwise, or
republish, to post on servers or to redistribute to lists, requires prior specific permission
and/or a fee. Request permissions from permissions@acm.org.
Conference’17, Washington, DC, USA
© 2026 Copyright held by the owner/author(s). Publication rights licensed to ACM.
ACM ISBN 978-x-xxxx-xxxx-x/YYYY/MM
https://doi.org/XXXXXXX.XXXXXXX

Figure 1: Key Idea of DeepEye-SQL

(LLMs) [42, 47, 52, 56] have substantially advanced Text-to-SQL,
achieving strong results on benchmarks such as Spider [51] and
BIRD [18]. For example, Alpha-SQL [15] leverages dynamic multi-
step reasoning, while XiYan-SQL [21] improves SQL generation and
multi-candidate SQL selection through task-specific fine-tuning.

Despite these advances, state-of-the-art performance on the
BIRD dataset remains around 70% execution accuracy [18], and
reliability further degrades in real-world deployments [6, 14]. This
observation indicates that recent advances, while promising, have
yet to translate into consistent system-level reliability.

The key limitation lies not in the optimization of individual mod-
ules – such as schema linking, reasoning, or post-hoc verification –
but in the lack of coherent orchestration that enforces correct-
ness across the entire workflow [7, 15, 21, 31, 32, 43, 48]. As a
result, current Text-to-SQL solutions struggle to: (i) define what
should be built, which requires precisely determining the semantic

Key IdeaSDLCSoftware DevelopmentLife Cycle Requirements AnalysisImplementationSDLC ModelTestingRelease1234Reverse EngineeringN-version ProgrammingUnit TestingQuality GateDeepEye-SQL    Parallel Execution   Direct Linking   Reversed LinkingValue-based Linking(Q, DB)   Union  Intent Scoping and Semantic Grounding    Skeleton-based ICL-based D&C-based    UnionN-version Programmingfor SQL Generation        Tool-Chain of CheckersLLMCheckerSQL Unit Testing and Revisionvia Tool-Chain    Conditional ExecutionSQL with ConﬁdenceUnbalanced VotingCalculate ScoreConﬁdence-aware SQL SelectionColumn ValuesLinked Schema  Correct SQL

Conference’17, July 2017, Washington, DC, USA

Boyan Li, Chong Chen, Zhujun Xue, Yinan Mei, and Yuyu Luo

scope of the user question and grounding it to the relevant database
entities through comprehensive schema linking and value retrieval;
(ii) implement the solution (i.e., SQL generation), which involves gen-
erating executable SQL queries that faithfully capture the inferred
semantics while maintaining diversity and completeness across
complex reasoning paths; (iii) verify its correctness, which requires
systematically validating the structural, logical, and semantic cor-
rectness of the generated SQL through interpretable checks [20];
and (iv) release the generated SQL, which requires quantifying confi-
dence through multi-source evidence and establishing measurable
acceptance criteria for determining whether a generated SQL query
is reliable enough for output.

This fundamental gap motivates a paradigm shift: Text-to-SQL
should be viewed not simply as a language generation task
powered by LLMs, but as a software-engineering problem that
requires structured orchestration and verifiable correctness.
From this perspective, generating a correct SQL query resembles
developing a small software program: the system must infer user
requirements from natural-language questions with respect to the
specified database, realize the intended logic through SQL genera-
tion, and ensure its correctness and reliability through systematic
testing and quality control. Inspired by the Software Development
Life Cycle (SDLC) [36] and illustrated in Figure 1, we structure
the Text-to-SQL generation workflow as a unified process that
integrates requirement analysis from natural-language questions,
SQL generation, verification of generated queries, and final release
through quality-gated control. However, implementing this idea in
practice is non-trivial and poses several challenges.

First, Text-to-SQL solutions must infer user intent from ambigu-
ous natural language and partially observed database schemas. We
term this challenge ambiguous requirement inference (challenge
C1). In the implementation stage, current methods rely on a single
reasoning path driven by one model [32] and one prompt config-
uration [14], resulting in insufficient fault tolerance (C2). In the
verification and validation stage, existing methods depend on prob-
abilistic signals such as self-consistency [15] or partial execution
feedback [54] rather than deterministic oracles to assess generated
SQL. We denote this challenge as unreliable verification and vali-
dation (C3). In the release stage, current methods lack calibrated
confidence estimation and measurable acceptance criteria for evaluat-
ing when a generated SQL query is reliable enough for output (C4).
Our Methodology: Software-Engineering-Inspired Frame-
work. To systematically address these challenges, we propose
DeepEye-SQL, which reframes Text-to-SQL as a verifiable SDLC-
style workflow with four stages (Figure 1). In requirements analysis,
we propose Semantic Value Retrieval and Robust Schema Linking,
i.e., combining direct, reversed, and value-based linking with re-
lational closure, to build a complete, database-grounded specifica-
tion, addressing ambiguous requirement inference (addressing the
challenge C1). In implementation, we adopt N-version program-
ming [4] with three independent generators (skeleton, in-context
learning, and divide-and-conquer) executed in parallel to diversify
reasoning under a fixed budget, providing fault tolerance (address-
ing C2). For verification and validation, we replace probabilistic
self-judgment with a tool-chain of checkers (syntax, clause/time,

Figure 2: DeepEye-SQL, a plug-and-play Text-to-SQL frame-
work, consistently surpasses prior SOTA methods using ∼30B
open-source LLMs without any task-specific fine-tuning.

JOIN, NULL/result) that trigger targeted LLM repair, ensuring ver-
ifiable correctness (addressing C3). Finally, in release, we introduce
confidence-aware selection that clusters execution results to esti-
mate confidence and then takes a high-confidence shortcut or runs
unbalanced pairwise adjudication in low-confidence cases, yielding
a calibrated, quality-gated output (addressing C4). As shown in Fig-
ure 2, this design enables DeepEye-SQL to integrate with diverse
LLMs and achieve notable accuracy improvements without any
fine-tuning.
Contributions. This paper makes the following contributions:
(1) A Novel SE-Inspired and Training-free Framework. We
propose DeepEye-SQL, which reframes Text-to-SQL as an SDLC-
guided, four-stage engineering workflow. The framework is training-
free and plug-and-play, improving system-level reliability across
diverse LLMs without any fine-tuning.
(2) A Suite of Principled Techniques for Reliability. We intro-
duce a set of techniques, each grounded in a specific software engi-
neering principle, to ensure end-to-end reliability. This includes: (i)
a fault-tolerant schema linking mechanism that combines multiple
strategies to guarantee specification completeness; (ii) a determin-
istic, tool-based revision process that acts as a unit testing suite for
reliable debugging; and (iii) an adaptive, confidence-aware selection
mechanism that serves as a quality gate for the final output.
(3) Extensive Experiments demonstrate that DeepEye-SQL achieves
state-of-the-art performance on challenging benchmarks. With the
Qwen3-Coder-30B-A3B model, DeepEye-SQL attains an execution
accuracy of 73.5% on BIRD-Dev and 89.8% on Spider-Test without
any model fine-tuning.

2 Problem Definition and Preliminary
2.1 Problem Definition

Text-to-SQL Task. The primary objective of the Text-to-SQL task
is to automatically translate a user’s question, expressed in natural
language, into a corresponding SQL query. Formally, given a data-
base schema D and a natural language question Q, the task is to
generate a SQL query S that correctly retrieves the answer to Q
from the database instance defined by D. The schema D is defined
as a set of tables {𝑇1,𝑇2, . . . ,𝑇𝑚 }, where each table 𝑇𝑖 consists of
a set of columns {𝐶𝑖1, 𝐶𝑖2, . . . , 𝐶𝑖𝑘 }. The goal is to find a mapping
function 𝑓 such that:

S = 𝑓 (Q, D)

BIRD (Dev)DeepEye-SQL30%40%50%60%70%80%CoT-BaselinePlug-in DeepEye-SQL+ 16.9%+ 9.6%73.5%69.7%SDLCSoftware DevelopmentLife Cycle LLM       Tool-Chain ofCheckers      Text-to-SQL SOTA (Alpha-SQL with Qwen2.5-Coder)Gemma-3Qwen2.5-CoderQwen3-Coder70.9%71.1%+ 11.8%DeepEye-SQL: A Software-Engineering-Inspired Text-to-SQL Framework

Conference’17, July 2017, Washington, DC, USA

Let ⟦S⟧D denote the result of executing query S on the database.
The generated query S is considered correct if ⟦S⟧D accurately
answers the user’s intent expressed in Q. The core challenge lies
in bridging the semantic gap between the unstructured natural
language Q and the structured query language representation S
within the context of the given schema D.

2.2 Text-to-SQL Solutions

The task of translating natural language into executable SQL queries
has evolved significantly [19]. The recent emergence of Large Lan-
guage Models (LLMs) has marked a new paradigm. Current re-
search on applying LLMs to Text-to-SQL is largely divided into two
categories: fine-tuning and prompting-based methods. Fine-tuning
methods adapt open-source models like Code Llama or Qwen for the
Text-to-SQL task by training them on large corpora of question-SQL
pairs [16, 17, 21, 40, 50]. This approach can yield highly efficient and
specialized models but may exhibit limited generalization to out-of-
domain or highly complex scenarios. In contrast, prompting-based
methods leverage the powerful in-context learning and reasoning
capabilities of very large, often proprietary, models like GPT-4o [10]
and Gemini [1] without requiring model training. To manage the
complexity of the task, these methods typically decompose the
process into a multi-stage pipeline, including sub-tasks like schema
linking, SQL generation, and refinement [14, 15, 27, 31, 32, 57].
While powerful, these frameworks often rely on a single generation
path and the fallible self-correction abilities of the LLM, which
can compromise robustness. Our work, DeepEye-SQL, belongs to
the prompting-based category but differentiates itself by explicitly
adopting a systematic framework inspired by software engineering.

2.3 Software Engineering

The challenge of building robust and reliable LLM-based systems
often mirrors the complexities of traditional software development.
In response, software engineering has established a set of core
principles to manage complexity and ensure product quality. The
Software Development Life Cycle (SDLC) [36] provides a founda-
tional, systematic process for software creation, typically involving
phases such as requirements analysis, implementation, testing, and
deployment. To deconstruct existing systems and inform new de-
signs, practitioners often employ Reverse Engineering [34], a process
of analyzing a finished product to deduce its underlying specifica-
tions. To enhance system reliability, fault tolerance techniques are
critical. A notable example is N-Version Programming [4], where
multiple, independently developed versions of a component are
executed in parallel, and their results are adjudicated to mask faults
and increase the likelihood of a correct outcome. For quality as-
surance, Unit Testing [35] is a fundamental practice. It involves the
granular testing of individual software components or “units” in
isolation to verify that each part functions correctly according to
its design specifications. This bottom-up approach is crucial for
identifying and rectifying defects early in the development process.
Finally, to govern the release process, a Quality Gate [37] acts as a
final checkpoint, enforcing a set of predefined criteria to determine
whether a software artifact meets the required quality standard
for deployment. While these principles are cornerstones of tradi-
tional software engineering, their systematic application to the

construction of LLM-based pipelines is an emerging area. Our work
is directly inspired by these paradigms, leveraging them to bring
a more structured, verifiable, and robust engineering discipline to
the Text-to-SQL problem.

3 DeepEye-SQL Overview
3.1 Overall Architecture

DeepEye-SQL is systematically organized as a multi-stage pipeline
inspired by the core principles of the Software Development Life
Cycle (SDLC). Rather than reproducing the entire SDLC process
literally, it abstracts and automates its essential workflow for Text-
to-SQL. Conceptually, DeepEye-SQL serves as a compressed and
self-contained microcosm of software development, where the “soft-
ware” being constructed is a single, correct SQL query. Following
this paradigm, the framework comprises four stages (Figure 3), each
aligned with a corresponding phase of the SDLC.
Phase-1: Intent Scoping and Semantic Grounding. Mirroring
the initial phase of any engineering project—answering “What
should be built?”—this stage is dedicated to accurately interpreting
user intent and defining the problem’s scope. It employs Semantic
Value Retrieval to ground the query in the database’s actual data and
Robust Schema Linking to identify necessary tables and columns.
This linking module uses a fault-tolerant hybrid strategy, com-
bining Direct, Reversed (inspired by reverse engineering [34]), and
Value-based methods avoid the “single point of failure” problem [45],
ensuring a comprehensive and fault-tolerant specification.
Phase-2: N-version Programming for SQL Generation. Analo-
gous to the implementation phase, this stage generates SQL queries.
To enhance robustness, we employ a strategy inspired by N-version
programming [4], a fault-tolerance technique where multiple, inde-
pendent implementations are created for the same problem. Our
framework instantiates this by producing a diverse set of SQL can-
didates in parallel from three distinct generators: a Skeleton-based,
an ICL-based, and a Divide-and-Conquer-based generator. It is cru-
cial to distinguish this approach from test-time scaling techniques
like self-consistency [46], which generate diversity by sampling
multiple outputs from a single generator. In contrast, our method
achieves a more principled and profound diversity, akin to true N-
version programming, as each generator employs a fundamentally
different reasoning process (e.g., SQL skeleton planning, example-
based reasoning, recursive decomposition). This engineered diver-
sity ensures a broader exploration of the solution space, significantly
increasing the probability of producing at least one correct query,
especially for complex scenarios where a single reasoning path
might fail.
Phase-3: SQL Unit Testing and Revision via Tool-Chain. This
phase embodies the critical software engineering principle of Unit
Testing [35]. Its purpose is to systematically verify the correctness
of each generated SQL candidate and revise any found defects. To
overcome the known unreliability of LLM self-correction [53], our
framework externalizes this process, emulating a rigorous, auto-
mated testing loop. Each SQL candidate is passed through a Tool-
Chain of Checkers—a suite of specialized, deterministic tools where
each checker acts as a test case for a specific unit of functionality

Conference’17, July 2017, Washington, DC, USA

Boyan Li, Chong Chen, Zhujun Xue, Yinan Mei, and Yuyu Luo

Figure 3: DeepEye-SQL Overview.

(e.g., syntax, JOIN correctness). If a flaw is detected, the tool pro-
vides an explicit and actionable directive to the LLM for a targeted
revision, mirroring a formal bug report and fix cycle.
Phase-4: Confidence-aware SQL Selection. The final phase cor-
responds to the release stage, governed by a Quality Gate. Instead
of simply choosing the most common answer, this stage arbitrates
which candidate is reliable enough to be “released”. Our Confidence-
aware SQL Selection mechanism performs this task. It first calculates
an execution-based confidence score for the top candidates. This
score is then evaluated against a predefined confidence threshold to
validate reliability. This validation determines the execution path:
high-confidence queries (those exceeding the threshold) pass the
quality gate directly for efficiency, while low-confidence queries
trigger a more nuanced, unbalanced LLM voting process to ensure
the most reliable query is ultimately selected.

4 The Design Details of DeepEye-SQL

In this section, we provide a detailed exposition of the technical
implementation of each phase within the DeepEye-SQL framework.
We will describe the specific algorithms and design rationales that
underlie our methodology.

4.1 Semantic Value Retrieval

A key Text-to-SQL challenge is the grounding problem: LLMs lack
awareness of specific database values, often generating SQL with
hallucinated or mismatched filter values (e.g., using country =
‘USA’ when the database stores ‘United States’). This issue is
particularly prevalent for high-cardinality, free-form text columns.
Addressing this mirrors the software engineering principle of depen-
dency resolution [30], which requires a system to be aware of valid
data constants it can operate on. To mitigate this, DeepEye-SQL
incorporates a Semantic Value Retrieval module that proactively
supplies the LLM with a contextually relevant subset of database
values, anchoring the generation process to the ground-truth data.

Phase-4: Conﬁdence-aware SQL SelectionQuestionRelevantColumn ValuesRevised SQLCandidatesRevised SQLCandidatesExecution-based Clustering &  Conﬁdence EstimationDatabaseClusteringConﬁdence EstimationTop-1 SQL, Conﬁdence: C1Top-2 SQL, Conﬁdence: C2……ExecutionResultClusteringRankingConﬁdence-Gated SelectionTop-K SQLsTop-1 SQL, Conﬁdence: C1Top-2 SQL, Conﬁdence: C2Top-K SQL, Conﬁdence: Ck……Final SQLThresholdValidationShortcut:High ConﬁdenceNeed Full Review:Low ConﬁdenceLLMC1 > C2UnbalancedVotingSQLWin RateUpdateAggregateConﬁdenceRerankSQL ScoreSQL withMax ScorePhase-3: SQL Unit Testing and Revision via Tool-ChainCheck-and-Revise ProcessQuestionLinkedSchemaRelevantColumn ValuesInitial SQLCandidatesChecker ToolsInitial SQLCandidatesTool-Chain of CheckersTool-Chain of CheckersTool-Chain of CheckersParallelRevised SQLCandidatesLLMChecker-1Checker-2…Checker-NCheckedErrorsReviseCollectSyntax CheckerResult CheckerJOIN CheckerTIME CheckerMaxMin CheckerNULL CheckerORDER-BY CheckerSELECT CheckerExecution-relatedStyle-relatedClause-relatedLLMLLMCheckedErrorsReviseCheckedErrorsReviseLinkedSchemaPhase-2: N-version Programming for SQL GenerationRelevantColumn ValuesLinkedSchemaQuestion❶ Skeleton-based SQL Generation❸ Divide-and-Conquer-based SQL Generation(a) SQL Component Analysis  & Planning(b) SQL Skeleton Generation(c) SQL Skeleton FillingSELECTFROMJOINGROUP BYORDER BY……LLMThinkingPlanningLLMSELECT……JOIN❷ ICL-based SQL GenerationFROMSQL SkeletonSQL SkeletonLLMSQL(a) Example Retrieval(b) Common Patterns Analysis(c) Mapping&Solving Target Question(a) Question  Decomposing(b) Sub-question Solving(c) Recursive ReassemblingQuestionTrainingDatasetRetrievalSimilarExamplesTop-KSimilarExamplesLLMParallelCommonPatternsCommonPatternsLLMSQLQuestionLLMSub-questionsSub-questionsLLMSub-answersSub-answersLLMSQLInitial SQL Candidates❶❷❸Phase-1: Intent Scoping and Semantic GroundingText-to-SQL InputQuestionDatabase❷ Robust Schema LinkingRelevantColumn ValuesDatabaseQuestionDirect Schema LinkingReversed Schema LinkingValue-based Schema LinkingParallelUnionLLMDirect ReasoningSQLOutputLinkedSchemaPrasingRelevantColumn ValuesThresholdFilterLoadValuesFew-shotsExtractRetrieveParallelOfﬂine Preprocessing❶ Semantic Value RetrievalDatabaseValuesResultEmbedderInputEmbeddingsOutputVector DatabaseHNSW-IndexQuestionLLMKeywordsVectorDatabaseC1CnColumn-levelParallel Retrieval…RelevantColumn ValuesOnline RetrievalLLMLinkedSchemaLinkedSchemaLinkedSchemaDeepEye-SQL: A Software-Engineering-Inspired Text-to-SQL Framework

Conference’17, July 2017, Washington, DC, USA

Algorithm 1 Online Semantic Value Retrieval
Input: User Question 𝑄, Set of Column Vector Indices { I𝑗 }𝑀

parameter 𝐾

Output: Retrieved Values Map M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 : 𝐶 𝑗 → V𝑗
// Step 1: Extract Keywords from the user question

1: K ← LLM − ExtractKeywords(𝑄 )

// Step 2: Retrieve values in parallel for each indexed column

𝑗 =1, Top-K

2: Initialize M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 ← ∅
3: for all index I𝑗 for column 𝐶 𝑗 in parallel do
4:
5:
6:
7:
8:
9:
10:

V𝑐𝑎𝑛𝑑𝑖𝑑𝑎𝑡𝑒𝑠 ← ∅
for all keyword 𝑘𝑖 ∈ K do
e𝑘𝑖 ← Embed(𝑘𝑖 )
V𝑝𝑎𝑟𝑡𝑖𝑎𝑙 ← SearchIndex( I𝑗 , e𝑘𝑖 , 𝐾 )
V𝑐𝑎𝑛𝑑𝑖𝑑𝑎𝑡𝑒𝑠 ← V𝑐𝑎𝑛𝑑𝑖𝑑𝑎𝑡𝑒𝑠 ∪ V𝑝𝑎𝑟𝑡𝑖𝑎𝑙

end for
V𝑠𝑜𝑟𝑡𝑒𝑑 ← SortBySimilarity( V𝑐𝑎𝑛𝑑𝑖𝑑𝑎𝑡𝑒𝑠 ) // Aggregate and

select top-K unique values

V𝑗 ← GetUniqueTopK( V𝑠𝑜𝑟𝑡𝑒𝑑, 𝐾 )

11:
12: M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 [𝐶 𝑗 ] ← V𝑗
13: end for
14: return M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑

Our value retrieval process is divided into two distinct stages: an ef-
ficient, one-time offline preprocessing stage for index construction,
and a rapid online retrieval stage executed at query time.
Offline Preprocessing. The primary objective of the offline phase
is to preprocess and index database values to enable efficient se-
mantic search. This process is executed once for any new database
and involves three steps.

Selective Value Extraction. Instead of a brute-force approach that
indexes every value—which would be computationally prohibitive
and introduce significant noise—we perform selective extraction.
We specifically target columns of type TEXT, as they are the primary
source of ambiguity and value-related hallucinations. To further
refine this process, we apply heuristics to exclude columns that,
despite being text-based, are unlikely to be used in semantic compar-
isons, such as columns containing UUIDs or exclusively numerical
identifiers. This strategic selection minimizes the indexing overhead
while enhancing the semantic relevance of the retrieved values.
Value Embedding. For each selected column 𝐶 𝑗 , we extract its unique
values. Each distinct value 𝑣 is then encoded into a high-dimensional
vector representation e𝑣 using a pretrained sentence embedding
model, specifically Qwen3-Embedding-0.6B [55]. This embedding
transforms discrete text strings into continuous semantic vectors,
where values with similar meanings are located closer to each other
in the vector space.

Vector Indexing. To facilitate fast similarity search, the generated
value embeddings for each column are used to build a vector in-
dex. We employ Chroma [5] with the Hierarchical Navigable Small
World (HNSW) algorithm [29] for this purpose. HNSW is highly
efficient for approximate nearest neighbor (ANN) search, making it
ideal for real-time applications. The result is a set of persistent, per-
column vector indices {I1, I2, ..., I𝑀 }, where each I𝑗 is an indexed
collection of all value embeddings for a column 𝐶 𝑗 .
Online Retrieval. During the online phase, when a user ques-

Algorithm 2 Robust Schema Linking
Input: User Question 𝑄, Database Schema D, Retrieved Values Map

M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 , Threshold 𝜃𝑣𝑎𝑙
Output: Final Linked Schema D𝑙𝑖𝑛𝑘𝑒𝑑

// Step 1: Execute the three linking strategies in parallel

1: begin parallel
2: D𝑑𝑖𝑟𝑒𝑐𝑡 ← LLM_DirectLink(𝑄, D, M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 )
S′ ← LLM_GenerateSQL(𝑄, D, M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 )
3:
4: D𝑟𝑒𝑣𝑒𝑟𝑠𝑒𝑑 ← ParseSchema( S′ )
5: D𝑣𝑎𝑙𝑢𝑒 ← FindValueBasedSchema( M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 , 𝜃𝑣𝑎𝑙 )
6: end parallel

// Step 2: Aggregate the results by taking the union

7: D𝑢𝑛𝑖𝑜𝑛 ← D𝑑𝑖𝑟𝑒𝑐𝑡 ∪ D𝑟𝑒𝑣𝑒𝑟𝑠𝑒𝑑 ∪ D𝑣𝑎𝑙𝑢𝑒

// Step 3: Enforce relational closure to ensure schema connectivity

8: D𝑙𝑖𝑛𝑘𝑒𝑑 ← EnforceClosure( D𝑢𝑛𝑖𝑜𝑛, D )
9: return D𝑙𝑖𝑛𝑘𝑒𝑑

tion 𝑄 is received, the system retrieves the most relevant values for
that question from the pre-built indices. This process is detailed in
Algorithm 1.

Keyword Extraction. First, we leverage the LLM to identify potential
entities and filter values within the user’s question 𝑄. Using a few-
shot prompting strategy, we instruct the LLM to extract a set of key
terms K = {𝑘1, 𝑘2, ..., 𝑘𝑁 } that are likely to appear in a WHERE clause.
For example, from the question “Show me all papers by authors
from France”, the LLM would extract keywords like “France”.

Parallel Multi-Column Retrieval. With the extracted keywords, we
perform a parallel search across all indexed columns. For each
indexed column 𝐶 𝑗 , we perform the following steps:

(1) For every keyword 𝑘𝑖 ∈ K, we generate its embedding e𝑘𝑖 us-

ing the same model from the offline phase.

(2) We query the corresponding column index I𝑗 with e𝑘𝑖 to
retrieve the top-𝐾 most similar values along with their simi-
larity scores (e.g., cosine similarity).

(3) After querying for all 𝑁 keywords, we obtain 𝑁 ×𝐾 candidate
values for column 𝐶 𝑗 . We aggregate these candidates, sort
them globally by their similarity scores in descending order,
and select the top-𝐾 unique values. This yields the final
retrieved value set V𝑗 for column 𝐶 𝑗 .

4.2 Robust Schema Linking

Schema linking, the task of identifying the correct subset of tables
and columns relevant to a user’s question, is a cornerstone of any
Text-to-SQL system [19]. Existing methods [14, 15, 43] often treat
this as a direct mapping task, which can be brittle when faced
with complex schemas or ambiguous questions. An error at this
stage is catastrophic, as an incomplete or incorrect schema makes
generating a correct SQL query nearly impossible. This critical
dependency is analogous to the role of a formal specification [8] in
software development; without an accurate specification, the final
product is destined to fail. To address this, we introduce a Robust
Schema Linking module that, inspired by the principle of fault
tolerance, combines multiple, diverse strategies to ensure the most
accurate and complete schema is identified. Our overall process is
detailed in Algorithm 2.

Conference’17, July 2017, Washington, DC, USA

Boyan Li, Chong Chen, Zhujun Xue, Yinan Mei, and Yuyu Luo

Our approach is a hybrid model that integrates three complemen-
tary linking techniques: (1) Direct Schema Linking, (2) Reversed
Schema Linking, and (3) Value-based Schema Linking.
Direct Schema Linking. This method represents the most con-
ventional approach, directly tasking the LLM with acting as a
schema analysis agent. Given the user’s question 𝑄, the full data-
base schema D, and the retrieved relevant values M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 , we
prompt the LLM to explicitly list all relevant schema components.
This process can be formalized as:

D𝑑𝑖𝑟𝑒𝑐𝑡 = LLMDirectLink (𝑄, D, M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 )

(1)

While effective for unambiguous queries, its performance can de-
grade in complex scenarios, making it an unreliable standalone
solution.
Reversed Schema Linking. Inspired by the software engineering
practice of reverse engineering [34], this technique reimagines the
schema linking process. Instead of asking the LLM to first identify
the schema, we prompt it to generate a draft SQL query directly,
providing it with the full context including the relevant values.
This approach is more effective because the task of generating
SQL code aligns more closely with an LLM’s pre-training on vast
code corpora [41]. We then use a static parser to extract all schema
components from the generated query 𝑆 ′. Formally, the process is:
D𝑟𝑒𝑣𝑒𝑟𝑠𝑒𝑑 = ParseSchema(LLMGenerateSQL (𝑄, D, M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 ))

(2)

This “answer-first” approach allows the LLM to implicitly perform
schema linking, often revealing components for complex joins or
subqueries that a direct analysis might miss.
Value-based Schema Linking. This technique provides an empiri-
cal, data-driven check to complement the model-driven approaches.
It operates on the principle that if a column contains values highly
similar to keywords in the question, that column is likely relevant.
This method leverages the retrieved values M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 from the
previous module. A column 𝐶 𝑗 is selected if any of its retrieved
values has a similarity score with any question keyword 𝑘 ∈ K that
exceeds a high-confidence threshold 𝜃𝑣𝑎𝑙 . This can be expressed as:
D𝑣𝑎𝑙𝑢𝑒 = {𝐶 𝑗 ∈ D |∃𝑣 ∈ M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 [𝐶 𝑗 ], ∃𝑘 ∈ K

s.t. Sim(𝑣, 𝑘) > 𝜃𝑣𝑎𝑙 }

(3)

This bottom-up method excels at resolving schema ambiguity. In
cases where multiple columns are plausible candidates, it precisely
identifies the correct one by grounding the selection in concrete
data values instead of potentially misleading column names.
Schema Union and Closure. The final step aggregates the results
and ensures the relational integrity of the linked schema. First, we
take the union of the schemas identified by all three methods:

D𝑢𝑛𝑖𝑜𝑛 = D𝑑𝑖𝑟𝑒𝑐𝑡 ∪ D𝑟𝑒𝑣𝑒𝑟𝑠𝑒𝑑 ∪ D𝑣𝑎𝑙𝑢𝑒

(4)

However, D𝑢𝑛𝑖𝑜𝑛 may be an incomplete, disconnected graph of
schema elements. To resolve this, we enforce relational closure. We
parse all foreign key relationships in the database schema D. For
any pair of tables (𝑇𝑖,𝑇𝑗 ) present in D𝑢𝑛𝑖𝑜𝑛, we automatically add
the corresponding primary and foreign key columns that link them.
This step guarantees that the final linked schema is a connected
graph, providing a solid foundation for constructing joins in the

Algorithm 3 N-version Programming for SQL Generation
Input: User Question 𝑄, Linked Schema D𝑙𝑖𝑛𝑘𝑒𝑑 , Retrieved Values Map

M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑

Output: Set of Initial SQL Candidates C𝑖𝑛𝑖𝑡𝑖𝑎𝑙

// Step 1: Retrieve few-shot examples for the ICL generator

1: E𝑓 𝑒𝑤−𝑠ℎ𝑜𝑡 ← RetrieveSimilarExamples(𝑄 )

// Step 2: Execute the three SQL generators in parallel

2: begin parallel
3:
4:
5:
6: end parallel

S𝑠𝑘𝑒𝑙 ← LLM_Skel(𝑄, D𝑙𝑖𝑛𝑘𝑒𝑑, M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 )
S𝑖𝑐𝑙 ← LLM_ICL(𝑄, D𝑙𝑖𝑛𝑘𝑒𝑑, M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 , E𝑓 𝑒𝑤−𝑠ℎ𝑜𝑡 )
S𝑑&𝑐 ← LLM_D&C(𝑄, D𝑙𝑖𝑛𝑘𝑒𝑑 , M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 )

// Step 3: Collect all generated SQLs into a candidate set

7: C𝑖𝑛𝑖𝑡𝑖𝑎𝑙 ← { S𝑠𝑘𝑒𝑙 , S𝑖𝑐𝑙 , S𝑑&𝑐 } // and other samples if N > 1 per gener-

ator

8: return C𝑖𝑛𝑖𝑡𝑖𝑎𝑙

SQL generation phase. This final, closed schema is defined as:

D𝑙𝑖𝑛𝑘𝑒𝑑 = EnforceClosure(D𝑢𝑛𝑖𝑜𝑛, D)

(5)

4.3 N-version Programming for SQL Generation

Upon establishing the query’s specification in the Intent Scoping
and Semantic Grounding phase, the framework proceeds to the im-
plementation stage: SQL generation. A single generation strategy,
however, often struggles with the diversity of user queries [31]; a
method effective for simple lookups may fail on complex analyt-
ical questions [32]. To address this, DeepEye-SQL instantiates a
fault-tolerant strategy inspired by the software engineering prin-
ciple of N-version programming [4]. Instead of relying on a single,
monolithic generator, we deploy three distinct and independent
SQL generators that run in parallel, each employing a different
methodology. This engineered diversity significantly increases the
likelihood of producing at least one correct candidate, enhancing
the system’s overall robustness. The entire workflow is detailed in
Algorithm 3.

The inputs to this phase are the user question 𝑄, the linked
schema D𝑙𝑖𝑛𝑘𝑒𝑑 , and the retrieved values M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 . The three
generators operate on this common set of inputs to produce a
unified pool of initial SQL candidates C𝑖𝑛𝑖𝑡𝑖𝑎𝑙 .
Skeleton-based SQL Generation. This generator is modeled after
the top-down design principle [44], where a high-level plan is for-
mulated before implementation details are filled in. This guides the
LLM to think systematically, reducing structural errors. It involves
three conceptual steps: component analysis, skeleton generation,
and slot-filling. The entire process is encapsulated in a single call
to the LLM, which is instructed to follow this reasoning path. We
can formalize this as:

𝑆𝑠𝑘𝑒𝑙 = LLMSkel (𝑄, D𝑙𝑖𝑛𝑘𝑒𝑑, M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 )

(6)

ICL-based SQL Generation. This generator leverages in-context
learning (ICL), analogous to case-based reasoning [12]. By providing
the LLM with relevant examples, we ground its generation in proven
patterns. The process involves retrieving schema-masked similar
examples from a training set following DAIL-SQL [7], instructing
the LLM to identify a common pattern, and then applying that

DeepEye-SQL: A Software-Engineering-Inspired Text-to-SQL Framework

Conference’17, July 2017, Washington, DC, USA

Algorithm 4 SQL Unit Testing and Revision via Tool-Chain
Input: A single SQL candidate S𝑐𝑎𝑛𝑑 , Context (𝑄, D𝑙𝑖𝑛𝑘𝑒𝑑 , M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 ),

Table 1: Specialized Checkers.

Checker

Error Detection

Example Cases

Tool-Chain C = {𝐶1, ..., 𝐶𝑁 }
Output: Revised SQL query S𝑟𝑒𝑣𝑖𝑠𝑒𝑑

1: S𝑐𝑢𝑟𝑟𝑒𝑛𝑡 ← S𝑐𝑎𝑛𝑑
2: for all checker 𝐶 𝑗 ∈ C do
3:
4:

𝑖𝑠_𝑣𝑎𝑙𝑖𝑑, 𝑑𝑒𝑟𝑟 ← Cj ( S𝑐𝑢𝑟𝑟𝑒𝑛𝑡 )
if not 𝑖𝑠_𝑣𝑎𝑙𝑖𝑑 then

Syntax Checker

JOIN Checker

ORDER-BY Checker

// Error found, trigger revision and update the current SQL

Time Checker

S𝑐𝑢𝑟𝑟𝑒𝑛𝑡 ← LLMRevise (𝑄, D𝑙𝑖𝑛𝑘𝑒𝑑 , M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 , S𝑐𝑢𝑟𝑟𝑒𝑛𝑡 , 𝑑𝑒𝑟𝑟 )

5:
6:
7: end for

end if

// All checkers in the chain have been processed

8: return S𝑐𝑢𝑟𝑟𝑒𝑛𝑡

pattern to the target question. This is formalized as:

𝑆𝑖𝑐𝑙 = LLMICL (𝑄, D𝑙𝑖𝑛𝑘𝑒𝑑, M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑, E𝑓 𝑒𝑤−𝑠ℎ𝑜𝑡 )

(7)

where E𝑓 𝑒𝑤−𝑠ℎ𝑜𝑡 represents the set of retrieved few-shot examples.
Divide-and-Conquer-based SQL Generation. For highly com-
plex questions requiring nested logic, this generator implements the
classic Divide and Conquer paradigm. It breaks a large problem into
smaller, manageable sub-problems that are solved recursively and
then reassembled. This involves decomposing the question, solving
each sub-question, and synthesizing the results into a single query.
The process is formalized as:

𝑆𝑑&𝑐 = LLMD&C (𝑄, D𝑙𝑖𝑛𝑘𝑒𝑑, M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 )

(8)

4.4 SQL Unit Testing and Revision via

Tool-Chain

SQL queries generated by LLMs, while often structurally sound,
can contain minor yet critical errors [20], such as incorrect function
usage or logical flaws in JOIN conditions. A well-known limitation
of LLMs is their unreliability in self-correction [33]; when asked
to review their own output, they exhibit a strong confirmation
bias and tend to overlook their mistakes [53]. This challenge is
directly analogous to a core principle in software engineering: code
should be validated by an independent testing suite, not just by the
developer who wrote it. To address this, our framework introduces
the SQL Unit Testing and Revision via Tool-Chain phase, which draws
direct inspiration from the practice of Unit Testing [35]. In this
paradigm, individual software components—or “units”—are tested
in isolation. We adapt this concept by treating each functional
component of a SQL query (e.g., its JOIN logic, a specific clause,
or its syntax) as a testable “unit”. The Tool-Chain operationalizes
this principle by externalizing the verification process. It uses a
deterministic chain of specialized checkers, where each checker acts
as an automated test case for a specific SQL unit. This allows the
system to systematically detect errors and guide the LLM through
a reliable, targeted revision process, as detailed in Algorithm 4.
Tool-Chain of Checkers. Our approach centers on a suite of spe-
cialized, deterministic programs we term “Checker Tools”. These
checkers are not applied randomly; they are organized into a se-
quential tool-chain that processes each SQL query in a specific
order to catch errors systematically, from fundamental syntax to

SQL syntax and
execution errors

Non-standard
JOIN conditions

Invalid ORDER BY
+ LIMIT combinations

Incorrect time function
usage and formatting

SELECT * FORM table (typo)
WHERE column = (incomplete)
ON cond1 OR cond2
ON column IN (...)

ORDER BY MAX(...) LIMIT 1
ORDER BY COUNT(*) LIMIT 3

STRFTIME(’%Y’, date) format
Invalid date comparisons
SELECT * → specific columns
Unnecessary wildcards

Ambiguous return
columns
Suboptimal MAX/MIN WHERE col = (SELECT MAX(...))
patterns

→ ORDER BY col DESC LIMIT 1
Add WHERE col IS NOT NULL
for ORDER BY columns

NULL values in
ORDER BY columns

Empty or meaningless
results

Queries returning only NULL
Zero-row result sets

SELECT Checker

MaxMin Checker

NULL Checker

Result Checker

semantic correctness. The complete, ordered sequence of checkers
and their functions is detailed in Table 1. The chain begins with
the most fundamental validation: the Syntax Checker ensures the
query is syntactically valid and executable, catching basic typos or
incomplete clauses. It then proceeds to clause-specific validation.
For example, the JOIN Checker flags non-standard conditions, the
ORDER-BY Checker corrects invalid patterns like using aggregations
with LIMIT, and the Time Checker validates date and time format-
ting. Subsequently, the chain addresses more semantic and stylistic
issues. The SELECT Checker replaces ambiguous wildcards like
SELECT * with specific column names, and the MaxMin Checker
refactors suboptimal patterns into more efficient ORDER BY ...
LIMIT 1 clauses. Finally, the NULL Checker and Result Checker add
guards for potential NULL issues and flag queries that are likely to
produce empty or meaningless results, ensuring the final output is
not only correct but also useful.
The Sequential Check-and-Revise Process. Our framework
implements an efficient, single-pass “check-and-revise” process,
detailed in Algorithm 4. Each initial SQL candidate, S ∈ C𝑖𝑛𝑖𝑡𝑖𝑎𝑙 ,
is passed through the Tool-Chain of Checkers exactly once. The
process for a single candidate S𝑐𝑎𝑛𝑑 is as follows:

(1) The candidate S𝑐𝑎𝑛𝑑 is sequentially evaluated by each checker

in the tool-chain, starting with the first.

(2) If a checker detects an error, the process is momentarily
paused. The checker generates a specific error report and
an actionable correction directive, 𝑑𝑒𝑟𝑟 . For example, if the
NULL Checker finds that a column in an ORDER BY clause
could contain NULL values, the directive would be a clear
instruction such as: “The ordering column [column_name]
may contain NULLs. Add a WHERE [column_name] IS NOT
NULL condition to ensure correct sorting.”

(3) The LLM is then invoked in a special “revision mode”. It
receives the original context, the faulty SQL S𝑐𝑎𝑛𝑑 , and the
explicit directive 𝑑𝑒𝑟𝑟 from the checker. The LLM’s task is
not to find the error, but to fix it based on the directive. This
can be formalized as:

S𝑟𝑒𝑣𝑖𝑠𝑒𝑑 = LLMRevise (𝑄, D𝑙𝑖𝑛𝑘𝑒𝑑, M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑, S𝑐𝑎𝑛𝑑, 𝑑𝑒𝑟𝑟 )

(9)

Conference’17, July 2017, Washington, DC, USA

Boyan Li, Chong Chen, Zhujun Xue, Yinan Mei, and Yuyu Luo

Algorithm 5 Confidence-aware SQL Selection
Input: Revised

Candidates

SQL

C𝑟𝑒𝑣𝑖𝑠𝑒𝑑 ,

Context

(𝑄, D𝑙𝑖𝑛𝑘𝑒𝑑 , M𝑟𝑒𝑡𝑟𝑖𝑒𝑣𝑒𝑑 ), Threshold 𝜃𝑐𝑜𝑛𝑓

Output: The Final SQL Query S𝑓 𝑖𝑛𝑎𝑙

// Step 1: Execute all candidates and cluster the results

1: R ← ExecuteAll( C𝑟𝑒𝑣𝑖𝑠𝑒𝑑 )
2: {Cluster1, ..., Cluster𝑀 }, { S1, ..., S𝑀 } ← ClusterAndRank( R )

// Step 2: Calculate confidence for the top-ranked candidate

3: 𝐶𝑜𝑛𝑓 ( S1 ) ← |Cluster1 |
|C𝑟𝑒𝑣𝑖𝑠𝑒𝑑 |
// Step 3: Confidence-Gated Selection Path

S𝑓 𝑖𝑛𝑎𝑙 ← S1 // High-Confidence Shortcut

4: if 𝐶𝑜𝑛𝑓 ( S1 ) > 𝜃𝑐𝑜𝑛𝑓 then
5:
6: else
7:

Let { S1, ..., S𝐾 } be the top-K candidates // Low-Confidence Full

Review

8:

9:

10:

for all candidate S𝑖 in { S1, ..., S𝐾 } do

𝐶𝑜𝑛𝑓 ( S𝑖 ) ← |Cluster𝑖 |
|C𝑟𝑒𝑣𝑖𝑠𝑒𝑑 |
𝑊 𝑖𝑛𝑅𝑎𝑡𝑒 ( S𝑖 ) ← LLM − PairwiseVoting( { S1, ..., S𝐾 } ) //

Using Eq. 11

𝑆𝑐𝑜𝑟𝑒 ( S𝑖 ) ← 𝐶𝑜𝑛𝑓 ( S𝑖 ) × 𝑊 𝑖𝑛𝑅𝑎𝑡𝑒 ( S𝑖 )

end for
S𝑓 𝑖𝑛𝑎𝑙 ← arg maxS𝑖 𝑆𝑐𝑜𝑟𝑒 ( S𝑖 )

11:
12:
13:
14: end if
15: return S𝑓 𝑖𝑛𝑎𝑙

(4) The newly revised query, S𝑟𝑒𝑣𝑖𝑠𝑒𝑑 , replaces S𝑐𝑎𝑛𝑑 , and the
evaluation continues with the next checker in the chain.
(5) The process terminates once the query has been evaluated

by all checkers in the chain.

This external, tool-guided debugging process is significantly more
reliable than unconstrained LLM self-correction. The final output
of this phase is a set of revised SQL candidates, C𝑟𝑒𝑣𝑖𝑠𝑒𝑑 , which have
been rigorously vetted and have a substantially higher probability
of being correct.

4.5 Confidence-aware SQL Selection

The preceding phases of our framework produce a set of high-
quality, revised SQL candidates, C𝑟𝑒𝑣𝑖𝑠𝑒𝑑 . However, these candi-
dates may not be identical and could yield different execution re-
sults. The most common approach for selecting a final query is
self-consistency [7, 15, 48], where all candidates are executed, and
the query corresponding to the most frequent result is chosen. This
method, while a strong baseline, has a critical flaw: the most popular
answer is not always the correct one, especially for complex problems
where multiple generation paths might converge on the same plausible
but incorrect logic. This final challenge mirrors the release stage in
a software lifecycle, which is governed by a Quality Gate [37]. A
quality gate’s purpose is not merely to accept the most-voted-for
version, but to enforce a set of objective quality criteria before a
product is released. Similarly, our Confidence-aware SQL Selection
phase acts as this quality gate for the generated SQL. It overcomes
the flaws of simple majority voting by using the initial vote’s confi-
dence as a quality metric to guide a more reliable, adaptive selection
process.
Execution-based Clustering and Confidence Estimation. The
process begins by executing every revised SQL candidate S ∈

C𝑟𝑒𝑣𝑖𝑠𝑒𝑑 on the database. The resulting datasets are then clustered,
such that queries producing identical results are grouped together.
These clusters are ranked based on their size (i.e., the number
of SQL queries they contain). For each of the top-𝐾 candidates
{S1, S2, ..., S𝐾 }, representing the top-𝐾 largest clusters, we calcu-
late an execution-based confidence score. The confidence of a can-
didate S𝑖 is the proportion of total queries that belong to its cluster:

𝐶𝑜𝑛𝑓 (S𝑖 ) =

|Cluster𝑖 |
|C𝑟𝑒𝑣𝑖𝑠𝑒𝑑 |

(10)

This score, particularly 𝐶𝑜𝑛𝑓 (S1), serves as a strong indicator of
the query’s likely correctness, as shown by the high correlation in
Figure 6.
Confidence-Gated Selection. Based on the confidence of the top-
ranked candidate S1, our framework follows one of two distinct
paths, as detailed in Algorithm 5.
High-Confidence Shortcut. If the confidence score 𝐶𝑜𝑛𝑓 (S1) exceeds
a predefined high-confidence threshold 𝜃𝑐𝑜𝑛𝑓 , we conclude that
there is overwhelming agreement among the generated candidates.
In this scenario, we directly select S1 as the final query. This short-
cut avoids unnecessary and costly LLM invocations for cases where
the answer is already clear, providing a practical trade-off between
accuracy and efficiency.
Low-Confidence Full Review. If 𝐶𝑜𝑛𝑓 (S1) < 𝜃𝑐𝑜𝑛𝑓 , it signifies sub-
stantial ambiguity or disagreement among the candidates, making
the top choice unreliable. It then triggers a full review pipeline.
(1) Establish Unbalanced Cognitive Prior. First, instead of a
neutral pairwise comparison, the LLM is explicitly primed with
a “cognitive prior”. It is informed that, based on execution results,
S𝑖 has a higher prior confidence than S𝑗 . We instructs the LLM
to select the higher-confidence candidate unless there is clear and
compelling evidence that it is incorrect or that the lower-confidence
candidate is demonstrably superior.
(2) Perform Pairwise Adjudication. Next, the LLM performs
pairwise comparisons for the top-𝐾 candidates. To ensure reliability,
we employ a self-consistency mechanism. For each pair (S𝑖, S𝑗 ),
we sample multiple judgments and define the final stable vote,
𝑉 (S𝑖, S𝑗 ), as the majority outcome. The vote 𝑉 (S𝑖, S𝑗 ) yields 1 if
S𝑖 is superior and 0 if S𝑗 is superior. From these consistent pairwise
results, we compute an aggregate win rate for each candidate S𝑖 as
its average score against all other competitors in the top-𝐾 set:

𝑊 𝑖𝑛𝑅𝑎𝑡𝑒 (S𝑖 ) =

1
𝐾 − 1

𝐾
∑︁

𝑗=1,𝑗≠𝑖

𝑉 (S𝑖, S𝑗 )

(11)

(3) Calculate Final Score. Finally, the decision is based on a
confidence-aware score that combines the prior execution-based
confidence with the LLM-adjudicated win rate:

𝑆𝑐𝑜𝑟𝑒 (S𝑖 ) = 𝐶𝑜𝑛𝑓 (S𝑖 ) × 𝑊 𝑖𝑛𝑅𝑎𝑡𝑒 (S𝑖 )

(12)

The query with the highest overall score, arg maxS𝑖 𝑆𝑐𝑜𝑟𝑒 (S𝑖 ), is
selected as the final SQL, S𝑓 𝑖𝑛𝑎𝑙 .

DeepEye-SQL: A Software-Engineering-Inspired Text-to-SQL Framework

Conference’17, July 2017, Washington, DC, USA

4.6 Workflow Optimization

While DeepEye-SQL’s multi-stage architecture ensures robustness,
we incorporate three key optimizations to maintain efficiency and
computational costs, preventing prohibitive latency or expense.
Efficient Prompting Strategy. Instead of sequential, costly LLM
API calls for multi-step reasoning (e.g., planning), we use a single,
sophisticated prompt for each generator. This prompt includes
a “chain-of-thought” instruction, directing the LLM to perform
the entire logical sequence internally and output only the final
SQL in one call. This preserves structured reasoning benefits while
eliminating the associated latency and token overhead.
Parallel Execution. To reduce end-to-end latency, our framework
heavily parallelizes independent tasks. Critical components are
executed concurrently, including: multi-column value retrieval, all
three schema linking strategies, the N-version SQL generators, and
the parallel revision of each SQL candidate.
Conditional Execution. To minimize unnecessary LLM invoca-
tions, DeepEye-SQL employs conditional execution at two critical
stages. First, during SQL Unit Testing and Revision, the LLM is only
called for revision if a checker tool detects an error. Second (Sec-
tion 4.4), LLM-based pairwise adjudication is only triggered in
low-confidence scenarios.

5 Experiments
5.1 Experimental Setup

Datasets. We evaluate the performance of DeepEye-SQL on two
widely-recognized and challenging cross-domain Text-to-SQL bench-
marks: BIRD [18] and Spider [51]. BIRD is a large-scale benchmark
designed to mirror complex, real-world scenarios. It contains 12,751
unique question-SQL pairs across 95 databases from over 37 profes-
sional domains. Its databases are notably large and feature messy
data and intricate schemas, making it a difficult test for grounding
and robustness. Spider is a foundational large-scale, cross-domain
benchmark in the field. It consists of 10,181 questions and 5,693
unique, complex SQL queries across 200 databases covering 138
different domains. Following prior works [3, 21, 31], we use the
development set of BIRD (BIRD-Dev) and the test set of Spider
(Spider-Test) for our main evaluation.
Evaluation Metrics. Following prior works [3, 21, 31], our primary
evaluation metric is Execution Accuracy (EX). A generated SQL
query is considered correct if its execution result is equivalent
to that of the ground-truth query after accounting for ordering.
To measure the potential of our N-version Programming for SQL
Generation module, we report the Upper-bound EX, which is the
execution accuracy an oracle would achieve by always selecting the
correct SQL from the generated candidates [31]. For evaluating the
Robust Schema Linking module, we use Table/Column Recall, the
proportion of ground-truth tables and columns correctly identified.
Finally, to assess practical efficiency, we measure Token Cost,
corresponding to the number of tokens processed by LLMs.
Baselines. We compare DeepEye-SQL against SOTA baselines from
two paradigms (Table 2). The first is fine-tuning-based methods,
which are trained on in-domain data, including strong competitors

like XiYan-SQL [21], CHASE-SQL [31], and OmniSQL [16]. The
second is prompting-based methods, which, like DeepEye-SQL,
are training-free. This group includes methods like Alpha-SQL [15],
RSL-SQL [3], and CHESS [43].
Implementation Details. All experiments are conducted on an
Ubuntu 22.04.3 LTS server with 512GB of RAM and dual 40-core
Intel(R) Xeon(R) Platinum 8383C CPUs. We deploy all open-source
LLMs locally using the vllm [13] framework on 4 NVIDIA A100
GPUs, each with 80GB of memory, and accelerate inference using a
tensor parallelism of 4. To validate the robustness and generalizabil-
ity of our framework, we integrated DeepEye-SQL with three dis-
tinct models from two leading series: Gemma3-27B-Instruct [11],
Qwen2.5-Coder-32B-Instruct [9], and Qwen3-Coder-30B-A3B-
Instruct [49]. Unless otherwise specified, the pipeline is config-
ured as follows. For Semantic Value Retrieval, where we retrieve up
to the top-5 most similar values for each TEXT-type column, we use
the Qwen3-Embedding-0.6B [55] model, and the similarity thresh-
old (𝜃𝑣𝑎𝑙 ) for Value-based Schema Linking is set to 0.98. The draft
SQL for Reversed Schema Linking is produced by the ICL-based
generator. For each LLM sub-task (e.g., Direct Schema Linking),
we set the sampling budget to 8 with a sampling temperature of
0.7. Finally, in the Confidence-aware SQL Selection phase, which
adjudicates between the top-2 ranked queries in low-confidence
scenarios, the confidence shortcut threshold (𝜃𝑐𝑜𝑛𝑓 ) is set to 0.6. All
prompt templates of our method are in the Appendix.

5.2 Overall Performance

RQ1: How does DeepEye-SQL perform against existing state-
of-the-art methods on challenging Text-to-SQL benchmarks?
To answer this, we present the main performance of DeepEye-
SQL on the BIRD-Dev and Spider-Test datasets in Table 2, com-
paring it against a wide range of state-of-the-art fine-tuning and
prompting-based methods. The results clearly demonstrate that our
software-grounded framework establishes a new benchmark for
training-free Text-to-SQL generation.

Specifically, when integrated with the Qwen3-Coder-30B-A3B
model, DeepEye-SQL achieves an execution accuracy of 73.5% on
BIRD-Dev. This result not only significantly outperforms all existing
prompting-based baselines but, more remarkably, it also surpasses
the leading fine-tuning-based systems like XiYan-SQL (73.3%) and
CHASE-SQL (73.0%). It is crucial to note that these competing meth-
ods rely on substantially larger and often proprietary models (e.g.,
GPT-4o and Gemini-1.5-Pro). On the Spider-Test dataset, DeepEye-
SQL with Qwen3-Coder-30B-A3B achieves an execution accuracy
of 89.8%. This performance matches the best fine-tuned method,
OmniSQL, and surpasses other strong competitors like XiYan-SQL
(89.7%). This demonstrates that our prompting-based framework
can attain the same level of accuracy as highly specialized, fine-
tuned models on this foundational benchmark without incurring
any training costs.

Furthermore, the consistently high performance of DeepEye-
SQL across all three tested open-source models—71.1% with Gemma3-
27B, 70.9% with Qwen2.5-Coder-32B, and 73.5% with Qwen3-Coder-
30B on BIRD, which underscores the robustness and generalizability
of our framework.

Conference’17, July 2017, Washington, DC, USA

Boyan Li, Chong Chen, Zhujun Xue, Yinan Mei, and Yuyu Luo

Table 2: Performance comparison on BIRD-Dev and Spider-Test datasets.

Methods

Model

# Parameters BIRD-EX (%)

Spider-EX (%)

Fine-tuning-based Baselines

CodeLLaMA-13B
CodeS-15B
GPT-4o

SENSE [50]
SFT CodeS [17]
Distillery [28]
XiYanSQL-QwenCoder [21] Qwen2.5-Coder-32B-Instruct
Qwen2.5-Coder-32B-Instruct
BASE-SQL [40]
Qwen2.5-Coder-32B-Instruct
OmniSQL [16]
XiYanSQL-QwenCoder-32B
CSC-SQL [39]
CHASE-SQL [31]
Gemini-1.5-Pro + Gemini-1.5-Flash
GPT-4o + Qwen2.5-Coder-32B-Instruct
XiYan-SQL [21]

Prompting-based Baselines

DIN-SQL [32]
DAIL-SQL [7]
SuperSQL [14]
RSL-SQL [3]
CHESS (IR,CG,UT) [43]
OpenSearch-SQL (v2) [48]
Alpha-SQL [15]

GPT-4
GPT-4
GPT-4
GPT-4o
Gemini-1.5-Pro
GPT-4o
Qwen2.5-Coder-32B-Instruct

∼13B
∼15B
>200B
∼32B
∼32B
∼32B
∼32B
>200B
>200B

>175B
>175B
>175B
>200B
>200B
>200B
∼32B

DeepEye-SQL
DeepEye-SQL
DeepEye-SQL

Our DeepEye-SQL (Prompting-based)

Gemma3-27B-Instruct
Qwen2.5-Coder-32B-Instruct
Qwen3-Coder-30B-A3B-Instruct

∼27B
∼32B
∼30B

55.5
58.5
67.2
67.1
67.5
67.0
71.3
73.0
73.3

50.7
55.9
58.5
67.2
68.3
69.3
69.7

71.1
70.9
73.5

86.6
-
-
88.4
88.9
89.8
-
87.6
89.7

85.3
86.6
-
87.9
-
87.1
-

88.9
88.7
89.8

Table 3: Performance comparison with same LLMs.

Methods

EX (%) Delta (%)

Table 4: Schema linking analysis with Qwen3-Coder-30B-
A3B on BIRD-Dev dataset.

Gemma3-27B-Instruction

CoT-Baseline
CHESS (IR,CG,UT)
Alpha-SQL
DeepEye-SQL (Ours)

Qwen2.5-Coder-32B-Instruct

CoT-Baseline
CHESS (IR,CG,UT)
Alpha-SQL
DeepEye-SQL (Ours)

54.2
66.1
68.6
71.1

61.3
67.7
69.7
70.9

Qwen3-Coder-30B-A3B-Instruct

CoT-Baseline
CHESS (IR,CG,UT)
Alpha-SQL
DeepEye-SQL (Ours)

61.7
67.9
71.2
73.5

-
+11.9
+14.4
+16.9

-
+6.4
+8.4
+9.6

-
+6.2
+9.5
+11.8

RQ2: Is the performance gain of DeepEye-SQL attributable
to its architectural design rather than the power of the un-
derlying base model?

To isolate our framework’s contribution from the base model’s in-
trinsic capabilities, we evaluated it against leading prompting-based
frameworks on identical open-source models (Table 3). The results
confirm that DeepEye-SQL’s architecture consistently provides
the most substantial performance improvement. For instance, on
Gemma3-27B-Instruct, DeepEye-SQL improves the CoT baseline
by +16.9%, significantly outpacing the gains from CHESS (+11.9%)

Schema Linking Methods

Table
Recall (%)

Column
Recall (%)

# Avg.
Tokens

No Schema Linking
Direct Schema Linking
Reversed Schema Linking
Value Schema Linking

Robust Schema Linking

-
94.2
97.0
47.3

98.1

-
80.9
94.0
18.0

95.4

5486.2
454.5
495.9
262.0

627.4

and Alpha-SQL (+14.4%). This trend holds across all tested models,
culminating in a state-of-the-art 73.5% EX on Qwen3-Coder-30B-
A3B (+11.8% gain).

5.3 Robust Schema Linking Analysis

RQ3: How do the individual components of our Robust Schema
Linking module contribute to its overall effectiveness and
efficiency?

We analyzed our Robust Schema Linking module’s components
on BIRD-Dev (Table 4), measuring schema recall and token effi-
ciency. The full approach achieves the highest recall (98.1% table,
95.4% column), providing a critical foundation for SQL generation.
It also dramatically boosts efficiency, reducing the input context by
9× from 5486.2 to 627.4 tokens compared to using the full schema.
Analyzing the components reveals complementary strengths.
Our novel Reversed Schema Linking (97.0% table, 94.0% column) sig-
nificantly outperforms Direct Schema Linking, especially in column

DeepEye-SQL: A Software-Engineering-Inspired Text-to-SQL Framework

Conference’17, July 2017, Washington, DC, USA

Question: Which accounts placed orders for “household payment”
in Pisek?
Evidence: k_symbol = ‘SIPO’ refers to household payment.

LLM-based Linking (Direct & Reversed):

> Found: account.account_id, district.district_id,

order.k_symbol, ...

X Missed: The essential column trans.k_symbol.

Value-based Linking:

✓ Recovered: trans.k_symbol by linking to value ‘SIPO’.

-- Gold SQL
SELECT DISTINCT T2 . account_id FROM trans AS T1 JOIN account
AS T2 ON T1 . account_id = T2 . account_id JOIN district AS T3
ON T2 . district_id = T3 . district_id WHERE T1 . k_symbol = ' SIPO
' AND T3 . A2 = ' Pisek '

Figure 4: A case study from BIRD-Dev (QID: 142) where Value-
based Linking recovers a critical column (trans.k_symbol)
missed by purely LLM-based linking methods.

Table 5: SQL generation analysis with Qwen3-Coder-30B-A3B
on BIRD-Dev dataset.

SQL Generation

EX (%) UB-EX (%)

Skeleton-based SQL Generation
ICL-based SQL Generation
D&C-based SQL Generation
N-version Programming for SQL Generation

69.2
70.9
70.3
71.7

77.9
78.3
78.5
81.1

recall (+13.1%). This validates our hypothesis that prompting for a
draft query is a more natural and effective reasoning method for
LLMs than explicit extraction.

Finally, Value-based Schema Linking, while low in overall re-
call, is not a standalone linker. It acts as a precise mechanism to
link columns via their data values, catching omissions from other
methods. For instance (Figure 4), it correctly identified trans.k_-
symbol by linking the query’s “household payment” to the data
value ‘SIPO’. This bridged a semantic gap that schema-level rea-
soners (Direct and Reversed) missed, as they were confused by an
ambiguous k_symbol name. This recovery proves the value-based
method’s essential role in our fault-tolerant design.

5.4 Analysis on N-Version Programming for

SQL Generation

RQ4: How do the different SQL generators contribute to the
overall performance, and does the N-version programming
approach provide a tangible benefit?

We analyzed our three SQL generators’ individual and combined
performance (EX and UB-EX) on BIRD-Dev (Table 5, Figure 5).
While all generators perform well individually (peaking at 70.9%
EX), combining them in our N-version module already yields a
71.7% EX. The true strength of this approach, however, lies in its
potential: the combined UB-EX reaches 81.1%, a significant +2.6%
gain over the best individual generator’s potential (78.5%). This

(a) EX Correctness Overlap.

(b) UB-EX Correctness Overlap.

Figure 5: Correctness overlap analysis of three SQL genera-
tion methods using Qwen3-Coder-30B-A3B model on BIRD-
Dev dataset.

Figure 6: Execution accuracy vs. SQL confidence on BIRD-Dev
dataset with Qwen3-Coder-30B-A3B model.

Table 6: Performance comparison with different SQL selec-
tion methods on BIRD-Dev dataset.

Selection Methods

BIRD-EX (%)

Spider-EX (%)

Gemma3-27B-Instruct

Consistency-based Voting
Confidence-aware SQL Selection

70.1
71.1 (↑1.0)

88.3
88.9 (↑0.6)

Qwen2.5-Coder-32B-Instruct

Consistency-based Voting
Confidence-aware SQL Selection

70.2
70.9 (↑0.7)

88.2
88.7 (↑0.5)

Qwen3-Coder-30B-A3B-Instruct

Consistency-based Voting
Confidence-aware SQL Selection

72.7
73.5 (↑0.8)

89.7
89.8 (↑0.1)

UB-EX increase confirms that the generators possess crucial diver-
sity, solving different subsets of problems where one’s failure is
covered by another’s success. The overlap analysis (Figure 5b) cor-
roborates this: while 70.9% of correct answers are found by all three
generators, a significant 10.2% are solved by only one or two. This
proves the generators are not redundant. This engineered diver-
sity—finding a correct answer for 81.1% of questions—validates our
fault-tolerant design and provides the rich candidate pool essential
for achieving state-of-the-art performance

5.5 Confidence-aware SQL Selection Analysis

RQ5: Can a selection mechanism that leverages voting confi-
dence outperform traditional consistency-based voting, and
what is the motivation for such a design?

DC only1.3%Skeleton only1.1%ICL only1.9%DC+Skeleton1.6%DC+ICL4.1%Skeleton+ICL1.7%All three63.6%None correct24.6%DC only1.7%Skeleton only1.4%ICL only2.0%DC+Skeleton1.4%DC+ICL2.5%Skeleton+ICL1.2%All three70.9%None correct18.9%0.20.40.60.81.0SQL Confidence Score020406080EX (%)Correlation: 0.95405001000Sample CountConference’17, July 2017, Washington, DC, USA

Boyan Li, Chong Chen, Zhujun Xue, Yinan Mei, and Yuyu Luo

Figure 7: Execution accuracy vs. Confidence Shorcut Thresh-
old on BIRD-Dev dataset with Qwen3-Coder-30B-A3B model.

To answer this, we first analyze the relationship between voting
confidence and correctness, and then present a direct comparison
of our method against the standard self-consistency approach.

The core motivation behind our Confidence-aware SQL Selection
is the observation that the reliability of consistency-based voting is
highly dependent on the degree of consensus among the generated
candidates. To validate this premise, we visualized the SQL confi-
dence score (defined as the proportion of candidates in the largest
execution cluster) against the actual execution accuracy for our
results on the BIRD-Dev dataset. As visualized in Figure 6, there is
a remarkably strong positive correlation between these two factors,
with a Pearson correlation coefficient [38] of 0.954. This result con-
firms that when the confidence score is high, the top-ranked SQL is
very likely to be correct. Conversely, in low-confidence scenarios
where candidates produce many different results, standard voting
is unreliable. This insight directly informs our two-path design: a
“shortcut” for high-confidence cases and a more discerning “full
review” for low-confidence ones.

To quantify the effectiveness of this design, we compared its
performance against traditional Consistency-based Voting [7, 15]
across three different base models. The results are shown in Table 6.
For every model and on both the BIRD and Spider datasets, our
method yields a notable improvement in execution accuracy. For
instance, with Gemma3-27B-Instruct, our method improves the
EX on BIRD by 1.0%, from 70.1% to 71.1%. This analysis validates
that by identifying and re-evaluating ambiguous, low-confidence
scenarios instead of blindly trusting the majority vote, our method
achieves a more robust and accurate final selection.

RQ6: How sensitive is the framework’s performance to the
choice of the confidence shortcut threshold (𝜃𝑐𝑜𝑛𝑓 )?

To evaluate the robustness of our selection mechanism, we con-
ducted a sensitivity analysis on the confidence shortcut threshold,
𝜃𝑐𝑜𝑛𝑓 . This threshold determines the trade-off between taking the
efficient shortcut and triggering the full, LLM-based review. As
shown in Figure 7, we varied 𝜃𝑐𝑜𝑛𝑓 from 0.0 (always perform full
review) to 1.0 (always take the shortcut) and observed the impact on
execution accuracy. The results demonstrate that our framework’s
performance is robust across a wide range of threshold values. The
accuracy remains high and stable, peaking at 73.5% with a threshold
of 0.6, and staying above 73.0% for all values between 0.4 and 1.0.
This indicates that our method is not overly sensitive to the precise
choice of this hyperparameter.

5.6 Ablation Study

RQ7: What is the contribution of each key component to the
overall performance of the DeepEye-SQL framework?

Table 7: Ablation study of DeepEye-SQL with Qwen3-Coder-
30B-A3B on BIRD-Dev dataset.

Configuration

DeepEye-SQL

- w/o Semantic Value Retrieval
- w/o Robust Schema Linking
- w/o Skeleton-based SQL Generation
- w/o ICL-based SQL Generation
- w/o D&C-based SQL Generation
- w/o SQL Unit Testing and Revision via Tool-Chain
- w/o Confidence-aware SQL Selection

EX (%) Delta (%)

73.5

71.4
71.8
72.2
71.0
72.3
71.4
72.7

-

-2.1
-1.7
-1.3
-2.5
-1.2
-2.1
-0.8

Table 8: Efficiency Comparison on BIRD-Dev with Qwen3-
Coder-30B-A3B model.

Methods

CHESS (IR,SS,CS)
Alpha-SQL

DeepEye-SQL
- Semantic Value Retrieval
- Robust Schema Linking
- N-version Programming for SQL Generation
- SQL Unit Testing and Revision via Tool-Chain
- Confidence-aware SQL Selection

Avg. Input
Tokens (K)

Avg. Output
Tokens (K)

EX (%)

327.02
138.03

23.21
0.67
13.91
5.28
3.16
0.19

27.83
72.21

23.16
0.03
6.33
11.38
5.41
0.01

67.9
71.2

73.5
-
-
-
-
-

To understand the impact of each module, we conducted an
ablation study on the BIRD-Dev dataset by progressively removing
one component at a time. The results are detailed in Table 7.

The primary conclusion is that every component makes a pos-
itive and integral contribution, as removing any single module
degrades performance. The ICL-based SQL Generation is the most
critical individual module, with its removal causing the largest
performance drop of 2.5%. Semantic Value Retrieval and SQL Unit
Testing and Revision via Tool-Chain are also highly impactful, each
accounting for a 2.1% gain. This highlights the necessity of ground-
ing the LLM in real data and externalizing the debugging process.
The significant contributions from the SQL generation modules
and the selection mechanism confirm the value of our N-version
programming and confidence-aware selection strategies. Overall,
the results confirm that the high performance of DeepEye-SQL is
not due to any single component, but rather the synergistic collab-
oration of all modules in its carefully designed pipeline.

5.7 Efficiency Analysis

RQ8: How does DeepEye-SQL’s efficiency, in terms of token
consumption, compare to other state-of-the-art prompting-
based frameworks?

To answer this, we conducted a cost study to evaluate the token
efficiency of our framework. While system latency is an important
practical concern, it is highly sensitive to external factors such as
hardware and deployment configuration. Therefore, we use token
efficiency (both input and output) as a more objective and repro-
ducible metric for the cost of LLM-based systems.

The results of our efficiency comparison on the BIRD-Dev dataset
are presented in Table 8. The data clearly shows that DeepEye-SQL
is substantially more token-efficient than other high-performing
methods, while also achieving superior accuracy. For instance,

0.00.20.40.60.81.0Confidence Shortcut Threshold72.5072.7573.0073.2573.50EX (%)72.7%72.8%73.2%73.5%73.3%73.0%DeepEye-SQL: A Software-Engineering-Inspired Text-to-SQL Framework

Conference’17, July 2017, Washington, DC, USA

Alpha-SQL consumes nearly 6× more input tokens (138.03K vs.
23.21K) and CHESS consumes over 14× more (327.02K vs. 23.21K)
than our method, yet both achieve lower execution accuracy. This
demonstrates that DeepEye-SQL’s carefully designed pipeline does
not rely on brute-force context stuffing; instead, it uses a structured
and efficient reasoning process. The table also provides a break-
down of token consumption for each module within our pipeline.
As expected, the most cost-intensive stages are Robust Schema Link-
ing and N-version Programming for SQL Generation, where the core
reasoning and generation occurs. In contrast, other modules like
Semantic Value Retrieval and Confidence-aware SQL Selection are
remarkably lightweight, adding minimal overhead.

6 Conclusion

In this paper, we presented DeepEye-SQL, which reframes Text-
to-SQL as a verifiable SDLC-style workflow. By unifying semantic
grounding, N-version programming, deterministic tool-chain veri-
fication, and confidence-aware selection, DeepEye-SQL enforces
end-to-end correctness and achieves system-level reliability. Ex-
tensive experiments validate that, using ∼30B open-source LLMs
without fine-tuning, DeepEye-SQL achieves 73.5% EX on BIRD-Dev
and 89.8% on Spider-Test, outperforming the state of the art. Our
results suggest that principled orchestration offers a promising path
toward system-level reliability in Text-to-SQL, beyond relying on
LLM scaling alone.

Conference’17, July 2017, Washington, DC, USA

Boyan Li, Chong Chen, Zhujun Xue, Yinan Mei, and Yuyu Luo

References
[1] Rohan Anil, Sebastian Borgeaud, Yonghui Wu, Jean-Baptiste Alayrac, Jiahui
Yu, Radu Soricut, Johan Schalkwyk, Andrew M. Dai, Anja Hauth, Katie Mil-
lican, David Silver, Slav Petrov, Melvin Johnson, Ioannis Antonoglou, Julian
Schrittwieser, Amelia Glaese, Jilin Chen, Emily Pitler, Timothy P. Lillicrap, Ange-
liki Lazaridou, Orhan Firat, James Molloy, Michael Isard, Paul Ronald Barham,
Tom Hennigan, Benjamin Lee, Fabio Viola, Malcolm Reynolds, Yuanzhong Xu,
Ryan Doherty, Eli Collins, Clemens Meyer, Eliza Rutherford, Erica Moreira, Ka-
reem Ayoub, Megha Goel, George Tucker, Enrique Piqueras, Maxim Krikun, Iain
Barr, Nikolay Savinov, Ivo Danihelka, Becca Roelofs, Anaïs White, Anders An-
dreassen, Tamara von Glehn, Lakshman Yagati, Mehran Kazemi, Lucas Gonzalez,
Misha Khalman, Jakub Sygnowski, and et al. 2023. Gemini: A Family of Highly
Capable Multimodal Models. CoRR abs/2312.11805 (2023). arXiv:2312.11805
doi:10.48550/ARXIV.2312.11805

[2] Jinheon Baek, Horst Samulowitz, Oktie Hassanzadeh, Dharmashankar Subrama-
nian, Sola Shirai, Alfio Gliozzo, and Debarun Bhattacharjya. 2025. Knowledge
Base Construction for Knowledge-Augmented Text-to-SQL. In Findings of the
Association for Computational Linguistics, ACL 2025, Vienna, Austria, July 27 -
August 1, 2025, Wanxiang Che, Joyce Nabende, Ekaterina Shutova, and Moham-
mad Taher Pilehvar (Eds.). Association for Computational Linguistics, 26569–
26583. https://aclanthology.org/2025.findings-acl.1363/

[3] Zhenbiao Cao, Yuanlei Zheng, Zhihao Fan, Xiaojin Zhang, Wei Chen, and Xiang
Bai. 2024. RSL-SQL: Robust Schema Linking in Text-to-SQL Generation. CoRR
abs/2411.00073 (2024). arXiv:2411.00073 doi:10.48550/ARXIV.2411.00073

[4] Liming Chen and Algirdas Avizienis. 1978. N-version programming: A fault-
tolerance approach to reliability of software operation. In Proc. 8th IEEE Int. Symp.
on Fault-Tolerant Computing (FTCS-8), Vol. 1. 3–9.

[5] chroma core. 2025. The AI-native open-source embedding database. https://github.

com/chroma-core/chroma Accessed: 2025-10-17.

[6] Yeounoh Chung, Gaurav Tarlok Kakkar, Yu Gan, Brenton Milne, and Fatma Ozcan.
2025. Is Long Context All You Need? Leveraging LLM’s Extended Context for
NL2SQL. Proc. VLDB Endow. 18, 8 (2025), 2735–2747.

[7] Dawei Gao, Haibin Wang, Yaliang Li, Xiuyu Sun, Yichen Qian, Bolin Ding, and
Jingren Zhou. 2024. Text-to-SQL Empowered by Large Language Models: A
Benchmark Evaluation. Proc. VLDB Endow. 17, 5 (2024), 1132–1145. doi:10.14778/
3641204.3641221

[8] Robert M. Hierons, Kirill Bogdanov, Jonathan P. Bowen, Rance Cleaveland, John
Derrick, Jeremy Dick, Marian Gheorghe, Mark Harman, Kalpesh Kapoor, Paul J.
Krause, Gerald Lüttgen, Anthony J. H. Simons, Sergiy A. Vilkomir, Martin R.
Woodward, and Hussein Zedan. 2009. Using formal specifications to support
testing. ACM Comput. Surv. 41, 2 (2009), 9:1–9:76. doi:10.1145/1459352.1459354
[9] Binyuan Hui, Jian Yang, Zeyu Cui, Jiaxi Yang, Dayiheng Liu, Lei Zhang, Tianyu
Liu, Jiajun Zhang, Bowen Yu, Kai Dang, An Yang, Rui Men, Fei Huang, Xingzhang
Ren, Xuancheng Ren, Jingren Zhou, and Junyang Lin. 2024. Qwen2.5-Coder
Technical Report. CoRR abs/2409.12186 (2024). arXiv:2409.12186 doi:10.48550/
ARXIV.2409.12186

[10] Aaron Hurst, Adam Lerer, Adam P. Goucher, Adam Perelman, Aditya Ramesh,
Aidan Clark, AJ Ostrow, Akila Welihinda, Alan Hayes, Alec Radford, Aleksander
Madry, Alex Baker-Whitcomb, Alex Beutel, Alex Borzunov, Alex Carney, Alex
Chow, Alex Kirillov, Alex Nichol, Alex Paino, Alex Renzin, Alex Tachard Passos,
Alexander Kirillov, Alexi Christakis, Alexis Conneau, Ali Kamali, Allan Jabri,
Allison Moyer, Allison Tam, Amadou Crookes, Amin Tootoonchian, Ananya
Kumar, Andrea Vallone, Andrej Karpathy, Andrew Braunstein, Andrew Cann,
Andrew Codispoti, Andrew Galu, Andrew Kondrich, Andrew Tulloch, Andrey
Mishchenko, Angela Baek, Angela Jiang, Antoine Pelisse, Antonia Woodford,
Anuj Gosalia, Arka Dhar, Ashley Pantuliano, Avi Nayak, Avital Oliver, Barret
Zoph, Behrooz Ghorbani, Ben Leimberger, Ben Rossen, Ben Sokolowsky, Ben
Wang, Benjamin Zweig, Beth Hoover, Blake Samic, Bob McGrew, Bobby Spero,
Bogo Giertler, Bowen Cheng, Brad Lightcap, Brandon Walkin, Brendan Quinn,
Brian Guarraci, Brian Hsu, Bright Kellogg, Brydon Eastman, Camillo Lugaresi,
Carroll L. Wainwright, Cary Bassin, Cary Hudson, Casey Chu, Chad Nelson,
Chak Li, Chan Jun Shern, Channing Conger, Charlotte Barette, Chelsea Voss,
Chen Ding, Cheng Lu, Chong Zhang, Chris Beaumont, Chris Hallacy, Chris
Koch, Christian Gibson, Christina Kim, Christine Choi, Christine McLeavey,
Christopher Hesse, Claudia Fischer, Clemens Winter, Coley Czarnecki, Colin
Jarvis, Colin Wei, Constantin Koumouzelis, and Dane Sherburn. 2024. GPT-4o
System Card. CoRR abs/2410.21276 (2024). arXiv:2410.21276 doi:10.48550/ARXIV.
2410.21276

[11] Aishwarya Kamath, Johan Ferret, Shreya Pathak, Nino Vieillard, Ramona Merhej,
Sarah Perrin, Tatiana Matejovicova, Alexandre Ramé, Morgane Rivière, Louis
Rouillard, Thomas Mesnard, Geoffrey Cideron, Jean-Bastien Grill, Sabela Ramos,
Edouard Yvinec, Michelle Casbon, Etienne Pot, Ivo Penchev, Gaël Liu, Francesco
Visin, Kathleen Kenealy, Lucas Beyer, Xiaohai Zhai, Anton Tsitsulin, Róbert Busa-
Fekete, Alex Feng, Noveen Sachdeva, Benjamin Coleman, Yi Gao, Basil Mustafa,
Iain Barr, Emilio Parisotto, David Tian, Matan Eyal, Colin Cherry, Jan-Thorsten
Peter, Danila Sinopalnikov, Surya Bhupatiraju, Rishabh Agarwal, Mehran Kazemi,
Dan Malkin, Ravin Kumar, David Vilar, Idan Brusilovsky, Jiaming Luo, Andreas
Steiner, Abe Friesen, Abhanshu Sharma, Abheesht Sharma, Adi Mayrav Gilady,

Adrian Goedeckemeyer, Alaa Saade, Alexander Kolesnikov, Alexei Bendebury,
Alvin Abdagic, Amit Vadi, András György, André Susano Pinto, Anil Das, Ankur
Bapna, Antoine Miech, Antoine Yang, Antonia Paterson, Ashish Shenoy, Ayan
Chakrabarti, Bilal Piot, Bo Wu, Bobak Shahriari, Bryce Petrini, Charlie Chen,
Charline Le Lan, Christopher A. Choquette-Choo, CJ Carey, Cormac Brick, Daniel
Deutsch, Danielle Eisenbud, Dee Cattle, Derek Cheng, Dimitris Paparas, Di-
vyashree Shivakumar Sreepathihalli, Doug Reid, Dustin Tran, Dustin Zelle, Eric
Noland, Erwin Huizenga, Eugene Kharitonov, Frederick Liu, Gagik Amirkhanyan,
Glenn Cameron, Hadi Hashemi, Hanna Klimczak-Plucinska, Harman Singh,
Harsh Mehta, Harshal Tushar Lehri, Hussein Hazimeh, Ian Ballantyne, Idan
Szpektor, Ivan Nardini, Jean Pouget-Abadie, Jetha Chan, Joe Stanton, John Wi-
eting, Jonathan Lai, Jordi Orbay, Joseph Fernandez, Josh Newlan, Ju-yeong Ji,
Jyotinder Singh, Kat Black, Kathy Yu, Kevin Hui, Kiran Vodrahalli, Klaus Greff,
Linhai Qiu, Marcella Valentine, Marina Coelho, Marvin Ritter, Matt Hoffman,
Matthew Watson, Mayank Chaturvedi, Michael Moynihan, Min Ma, Nabila Babar,
Natasha Noy, Nathan Byrd, Nick Roy, Nikola Momchev, Nilay Chauhan, Oskar
Bunyan, Pankil Botarda, Paul Caron, Paul Kishan Rubenstein, Phil Culliton,
Philipp Schmid, Pier Giuseppe Sessa, Pingmei Xu, Piotr Stanczyk, Pouya Tafti,
Rakesh Shivanna, Renjie Wu, Renke Pan, Reza Rokni, Rob Willoughby, Rohith
Vallu, Ryan Mullins, Sammy Jerome, Sara Smoot, Sertan Girgin, Shariq Iqbal,
Shashir Reddy, Shruti Sheth, Siim Põder, Sijal Bhatnagar, Sindhu Raghuram Pa-
nyam, Sivan Eiger, Susan Zhang, Tianqi Liu, Trevor Yacovone, Tyler Liechty,
Uday Kalra, Utku Evci, Vedant Misra, Vincent Roseberry, Vlad Feinberg, Vlad
Kolesnikov, Woohyun Han, Woosuk Kwon, Xi Chen, Yinlam Chow, Yuvein Zhu,
Zichuan Wei, Zoltan Egyed, Victor Cotruta, Minh Giang, Phoebe Kirk, Anand Rao,
Jessica Lo, Erica Moreira, Luiz Gustavo Martins, Omar Sanseviero, Lucas Gonzalez,
Zach Gleicher, Tris Warkentin, Vahab Mirrokni, Evan Senter, Eli Collins, Joelle K.
Barral, Zoubin Ghahramani, Raia Hadsell, Yossi Matias, D. Sculley, Slav Petrov,
Noah Fiedel, Noam Shazeer, Oriol Vinyals, Jeff Dean, Demis Hassabis, Koray
Kavukcuoglu, Clément Farabet, Elena Buchatskaya, Jean-Baptiste Alayrac, Rohan
Anil, Dmitry (Dima) Lepikhin, Sebastian Borgeaud, Olivier Bachem, Armand
Joulin, Alek Andreev, Cassidy Hardin, Robert Dadashi, and Léonard Hussenot.
2025. Gemma 3 Technical Report. CoRR abs/2503.19786 (2025). arXiv:2503.19786
doi:10.48550/ARXIV.2503.19786

[12] Janet L. Kolodner. 1993. Case-Based Reasoning. Morgan Kaufmann. doi:10.1016/

C2009-0-27670-7

[13] Woosuk Kwon, Zhuohan Li, Siyuan Zhuang, Ying Sheng, Lianmin Zheng,
Cody Hao Yu, Joseph Gonzalez, Hao Zhang, and Ion Stoica. 2023. Efficient
Memory Management for Large Language Model Serving with PagedAtten-
tion. In Proceedings of the 29th Symposium on Operating Systems Principles, SOSP
2023, Koblenz, Germany, October 23-26, 2023, Jason Flinn, Margo I. Seltzer, Pe-
ter Druschel, Antoine Kaufmann, and Jonathan Mace (Eds.). ACM, 611–626.
doi:10.1145/3600006.3613165

[14] Boyan Li, Yuyu Luo, Chengliang Chai, Guoliang Li, and Nan Tang. 2024. The
Dawn of Natural Language to SQL: Are We Fully Ready? [Experiment, Analysis &
Benchmark ]. Proc. VLDB Endow. 17, 11 (2024), 3318–3331. doi:10.14778/3681954.
3682003

[15] Boyan Li, Jiayi Zhang, Ju Fan, Yanwei Xu, Chong Chen, Nan Tang, and Yuyu
Luo. 2025. Alpha-SQL: Zero-Shot Text-to-SQL using Monte Carlo Tree Search.
In Forty-second International Conference on Machine Learning. OpenReview.net.
https://openreview.net/forum?id=kGg1ndttmI

[16] Haoyang Li, Shang Wu, Xiaokang Zhang, Xinmei Huang, Jing Zhang, Fuxin Jiang,
Shuai Wang, Tieying Zhang, Jianjun Chen, Rui Shi, Hong Chen, and Cuiping Li.
2025. OmniSQL: Synthesizing High-quality Text-to-SQL Data at Scale. Proc. VLDB
Endow. 18, 11 (2025), 4695–4709. https://www.vldb.org/pvldb/vol18/p4695-li.pdf
[17] Haoyang Li, Jing Zhang, Hanbing Liu, Ju Fan, Xiaokang Zhang, Jun Zhu, Renjie
Wei, Hongyan Pan, Cuiping Li, and Hong Chen. 2024. CodeS: Towards Building
Open-source Language Models for Text-to-SQL. Proc. ACM Manag. Data 2, 3
(2024), 127. doi:10.1145/3654930

[18] Jinyang Li, Binyuan Hui, Ge Qu, Jiaxi Yang, Binhua Li, Bowen Li, Bailin Wang,
Bowen Qin, Ruiying Geng, Nan Huo, et al. 2024. Can llm already serve as a
database interface? a big bench for large-scale database grounded text-to-sqls.
Advances in Neural Information Processing Systems 36 (2024).

[19] Xinyu Liu, Shuyu Shen, Boyan Li, Peixian Ma, Runzhi Jiang, Yuxin Zhang, Ju
Fan, Guoliang Li, Nan Tang, and Yuyu Luo. 2025. A Survey of Text-to-SQL in
the Era of LLMs: Where Are We, and Where Are We Going? IEEE Trans. Knowl.
Data Eng. 37, 10 (2025), 5735–5754.

[20] Xinyu Liu, Shuyu Shen, Boyan Li, Nan Tang, and Yuyu Luo. 2025. NL2SQL-
BUGs: A Benchmark for Detecting Semantic Errors in NL2SQL Translation. CoRR
abs/2503.11984 (2025). arXiv:2503.11984 doi:10.48550/ARXIV.2503.11984
[21] Yifu Liu, Yin Zhu, Yingqi Gao, Zhiling Luo, Xiaoxia Li, Xiaorong Shi, Yuntao
Hong, Jinyang Gao, Yu Li, Bolin Ding, and Jingren Zhou. 2025. XiYan-SQL: A
Novel Multi-Generator Framework For Text-to-SQL. CoRR abs/2507.04701 (2025).
arXiv:2507.04701 doi:10.48550/ARXIV.2507.04701

[22] Tianqi Luo, Chuhan Huang, Leixian Shen, Boyan Li, Shuyu Shen, Wei Zeng,
Nan Tang, and Yuyu Luo. 2025. nvBench 2.0: Resolving Ambiguity in Text-
to-Visualization through Stepwise Reasoning. arXiv preprint arXiv:2503.12880
(2025).

DeepEye-SQL: A Software-Engineering-Inspired Text-to-SQL Framework

Conference’17, July 2017, Washington, DC, USA

[23] Yuyu Luo, Guoliang Li, Ju Fan, Chengliang Chai, and Nan Tang. 2025. Natural
Language to SQL: State of the Art and Open Problems. Proc. VLDB Endow. 18, 12
(2025), 5466–5471.

[24] Yuyu Luo, Xuedi Qin, Nan Tang, and Guoliang Li. 2018. DeepEye: Towards
Automatic Data Visualization. In 34th IEEE International Conference on Data
Engineering, ICDE 2018, Paris, France, April 16-19, 2018. IEEE Computer Society,
101–112. doi:10.1109/ICDE.2018.00019

[25] Yuyu Luo, Nan Tang, Guoliang Li, Chengliang Chai, Wenbo Li, and Xuedi Qin.
2021. Synthesizing Natural Language to Visualization (NL2VIS) Benchmarks from
NL2SQL Benchmarks. In SIGMOD ’21: International Conference on Management
of Data, Virtual Event, China, June 20-25, 2021, Guoliang Li, Zhanhuai Li, Stratos
Idreos, and Divesh Srivastava (Eds.). ACM, 1235–1247. doi:10.1145/3448016.
3457261

[26] Yuyu Luo, Nan Tang, Guoliang Li, Jiawei Tang, Chengliang Chai, and Xuedi Qin.
2022. Natural Language to Visualization by Neural Machine Translation. IEEE
Trans. Vis. Comput. Graph. 28, 1 (2022), 217–226. doi:10.1109/TVCG.2021.3114848
[27] Peixian Ma, Boyan Li, Runzhi Jiang, Ju Fan, Nan Tang, and Yuyu Luo. 2024. A
Plug-and-Play Natural Language Rewriter for Natural Language to SQL. CoRR
abs/2412.17068 (2024). arXiv:2412.17068 doi:10.48550/ARXIV.2412.17068
[28] Karime Maamari, Fadhil Abubaker, Daniel Jaroslawicz, and Amine Mhedhbi.
2024. The Death of Schema Linking? Text-to-SQL in the Age of Well-Reasoned
Language Models. CoRR abs/2408.07702 (2024). arXiv:2408.07702 doi:10.48550/
ARXIV.2408.07702

[29] Yury A. Malkov and Dmitry A. Yashunin. 2020. Efficient and Robust Approximate
Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs. IEEE
Trans. Pattern Anal. Mach. Intell. 42, 4 (2020), 824–836. doi:10.1109/TPAMI.2018.
2889473

[30] Joel Ossher, Sushil Krishna Bajracharya, and Cristina Videira Lopes. 2010. Au-
tomated dependency resolution for open source software. In Proceedings of the
7th International Working Conference on Mining Software Repositories, MSR 2010
(Co-located with ICSE), Cape Town, South Africa, May 2-3, 2010, Proceedings, Jim
Whitehead and Thomas Zimmermann (Eds.). IEEE Computer Society, 130–140.
doi:10.1109/MSR.2010.5463346

[31] Mohammadreza Pourreza, Hailong Li, Ruoxi Sun, Yeounoh Chung, Shayan Talaei,
Gaurav Tarlok Kakkar, Yu Gan, Amin Saberi, Fatma Ozcan, and Sercan Ö. Arik.
2025. CHASE-SQL: Multi-Path Reasoning and Preference Optimized Candidate
Selection in Text-to-SQL. In The Thirteenth International Conference on Learning
Representations, ICLR 2025, Singapore, April 24-28, 2025. OpenReview.net. https:
//openreview.net/forum?id=CvGqMD5OtX

[32] Mohammadreza Pourreza and Davood Rafiei. 2023. DIN-SQL: Decomposed In-
Context Learning of Text-to-SQL with Self-Correction. In Advances in Neural
Information Processing Systems 36: Annual Conference on Neural Information
Processing Systems 2023, NeurIPS 2023, New Orleans, LA, USA, December 10 - 16,
2023, Alice Oh, Tristan Naumann, Amir Globerson, Kate Saenko, Moritz Hardt,
and Sergey Levine (Eds.). http://papers.nips.cc/paper_files/paper/2023/hash/
72223cc66f63ca1aa59edaec1b3670e6-Abstract-Conference.html

[33] Ge Qu, Jinyang Li, Bowen Qin, Xiaolong Li, Nan Huo, Chenhao Ma, and Reynold
Cheng. 2025. SHARE: An SLM-based Hierarchical Action CorREction Assistant
for Text-to-SQL. In Proceedings of the 63rd Annual Meeting of the Association for
Computational Linguistics (Volume 1: Long Papers), ACL 2025, Vienna, Austria,
July 27 - August 1, 2025, Wanxiang Che, Joyce Nabende, Ekaterina Shutova, and
Mohammad Taher Pilehvar (Eds.). Association for Computational Linguistics,
11268–11292. https://aclanthology.org/2025.acl-long.552/

[34] M. G. Rekoff. 1985. On reverse engineering. IEEE Trans. Syst. Man Cybern. 15, 2

(1985), 244–252. doi:10.1109/TSMC.1985.6313354

[35] Per Runeson. 2006. A Survey of Unit Testing Practices. IEEE Softw. 23, 4 (2006),

22–29. doi:10.1109/MS.2006.91

[36] Nayan B. Ruparelia. 2010. Software development lifecycle models. ACM SIGSOFT

Softw. Eng. Notes 35, 3 (2010), 8–13.

[37] Joscha Schnell and Gunther Reinhart. 2016. Quality management for battery

production: a quality gate concept. Procedia CIRP 57 (2016), 568–573.
[38] Philip Sedgwick. 2012. Pearson’s correlation coefficient. Bmj 345 (2012).
[39] Lei Sheng and Shuai-Shuai Xu. 2025. CSC-SQL: Corrective Self-Consistency
in Text-to-SQL via Reinforcement Learning. CoRR abs/2505.13271 (2025).
arXiv:2505.13271 doi:10.48550/ARXIV.2505.13271

[40] Lei Sheng, Shuai-Shuai Xu, and Wei Xie. 2025. BASE-SQL: A powerful open source
Text-To-SQL baseline approach. CoRR abs/2502.10739 (2025). arXiv:2502.10739
doi:10.48550/ARXIV.2502.10739

[41] Vladislav Shkapenyuk, Divesh Srivastava, Theodore Johnson, and Parisa Ghane.
2025. Automatic Metadata Extraction for Text-to-SQL. CoRR abs/2505.19988
(2025). arXiv:2505.19988 doi:10.48550/ARXIV.2505.19988

[42] Zhihao Shuai, Boyan Li, Siyu Yan, Yuyu Luo, and Weikai Yang. 2025. DeepVIS:
Bridging Natural Language and Data Visualization Through Step-wise Reasoning.
CoRR abs/2508.01700 (2025). arXiv:2508.01700 doi:10.48550/ARXIV.2508.01700

[43] Shayan Talaei, Mohammadreza Pourreza, Yu-Chen Chang, Azalia Mirhoseini, and
Amin Saberi. 2024. CHESS: Contextual Harnessing for Efficient SQL Synthesis.
CoRR abs/2405.16755 (2024). arXiv:2405.16755 doi:10.48550/ARXIV.2405.16755

[44] Martyn Thomas and Frank E. McGarry. 1994. Top-Down vs. Bottom-Up Process

Improvement. IEEE Softw. 11, 4 (1994), 12–13. doi:10.1109/52.300121

[45] Peter Ulbrich, Martin Hoffmann, Rüdiger Kapitza, Daniel Lohmann, Wolfgang
Schroder-Preikschat, and Reiner Schmid. 2012. Eliminating single points of failure
in software-based redundancy. In 2012 Ninth European Dependable Computing
Conference. IEEE, 49–60.

[46] Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc V. Le, Ed H. Chi, Sharan Narang,
Aakanksha Chowdhery, and Denny Zhou. 2023. Self-Consistency Improves
Chain of Thought Reasoning in Language Models. In The Eleventh International
Conference on Learning Representations, ICLR 2023, Kigali, Rwanda, May 1-5, 2023.
OpenReview.net. https://openreview.net/forum?id=1PL1NIMMrw

[47] Yifan Wu, Jingze Shi, Bingheng Wu, Jiayi Zhang, Xiaotian Lin, Nan Tang, and
Yuyu Luo. 2025. Concise Reasoning, Big Gains: Pruning Long Reasoning Trace
with Difficulty-Aware Prompting. CoRR abs/2505.19716 (2025).

[48] Xiangjin Xie, Guangwei Xu, Lingyan Zhao, and Ruijie Guo. 2025. OpenSearch-
SQL: Enhancing Text-to-SQL with Dynamic Few-shot and Consistency Align-
ment. Proc. ACM Manag. Data 3, 3 (2025), 194:1–194:24. doi:10.1145/3725331
[49] An Yang, Anfeng Li, Baosong Yang, Beichen Zhang, Binyuan Hui, Bo Zheng,
Bowen Yu, Chang Gao, Chengen Huang, Chenxu Lv, Chujie Zheng, Dayiheng
Liu, Fan Zhou, Fei Huang, Feng Hu, Hao Ge, Haoran Wei, Huan Lin, Jialong
Tang, Jian Yang, Jianhong Tu, Jianwei Zhang, Jian Yang, Jiaxi Yang, Jingren Zhou,
Junyang Lin, Kai Dang, Keqin Bao, Kexin Yang, Le Yu, Lianghao Deng, Mei Li,
Mingfeng Xue, Mingze Li, Pei Zhang, Peng Wang, Qin Zhu, Rui Men, Ruize Gao,
Shixuan Liu, Shuang Luo, Tianhao Li, Tianyi Tang, Wenbiao Yin, Xingzhang
Ren, Xinyu Wang, Xinyu Zhang, Xuancheng Ren, Yang Fan, Yang Su, Yichang
Zhang, Yinger Zhang, Yu Wan, Yuqiong Liu, Zekun Wang, Zeyu Cui, Zhenru
Zhang, Zhipeng Zhou, and Zihan Qiu. 2025. Qwen3 Technical Report. CoRR
abs/2505.09388 (2025). arXiv:2505.09388 doi:10.48550/ARXIV.2505.09388
[50] Jiaxi Yang, Binyuan Hui, Min Yang, Jian Yang, Junyang Lin, and Chang Zhou. 2024.
Synthesizing Text-to-SQL Data from Weak and Strong LLMs. In Proceedings of the
62nd Annual Meeting of the Association for Computational Linguistics (Volume 1:
Long Papers), ACL 2024, Bangkok, Thailand, August 11-16, 2024, Lun-Wei Ku, Andre
Martins, and Vivek Srikumar (Eds.). Association for Computational Linguistics,
7864–7875. doi:10.18653/V1/2024.ACL-LONG.425

[51] Tao Yu, Rui Zhang, Kai Yang, Michihiro Yasunaga, Dongxu Wang, Zifan Li, James
Ma, Irene Li, Qingning Yao, Shanelle Roman, Zilin Zhang, and Dragomir R. Radev.
2018. Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-
Domain Semantic Parsing and Text-to-SQL Task. In EMNLP. Association for
Computational Linguistics, 3911–3921.

[52] Jiayi Zhang, Jinyu Xiang, Zhaoyang Yu, Fengwei Teng, Xionghui Chen, Jiaqi
Chen, Mingchen Zhuge, Xin Cheng, Sirui Hong, Jinlin Wang, Bingnan Zheng,
Bang Liu, Yuyu Luo, and Chenglin Wu. 2025. AFlow: Automating Agentic
Workflow Generation. In The Thirteenth International Conference on Learning
Representations, ICLR 2025, Singapore, April 24-28, 2025. OpenReview.net. https:
//openreview.net/forum?id=z5uVAKwmjf

[53] Qingjie Zhang, Di Wang, Haoting Qian, Yiming Li, Tianwei Zhang, Minlie Huang,
Ke Xu, Hewu Li, Liu Yan, and Han Qiu. 2025. Understanding the Dark Side of
LLMs’ Intrinsic Self-Correction. In Proceedings of the 63rd Annual Meeting of
the Association for Computational Linguistics (Volume 1: Long Papers), ACL 2025,
Vienna, Austria, July 27 - August 1, 2025, Wanxiang Che, Joyce Nabende, Ekaterina
Shutova, and Mohammad Taher Pilehvar (Eds.). Association for Computational
Linguistics, 27066–27101. https://aclanthology.org/2025.acl-long.1314/

[54] Yuxin Zhang, Meihao Fan, Ju Fan, Mingyang Yi, Yuyu Luo, Jian Tan, and Guoliang
Li. 2025. Reward-SQL: Boosting Text-to-SQL via Stepwise Reasoning and Process-
Supervised Rewards. CoRR abs/2505.04671 (2025).

[55] Yanzhao Zhang, Mingxin Li, Dingkun Long, Xin Zhang, Huan Lin, Baosong
Yang, Pengjun Xie, An Yang, Dayiheng Liu, Junyang Lin, Fei Huang, and Jingren
Zhou. 2025. Qwen3 Embedding: Advancing Text Embedding and Reranking
Through Foundation Models. CoRR abs/2506.05176 (2025). arXiv:2506.05176
doi:10.48550/ARXIV.2506.05176

[56] Yizhang Zhu, Shiyin Du, Boyan Li, Yuyu Luo, and Nan Tang. 2024. Are Large

Language Models Good Statisticians?. In NeurIPS.

[57] Yizhang Zhu, Runzhi Jiang, Boyan Li, Nan Tang, and Yuyu Luo. 2025. El-
lieSQL: Cost-Efficient Text-to-SQL with Complexity-Aware Routing. CoRR
abs/2503.22402 (2025).

