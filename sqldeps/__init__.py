"""SQLDeps: SQL Dependency Extractor using Large Language Models.

SQLDeps provides tools to automatically extract and map table and colum dependencies
from SQL scripts using LLMs. It identifies both dependencies (tables/columns needed
before execution) and outputs (tables/columns created or modified by the query).
"""

from importlib.metadata import version

__version__ = version("sqldeps")
