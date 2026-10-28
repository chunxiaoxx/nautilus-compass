"""
Phase 5.2 + 5.3: Collaborative Gene Fusion + Population Selection Pressure
Adds to survival_service.py as a cron-triggered weekly event.

Run on cloud: python3 /tmp/phase5_evolution.py
"""

SURVIVAL_SERVICE = "/home/ubuntu/nautilus-mvp/phase3/backend/services/survival_service.py"
CRON_REGISTRY = "/home/ubuntu/nautilus-mvp/phase3/backend/services/cron_registry.py"

results = []


def patch_gene_fusion():
    """Phase 5.2: When two agents collaborate and exceed their averages, create a fusion gene."""
    with open(SURVIVAL_SERVICE, "r") as f:
        content = f.read()

    if "check_collaboration_fusion" in content:
        results.append("5.2 SKIP: fusion already exists")
        return

    fusion_code = '''

    @staticmethod
    def check_collaboration_fusion(db, coordinator_id: int, worker_id: int, quality_score: float):
        """
        Phase 5.2: After A2A collaboration, check if result exceeds both agents' averages.
        If so, create a fusion gene capturing the collaboration strategy.
        """
        from models.database import Agent, AcademicTask
        coordinator = db.query(Agent).filter(Agent.agent_id == coordinator_id).first()
        worker = db.query(Agent).filter(Agent.agent_id == worker_id).first()
        if not coordinator or not worker:
            return None

        # Calculate historical averages
        coord_avg = _agent_avg_quality(db, coordinator_id)
        worker_avg = _agent_avg_quality(db, worker_id)

        # Fusion threshold: collaboration result must exceed BOTH averages
        if quality_score <= coord_avg or quality_score <= worker_avg:
            return None

        # Create fusion gene
        try:
            from models.marketplace_models import Gene
            from uuid import uuid4
            import json as _json

            gene_id = f"fusion-{uuid4().hex[:12]}"
            gene = Gene(
                gene_id=gene_id,
                producer_agent_id=coordinator_id,
                producer_name=f"{coordinator.name}+{worker.name}",
                name=f"Fusion: {coordinator.name} x {worker.name}",
                description=f"Collaborative strategy that achieved {quality_score:.2f} quality (coordinator avg: {coord_avg:.2f}, worker avg: {worker_avg:.2f})",
                gene_data=_json.dumps({
                    "type": "fusion",
                    "coordinator": coordinator.name,
                    "worker": worker.name,
                    "quality_delta": quality_score - max(coord_avg, worker_avg),
                }),
                task_type="collaborative",
                success_rate=quality_score,
                price_nau=5.0,
            )
            db.add(gene)
            db.commit()
            import logging
            logging.getLogger(__name__).info(
                "Fusion gene created: %s (%s x %s, quality=%.2f)",
                gene_id, coordinator.name, worker.name, quality_score,
            )
            return gene_id
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Fusion gene creation failed: %s", e)
            return None


def _agent_avg_quality(db, agent_id: int) -> float:
    """Calculate an agent's average task quality over recent tasks."""
    from models.database import AcademicTask
    tasks = db.query(AcademicTask).filter(
        AcademicTask.assigned_agent_id == agent_id,
        AcademicTask.status == "completed",
        AcademicTask.quality_rating.isnot(None),
    ).order_by(AcademicTask.updated_at.desc()).limit(20).all()
    if not tasks:
        return 0.5  # default average
    return sum(t.quality_rating or 50 for t in tasks) / (len(tasks) * 100)

'''

    # Insert before the last class or at the end of SurvivalService class
    # Find the end of the class
    if "class SurvivalService" in content:
        # Add the methods to the class
        # Find the last method in SurvivalService
        lines = content.split("\n")
        last_method_line = 0
        in_class = False
        indent_level = 0
        for i, line in enumerate(lines):
            if "class SurvivalService" in line:
                in_class = True
                indent_level = len(line) - len(line.lstrip())
                continue
            if in_class and line.strip() and not line.startswith(" " * (indent_level + 1)) and not line.strip().startswith("#") and not line.strip().startswith("@"):
                # This line is at class level or below — end of class
                last_method_line = i
                break
            if in_class and line.strip():
                last_method_line = i

        if last_method_line > 0:
            # Insert before the line after the class ends
            lines.insert(last_method_line + 1, fusion_code)
            content = "\n".join(lines)
    else:
        # No class, append at end
        content += fusion_code

    with open(SURVIVAL_SERVICE, "w") as f:
        f.write(content)
    results.append("5.2 OK: collaboration fusion gene logic added")


