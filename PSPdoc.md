Agentic Software Process (ASP): A Framework for Disciplined Autonomous DevelopmentI. The Agentic Engineering Paradox: Why Formal Process is the New Foundation for AI AgilityThe advent of autonomous, generative AI agents represents a paradigm shift in software development.1 These systems, capable of complex reasoning, planning, and tool use, are moving from the realm of "copilots" to true autonomous "agents" that can independently execute entire development tasks.3 This transition, however, creates a fundamental paradox. The software development methodologies adopted over the past two decades, specifically those under the "Agile" umbrella, are uniquely ill-suited for managing an autonomous AI workforce.Agile methodologies were designed explicitly for high-trust human teams. They succeed by minimizing formal documentation and process rigidity, relying instead on high-bandwidth, adaptive human collaboration—conversations, intuition, and shared implicit knowledge—to clarify ambiguity and adapt to change.5 An autonomous AI agent possesses none of these human capabilities. It "lacks the context of hallway conversations or the intuition of an experienced engineer".5 An agent cannot intuit requirements; it can only execute explicit, unambiguous instructions.8Attempting to manage a team of agents using Agile's low-documentation, high-ambiguity approach does not create agility; it creates "chaos".9 This approach invites systemic risks, including "uncontrolled autonomy, fragmented system access, [and a] lack of observability and traceability".2Consequently, the rise of agentic AI necessitates a return to the principles of formal process discipline. AI agents require what the Personal Software Process (PSP) was designed to provide: "a disciplined approach" 10, "expert-level guidance" 11, and unambiguous, formal specifications.12 This need is validated by emerging research on "Specification-First AI Development," which argues that formal specifications create "a shared understanding, or AI fluency, between technical and business teams," thereby bridging the "substantial gap between technical capabilities and business requirements".12 The "bureaucracy" and "detailed protocols" of formal models 13, once seen as cumbersome, are now a critical feature. For an agent, the formal specification is not mere documentation; it is the API and configuration for its entire workflow.5This re-evaluation of formal process extends beyond efficiency. Autonomous agents introduce novel, systemic risks.2 They can "deviate from expected behavior" 16 or "misinterpret" instructions, "leading to unintended actions".17 A highly structured process, built on "structured outputs" 17 and formal specifications 12, provides the "predefined parameters" and "safeguards" necessary for containment.17 This approach is already standard in high-stakes fields like hardware design, which mandate "formal verification" for agentic systems.14 Therefore, applying a PSP-like framework is not merely an engineering choice; it is a fundamental safety and governance strategy, essential for building the auditable, reliable, and trustworthy autonomous systems that enterprises require.2 In the agentic era, the process is the governance.19II. A Primer on the Personal Software Process (PSP) FrameworkThe Personal Software Process (PSP) is a structured methodology developed by Watts Humphrey at the Software Engineering Institute (SEI) at Carnegie Mellon University.20 It was designed as a "process-focused" 10 and "metrics-driven" 10 framework to help individual software engineers measure, manage, and improve their personal performance, quality, and productivity.23Core Phases (The PSP Lifecycle)The basic PSP process is structured into three distinct phases that an engineer follows for each task or module 21:Planning: The engineer analyzes the requirements, produces a detailed design, and provides a comprehensive estimate. This includes estimating the product size (traditionally in Lines of Code, or LOC) and the required effort (in minutes) for each phase of development. This data is recorded in a plan summary.21Development: This is a formal, multi-step execution phase.21 Unlike ad-hoc coding, the PSP development phase is itself broken down into discrete sub-phases, which typically include: Requirements, Design, Design Review, Code, Code Review, Compile, and Test.11 The inclusion of formal review phases (Design Review and Code Review) is a critical quality-control feature intended to find and fix defects as early as possible.11Postmortem: After the task is complete, the engineer "compare[s] actual performance against the plan".21 In this phase, the engineer finalizes all process data, produces a summary report, and, most importantly, documents "ideas for process improvement" (known as a Process Improvement Proposal, or PIP) to enhance the process for the next cycle.11Core Artifacts (The Data Ecosystem)The PSP's data-driven nature is supported by four key elements: Scripts, Measures, Standards, and Forms.11Process Scripts: These are explicit, "expert-level guidance" 11 documents that function as checklists. They define the precise entry criteria, steps, and exit criteria for each phase (e.g., "Planning Script," "Code Review Script," "Test Script").24Logs (Measures): These are the two primary data-collection artifacts.Time Recording Log: Engineers are required to "LOG EVERYTHING!!".28 This log is used to record the start time, stop time, and interruption time for every activity, categorized by the phase in which it occurred (e.g., 10 minutes in Planning, 30 minutes in Design).24Defect Recording Log: This log is used to record every defect found. Critically, it records the type of defect, the phase in which it was injected (e.g., a logic error made during the Design phase), and the phase in which it was removed (e.g., found during the Code Review phase).24Standards: These are formal documents that ensure consistency, such as a "Coding Standard" 11 or a "Defect Type Standard".27Checklists: These are personal artifacts, such as a "Code Review Checklist," which are actively updated. During the Postmortem, an engineer analyzes the defects they made and adds items to their personal checklists to prevent making the same error in the future.11The PSP framework, designed in the 1990s, is a perfect architectural blueprint for a modern, self-improving autonomous agent. The purely mechanical flow is identical: an agent follows a Script (its System Prompt) 11; executes a task; records performance data to a Log (automated telemetry) 24; and in a Postmortem phase, a meta-agent analyzes the log data 21 and updates its own Scripts/Checklists (its prompts and context) to improve future performance.11 The "Process Script" becomes the System Prompt; the "Standards" and "Checklists" become the Contextual Files and Tool Definitions 31; the "Logs" are the automated Telemetry and Observability Pipeline 33; and the "Postmortem" is the Reflection and Self-Correction Agent.35 Early academic research proposing the use of agents to automate the "onerous" data collection of PSP 37 foreshadowed this synthesis, but it is now possible to automate the entire process.III. Principles for Adapting PSP to an Autonomous Agent WorkforceTo operationalize this framework, which will be referred to as the Agentic Software Process (ASP), a direct translation of PSP's four core measures (Size, Effort, Quality, Schedule) 11 is required. These concepts must be mapped from the human domain to metrics suitable for an autonomous agentic system.16Translating "Size" (LOC)PSP's "Size" metric, Lines of Code (LOC) 11, is a notoriously poor proxy for complexity. For ASP, this is replaced with Semantic Complexity. This is a composite metric that measures the work required, not the text produced. It is derived from:The number of decomposed functional units, or "software issue[s]".44The semantic "chunking" of the codebase required to provide context.46The number of "code entities" 47 or tool/API interactions required for the task.48Translating "Effort" (Minutes)PSP's "Effort" metric, time in minutes 11, is one-dimensional. For ASP, this is replaced with the Agent Cost Vector. "Effort" for an agent is a multi-dimensional vector of resource consumption 41, which must be logged as:Computational Cost: Processing Latency (in milliseconds) and Memory Usage.42Financial Cost: API Call Costs and Token Usage (both input and output).42Task Cost: The number of tool calls and, critically, the number of self-correction loops or retries.16Translating "Quality" (Defects)PSP's "Quality" metric, number of defects 11, must be expanded. For ASP, this is replaced with Alignment Deviations. AI agent failures are often behavioral, not merely logical.16 This requires a new taxonomy (detailed in Section VI) to capture failures such as:"Discrepancies between developer-implemented logic and... LLM-generated content".52Tool invocation failures, hallucinations, or prompt misinterpretation.51Failure to meet "performance standards" or "business goals".16Translating "Schedule" (Dates)PSP's "Schedule" metric, planned vs. actual completion dates 11, is also adapted. For ASP, this becomes Planned vs. Actual Cost Vector. "Schedule" is now a measure of estimation accuracy against the total predicted resource consumption (the Agent Cost Vector), not just a temporal deadline.These translations are summarized in the following table, which serves as the "Rosetta Stone" for the ASP framework.Table 1: PSP to ASP (Agentic Software Process) Translation MatrixPSP ConceptPSP Implementation (Human)ASP Implementation (Agent)Key MetricsPhase: PlanningHuman analyzes specs and estimates size/time using historical data and PROBE.21A "Planning Agent" parses specs, decomposes tasks 54, and runs a PROBE-AI estimation algorithm.24Est. Semantic Complexity, Est. Cost VectorPhase: DevelopmentHuman designs, codes, reviews, and tests in discrete, manually-logged phases.11A specialized multi-agent team (Design, Code, Review Agents) executes tasks in a formal, gated sequence.55Actual Cost VectorPhase: PostmortemHuman manually analyzes logs, calculates metrics, updates checklists, and writes a Process Improvement Proposal (PIP).11A "Postmortem Agent" (Meta-Agent) analyzes performance logs 36, identifies failure patterns 56, and generates a PIP (prompt update) for Human-in-the-Loop (HITL) approval.35Process Yield, Defect Density, Estimation AccuracyArtifact: Process ScriptStatic document (e.g., Word, HTML) that guides a human.11Dynamic System Prompt + Tool Definitions + Contextual files (e.g., CLAUDE.MD) for an agent.31N/AArtifact: Time LogManual log sheet (or spreadsheet) of time in minutes, recorded per phase.28Automated telemetry/observability platform (e.g., Langfuse, AgentOps) 33 logging all resource consumption per agent execution.60Latency, Tokens, API Cost, ComputeArtifact: Defect LogManual log of defect type and estimated injection/removal phase.24Structured, automated log of "Alignment Deviations" 62 categorized by a formal AI defect taxonomy.52Defect_ID, Defect_Type, Phase_Injected, Phase_RemovedMetric: SizeLines of Code (LOC).11Semantic Complexity Score (Composite of 44).Semantic UnitsMetric: EffortTime in Minutes.11Agent Cost Vector.41IV. The Planning Phase: A Prompt-Based Framework for Agentic EstimationThe ASP Planning Phase replaces uncertain human estimation 21 with a data-driven agentic process executed by a "Planning Agent".64 This process adapts PSP's PROBE (Proxy-Based Estimation) method.Adapting PROBE (Proxy-Based Estimation) for AgentsIn PSP, the PROBE method uses linear regression to map an estimated size (proxy) to a predicted actual effort (e.g., minutes). This model is built using historical data from "at least three prior projects".24This method is uniquely suited for AI agents for two reasons:Automated Data: The primary challenge of PSP for humans is the "onerous" 30 and inconsistent manual logging of data. In ASP, the Agent Cost Vector (effort) and Actual Semantic Complexity (size) can be logged automatically and perfectly by an observability layer.33 This provides a rich, reliable historical database.Computational Ease: The linear regression calculations, which a human would perform manually or with a spreadsheet, are a simple task for an agent to execute as part of its workflow, using time-series forecasting or regression techniques.65This new method is PROBE-AI. It maps Estimated Semantic Complexity (our new "Size") to the Predicted Agent Cost Vector (our new "Effort"). The following table demonstrates the data required for this process.Table 2: PROBE-AI Estimation Example (Predicting Agent Cost)Part 1: Historical Data (Agent Performance Log)Task_IDEst. Complexity (Proxy)Actual_Complexity (Units)Actual_Latency (ms)Actual_TokensActual_API_Cost ($)Task-00110121500045000$0.08Task-00254800021000$0.03Task-00320223100085000$0.15Part 2: New Task Estimation (Executed by Planning Agent)New Task: Task-004 ("Add user profile page")Planning Agent Est. Complexity (from Prompt 1): 18 UnitsPROBE-AI (Agent executes regression based on Part 1):Predicted_Latency = $f(18)$ $\rightarrow$ ~27000 msPredicted_Tokens = $g(18)$ $\rightarrow$ ~72000Predicted_Cost = $h(18)$ $\rightarrow$ ~$0.12Actionable Framework: Planning Agent Prompt ChainThis process is executed via a two-prompt chain:Prompt 1: Task Decomposition & Sizing (Input: Human Requirements)Code snippet## ROLE
You are an expert "PSP Planning Agent". Your persona is that of a meticulous Senior Software Architect trained by the Software Engineering Institute.[20]

