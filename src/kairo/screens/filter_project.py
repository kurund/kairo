"""Filter by project screen for Kairo TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class FilterProjectScreen(ModalScreen[str]):
    """Modal screen for filtering tasks by project."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("enter", "apply", "Apply", show=False),
        Binding("ctrl+d", "clear", "Clear", show=False),
    ]

    CSS = """
    FilterProjectScreen {
        align: center middle;
    }

    #filter_dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #filter_dialog Label {
        margin: 1 0;
    }

    #filter_dialog Input {
        margin-bottom: 1;
    }

    #filter_dialog Horizontal {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    #filter_dialog Button {
        margin: 0 1;
    }
    """

    def __init__(self, current_filter: str, available_projects: list[str]):
        self._current_filter = current_filter
        self._available_projects = available_projects
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the filter dialog."""
        with Vertical(id="filter_dialog"):
            yield Label("[bold]Filter Tasks by Project[/bold]")

            if self._current_filter:
                yield Label(
                    f"Current filter: [magenta]{self._current_filter}[/magenta]"
                )
            else:
                yield Label("Current filter: [dim]None (showing all)[/dim]")

            yield Label("\nEnter project name (or leave empty for all tasks):")
            yield Input(
                value=self._current_filter or "",
                placeholder="Enter project name",
                id="project_input",
            )

            if self._available_projects:
                yield Label(
                    f"\nAvailable projects: [magenta]{', '.join(sorted(self._available_projects))}[/magenta]"
                )

            with Horizontal():
                yield Button("Apply", variant="primary", id="apply_btn")
                yield Button("Clear", variant="warning", id="clear_btn")
                yield Button("Cancel", variant="default", id="cancel_btn")

    def _apply_filter(self) -> None:
        """Apply the current filter."""
        project_input = self.query_one("#project_input", Input)
        self.dismiss(project_input.value.strip())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "apply_btn":
            self._apply_filter()
        elif event.button.id == "clear_btn":
            self.dismiss("")
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in project input."""
        if event.input.id == "project_input":
            self._apply_filter()

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(None)

    def action_apply(self) -> None:
        """Apply the filter (Enter shortcut)."""
        self._apply_filter()

    def action_clear(self) -> None:
        """Clear the filter (Ctrl+D shortcut)."""
        self.dismiss("")