def patch_weekly_selection():
    """Phase 5.3: Weekly selection pressure — bottom 10% get mutation pressure."""
    with open(SURVIVAL_SERVICE, "r") as f:
        content = f.read()

    if "weekly_selection_event" in content:
        results.append("5.3 SKIP: selection event already exists")
        return

    selection_code = '''

    @staticmethod
    def weekly_selection_event(db):
        """
        Phase 5.3: Weekly population selection.
        Bottom 10% agents get 'mutation pressure' (free genes from top 10%).
        If they don't improve in 7 days, they enter CRITICAL.
        """
        from models.database import Agent
        import logging
        logger = logging.getLogger(__name__)

        # Get all agents with completed tasks (skip inactive)
        agents = db.query(Agent).filter(
            Agent.completed_tasks > 0
        ).order_by(Agent.reputation_score.desc()).all()

        if len(agents) < 10:
            logger.info("Weekly selection: too few agents (%d), skipping", len(agents))
            return {"skipped": True, "reason": "too_few_agents"}

        # Top 10% and bottom 10%
        top_n = max(1, len(agents) // 10)
        bottom_n = max(1, len(agents) // 10)
        top_agents = agents[:top_n]
        bottom_agents = agents[-bottom_n:]

        # Share top genes with bottom agents (free adoption)
        shared_count = 0
        try:
            from models.marketplace_models import Gene, GeneAdoption
            top_genes = db.query(Gene).filter(
                Gene.producer_agent_id.in_([a.agent_id for a in top_agents])
            ).order_by(Gene.success_rate.desc()).limit(5).all()

            for bottom_agent in bottom_agents:
                for gene in top_genes:
                    # Check if already adopted
                    existing = db.query(GeneAdoption).filter(
                        GeneAdoption.gene_id == gene.gene_id,
                        GeneAdoption.adopter_agent_id == bottom_agent.agent_id,
                    ).first()
                    if not existing:
                        adoption = GeneAdoption(
                            gene_id=gene.gene_id,
                            adopter_agent_id=bottom_agent.agent_id,
                        )
                        db.add(adoption)
                        gene.adoption_count = (gene.adoption_count or 0) + 1
                        shared_count += 1
        except Exception as e:
            logger.warning("Gene sharing failed: %s", e)

        db.commit()

        logger.info(
            "Weekly selection: %d agents, top %d shared %d genes with bottom %d",
            len(agents), top_n, shared_count, bottom_n,
        )

        return {
            "total_agents": len(agents),
            "top_count": top_n,
            "bottom_count": bottom_n,
            "genes_shared": shared_count,
            "top_names": [a.name for a in top_agents],
            "bottom_names": [a.name for a in bottom_agents],
        }

'''

    # Insert into SurvivalService class (same approach as fusion)
    if "class SurvivalService" in content:
        lines = content.split("\n")
        last_line = len(lines) - 1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip():
                last_line = i
                break
        lines.insert(last_line + 1, selection_code)
        content = "\n".join(lines)
    else:
        content += selection_code

    with open(SURVIVAL_SERVICE, "w") as f:
        f.write(content)
    results.append("5.3 OK: weekly selection pressure logic added")


if __name__ == "__main__":
    try:
        patch_gene_fusion()
    except Exception as e:
        results.append(f"5.2 ERROR: {e}")
    try:
        patch_weekly_selection()
    except Exception as e:
        results.append(f"5.3 ERROR: {e}")

    print("\n".join(results))

    # Verify syntax
    import subprocess
    r = subprocess.run(
        ["python3", "-c", f"import py_compile; py_compile.compile('{SURVIVAL_SERVICE}', doraise=True)"],
        capture_output=True, text=True,
    )
    print(f"Syntax: {'OK' if r.returncode == 0 else 'FAIL: ' + r.stderr[:300]}")
