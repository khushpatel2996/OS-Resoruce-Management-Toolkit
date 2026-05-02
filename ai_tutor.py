"""
Context-aware AI Study Tutor for the OS Resource Management Toolkit.

The tutor is intentionally local and deterministic so the project works in
college labs without an API key or internet access. It behaves like an
educational assistant by combining topic matching, current simulator state,
concept explanations, debugging guidance, and viva-style questions.
"""

import json
import os
import re
from difflib import SequenceMatcher

CONCEPTS = {
    "fcfs": {
        "title": "First Come First Serve (FCFS)",
        "explain": "FCFS executes processes in arrival order. It is easy to understand and fair by queue order, but a long process at the front can make every later process wait.",
        "use": "Best for simple batch workloads where arrival order matters more than response time.",
        "risk": "Convoy effect and high average waiting time when burst times vary widely.",
    },
    "sjf": {
        "title": "Shortest Job First (SJF)",
        "explain": "SJF chooses the ready process with the smallest burst time. It often minimizes average waiting time for non-preemptive scheduling.",
        "use": "Best when burst times are known and the system wants low waiting time.",
        "risk": "Long processes may wait too much if short jobs keep arriving.",
    },
    "srtf": {
        "title": "Shortest Remaining Time First (SRTF)",
        "explain": "SRTF is the preemptive version of SJF. If a new process arrives with a shorter remaining time, the CPU switches to it.",
        "use": "Best for interactive workloads where short tasks should finish quickly.",
        "risk": "More context switches and possible starvation for long processes.",
    },
    "round robin": {
        "title": "Round Robin",
        "explain": "Round Robin gives each process a fixed time quantum. After its quantum expires, the process goes to the back of the ready queue if it is not finished.",
        "use": "Best for time-sharing systems where every process should get regular CPU time.",
        "risk": "Too small a quantum increases context switching; too large a quantum behaves like FCFS.",
    },
    "priority": {
        "title": "Priority Scheduling",
        "explain": "Priority scheduling chooses the process with the highest priority. In this project, lower priority numbers represent higher priority.",
        "use": "Best when some tasks are more important than others.",
        "risk": "Low-priority processes can starve unless aging is used.",
    },
    "fifo": {
        "title": "FIFO Page Replacement",
        "explain": "FIFO removes the page that entered memory earliest. It is simple, but it does not check whether the page is still frequently used.",
        "use": "Best for demonstrating simple page replacement logic.",
        "risk": "Can produce unnecessary page faults and may show Belady's anomaly.",
    },
    "lru": {
        "title": "LRU Page Replacement",
        "explain": "LRU removes the page that has not been used for the longest time. It uses recent access history as a prediction of future use.",
        "use": "Usually better than FIFO when recent pages are likely to be reused.",
        "risk": "Needs tracking overhead in a real operating system.",
    },
    "fragmentation": {
        "title": "Fragmentation",
        "explain": "Internal fragmentation is wasted space inside an allocated block. External fragmentation is free memory split into pieces that may not fit a new process.",
        "use": "Useful for comparing First Fit, Best Fit, and Worst Fit.",
        "risk": "High fragmentation lowers useful memory even when total free space looks enough.",
    },
    "deadlock": {
        "title": "Resource Waiting and Deadlock Risk",
        "explain": "A process waits when a requested resource is already occupied. Deadlock risk appears when processes hold resources while waiting for other resources.",
        "use": "The resource manager helps visualize busy resources, waiting queues, and release flow.",
        "risk": "Long queues and unreleased resources reduce system progress.",
    },
    "starvation": {
        "title": "Starvation",
        "explain": "Starvation happens when a process waits for a very long time because other processes keep getting selected first.",
        "use": "Useful while studying SJF, SRTF, and Priority Scheduling because long or low-priority jobs can be delayed.",
        "risk": "Aging is normally used to reduce starvation by slowly increasing the priority of waiting processes.",
    },
    "aging": {
        "title": "Aging",
        "explain": "Aging gradually increases the priority of a process the longer it waits in the ready queue.",
        "use": "It improves priority scheduling by protecting low-priority processes from starvation.",
        "risk": "If aging is too aggressive, priority scheduling becomes less strict.",
    },
    "context switch": {
        "title": "Context Switching",
        "explain": "A context switch saves the current process state and loads another process state so the CPU can run a different process.",
        "use": "Important in Round Robin, SRTF, and preemptive priority scheduling.",
        "risk": "Too many context switches add overhead and reduce effective CPU time.",
    },
    "turnaround time": {
        "title": "Turnaround Time",
        "explain": "Turnaround time is the total time from process arrival to completion.",
        "use": "Formula: completion time - arrival time.",
        "risk": "A low waiting time usually helps, but long burst time can still make turnaround time high.",
    },
    "waiting time": {
        "title": "Waiting Time",
        "explain": "Waiting time is the total time a process spends in the ready queue without using the CPU.",
        "use": "Formula: turnaround time - burst time.",
        "risk": "High waiting time means the scheduling algorithm may not fit the workload.",
    },
    "response time": {
        "title": "Response Time",
        "explain": "Response time is the time between process arrival and the first time it gets CPU service.",
        "use": "Very important for interactive systems.",
        "risk": "Batch-friendly algorithms may give poor response time for interactive workloads.",
    },
    "throughput": {
        "title": "Throughput",
        "explain": "Throughput is the number of processes completed per unit time.",
        "use": "It helps compare how much work a system completes.",
        "risk": "High throughput alone does not guarantee fairness or good response time.",
    },
    "paging": {
        "title": "Paging",
        "explain": "Paging divides logical memory into pages and physical memory into frames. Pages are loaded into frames as needed.",
        "use": "It avoids external fragmentation and supports non-contiguous memory allocation.",
        "risk": "Page faults can slow execution if needed pages are not already in memory.",
    },
    "page fault": {
        "title": "Page Fault",
        "explain": "A page fault occurs when a process references a page that is not currently present in physical memory.",
        "use": "Page replacement algorithms such as FIFO and LRU decide which page should be removed.",
        "risk": "Too many page faults can cause poor performance and thrashing.",
    },
    "thrashing": {
        "title": "Thrashing",
        "explain": "Thrashing happens when the system spends more time handling page faults than executing useful work.",
        "use": "It is connected to paging, frame allocation, and working set size.",
        "risk": "Low frame count and large active working sets can increase thrashing.",
    },
    "segmentation": {
        "title": "Segmentation",
        "explain": "Segmentation divides memory according to logical program parts such as code, data, stack, and heap.",
        "use": "It matches the programmer's view of memory better than fixed-size pages.",
        "risk": "Segmentation can suffer from external fragmentation.",
    },
    "first fit": {
        "title": "First Fit",
        "explain": "First Fit places a process in the first memory block large enough to hold it.",
        "use": "It is fast because it stops searching after finding the first valid block.",
        "risk": "It may leave small unusable gaps near the beginning of memory.",
    },
    "best fit": {
        "title": "Best Fit",
        "explain": "Best Fit places a process in the smallest block that is large enough.",
        "use": "It tries to reduce wasted space per allocation.",
        "risk": "It can create many tiny leftover fragments.",
    },
    "worst fit": {
        "title": "Worst Fit",
        "explain": "Worst Fit places a process in the largest available block.",
        "use": "It tries to keep remaining free blocks large enough for future processes.",
        "risk": "It can waste large blocks quickly if the workload is not suitable.",
    },
}


