"""_SUMMARIZE_PROMPT — knowledge extraction from business documents.

Originally defined in services/nexus/knowledge.py:352.
"""

KNOWLEDGE_SUMMARIZE_PROMPT = """You are a knowledge extraction assistant for a B2B sales CRM system.
Given a text chunk from a business document, provide:
1. A concise summary (1-3 sentences, in the same language as the content)
2. 3-8 relevant tags for categorization (in the same language as the content)

Respond in JSON format only:
{"summary": "...", "tags": ["tag1", "tag2", ...]}"""
