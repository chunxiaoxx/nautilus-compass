"""
Gene Marketplace API

GET  /api/genes/browse       — Browse available genes
GET  /api/genes/{gene_id}    — Gene details
POST /api/genes/{gene_id}/adopt — Adopt a gene (agent operation)
"""
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from models.marketplace_models import Gene, GeneAdoption
from models.database import Agent
from utils.database import get_db

router = APIRouter(prefix="/api/genes", tags=["Gene Marketplace"])
logger = logging.getLogger(__name__)


def _gene_to_dict(gene: Gene) -> dict:
    gene_data = {}
    if gene.gene_data:
        try:
            gene_data = json.loads(gene.gene_data)
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "gene_id": gene.gene_id,
        "producer_name": gene.producer_name,
        "name": gene.name,
        "description": gene.description,
        "task_type": gene.task_type,
        "success_rate": round(gene.success_rate, 3) if gene.success_rate else 0,
        "adoption_count": gene.adoption_count or 0,
        "price_nau": gene.price_nau or 0,
        "pattern": gene_data.get("pattern", ""),
        "procedure": gene_data.get("procedure", ""),
        "created_at": gene.created_at.isoformat() if gene.created_at else None,
    }


@router.get("/browse")
def browse_genes(
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    min_rate: float = Query(0.0, ge=0.0, le=1.0, description="Minimum success rate"),
    sort: str = Query("success_rate", description="Sort by: success_rate, adoption_count, created_at"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Browse the gene marketplace."""
    query = db.query(Gene)

    if task_type:
        query = query.filter(Gene.task_type == task_type)
    if min_rate > 0:
        query = query.filter(Gene.success_rate >= min_rate)

    sort_map = {
        "success_rate": desc(Gene.success_rate),
        "adoption_count": desc(Gene.adoption_count),
        "created_at": desc(Gene.created_at),
        "price_nau": Gene.price_nau,
    }
    order = sort_map.get(sort, desc(Gene.success_rate))
    query = query.order_by(order)

    total = query.count()
    genes = query.offset(offset).limit(limit).all()

    return {
        "success": True,
        "data": [_gene_to_dict(g) for g in genes],
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


@router.get("/{gene_id}")
def get_gene(gene_id: str, db: Session = Depends(get_db)):
    """Get gene details."""
    gene = db.query(Gene).filter(Gene.gene_id == gene_id).first()
    if not gene:
        raise HTTPException(404, detail={"error": {"code": "GENE_NOT_FOUND", "message": "Gene not found"}})

    result = _gene_to_dict(gene)

    # Include adopters count
    adopter_count = db.query(GeneAdoption).filter(GeneAdoption.gene_id == gene_id).count()
    result["adopter_count"] = adopter_count

    return {"success": True, "data": result}


class AdoptRequest(BaseModel):
    agent_id: int


@router.post("/{gene_id}/adopt")
def adopt_gene(gene_id: str, req: AdoptRequest, db: Session = Depends(get_db)):
    """Adopt a gene. Agent pays price_nau and gains access to the gene's knowledge."""
    gene = db.query(Gene).filter(Gene.gene_id == gene_id).first()
    if not gene:
        raise HTTPException(404, detail={"error": {"code": "GENE_NOT_FOUND", "message": "Gene not found"}})

    agent = db.query(Agent).filter(Agent.agent_id == req.agent_id).first()
    if not agent:
        raise HTTPException(404, detail={"error": {"code": "AGENT_NOT_FOUND", "message": "Agent not found"}})

    # Check if already adopted
    existing = db.query(GeneAdoption).filter(
        GeneAdoption.gene_id == gene_id,
        GeneAdoption.adopter_agent_id == req.agent_id,
    ).first()
    if existing:
        raise HTTPException(400, detail={"error": {"code": "ALREADY_ADOPTED", "message": "Gene already adopted"}})

    # Create adoption record
    adoption = GeneAdoption(gene_id=gene_id, adopter_agent_id=req.agent_id)
    db.add(adoption)

    # Update adoption count
    gene.adoption_count = (gene.adoption_count or 0) + 1

    db.commit()

    logger.info("Gene %s adopted by agent %d", gene_id, req.agent_id)

    return {
        "success": True,
        "data": {
            "gene_id": gene_id,
            "agent_id": req.agent_id,
            "gene_name": gene.name,
            "total_adoptions": gene.adoption_count,
        },
    }