QUICK_PROMPTS = [
    "Explain my current CPU scheduling result",
    "Analyze my memory management output",
    "Give debugging and testing checklist",
    "Create viva questions from this project",
    "Explain deadlock, starvation, and aging",
    "Difference between paging and segmentation",
]


def build_tutor_response(question, context, ai_source="offline"):
    query = (question or "").strip().lower()
    if not query:
        return _welcome(context)

    # Use offline AI response only
    return _offline_response(question, context)

def _offline_response(question, context):
    query = (question or "").strip().lower()
    if any(word in query for word in ("debug", "test", "error", "bug", "validation")):
        return _debugging_response(context)
    if any(word in query for word in ("viva", "quiz", "question", "practice")):
        return _quiz_response(context)
    if any(word in query for word in ("current", "result", "output", "analyze", "analysis")):
        return _context_analysis(context)
    if _is_comparison_question(query):
        return _comparison_response(query, context)

    matched = _match_concepts(query)
    if matched:
        return _concept_response(matched, context)

    return _general_response(query, context)


def _welcome(context):
    return "\n".join(
        [
            "AI Study Tutor ready.",
            "",
            "I can explain OS concepts, analyze your current simulator output, create viva questions, and help with debugging and testing.",
            "",
            _context_snapshot(context),
        ]
    )


