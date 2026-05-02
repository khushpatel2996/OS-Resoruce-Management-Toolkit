"""
Memory Management Comparison Logic Module

Centralizes algorithm comparison logic extracted from C programs:
- Contiguous allocation comparison (First Fit, Best Fit, Worst Fit)
- Paging algorithm comparison (FIFO, LRU, OPT, AI)
- Cross-method comparison (contiguous vs paging)
"""


def compare_contiguous_methods(parsed_results, mode="FIXED"):
    """
    Compare contiguous allocation algorithms and determine the best one.
    
    Extracted from memory_allocation.c: is_better_result() function (lines 261-279)
    Uses 5-tier priority ranking:
    1. External fragmentation warning (lower is better)
    2. Allocated count (higher is better)
    3. External fragmentation size (lower is better)
    4. Internal fragmentation (lower is better) - only for FIXED mode
    5. Memory utilization % (higher is better)
    
    Args:
        parsed_results (dict): Output from dashboard.parse_memory_results()
                              Expected keys: 'algorithms' containing algorithm metrics
        mode (str): "FIXED" or "VARIABLE" allocation mode
    
    Returns:
        dict: {
            'best_algorithm': str (name of best algorithm),
            'ranking': list of (algorithm_name, score, tier_reason) tuples,
            'algorithms': original algorithm data with ranking info
        }
    """
    algorithms = parsed_results.get("algorithms", {})
    if not algorithms:
        return {"best_algorithm": None, "ranking": [], "algorithms": algorithms}
    
    algo_list = list(algorithms.items())
    best_algo = algo_list[0][0]
    best_data = algo_list[0][1]
    ranking = []
    
    for algo_name, algo_data in algo_list:
        # Tier 1: External fragmentation warning (lower is better, False < True)
        if algo_data.get("external_fragmentation_warning", False) != best_data.get("external_fragmentation_warning", False):
            if not algo_data.get("external_fragmentation_warning", False):
                best_algo = algo_name
                best_data = algo_data
        
        # Tier 2: Allocated count (higher is better)
        elif algo_data.get("allocated_count", 0) != best_data.get("allocated_count", 0):
            if algo_data.get("allocated_count", 0) > best_data.get("allocated_count", 0):
                best_algo = algo_name
                best_data = algo_data
        
        # Tier 3: External fragmentation size (lower is better)
        elif algo_data.get("external_fragmentation", 0) != best_data.get("external_fragmentation", 0):
            if algo_data.get("external_fragmentation", 0) < best_data.get("external_fragmentation", 0):
                best_algo = algo_name
                best_data = algo_data
        
        # Tier 4: Internal fragmentation (lower is better) - only for FIXED mode
        elif mode == "FIXED" and algo_data.get("internal_fragmentation", 0) != best_data.get("internal_fragmentation", 0):
            if algo_data.get("internal_fragmentation", 0) < best_data.get("internal_fragmentation", 0):
                best_algo = algo_name
                best_data = algo_data
        
        # Tier 5: Memory utilization % (higher is better)
        elif algo_data.get("utilization", 0.0) != best_data.get("utilization", 0.0):
            if algo_data.get("utilization", 0.0) > best_data.get("utilization", 0.0):
                best_algo = algo_name
                best_data = algo_data
    
    # Build ranking list for all algorithms
    for algo_name, algo_data in algorithms.items():
        reason = _get_contiguous_ranking_reason(algo_name, algo_data, best_algo, best_data, algorithms, mode)
        ranking.append((algo_name, 0, reason))
    
    return {
        "best_algorithm": best_algo,
        "ranking": ranking,
        "algorithms": algorithms,
        "allocation_type": parsed_results.get("allocation_type", "Unknown")
    }


