"""Filter selection screen for Kairo TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class FilterSelectScreen(ModalScreen[str]):
    """Modal screen for selecting filter type."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("t", "select_tag", "Tag", show=False),
        Binding("p", "select_project", "Project", show=False),
        Binding("c", "clear_filters", "Clear", show=False),
    ]

    CSS = """
    FilterSelectScreen {
        align: center middle;
    }

    #filter_dialog {
        width: 50;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #filter_dialog Label {
        margin: 1 0;
    }

    #filter_dialog Button {
        width: 100%;
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the filter selection dialog."""
        with Vertical(id="filter_dialog"):
            yield Label("[bold]Choose Filter Type[/bold]")
            yield Button("[t] Filter by Tag", variant="primary", id="tag_btn")
            yield Button("[p] Filter by Project", variant="primary", id="project_btn")
            yield Button("[c] Clear All Filters", variant="default", id="clear_btn")
            yield Button("Cancel", variant="default", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "tag_btn":
            self.dismiss("tag")
        elif event.button.id == "project_btn":
            self.dismiss("project")
        elif event.button.id == "clear_btn":
            self.dismiss("clear")
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(None)

    def action_select_tag(self) -> None:
        """Select tag filter."""
        self.dismiss("tag")

    def action_select_project(self) -> None:
        """Select project filter."""
        self.dismiss("project")

    def action_clear_filters(self) -> None:
        """Clear all filters."""
        self.dismiss("clear")