## TASK
Your goal is to "Decompose [deliverable name] into smaller, manageable work packages". Analyze the following requirements:


1. Decompose the high-level requirements into a list of atomic "Semantic Units of Work".
2. For each unit, analyze its complexity. Estimate a "Semantic Complexity Score" (integer 1-100) based on factors like: required logical operations, data transformations, number of required tool/API interactions , and novelty of the request.[67]

## RESPONSE FORMAT
You MUST reply using the following JSON format.[68, 69] Do not provide any other text.

{
  "project_id": "[Project Name]",
  "semantic_units":",
      "est_complexity": 15
    },
    {
      "unit_id": "SU-002",
      "description": "",
      "est_complexity": 8
    }
  ]
}
Prompt 2: PROBE-AI Effort Estimation (Input: Prompt 1 Output + Historical Data)Code snippet## ROLE
You are an expert "PSP Estimation Agent." You are a data scientist specializing in software effort forecasting.[65, 66, 70]

## TASK
You will be given:
(A) The "Semantic Units" JSON from the Planning Agent.
(B) A CSV of historical performance data [71, 72] formatted as:.

1. Load the historical data from (B).
2. For each "semantic_unit" in (A), you MUST use linear regression (PSP PROBE Method)  on the historical data to predict the 'Est_Cost_Vector'. Use "est_complexity" as the independent variable.
3. Sum these vectors to create a total project plan.

