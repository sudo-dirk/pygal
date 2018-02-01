import helpers
import items


class help_object(items.base_object):
    LOG_PREFIX = 'Help:'
    TYPE = None

    def __init__(self, rel_path, base_path, slideshow, force_user, help_type):
        items.base_object.__init__(self, rel_path, base_path, slideshow, force_user)
        self.help_type = help_type

    def help_content(self):
        if self.help_type == 'search':
            return self.search()
        else:
            return "Help Information for %s is not yet implemented" % self.help_type

    def item_url(self, args=None):
        return self._url() + (helpers.strargs(args) if args is not None else '')
    def search(self):
        return """
<h2> Search ... </h2>
Without any special activity, the search will find your pattern in the path (inside pygal) and your tags. If you want to search in the tags or path only, see also the key definitions and examples.<br> You can use wildcards, ...
<h2> Keys </h2>
<h3> Common Keys </h3>
    <ul>
      <li>path (TEXT)</li>
      <li>tags (TEXT)</li>
      <li>type (TEXT)</li>
        <ul>
          <li>picture</li>
          <li>video</li>
          <li>all kind of extentions, if not picture or video</li>
        </ul>
      <li>upload_user (TEXT)</li>
      <li>upload_ip (TEXT)</li>
      <li>upload_date (DATETIME)</li>
    </ul>
<h3> Keys for pictures </h3>
    <ul>
      <li>date (DATETIME)</li>
      <li>height (NUMERIC)</li>
      <li>width (NUMERIC)</li>
      <li>camera (TEXT)</li>
      <li>orientation (NUMERIC)</li>
      <li>flash (TEXT)</li>
      <li>aperture (NUMERIC)</li>
      <li>focal_length (NUMERIC)</li>
      <li>exposure_time (NUMERIC)</li>
      <li>exposure_program (TEXT)</li>
      <li>iso (NUMERIC)</li>
    </ul>
<h3> Keys for videos </h3>
    <ul>
      <li>date (DATETIME)</li>
      <li>height (NUMERIC)</li>
      <li>width (NUMERIC)</li>
      <li>duration (NUMERIC)</li>
    </ul>
<h3> Examples </h3>
    <ul>
      <li><a href="%(search_example1)s">type:video AND date:2018</a> gives results with all videos in year 2018</li>
      <li><a href="%(search_example2)s">date:[-2y to now]</a> gives results with all item of the last two years</li>
      <li><a href="%(search_example3)s">path:2018</a> gives results with all item having 2018 in their path</li>
      <li><a href="%(search_example4)s">tags:Test</a> gives results with all item having Test in their tags</li>
    </ul>
""" % {'search_example1': self.item_url({'q': 'type:video AND date:2018'}),
       'search_example2': self.item_url({'q': 'date:[-2y to now]'}),
       'search_example3': self.item_url({'q': 'path:2018'}),
       'search_example4': self.item_url({'q': 'tags:Test'}),}