def _match_concepts(query):
    aliases = {
        "first come": "fcfs",
        "shortest job": "sjf",
        "shortest remaining": "srtf",
        "rr": "round robin",
        "time quantum": "round robin",
        "page fault": "fifo",
        "least recently": "lru",
        "page replacement": "page fault",
        "internal": "fragmentation",
        "external": "fragmentation",
        "resource": "deadlock",
        "waiting": "deadlock",
        "convoy": "fcfs",
        "preemptive": "srtf",
        "non preemptive": "sjf",
        "non-preemptive": "sjf",
        "completion time": "turnaround time",
        "tat": "turnaround time",
        "wt": "waiting time",
        "rt": "response time",
    }
    matched = []
    for key in CONCEPTS:
        if _has_phrase(query, key) or _has_fuzzy_phrase(query, key):
            matched.append(key)
    for text, key in aliases.items():
        if (_has_phrase(query, text) or _has_fuzzy_phrase(query, text)) and key not in matched:
            matched.append(key)
    return matched


def _has_phrase(query, phrase):
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", query) is not None


def _has_fuzzy_phrase(query, phrase):
    query_words = re.findall(r"[a-z0-9]+", query)
    phrase_words = phrase.split()
    if not query_words or not phrase_words:
        return False
    if len(phrase_words) == 1:
        target = phrase_words[0]
        return any(_word_matches(word, target) for word in query_words)
    for start in range(0, len(query_words) - len(phrase_words) + 1):
        window = query_words[start:start + len(phrase_words)]
        scores = [_similar(word, target) for word, target in zip(window, phrase_words)]
        if min(scores) >= 0.78 and sum(scores) / len(scores) >= 0.84:
            return True
    return False


def _similar(left, right):
    return SequenceMatcher(None, left, right).ratio()


def _word_matches(word, target):
    if abs(len(word) - len(target)) > 3:
        return False
    if len(target) <= 5 and word[:1] != target[:1]:
        return False
    return _similar(word, target) >= 0.82


def _is_comparison_question(query):
    if " vs " in query:
        return True
    comparison_words = ("difference", "different", "compare", "comparison", "between")
    query_words = re.findall(r"[a-z0-9]+", query)
    return any(any(_word_matches(word, target) for target in comparison_words) for word in query_words)


def _concept_response(keys, context):
    parts = []
    for key in keys:
        concept = CONCEPTS[key]
        parts.extend(
            [
                concept["title"],
                concept["explain"],
                f"Use in project: {concept['use']}",
                f"Important limitation: {concept['risk']}",
                "",
            ]
        )
    parts.append("Project connection:")
    parts.append(_context_hint_for(keys, context))
    return "\n".join(parts).strip()


def _context_analysis(context):
    sections = ["Current Simulation Analysis", ""]
    sections.append(_cpu_analysis(context.get("cpu")))
    sections.append("")
    sections.append(_memory_analysis(context.get("memory")))
    sections.append("")
    sections.append(_resource_analysis(context.get("resource")))
    sections.append("")
    sections.append("Learning takeaway:")
    sections.append("Compare algorithms using measurable output: waiting time, turnaround time, page faults, fragmentation, utilization, and queue length.")
    return "\n".join(sections)