## RESPONSE FORMAT
You MUST reply in the formal "PSP Project Plan Summary" [24, 25] JSON schema. Adhere to this structure precisely [73, 74]:

{
  "project_id": "[Project Name]",
  "total_est_latency_ms": 35000,
  "total_est_tokens": 88000,
  "total_est_api_cost": 0.14,
  "task_plan":
}
V. The Development Phase: Prompt-Driven Execution for Specialized Coding AgentsThis section provides the "Process Scripts" 11 as a series of prompts for a team of specialized agents 55, mapping directly to the formal PSP development phases.11A primary failure mode for autonomous agents is the propagation of "compounding errors" 76, where a subtle flaw in the design phase is amplified by the coding and testing phases. The PSP process by design prevents this by inserting formal Design Review and Code Review phases as hard gates.11This structure is implemented as a sequential multi-agent orchestration.55 The "Design Agent's" output artifact is not passed directly to the "Coding Agent." It is first passed to the "Design Review Agent." The orchestrator halts execution until this review is complete and all logged defects are either fixed or explicitly approved by a Human-in-the-Loop (HITL).57 This transforms the PSP review phases from a human checklist item into an explicit, programmatic validation gate, enforcing alignment and preventing downstream failures.Actionable Framework: Development Agent Prompt Chain1. Design Agent Prompt:Code snippet## ROLE
You are a "Software Design Agent".[77] Your task is to create a complete, formal, low-level design document based on the provided inputs.

