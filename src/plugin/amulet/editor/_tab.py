class ToolAboutToHide:
    def tool_about_to_hide(self) -> bool:
        """
        Called when the tool is about to be hidden.
        Return False to prevent the tool being hidden.
        This is called when switching world tabs, switching tools, or closing the level tab.
        """
        return True


class TabAboutToHide:
    def tab_about_to_hide(self) -> bool:
        """
        Called when the tab is about to be hidden.
        Return False to prevent the tab from being hidden.
        """
        return True


class TabAboutToClose:
    def tab_about_to_close(self) -> bool:
        """
        Called when the tab is about to be closed.
        Return False to prevent the tab from being closed.
        """
        return True
