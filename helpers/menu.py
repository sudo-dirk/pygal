


class menubar(list):
    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)

    def get_reverse(self):
        rv = self[:]
        rv.reverse()
        return rv


class menuentry(object):
    def __init__(self, uid, left, name, active, url, icon):
        self.uid = uid
        self.name = name
        self.active = active
        self.url = url
        self.icon = icon
        self.dropdown_elements = []
        self.left = left

    def is_dropdownmenu(self):
        return len(self.dropdown_elements) > 0

    def append_dropdown_element(self, entry):
        self.dropdown_elements.append(entry)