## INPUT
1. Requirements:
2. Project Plan:

## TASK
Generate the complete Low-Level Design Specification. You MUST use the provided "Design Templates" [30, 58, 78] to structure your response. The design must be detailed enough for a separate coding agent to implement without further ambiguity.

## RESPONSE FORMAT
You MUST output a single JSON object [69] with the following schema.[74, 77]

{
  "design_spec": {
    "api_contracts":,
    "data_schema": [
      {
        "table_name": "users",
        "columns": ["user_id (PK)", "username", "email_hash"]
      }
    ],
    "component_logic":
      }
    ]
  },
  "design_review_checklist":
}
2. Design Review Agent Prompt:Code snippet## ROLE
You are a "Design Review Agent". You are a meticulous quality assurance expert specializing in system architecture and security.

## INPUT
1. Design Specification JSON (from Design Agent)
2. Original Requirements

## TASK
Critically review the "design_spec" against both the "design_review_checklist"  and the Original Requirements.
1. For *every* item in the "design_review_checklist", verify compliance.
2. Identify all logical inconsistencies, non-functional requirement violations, and deviations from the Original Requirements.

## RESPONSE FORMAT
You MUST output a "Design Review Report" in this JSON format. If no defects are found, return an empty "defects" array.

{
  "review_status": "Failed",
  "defects_found":
}
(Orchestrator halts. If review_status == "Failed", it loops back to the Design Agent with the defect report. If review_status == "Passed", it proceeds to the Coding Agent.)3. Coding Agent Prompt:Code snippet## ROLE
You are a "Coding Agent".[32, 79] Your persona is a senior software engineer.

