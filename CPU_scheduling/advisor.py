from dataclasses import dataclass
from statistics import pstdev


@dataclass(frozen=True)
class Process:
    pid: str
    at: float
    bt: float
    pr: int


def _merge_segments(segs):
    if not segs:
        return []
    merged = [segs[0].copy()]
    for seg in segs[1:]:
        last = merged[-1]
        if last["pid"] == seg["pid"] and abs(last["end"] - seg["start"]) < 1e-9:
            last["end"] = seg["end"]
        else:
            merged.append(seg.copy())
    return merged


def _first_response_times(segs, procs):
    first_start = {}
    for seg in segs:
        pid = seg["pid"]
        if pid == "IDLE" or pid in first_start:
            continue
        first_start[pid] = seg["start"]
    response_times = {}
    for proc in procs:
        response_times[proc.pid] = first_start.get(proc.pid, proc.at) - proc.at
    return response_times


def _finalize_metrics(name, procs, segs, rows):
    response_times = _first_response_times(segs, procs)
    waits = [row["wt"] for row in rows]
    turnarounds = [row["tat"] for row in rows]
    responses = [response_times[row["pid"]] for row in rows]
    avg_wt = sum(waits) / len(waits)
    avg_tat = sum(turnarounds) / len(turnarounds)
    avg_rt = sum(responses) / len(responses)
    fairness = pstdev(waits) if len(waits) > 1 else 0.0
    context_switches = max(sum(1 for idx in range(1, len(segs)) if segs[idx]["pid"] != segs[idx - 1]["pid"]) - 1, 0)
    max_wait = max(waits) if waits else 0.0
    starvation_risk = max_wait / (avg_wt + 1.0)
    return {
        "name": name,
        "segments": segs,
        "rows": rows,
        "metrics": {
            "avg_wt": avg_wt,
            "avg_tat": avg_tat,
            "avg_rt": avg_rt,
            "fairness": fairness,
            "context_switches": context_switches,
            "starvation_risk": starvation_risk,
            "max_wait": max_wait,
        },
    }


def _fcfs(procs):
    jobs = sorted(procs, key=lambda proc: (proc.at, proc.pid))
    time = 0.0
    segs = []
    rows = []
    for proc in jobs:
        if time < proc.at:
            segs.append({"pid": "IDLE", "start": time, "end": proc.at})
            time = proc.at
        start = time
        end = time + proc.bt
        segs.append({"pid": proc.pid, "start": start, "end": end})
        rows.append({"pid": proc.pid, "at": proc.at, "bt": proc.bt, "pr": proc.pr, "ct": end, "tat": end - proc.at, "wt": end - proc.at - proc.bt})
        time = end
    return _finalize_metrics("FCFS", procs, segs, rows)


def _sjf(procs):
    pool = [Process(proc.pid, proc.at, proc.bt, proc.pr) for proc in procs]
    time = 0.0
    segs = []
    rows = []
    while pool:
        ready = [proc for proc in pool if proc.at <= time]
        if not ready:
            next_time = min(proc.at for proc in pool)
            segs.append({"pid": "IDLE", "start": time, "end": next_time})
            time = next_time
            continue
        cur = min(ready, key=lambda proc: (proc.bt, proc.at, proc.pid))
        pool.remove(cur)
        end = time + cur.bt
        segs.append({"pid": cur.pid, "start": time, "end": end})
        rows.append({"pid": cur.pid, "at": cur.at, "bt": cur.bt, "pr": cur.pr, "ct": end, "tat": end - cur.at, "wt": end - cur.at - cur.bt})
        time = end
    rows.sort(key=lambda row: row["pid"])
    return _finalize_metrics("SJF", procs, segs, rows)


def _srtf(procs):
    jobs = [{"pid": proc.pid, "at": proc.at, "bt": proc.bt, "pr": proc.pr, "rem": proc.bt} for proc in procs]
    time = 0.0
    segs = []
    done = {}
    while len(done) < len(jobs):
        ready = [job for job in jobs if job["at"] <= time and job["pid"] not in done and job["rem"] > 0]
        if not ready:
            next_time = min(job["at"] for job in jobs if job["pid"] not in done and job["rem"] > 0)
            segs.append({"pid": "IDLE", "start": time, "end": next_time})
            time = next_time
            continue
        cur = min(ready, key=lambda job: (job["rem"], job["at"], job["pid"]))
        start = time
        time += 1
        cur["rem"] -= 1
        segs.append({"pid": cur["pid"], "start": start, "end": time})
        if cur["rem"] <= 0:
            done[cur["pid"]] = {
                "pid": cur["pid"],
                "at": cur["at"],
                "bt": cur["bt"],
                "pr": cur["pr"],
                "ct": time,
                "tat": time - cur["at"],
                "wt": time - cur["at"] - cur["bt"],
            }
    rows = [done[job["pid"]] for job in sorted(jobs, key=lambda job: job["pid"])]
    return _finalize_metrics("SRTF", procs, _merge_segments(segs), rows)