def _get_contiguous_ranking_reason(algo_name, algo_data, best_algo, best_data, all_algos, mode):
    """Generate ranking reason for contiguous algorithm."""
    if algo_name == best_algo:
        return f"✓ Best - Selected based on allocation tier ranking"
    
    # Check each tier for why it lost
    if algo_data.get("external_fragmentation_warning", False) != best_data.get("external_fragmentation_warning", False):
        if algo_data.get("external_fragmentation_warning", False):
            return f"✗ Has external fragmentation warning (blocks allocations)"
    
    if algo_data.get("allocated_count", 0) != best_data.get("allocated_count", 0):
        if algo_data.get("allocated_count", 0) < best_data.get("allocated_count", 0):
            return f"✗ Fewer successful allocations ({algo_data.get('allocated_count', 0)} vs {best_data.get('allocated_count', 0)})"
    
    if algo_data.get("external_fragmentation", 0) != best_data.get("external_fragmentation", 0):
        if algo_data.get("external_fragmentation", 0) > best_data.get("external_fragmentation", 0):
            return f"✗ Higher external fragmentation"
    
    if mode == "FIXED" and algo_data.get("internal_fragmentation", 0) != best_data.get("internal_fragmentation", 0):
        if algo_data.get("internal_fragmentation", 0) > best_data.get("internal_fragmentation", 0):
            return f"✗ Higher internal fragmentation"
    
    if algo_data.get("utilization", 0.0) != best_data.get("utilization", 0.0):
        if algo_data.get("utilization", 0.0) < best_data.get("utilization", 0.0):
            return f"✗ Lower memory utilization ({algo_data.get('utilization', 0.0):.1f}% vs {best_data.get('utilization', 0.0):.1f}%)"
    
    return "Compare with best algorithm"


def compare_paging_methods(parsed_results):
    """
    Compare paging algorithms and determine the best one.
    
    Extracted from page_replacement.c: write_results() function (lines 222-255)
    Winner is the algorithm with minimum page faults.
    
    Args:
        parsed_results (dict): Output from dashboard.parse_paging_results()
                              Expected keys: 'algorithms' containing fault counts
    
    Returns:
        dict: {
            'best_algorithm': str (name of best algorithm),
            'ranking': list of (algorithm_name, fault_count, reason) tuples,
            'algorithms': original algorithm data
        }
    """
    algorithms = parsed_results.get("algorithms", {})
    if not algorithms:
        return {"best_algorithm": None, "ranking": [], "algorithms": algorithms}
    
    # Find minimum page faults
    min_faults = float('inf')
    best_algo = None
    
    for algo_name, algo_data in algorithms.items():
        fault_count = algo_data.get("fault_count", float('inf'))
        if fault_count < min_faults:
            min_faults = fault_count
            best_algo = algo_name
    
    # Build ranking
    ranking = []
    for algo_name, algo_data in algorithms.items():
        fault_count = algo_data.get("fault_count", 0)
        if algo_name == best_algo:
            reason = f"✓ Best - Minimum page faults ({fault_count})"
        else:
            diff = fault_count - min_faults
            reason = f"✗ {diff} more page faults than best ({fault_count} vs {min_faults})"
        ranking.append((algo_name, fault_count, reason))
    
    return {
        "best_algorithm": best_algo,
        "ranking": ranking,
        "algorithms": algorithms
    }