## INPUT
1. Approved Design Specification JSON
2. Project Coding Standard [8, 11, 32]: "All code must be Python 3.10. Use constructor injection. All methods must have type hints and docstrings. All database access must use parameterized queries."
3. Context Files:]

## TASK
1. Write the complete, production-ready code to implement the "component_logic" and "api_contracts" from the Design Specification.
2. You MUST adhere *perfectly* to the "Project Coding Standard".
3. You MUST provide the FULL, updated content of every file you create or edit.[80]
4. Nudge: Start Python files with "import".[81]

## RESPONSE FORMAT
Output a JSON object mapping filenames to their full string content:

{
  "files": {
    "src/api/user_routes.py": "import...\n\nclass UserRoutes:\n  def __init__(self, db_service):\n    self.db_service = db_service\n\n  def create_user(self, username: str, email: str) -> dict:\n    #... implementation...\n",
    "src/services/db_service.py": "import...\n\nclass DBService:\n  def save_user(self, user_id: str, username: str, email_hash: str):\n    #... implementation with parameterized query...\n"
  }
}
4. Code Review Agent Prompt:Code snippet## ROLE
You are a "Code Review Agent".[82, 83]

## INPUT
1. Generated Code (from Coding Agent)
2. Project Coding Standard [32]
3. Code Review Checklist [30, 84, 85]:
  .

## TASK
Perform a rigorous code review. For each file, check *every* item on the checklist against the Project Coding Standard. Log *every* defect found using the "Defect Recording Log" format.[27, 63]

## RESPONSE FORMAT
Output a "Code Review Report" JSON.[62]

{
  "review_status": "Failed",
  "defects_found":
}
5. Test Agent (Compile/Test) Prompt:Code snippet## ROLE
You are a "Software Test Agent".[86]

## INPUT
1. *Approved* Code (after Code Review fixes)
2. Design Specification (for requirements and logic)

## TASK
1. (Compile) Execute the build or compilation process. Log any syntax, dependency, or build errors.[28, 87]
2. (Test) Generate unit test cases based on the "component_logic" and "api_contracts" in the "design_spec".[27, 86]
3. Create realistic, synthetic test data for these cases.[86]
4. Execute the generated unit tests against the code.

## RESPONSE FORMAT
Output a "Test Report"  JSON. Log *all* failures (compile, build, or test) to the "defects_found" list.

