"""Batch enrich all tenders that haven't been enriched yet.

Logs progress to stdout and /tmp/enrich-all-progress.log.
"""

import sys
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/tmp/enrich-all-progress.log", mode="w"),
    ],
)
logger = logging.getLogger(__name__)

from services.nexus.tenders import _load_all_cases, _find_case_file, enrich_tender

def main():
    all_cases = _load_all_cases()
    needs_enrich = []

    for t in all_cases:
        md_file = _find_case_file(t["job_number"])
        if not md_file:
            continue
        content = md_file.read_text(encoding="utf-8")
        if "## 投標須知" not in content:
            needs_enrich.append(t)

    total = len(needs_enrich)
    logger.info("=== Starting batch enrich: %d tenders ===", total)

    success = 0
    failed = 0
    skipped = 0

    for i, t in enumerate(needs_enrich, 1):
        jn = t["job_number"]
        name = t["name"][:30]
        logger.info("[%d/%d] Enriching %s (%s)...", i, total, jn, name)

        try:
            result = enrich_tender(jn)
            sections = result.get("sections_added", 0)
            backfilled = result.get("fields_backfilled", False)
            logger.info(
                "[%d/%d] OK — %s: +%d sections, backfill=%s",
                i, total, jn, sections, backfilled,
            )
            success += 1
        except Exception as e:
            logger.error("[%d/%d] FAILED — %s: %s", i, total, jn, e)
            failed += 1

        # Brief pause to avoid hammering pcc.gov.tw
        time.sleep(1)

    logger.info("=== Done: %d success, %d failed, %d total ===", success, failed, total)


if __name__ == "__main__":
    main()
