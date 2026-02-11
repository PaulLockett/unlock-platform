"""Unified worker runner for all Temporal components.

Each Railway service runs the same Docker image with a different CLI argument
to select which component's workflows/activities to expose on that worker.
"""
