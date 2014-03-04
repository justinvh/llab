import sys
import re
import json

from django.shortcuts import render
from django.core.urlresolvers import RegexURLPattern, RegexURLResolver
from django.utils.datastructures import SortedDict
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode


# Pattern for recognizing unnamed url parameters
RE_KWARG = re.compile(r"(\(\?P\<(.*?)\>.*?\))")

# Pattern for recongnizing named parameters in urls
RE_ARG = re.compile(r"(\(.*?\))")


def handle_url_module(js_patterns, module_name, prefix="", namespace=None):
    """Processes a specific URL module.

    Each URL module will be resolved and then the regex will be mapped
    for a JavaScript expression.

    """

    def parse_regex_url_resolver(pattern, js_patterns, namespace=None):
        """Parse a specific URL resolver from a URL module.

        This will nest namespaces appropriately.

        """
        kwargs = {}
        full_namespace = pattern.namespace
        if pattern.namespace:
            if namespace:
                full_namespace = u'{}:{}'.format(namespace, pattern.namespace)
            kwargs['namespace'] = full_namespace
        namespace = pattern.urlconf_name or pattern_namespace
        prefix = pattern.regex.pattern
        handle_url_module(js_patterns, namespace, prefix=prefix, **kwargs)

    def parse_regex_url_pattern(prefix, namespace, pattern, js_patterns):
        """Parse a specific URL regex instance.

        This method ultimately creates the pattern that will be used
        by JavaScript to resolve the URLs.

        """
        full_url = prefix + pattern.regex.pattern
        for char in ('^', '$'):
            full_url = full_url.replace(char, '')

        kwarg_matches = RE_KWARG.findall(full_url)
        if kwarg_matches:
            for e in kwarg_matches:
                full_url = full_url.replace(e[0], '<{}>'.format(e[1]))

        args_matches = RE_ARG.findall(full_url)
        if args_matches:
            for el in args_matches:
                full_url = full_url.replace(el, '<>')

        key = pattern.name
        if namespace:
            key = '{}:{}'.format(namespace, pattern.name)
        js_patterns[key] = '/{}'.format(full_url)


    if isinstance(module_name, basestring):
        __import__(module_name)
        root_urls = sys.modules[module_name]
        patterns = root_urls.urlpatterns
    else:
        root_urls = module_name
        patterns = root_urls

    if not hasattr(patterns, "__iter__"):
        patterns = patterns.urlpatterns

    for pattern in patterns:
        if issubclass(pattern.__class__, RegexURLPattern):
            if pattern.name:
                parse_regex_url_pattern(prefix, namespace, pattern, js_patterns)

        elif issubclass(pattern.__class__, RegexURLResolver):
            if pattern.urlconf_name or pattern.namespace:
                parse_regex_url_resolver(pattern, js_patterns, namespace)


def urls(request):
    js_patterns = SortedDict()
    handle_url_module(js_patterns, settings.ROOT_URLCONF)
    patterns = mark_safe(force_unicode(json.dumps(js_patterns, indent=4)))
    context = {'urls': patterns, 'namespace': u'llab'}
    return render(request, 'urls.js', context, content_type='text/javascript')
