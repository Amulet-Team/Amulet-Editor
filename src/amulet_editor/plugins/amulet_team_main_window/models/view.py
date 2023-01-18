class View:
    def activate_view(self):
        """
        Run every time the view is activated by code or by clicking the tool button associated with the view.
        :meth:`wake_view` will be called after if the view did not have focus.
        This is useful if the view wants to reset to a default state every time the tool button is clicked.
        """
        pass

    def wake_view(self):
        """
        This is run when the view gains focus.
        If the view was focused by clicking the associated tool button :meth:`activate_view` will be called first.
        Useful in combination with :meth:`sleep_view` to switch between a high and low processing mode.
        """
        pass

    def sleep_view(self):
        """
        This is run when the view looses focus.
        This is useful to put the view into a low processing mode.
        This method must leave the view in a state where it can be disabled or woken again.
        """
        pass

    def can_disable_view(self) -> bool:
        """
        Can the view be disabled.
        Return False if for some reason the view cannot be disabled.

        :return: True if the view can be disabled. False otherwise.
        """
        return True

    def disable_view(self):
        """
        This is run when a view is about to be removed from a view container.
        This gives the view a chance to do any cleaning up before it is removed and potentially destroyed.
        This method must leave the view in a state where it can be destroyed or activated again.
        """
        pass