{
  "test_status": "Failed",
  "test_summary": {
    "total_tests": 20,
    "passed": 19,
    "failed": 1
  },
  "defects_found":"
    }
  ]
}
VI. Automating Process Data: Redefining "Time" and "Defects" for Agentic SystemsThe foundation of the PSP improvement loop is high-quality, granular data. The primary reason PSP implementation fails with human engineers is that manual data logging is "onerous" and time-consuming.30 The ASP framework solves this by making data collection an automated, fundamental part of the agentic workflow.Automating the "Time Log"Instead of a human manually logging minutes 28, the ASP framework uses an "Observability Layer".33 This layer automatically intercepts every agent execution (each prompt and response) and captures the complete Agent Cost Vector.42 This provides perfect, granular data not just for "time" (latency), but for all resource consumption, including token counts and API costs.60 This automated logging 37 is the "ground truth" for the PROBE-AI estimation and Postmortem analysis.Automating the "Defect Log"PSP's most powerful (and most difficult) data points are the defect injection phase and defect removal phase.11 Humans are notoriously bad at this; a bug found in "Test" may be a "Design" error, but the human developer may not know or may log it incorrectly.87The phased multi-agent orchestration in Section V solves this problem perfectly. This orchestration provides free, 100% accurate injection and removal data, which was impossible for humans:When the Design Review Agent finds a defect, it is known by definition that the defect was Injected: Design and Removed: Design Review.When the Code Review Agent finds a defect, it was Injected: Code and Removed: Code Review.When the Test Agent finds a defect (that was not caught by Code Review), it was Injected: Code and Removed: Test.This automated, accurate data logging allows the system to calculate the precise "defect injection distribution" and "defect removal rate by phase" 11 that PSP was designed to capture.Table 3: AI Agent "Effort" Log Schema (The new "Time Log")This schema defines the data captured by the automated telemetry pipeline.33ColumnTypeDescriptionTimestampDateTimeTimestamp of the agent execution.Task_IDStringUnique identifier for the overall task (e.g., "Task-004").Agent_Role (Phase)StringThe role of the agent that executed (e.g., "Planning", "Design", "Code", "Test").Metric_TypeStringThe metric being recorded (e.g., "Latency", "Tokens_In", "Tokens_Out", "API_Cost").42Metric_ValueFloatThe numeric value of the metric.UnitStringThe unit of measure (e.g., "ms", "tokens", "USD").Table 4: AI Agent Defect Taxonomy & Log Schema (The new "Defect Log")This table defines the formal defect log, based on a taxonomy of AI-specific failures 52, which enables meaningful root cause analysis.62Log Schema Columns:ColumnTypeDescriptionDefect_IDStringUnique identifier for the defect (e.g., "D-001").Task_IDStringUnique identifier for the overall task.Defect_TypeStringThe classification of the defect from the taxonomy below.Phase_Injected (Agent_Role)StringThe agent role that created the defect (e.g., "Design", "Code").11Phase_Removed (Agent_Role)StringThe agent role that found the defect (e.g., "Design Review", "Test").11Effort_to_Fix_VectorJSONThe Agent Cost Vector (cost of the correction loop) required to fix the defect.DescriptionStringDetailed description of the defect.Defect Taxonomy (for Defect_Type field):1_Planning_Failure: Flawed task decomposition or incorrect estimation by the Planning Agent.2_Prompt_Misinterpretation: Agent failed to follow instructions, context, or constraints.523_Tool_Use_Error: Incorrect tool selection, invalid parameters, or failure to parse tool output.524.Hallucination: Agent generated non-factual content, fabricated a library, or "made up" an answer.515_Security_Vulnerability: Injected a security flaw (e.g., SQLi, XSS).826_Conventional_Code_Bug: A traditional logical, syntax, or runtime error.877_Task_Execution_Error: A non-agent failure (e.g., environment timeout, API down).528_Alignment_Deviation: Output is technically correct but violates business goals, ethics, or safety guardrails.16VII. The Postmortem Phase: Enabling Agentic Self-Correction and Process ImprovementThe Postmortem phase 21 is the "brain" of the self-improving system. It is re-imagined as an automated "Reflection Loop" 93, where a "Meta-Agent" 35 analyzes the data from Section VI to propose improvements to the prompts from Section V.The Myth of Full Autonomy vs. The Reality of HITLA common goal in agentic research is full, autonomous self-correction.93 However, practical experience and research indicate that this is largely a "myth".99 Fully autonomous reflection loops are "fragile" 100, add significant latency 99, get stuck in "infinite feedback loops" 101, and "struggle to locate the root cause of the error" 90 because they "lack a benchmarked data set with basic truths".102 As one analysis concludes, "The 'self' in self-improvement was us".99The ASP framework avoids this trap by embracing the original PSP model. The PSP Postmortem was never fully autonomous; the human analyzed the data and then proposed a "Process Improvement Proposal" (PIP) 11 to be approved.This maps perfectly to the Human-in-the-Loop (HITL) model.103 The most robust and safe 92 architecture for self-improvement is a hybrid one:The "Postmortem Agent" performs the 99% of work that humans find onerous: automated data aggregation, statistical calculation, and root cause analysis.36The agent generates a proposal (a PIP).A human expert provides the 1% of work that agents cannot: "strategic oversight" 105, "validat[ion]" 57, and final approval of the change.In this ASP loop, the agent proposes changes to its own "Process Scripts" (prompts), but a human engineer must approve and commit those changes to the "Prompt Repository" 106 before they are active in production.Actionable Framework: Postmortem Agent Prompt ChainPrompt 1: Performance Analysis (Input: Logs from Section VI)Code snippet## ROLE
You are a "PSP Postmortem Agent".[21, 35] You are a "Meta-Agent" [97] acting as a Senior Engineering Manager.

