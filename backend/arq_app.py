from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.logging import logger


async def startup(ctx: dict) -> None:
    logger.info("arq.worker.startup", queue=settings.arq_queue_name)


async def shutdown(ctx: dict) -> None:
    logger.info("arq.worker.shutdown")


async def scrape_source(ctx: dict, source: str) -> dict:
    from app.scraper.engine import ScrapingEngine

    engine = ScrapingEngine()
    source_info = engine.sources.get(source)
    if not source_info:
        return {"status": "failed", "error": f"Unknown source: {source}"}

    logger.info("arq.scrape.started", source=source, url=source_info["url"])

    from app.core.database import async_session_factory
    from app.models.scraping import ScrapingJob

    async with async_session_factory() as session:
        job = ScrapingJob(
            source_name=source_info["name"],
            source_url=source_info["url"],
            job_type="scheduled",
            status="running",
        )
        session.add(job)
        await session.flush()
        job_id = job.id

        try:
            found, created, updated = await engine.scrape_source(source, job)
            job.status = "completed" if found > 0 else "partial"
            job.schemes_found = found
            job.schemes_new = created
            job.schemes_updated = updated
            job.finished_at = datetime.now(timezone.utc)

            logger.info(
                "arq.scrape.completed",
                source=source,
                found=found,
                new=created,
                updated=updated,
            )
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)[:1000]
            job.finished_at = datetime.now(timezone.utc)
            logger.error("arq.scrape.failed", source=source, error=str(exc))

        await session.commit()

    return {
        "status": job.status,
        "source": source,
        "job_id": str(job_id),
    }


async def scrape_all_sources(ctx: dict) -> list[dict]:
    from app.scraper.engine import ScrapingEngine
    engine = ScrapingEngine()
    results = []
    for source_key in engine.sources:
        result = await scrape_source(ctx, source_key)
        results.append(result)
    return results


async def embed_scheme_chunks(ctx: dict, scheme_id: str) -> dict:
    from app.ai.rag.embedder import Embedder
    from app.ai.rag.chunker import TextChunker
    from app.core.database import async_session_factory
    from app.models.scheme import Scheme
    from app.models.document import DocumentChunk
    from sqlalchemy import select

    embedder = Embedder()
    chunker = TextChunker()

    async with async_session_factory() as session:
        stmt = select(Scheme).where(Scheme.id == scheme_id)
        result = await session.execute(stmt)
        scheme = result.scalar_one_or_none()
        if not scheme:
            return {"status": "failed", "error": "Scheme not found"}

        existing_chunks_stmt = select(DocumentChunk).where(DocumentChunk.scheme_id == scheme_id)
        existing = await session.execute(existing_chunks_stmt)
        for chunk in existing.scalars().all():
            await session.delete(chunk)
        await session.flush()

        chunks = chunker.chunk_scheme(
            title=scheme.title,
            description=scheme.description,
            metadata={
                "scheme_id": str(scheme.id),
                "source_url": scheme.source_url,
                "title": scheme.title,
                "state_code": scheme.state_code,
                "level": scheme.level.value if scheme.level else None,
                "category": str(scheme.category_id),
            },
        )

        for c in chunks:
            try:
                embedding = await embedder.embed_query(c["content"])
            except Exception as exc:
                logger.warning("arq.embed.failed_for_chunk", scheme_id=scheme_id, index=c["chunk_index"], error=str(exc))
                embedding = []

            doc_chunk = DocumentChunk(
                scheme_id=scheme.id,
                chunk_index=c["chunk_index"],
                content=c["content"],
                chunk_metadata=c["chunk_metadata"],
                token_count=c["token_count"],
            )
            session.add(doc_chunk)

        await session.commit()

    return {"status": "completed", "scheme_id": scheme_id, "chunks": len(chunks)}


async def reindex_all_schemes(ctx: dict) -> dict:
    from app.ai.rag.embedder import Embedder
    from app.ai.rag.chunker import TextChunker
    from app.core.database import async_session_factory
    from app.models.scheme import Scheme
    from app.models.document import DocumentChunk
    from sqlalchemy import select

    embedder = Embedder()
    chunker = TextChunker()
    processed = 0

    async with async_session_factory() as session:
        stmt = select(Scheme).where(Scheme.status == "active").limit(500)
        result = await session.execute(stmt)
        schemes = list(result.scalars().all())

        for scheme in schemes:
            chunks = chunker.chunk_scheme(
                title=scheme.title,
                description=scheme.description,
                metadata={
                    "scheme_id": str(scheme.id),
                    "source_url": scheme.source_url,
                    "title": scheme.title,
                },
            )

            for c in chunks:
                try:
                    embedding = await embedder.embed_query(c["content"])
                except Exception:
                    embedding = []

                doc_chunk = DocumentChunk(
                    scheme_id=scheme.id,
                    chunk_index=c["chunk_index"],
                    content=c["content"],
                    chunk_metadata=c["chunk_metadata"],
                    token_count=c["token_count"],
                )
                session.add(doc_chunk)

            processed += 1
            if processed % 20 == 0:
                await session.commit()
                logger.info("arq.reindex.progress", processed=processed, total=len(schemes))

        await session.commit()

    return {"status": "completed", "schemes_reindexed": processed}


class WorkerSettings:
    host = settings.upstash_redis_url
    queue_name = settings.arq_queue_name
    max_jobs = settings.arq_max_jobs
    job_timeout = settings.arq_job_timeout
    keep_result = 86400
    poll_delay = 5.0
    on_startup = startup
    on_shutdown = shutdown
    functions = [
        scrape_source,
        scrape_all_sources,
        embed_scheme_chunks,
        reindex_all_schemes,
    ]