def _cpu_analysis(cpu):
    if not cpu:
        return "CPU Scheduling: No algorithm has been executed yet. Run a CPU algorithm or use Smart Scheduler Advisor first."

    rows = cpu.get("rows", [])
    avg_wt = cpu.get("avg_wt", 0)
    avg_tat = cpu.get("avg_tat", 0)
    longest = max(rows, key=lambda row: row.get("wt", 0), default=None)
    parts = [
        "CPU Scheduling:",
        f"- Average waiting time: {avg_wt:.2f}",
        f"- Average turnaround time: {avg_tat:.2f}",
    ]
    if longest:
        parts.append(f"- Highest waiting process: {longest.get('pid')} waited {longest.get('wt'):.2f} time units")
    if avg_wt > 8:
        parts.append("- Tutor note: Waiting time is high, so compare with SJF, SRTF, or Round Robin depending on the workload.")
    else:
        parts.append("- Tutor note: Waiting time is controlled for this input, so explain why this algorithm fits the workload.")
    return "\n".join(parts)


def _memory_analysis(memory):
    if not memory:
        return "Memory Management: No memory or paging result is available yet."

    if memory.get("mode") == "contiguous":
        best = memory.get("best", "Unknown")
        selected = memory.get("selected", best)
        data = memory.get("algorithms", {}).get(selected, {})
        return "\n".join(
            [
                "Memory Management:",
                f"- Mode: {memory.get('allocation_type', 'Contiguous Allocation')}",
                f"- Best algorithm: {best}",
                f"- Selected algorithm: {selected}",
                f"- Allocated processes: {data.get('allocated_count', 0)}",
                f"- Failed processes: {data.get('failed', 0)}",
                f"- Utilization: {data.get('utilization', 0):.1f}%",
                f"- Internal fragmentation: {data.get('internal_fragmentation', 0)} bytes",
                f"- External fragmentation warning: {'Yes' if data.get('external_fragmentation_warning') else 'No'}",
            ]
        )

    algorithms = memory.get("algorithms", {})
    faults = ", ".join(f"{name}: {data.get('fault_count', 0)}" for name, data in algorithms.items())
    return "\n".join(
        [
            "Paging:",
            f"- Frames: {memory.get('frames', '-')}",
            f"- Reference string length: {len(memory.get('refs', []))}",
            f"- Page faults: {faults or 'No fault data'}",
            f"- Better algorithm: {memory.get('better', 'Unknown')}",
        ]
    )


def _resource_analysis(resource):
    if not resource:
        return "Resource Manager: No resource state available."
    busy = resource.get("busy", 0)
    waiting = resource.get("waiting", 0)
    events = resource.get("events", 0)
    lines = [
        "Resource Manager:",
        f"- Busy resources: {busy}/{resource.get('total', 0)}",
        f"- Waiting clients: {waiting}",
        f"- Logged events: {events}",
    ]
    if waiting:
        lines.append("- Tutor note: Waiting queues are useful for explaining contention and release handling.")
    else:
        lines.append("- Tutor note: No current waiting queue, so the system is in a low-contention state.")
    return "\n".join(lines)


def _debugging_response(context):
    return "\n".join(
        [
            "Advanced Debugging and Testing Checklist",
            "",
            "1. CPU Scheduling",
            "- Test empty, negative, and zero burst-time inputs.",
            "- Compare FCFS, SJF, SRTF, Round Robin, and Priority with the same process table.",
            "- Verify completion time, turnaround time, waiting time, and Gantt chart order.",
            "",
            "2. Memory Management",
            "- Test fixed and variable allocation with small and large block sizes.",
            "- Confirm First Fit, Best Fit, and Worst Fit choose expected blocks.",
            "- Check internal fragmentation, external fragmentation, failed allocation, and utilization.",
            "",
            "3. Paging",
            "- Run the same reference string for FIFO and LRU.",
            "- Verify page fault count manually for a short input.",
            "- Test invalid pages and frame counts.",
            "",
            "4. Resource Manager",
            "- Request an already busy resource and confirm waiting queue behavior.",
            "- Release a resource and check whether waiting clients are handled correctly.",
            "- Confirm event log entries are written with client, PID, resource, and action.",
            "",
            "Current context:",
            _context_snapshot(context),
        ]
    )


