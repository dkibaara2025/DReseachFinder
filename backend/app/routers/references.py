from fastapi import APIRouter

from app.schemas.paper import ReferenceRequest, ReferenceResponse
from app.services.reference_service import format_citation, resolve_identifier

router = APIRouter(prefix="/references", tags=["References"])


@router.post("", response_model=list[ReferenceResponse])
async def format_references(body: ReferenceRequest):
    results = []
    for identifier in body.identifiers:
        metadata = await resolve_identifier(identifier)
        if metadata:
            formatted = format_citation(metadata, body.format)
            results.append(
                ReferenceResponse(
                    identifier=identifier,
                    formatted_citation=formatted,
                    metadata=metadata,
                )
            )
        else:
            results.append(
                ReferenceResponse(
                    identifier=identifier,
                    formatted_citation=f"[Could not resolve: {identifier}]",
                    metadata=None,
                )
            )
    return results