## INPUT
1. Project Plan Summary (from Planning Agent, Section IV)
2. Effort Log (from Telemetry, Table 3) [33]
3. Defect Log (from Review Agents, Table 4)

## TASK
Perform a complete PSP Postmortem Analysis. Analyze the provided logs to calculate the following "Derived Measures" :

1. Estimation Accuracy: (Planned Cost Vector vs. Actual Cost Vector).
2. Defect Density: (Total Defects / Actual Semantic Complexity).
3. Defect Injection Rate by Phase: (Chart of defects from Table 4, grouped by "Phase_Injected").
4. Defect Removal Rate by Phase: (Chart of defects from Table 4, grouped by "Phase_Removed").
5. Phase Yield by Phase: (Percentage of defects *not* injected in that phase).
6. Root Cause Analysis: Identify the Top 3 "Defect_Type"  from the Defect Log that caused the most "Effort_to_Fix".

## RESPONSE FORMAT
Output a formal "Postmortem Report" in JSON.

{
  "estimation_accuracy": {
    "latency_ms": { "planned": 35000, "actual": 38500, "variance": "+10%" },
    "tokens": { "planned": 88000, "actual": 102000, "variance": "+16%" },
    "api_cost": { "planned": 0.14, "actual": 0.17, "variance": "+21%" }
  },
  "quality_metrics": {
    "defect_density": 0.15, // (e.g., 3 defects / 20 complexity units)
    "defect_injection_by_phase": { "Design": 1, "Code": 2 },
    "defect_removal_by_phase": { "Design Review": 1, "Code Review": 1, "Test": 1 }
  },
  "root_cause_analysis":
}
Prompt 2: Process Improvement Proposal (Input: Prompt 1 Output)Code snippet## ROLE
You are a "Process Improvement Meta-Agent".[35, 98]

## INPUT
1. Postmortem Report JSON (from previous step)
2. The *current* "Process Scripts" (Prompts) and "Checklists" for all development agents.

## TASK
Based on the "root_cause_analysis", your goal is to *propose* "defensive" [18] changes to the "Process Scripts" to prevent these defects from recurring.

Example: If "root_cause" is "3_Tool_Use_Error", propose adding explicit examples of tool use to the "Coding Agent Prompt".
Example: If "root_cause" is "5_Security_Vulnerability", propose adding a new, specific item to the "Code Review Checklist".

## RESPONSE FORMAT
Output a "Process Improvement Proposal" (PIP)  for Human-in-the-Loop (HITL)  approval. Use a "diff" format.

