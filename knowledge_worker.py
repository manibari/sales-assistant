"""
Knowledge Parse Worker.

Standalone process that polls the knowledge_parse_queue table
and processes file parsing tasks (text extraction + AI summarization).
"""
import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.nexus.knowledge import (
    get_next_parse_task,
    update_parse_status,
    update_file_parse_status,
    delete_knowledge_by_file,
    extract_text_from_file,
    summarize_chunk,
    create_knowledge_chunk,
    PARSEABLE_EXTENSIONS,
    _get_file_extension,
)
from services.nexus.documents import get_file


def process_single_task():
    """Fetch and process one parse task."""
    task = get_next_parse_task()
    if not task:
        return

    queue_id = task["id"]
    file_id = task["file_id"]
    logger.info("Processing parse task #%d for file #%d", queue_id, file_id)

    try:
        # 1. Get file record
        file_record = get_file(file_id)
        if not file_record:
            update_parse_status(queue_id, "failed", "File record not found")
            return

        file_name = file_record["file_name"]
        file_path = file_record["file_path"]
        client_id = file_record.get("client_id")
        ext = _get_file_extension(file_name)

        # 2. Check if parseable
        if ext not in PARSEABLE_EXTENSIONS:
            update_parse_status(queue_id, "skipped", f"Unsupported type: {ext}")
            update_file_parse_status(file_id, "skipped")
            logger.info("  Skipped: unsupported file type %s", ext)
            return

        # 3. Update status to parsing
        update_file_parse_status(file_id, "parsing")

        # 4. Clear old knowledge chunks (supports re-parse)
        deleted = delete_knowledge_by_file(file_id)
        if deleted:
            logger.info("  Cleared %d old chunks", deleted)

        # 5. Extract text
        try:
            chunks = extract_text_from_file(file_path, file_name)
        except FileNotFoundError as e:
            update_parse_status(queue_id, "failed", str(e))
            update_file_parse_status(file_id, "failed")
            return

        if not chunks:
            update_parse_status(queue_id, "done", "Empty file")
            update_file_parse_status(file_id, "empty")
            logger.info("  Empty file, no chunks extracted")
            return

        logger.info("  Extracted %d chunks", len(chunks))

        # 6. Process each chunk: AI summarize + store
        ai_failures = 0
        for i, chunk in enumerate(chunks):
            content = chunk["content"]
            metadata = chunk.get("metadata")

            # AI summarize
            ai_result = summarize_chunk(content)
            if ai_result["summary"] is None:
                ai_failures += 1

            create_knowledge_chunk(
                file_id=file_id,
                client_id=client_id,
                chunk_index=i,
                content=content,
                summary=ai_result["summary"],
                tags=ai_result["tags"],
                metadata=metadata,
            )

        # 7. Determine final status
        if ai_failures == 0:
            final_status = "done"
        elif ai_failures < len(chunks):
            final_status = "partial"
        else:
            final_status = "done"  # chunks saved, just no AI summaries

        update_parse_status(queue_id, "done")
        update_file_parse_status(file_id, final_status)
        logger.info(
            "  Completed: %d chunks, %d AI failures → %s",
            len(chunks), ai_failures, final_status,
        )

    except Exception as e:
        error_msg = str(e)
        logger.error("Parse task #%d failed: %s", queue_id, error_msg)
        update_parse_status(queue_id, "failed", error_msg)
        update_file_parse_status(file_id, "failed")


def main_loop():
    """Main worker loop — poll every 10 seconds."""
    logger.info("Knowledge Worker started. Press Ctrl+C to exit.")
    while True:
        try:
            process_single_task()
        except Exception as e:
            logger.error("Unexpected error in worker loop: %s", e)
        time.sleep(10)


if __name__ == "__main__":
    main_loop()
