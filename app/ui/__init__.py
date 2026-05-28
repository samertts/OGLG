"""User interface layer for the Correspondence System.

Provides the complete PySide6 GUI infrastructure including shell,
navigation, theme, dialogs, widgets, viewmodels, and controllers.

Architecture:
    View (Qt Widgets)
        -> ViewModel (state & presentation logic)
            -> Controller (orchestration)
                -> Application Services

Rules:
    - No business logic inside UI layer
    - No database access inside widgets
    - No blocking UI operations
    - Controllers access services, not repositories directly
"""

from __future__ import annotations