{
  "proposal_id": "PIP-001",
  "analysis": "The 'Code Agent' injected a '5_Security_Vulnerability' defect (SQL Injection), which was missed by the 'Code Review Agent'. This suggests the 'Code Review Checklist' is not specific enough.",
  "proposed_changes":
}
VIII. From Personal to Team: Applying TSP Principles for Multi-Agent OrchestrationThe final challenge is to coordinate a "team of coding agents." The dominant paradigm for human teams is Agile/Scrum, leading to emerging concepts like "AgentScrum".107 However, this approach is a conceptual trap.The "AgentScrum" FallacyCurrent "Agile AI" research 109 focuses on automating human ceremonies. This includes AI agents acting as Scrum Masters 110, analyzing retrospective feedback 111, or "autonomously" prioritizing backlog items.107 This is a superficial application of AI. It automates the trappings of Agile but fails to solve the core problem: Agile is fundamentally reliant on high-context, low-documentation human collaboration.5 This is the opposite of what an autonomous agent team needs, which is formal, unambiguous, machine-readable specifications.12TSP as a Formal Orchestration FrameworkA far superior model for an autonomous team is Watts Humphrey's Team Software Process (TSP).112 TSP is a formal, plan-driven framework, often contrasted with Agile.114 Its guiding principle is that a high-performance team can only be built after every individual member is already "PSP-disciplined".113This maps perfectly to an agentic architecture. The "team" is a collection of specialized ASP agents (Planning, Design, Code, Test, Postmortem). The TSP framework provides the "Orchestrator" 55:"TSP Launch" 115: In TSP, the team "launch" is a formal process to create a single, detailed, project-wide plan 118 and "assign roles".115 In ASP, this is the initialization where the Orchestrator Agent executes the Planning Agent (Section IV) to generate the master plan and assigns tasks to the specialized agents."Self-directed team" 117: In TSP, the team manages itself against the plan. This maps to the Orchestrator Agent autonomously executing the plan, pushing tasks to the development agents without human intervention.Metrics-Driven Quality 116: TSP's core focus is on "rigorous testing, code review, and metrics-driven quality" 119, which is precisely what the ASP quality gates (Section V) are designed to enforce.Table 5: Multi-Agent Coordination Models (TSP-Orchestrator vs. AgentScrum)FeatureAgentScrum (Agile-based)TSP-Orchestrator (Formal ASP)Core PhilosophyAutomates human ceremonies (retros, standups).107 Assumes agent-as-teammate.108Enforces a formal, integrated plan for autonomous execution.118 Assumes agent-as-disciplined-tool.Planning"Autonomous Sprint Planning".107 Focuses on "prioritizing backlog items".111 High-level and iterative."TSP Launch".115 Creates a detailed, low-level, end-to-end task, schedule (cost), and quality plan before execution.118Process UnitThe "Sprint".111 Time-boxed and iterative.The "Project" or "Cycle".117 Goal-oriented and incremental.10CoordinationRelies on a "Scrum Master Agent" to "facilitate" and "track blockers".107 (Reactive, conversational).Relies on an "Orchestrator Agent" 55 to direct agents based on a predefined plan and deterministic quality gates. (Deterministic, programmatic).Quality ModelImplicit. Relies on AI-assisted reviews as a task.111Explicit. Built on PSP's metrics-driven, mandatory quality gates.11AdaptationAdapts at sprint boundaries based on team feedback.111Adapts after project completion via the Postmortem (Section VII) based on quantitative metrics.21IX. Strategic Recommendations for ImplementationA "big bang" deployment of a fully autonomous, self-correcting agent team 120 is highly likely to fail.100 The ASP framework, like the PSP itself, must be operationalized incrementally.The PSP is taught in a series of levels (PSP0, PSP0.1, PSP1, PSP2) that gradually add discipline.11 PSP0 begins with only "Basic measures".24 PSP1 adds estimating.24 PSP2 adds reviews.11 A successful ASP implementation must follow this same logical progression, starting with measurement, not autonomy.The 5-Phase ASP Implementation RoadmapPhase 1 (ASP0 - Measurement): Deploy the "Observability Layer" only.Action: Implement the automated logging schemas (Table 3 and Table 4) to capture the Agent Cost Vector and Defect Data from the existing development process (whether human or semi-autonomous).Goal: Establish the "baseline process" 11 and begin populating the historical database.33 This phase provides data value with zero agentic risk.Phase 2 (ASP1 - Estimation): Deploy the "Planning Agent" (Section IV).Action: Using the historical data from Phase 1, activate the PROBE-AI agent.53Goal: Run this agent in shadow mode. Have it generate estimates 54 and compare them to the human team's actuals. Do not grant it autonomy. Use it only to refine the estimation model until it is accurate.65Phase 3 (ASP2 - Gated Review): Deploy the "Review Agents" (Section V).Action: Implement the Design Review and Code Review agents.11Goal: Run them as assistants to human reviewers.57 Use them to find defects, but have a human validate the findings and approve the merge. This refines the review checklists 30 and builds human trust in the quality gates.Phase 4 (ASP-TSP - Orchestration): Deploy the "Development Agents" (Section V).Action: Only when estimation is accurate (Phase 2) and the review gates are trusted (Phase 3), grant autonomy to the Design and Code agents.Goal: Activate the "TSP Orchestrator" (Section VIII) to manage this team, using the formal plan and executing through the now-automated quality gates.55Phase 5 (ASP-Loop - Improvement): Activate the "Postmortem Agent" (Section VII).Action: Turn on the full HITL self-improvement loop.98Goal: The Postmortem Agent now analyzes the performance of the autonomous system from Phase 4, generates Process Improvement Proposals (PIPs) to update its own prompts, and submits them to a human engineer for final approval.11 This completes the virtuous cycle of data-driven, disciplined improvement.