def _quiz_response(context):
    return "\n".join(
        [
            "Viva / Practice Questions",
            "",
            "1. Why can FCFS cause the convoy effect?",
            "2. How does SRTF differ from SJF?",
            "3. Why does Round Robin need a suitable time quantum?",
            "4. What is the difference between internal and external fragmentation?",
            "5. Why can LRU give fewer page faults than FIFO?",
            "6. What does a waiting queue show in resource management?",
            "7. Which metrics did your project use to compare algorithms?",
            "",
            "Strong answer pattern:",
            "Define the concept, connect it to your simulator output, then mention one limitation.",
            "",
            _context_snapshot(context),
        ]
    )


def _general_response(query, context):
    return "\n".join(
        [
            "I can answer that as an OS tutor, but I need a clearer operating-system keyword.",
            "",
            "Try asking about CPU scheduling, FCFS, SJF, SRTF, Round Robin, priority, starvation, aging, context switching, paging, segmentation, page faults, FIFO, LRU, fragmentation, first fit, best fit, worst fit, deadlock, resource allocation, debugging, testing, or viva.",
            "",
            "Meanwhile, here is the current project snapshot:",
            _context_snapshot(context),
        ]
    )


def _comparison_response(query, context):
    pairs = [
        (("paging", "segmentation"), "Paging uses fixed-size pages and frames, while segmentation uses logical variable-size segments like code, data, stack, and heap. Paging avoids external fragmentation but can cause internal fragmentation. Segmentation matches program structure but can cause external fragmentation."),
        (("fifo", "lru"), "FIFO replaces the oldest loaded page, while LRU replaces the page that has not been used for the longest time. FIFO is simpler, but LRU usually performs better because recent use often predicts near-future use."),
        (("sjf", "srtf"), "SJF is non-preemptive and runs the shortest ready job until completion. SRTF is preemptive and can interrupt the current process when a new process has a shorter remaining time."),
        (("fcfs", "round robin"), "FCFS runs processes in arrival order until completion. Round Robin gives each process a time quantum, so it improves responsiveness in time-sharing systems."),
        (("internal", "external"), "Internal fragmentation is wasted space inside an allocated block. External fragmentation is free memory split into small separated holes."),
        (("first fit", "best fit"), "First Fit chooses the first suitable block and is faster. Best Fit chooses the smallest suitable block and tries to reduce immediate waste, but can create tiny fragments."),
        (("best fit", "worst fit"), "Best Fit uses the smallest suitable block. Worst Fit uses the largest block so the leftover space may still be useful for later allocations."),
    ]
    for words, answer in pairs:
        if all(_has_phrase(query, word) or _has_fuzzy_phrase(query, word) for word in words):
            return "\n".join(["Comparison", "", answer, "", "Project connection:", _context_snapshot(context)])
    return "\n".join(
        [
            "Comparison",
            "",
            "For OS comparisons, focus on selection rule, performance metric, advantage, and limitation.",
            "Example: FIFO and LRU are both page replacement algorithms, but FIFO uses arrival order while LRU uses recent access history.",
            "",
            _context_snapshot(context),
        ]
    )


def _context_hint_for(keys, context):
    if any(key in ("fcfs", "sjf", "srtf", "round robin", "priority") for key in keys):
        return _cpu_analysis(context.get("cpu"))
    if any(key in ("fifo", "lru", "fragmentation", "paging", "page fault", "thrashing", "segmentation", "first fit", "best fit", "worst fit") for key in keys):
        return _memory_analysis(context.get("memory"))
    if "deadlock" in keys:
        return _resource_analysis(context.get("resource"))
    return _context_snapshot(context)


def _context_snapshot(context):
    cpu = "available" if context.get("cpu") else "not run yet"
    memory = "available" if context.get("memory") else "not run yet"
    resource = context.get("resource") or {}
    return (
        f"Context: CPU result {cpu}; memory result {memory}; "
        f"{resource.get('busy', 0)} busy resources; {resource.get('waiting', 0)} waiting clients."
    )