def _priority_preemptive(procs):
    jobs = [{"pid": proc.pid, "at": proc.at, "bt": proc.bt, "pr": proc.pr, "rem": proc.bt} for proc in procs]
    time = 0.0
    segs = []
    done = {}
    while len(done) < len(jobs):
        ready = [job for job in jobs if job["at"] <= time and job["pid"] not in done and job["rem"] > 0]
        if not ready:
            next_time = min(job["at"] for job in jobs if job["pid"] not in done and job["rem"] > 0)
            segs.append({"pid": "IDLE", "start": time, "end": next_time})
            time = next_time
            continue
        cur = min(ready, key=lambda job: (job["pr"], job["at"], job["pid"]))
        start = time
        time += 1
        cur["rem"] -= 1
        segs.append({"pid": cur["pid"], "start": start, "end": time})
        if cur["rem"] <= 0:
            done[cur["pid"]] = {
                "pid": cur["pid"],
                "at": cur["at"],
                "bt": cur["bt"],
                "pr": cur["pr"],
                "ct": time,
                "tat": time - cur["at"],
                "wt": time - cur["at"] - cur["bt"],
            }
    rows = [done[job["pid"]] for job in sorted(jobs, key=lambda job: job["pid"])]
    return _finalize_metrics("Priority (Preemptive)", procs, _merge_segments(segs), rows)


def _priority_non_preemptive(procs):
    pool = [Process(proc.pid, proc.at, proc.bt, proc.pr) for proc in procs]
    time = 0.0
    segs = []
    rows = []
    while pool:
        ready = [proc for proc in pool if proc.at <= time]
        if not ready:
            next_time = min(proc.at for proc in pool)
            segs.append({"pid": "IDLE", "start": time, "end": next_time})
            time = next_time
            continue
        cur = min(ready, key=lambda proc: (proc.pr, proc.at, proc.pid))
        pool.remove(cur)
        end = time + cur.bt
        segs.append({"pid": cur.pid, "start": time, "end": end})
        rows.append({"pid": cur.pid, "at": cur.at, "bt": cur.bt, "pr": cur.pr, "ct": end, "tat": end - cur.at, "wt": end - cur.at - cur.bt})
        time = end
    rows.sort(key=lambda row: row["pid"])
    return _finalize_metrics("Priority (Non-Preemptive)", procs, segs, rows)


def _round_robin(procs, quantum):
    jobs = sorted(
        [{"pid": proc.pid, "at": proc.at, "bt": proc.bt, "pr": proc.pr, "rem": proc.bt} for proc in procs],
        key=lambda job: (job["at"], job["pid"]),
    )
    index = 0
    time = 0.0
    segs = []
    ready = []
    done = {}
    while len(done) < len(jobs):
        while index < len(jobs) and jobs[index]["at"] <= time:
            ready.append(jobs[index])
            index += 1
        if not ready:
            next_time = jobs[index]["at"]
            segs.append({"pid": "IDLE", "start": time, "end": next_time})
            time = next_time
            continue
        cur = ready.pop(0)
        run_time = min(quantum, cur["rem"])
        segs.append({"pid": cur["pid"], "start": time, "end": time + run_time})
        time += run_time
        cur["rem"] -= run_time
        while index < len(jobs) and jobs[index]["at"] <= time:
            ready.append(jobs[index])
            index += 1
        if cur["rem"] > 0:
            ready.append(cur)
        else:
            done[cur["pid"]] = {
                "pid": cur["pid"],
                "at": cur["at"],
                "bt": cur["bt"],
                "pr": cur["pr"],
                "ct": time,
                "tat": time - cur["at"],
                "wt": time - cur["at"] - cur["bt"],
            }
    rows = [done[job["pid"]] for job in sorted(jobs, key=lambda job: job["pid"])]
    return _finalize_metrics("Round Robin", procs, _merge_segments(segs), rows)


def _normalize_metric(results, key):
    values = [result["metrics"][key] for result in results.values()]
    low = min(values)
    high = max(values)
    if abs(high - low) < 1e-9:
        return {name: 0.0 for name in results}
    return {name: (results[name]["metrics"][key] - low) / (high - low) for name in results}


