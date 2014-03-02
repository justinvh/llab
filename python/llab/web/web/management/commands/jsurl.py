import sys
import re
import json

from django.core.urlresolvers import RegexURLPattern, RegexURLResolver
from django.core.management.base import BaseCommand
from django.utils.datastructures import SortedDict
from django.conf import settings

# Pattern for recognizing unnamed url parameters
# Pattern for recongnizing named parameters in urls
RE_KWARG = re.compile(r"(\(\?P\<(.*?)\>.*?\))")
RE_ARG = re.compile(r"(\(.*?\))")


JS_PRELOAD = """
var llab = {};
llab.urls = %s;

llab.resolve = function (name, kwargs) {
    var path = llab.urls[name];

    if (!path) {
        throw('URL not found for view: ' + name);
    }

    var original_path = path;
    for (var key in kwargs) {
        if (!kwargs.hasOwnProperty(key)) {
            continue;
        }

        if (!path.match('<' + key +'>')) {
            throw(key + ' does not exist in ' + original_path);
        }

        path = path.replace('<' + key +'>', kwargs[key]);
    }

    var re = new RegExp('<[a-zA-Z0-9-_]{1,}>', 'g');
    var missing_args = path.match(re);
    if (missing_args) {
        throw('Missing arguments ('
            + missing_args.join(", ") + ') for url ' + _path);
    }

    return path;
};

llab.getJSON = function (name, kwargs, params, callback) {
    if (typeof(params) === "function") {
        callback = params;
        params = {};
    }
    return $.getJSON(llab.resolve(name, kwargs), params, callback);
};

"""


class Command(BaseCommand):
    def handle(self, *args, **options):
        return sys.stdout.write(Command.autocreate())

    @staticmethod
    def autocreate():
        js_patterns = SortedDict()
        Command.handle_url_module(js_patterns, settings.ROOT_URLCONF)
        patterns = json.dumps(js_patterns, indent=4)
        return JS_PRELOAD % patterns

    @staticmethod
    def parse_regex_url_pattern(prefix, namespace, pattern, js_patterns):
        full_url = prefix + pattern.regex.pattern
        for char in ('^', '$'):
            full_url = full_url.replace(char, '')

        # handle kwargs, args
        kwarg_matches = RE_KWARG.findall(full_url)
        if kwarg_matches:
            for e in kwarg_matches:
                # prepare the output for JS resolver
                full_url = full_url.replace(e[0], '<{}>'.format(e[1]))

        #after processing all kwargs try args
        args_matches = RE_ARG.findall(full_url)
        if args_matches:
            for el in args_matches:
                # replace by a empty parameter name
                full_url = full_url.replace(el, '<>')

        # Determine namespace or not
        key = pattern.name
        if namespace:
            key = '{}:{}'.format(namespace, pattern.name)
        js_patterns[key] = '/{}'.format(full_url)

    @staticmethod
    def parse_regex_url_resolver(pattern, js_patterns):
        kwargs = {}
        if pattern.namespace:
            kwargs['namespace'] = pattern.namespace
        namespace = pattern.urlconf_name or pattern.namespace
        prefix = pattern.regex.pattern
        Command.handle_url_module(js_patterns,
                                  namespace,
                                  prefix=prefix,
                                  **kwargs)

    @staticmethod
    def handle_url_module(js_patterns, module_name, prefix="", namespace=None):
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
                    Command.parse_regex_url_pattern(
                        prefix, namespace, pattern, js_patterns)

            elif issubclass(pattern.__class__, RegexURLResolver):
                if pattern.urlconf_name or pattern.namespace:
                    Command.parse_regex_url_resolver(pattern, js_patterns)
