class WindowTabClose:
    def close_tab(self) -> bool:
        """
        Called just before the tab is closed.
        Return False to prevent the tab from being closed.
        """
        return True