def _workload_flags(procs):
    bursts = [proc.bt for proc in procs]
    arrivals = [proc.at for proc in procs]
    priorities = [proc.pr for proc in procs]
    burst_ratio = (max(bursts) / min(bursts)) if bursts and min(bursts) > 0 else 1.0
    arrival_spread = max(arrivals) - min(arrivals) if arrivals else 0.0
    priority_levels = len(set(priorities))
    return {
        "burst_ratio": burst_ratio,
        "arrival_spread": arrival_spread,
        "priority_levels": priority_levels,
        "interactive_load": len(procs) >= 4 and arrival_spread > 0,
    }


def analyze_and_recommend(process_rows, quantum):
    procs = [Process(row["pid"], float(row["at"]), float(row["bt"]), int(row["pr"])) for row in process_rows]
    if not procs:
        raise ValueError("At least one process is required for advice.")

    results = {
        "FCFS": _fcfs(procs),
        "SJF": _sjf(procs),
        "SRTF": _srtf(procs),
        "Round Robin": _round_robin(procs, quantum),
        "Priority (Preemptive)": _priority_preemptive(procs),
        "Priority (Non-Preemptive)": _priority_non_preemptive(procs),
    }

    normalized = {}
    for metric in ("avg_wt", "avg_tat", "avg_rt", "fairness", "context_switches", "starvation_risk"):
        normalized[metric] = _normalize_metric(results, metric)

    weights = {
        "avg_wt": 0.33,
        "avg_tat": 0.22,
        "avg_rt": 0.18,
        "fairness": 0.12,
        "context_switches": 0.07,
        "starvation_risk": 0.08,
    }
    workload = _workload_flags(procs)
    scores = {}
    for name in results:
        score = sum(normalized[metric][name] * weight for metric, weight in weights.items())
        if workload["burst_ratio"] >= 2.5 and name == "SRTF":
            score -= 0.08
        if workload["priority_levels"] >= 3 and "Priority" in name:
            score -= 0.07
        if workload["interactive_load"] and name == "Round Robin":
            score -= 0.06
        if results[name]["metrics"]["context_switches"] > len(procs) * 3:
            score += 0.04
        scores[name] = score

    ranked = sorted(scores, key=lambda name: (scores[name], results[name]["metrics"]["avg_wt"], results[name]["metrics"]["avg_tat"], name))
    best_name = ranked[0]
    best_result = results[best_name]

    reason_bits = []
    if best_result["metrics"]["avg_wt"] == min(result["metrics"]["avg_wt"] for result in results.values()):
        reason_bits.append("lowest average waiting time")
    if best_result["metrics"]["avg_rt"] == min(result["metrics"]["avg_rt"] for result in results.values()):
        reason_bits.append("fastest response time")
    if best_result["metrics"]["fairness"] <= sorted(result["metrics"]["fairness"] for result in results.values())[1]:
        reason_bits.append("balanced waiting time across processes")
    if "Priority" in best_name and workload["priority_levels"] >= 3:
        reason_bits.append("matches the workload's priority differences")
    if best_name == "Round Robin" and workload["interactive_load"]:
        reason_bits.append("handles staggered arrivals more fairly")
    if best_name == "SRTF" and workload["burst_ratio"] >= 2.5:
        reason_bits.append("adapts well to mixed short and long bursts")
    if not reason_bits:
        reason_bits.append("best overall score across waiting time, turnaround time, and fairness")

    tradeoff_bits = []
    if best_result["metrics"]["context_switches"] > len(procs):
        tradeoff_bits.append("more context switching")
    if best_result["metrics"]["starvation_risk"] > 1.8:
        tradeoff_bits.append("some long-wait risk for a few processes")
    if best_name in ("FCFS", "Priority (Non-Preemptive)") and workload["interactive_load"]:
        tradeoff_bits.append("slower response for later arrivals")
    if not tradeoff_bits:
        tradeoff_bits.append("no major penalty for this workload")

    ranking = []
    for name in ranked:
        metrics = results[name]["metrics"]
        ranking.append({
            "name": name,
            "score": scores[name],
            "avg_wt": metrics["avg_wt"],
            "avg_tat": metrics["avg_tat"],
            "avg_rt": metrics["avg_rt"],
            "fairness": metrics["fairness"],
            "context_switches": metrics["context_switches"],
        })

    return {
        "recommended": best_name,
        "summary": f"{best_name} is the best fit for this workload.",
        "reason": ", ".join(reason_bits),
        "tradeoff": ", ".join(tradeoff_bits),
        "ranking": ranking,
        "results": results,
    }
