"""Data Manager: Temporal Workflow definitions.

Orchestrates the data platform through four workflows:
- IngestWorkflow: Source Access → Transform Engine → Data Access
- QueryWorkflow: Config Access → Data Access → Schema Engine → Access Engine
- ConfigureWorkflow: Validate inputs → Config Access
- ShareWorkflow: Config Access → Access Engine → generate link
"""