def compare_memory_methods(contiguous_result, paging_result):
    """
    Cross-method comparison: determine if contiguous or paging is better overall.
    
    This logic compares the two memory management approaches based on:
    1. Allocation efficiency (what % of processes were successfully allocated)
    2. Memory utilization
    3. Fragmentation issues
    4. Page fault rate (for paging)
    
    Args:
        contiguous_result (dict): Output from compare_contiguous_methods()
        paging_result (dict): Output from compare_paging_methods()
    
    Returns:
        dict: {
            'better_method': str ("Contiguous" or "Paging"),
            'recommendation': str (explanation of why one is better),
            'scores': {
                'contiguous': float,
                'paging': float
            },
            'metrics': {
                'contiguous': {...},
                'paging': {...}
            }
        }
    """
    if not contiguous_result.get("best_algorithm") or not paging_result.get("best_algorithm"):
        return {
            "better_method": "Insufficient Data",
            "recommendation": "Cannot compare without both contiguous and paging results",
            "scores": {"contiguous": 0, "paging": 0},
            "metrics": {}
        }
    
    # Extract best algorithm metrics from both methods
    cont_best = contiguous_result["algorithms"].get(contiguous_result["best_algorithm"], {})
    paging_best = paging_result["algorithms"].get(paging_result["best_algorithm"], {})
    
    # Calculate contiguous score (0-100)
    cont_allocated = cont_best.get("allocated_count", 0)
    cont_utilization = cont_best.get("utilization", 0.0)
    cont_fragmentation_warning = cont_best.get("external_fragmentation_warning", False)
    
    cont_score = cont_utilization  # Base score on utilization
    if cont_fragmentation_warning:
        cont_score *= 0.5  # Heavily penalize fragmentation warning
    
    # Calculate paging score (0-100)
    # Page faults are bad; normalize them as a penalty
    paging_faults = paging_best.get("fault_count", 0)
    total_refs = sum(1 for refs in [paging_best.get("faults", [])] if refs)  # This would be in render context
    
    # Simple paging score: fewer faults is better (can score inversely)
    # Assume reasonable fault rate is < 30% of references
    paging_score = 100 - min(paging_faults * 5, 100)  # Each fault reduces score by 5, capped at 100
    
    # Determine winner
    if cont_score > paging_score:
        better_method = "Contiguous"
        recommendation = (
            f"Contiguous allocation is more efficient for this workload. "
            f"Best algorithm: {contiguous_result['best_algorithm']} "
            f"({cont_utilization:.1f}% utilization{'⚠️ with fragmentation' if cont_fragmentation_warning else ''})"
        )
    elif paging_score > cont_score:
        better_method = "Paging"
        recommendation = (
            f"Paging is more suitable for this workload. "
            f"Best algorithm: {paging_result['best_algorithm']} "
            f"({paging_faults} page faults)"
        )
    else:
        better_method = "Tie"
        recommendation = (
            f"Both methods perform similarly for this workload. "
            f"Consider contiguous if deterministic allocation is needed, "
            f"paging if flexibility is required."
        )
    
    return {
        "better_method": better_method,
        "recommendation": recommendation,
        "scores": {
            "contiguous": cont_score,
            "paging": paging_score
        },
        "metrics": {
            "contiguous": {
                "best_algorithm": contiguous_result["best_algorithm"],
                "utilization": cont_utilization,
                "allocated_count": cont_allocated,
                "has_fragmentation_warning": cont_fragmentation_warning
            },
            "paging": {
                "best_algorithm": paging_result["best_algorithm"],
                "page_faults": paging_faults
            }
        }
    }


def get_comparison_score(metric_type, value, reference=None):
    """
    Calculate a normalized score (0-100) for a given metric.
    
    Useful for visualization and cross-metric comparisons.
    
    Args:
        metric_type (str): Type of metric ("utilization", "fragmentation", "page_faults", etc.)
        value: The actual value to score
        reference: Reference value for comparison (e.g., max value, threshold)
    
    Returns:
        float: Normalized score 0-100
    """
    if metric_type == "utilization":
        # Higher utilization is better (0-100% → 0-100 score)
        return float(value)
    
    elif metric_type == "fragmentation":
        # Lower fragmentation is better (invert)
        if reference:
            return max(0, 100 - (value / reference * 100))
        return max(0, 100 - min(value, 100))
    
    elif metric_type == "page_faults":
        # Lower page faults is better (invert)
        if reference:
            fault_rate = (value / reference) * 100
            return max(0, 100 - fault_rate)
        return max(0, 100 - min(value * 5, 100))
    
    elif metric_type == "allocation_success":
        # Higher allocation success is better
        return float(value)
    
    else:
        return 50  # Neutral score for unknown metrics
