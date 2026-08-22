"""India GST agent tools.

v1 exposes none — ``get_tools()`` returning ``[]`` is a valid, documented
choice (verifactu ships none either). Revisit with a READ-only
``get_gst_summary`` tool (wrapping ``reports.build_summary``) if agent
visibility into GST filings is wanted later.
"""

from app.core.agents.tools.tool import Tool


def get_tools() -> list[Tool]:
    return []
