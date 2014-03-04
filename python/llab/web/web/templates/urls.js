var {{ namespace }} = {};
{{ namespace }}.urls = {{ urls }};

{{ namespace }}.resolve = function (name, kwargs) {
    var path = {{ namespace }}.urls[name];

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

{{ namespace }}.getJSON = function (name, kwargs, params, callback) {
    if (typeof(params) === "function") {
        callback = params;
        params = {};
    }
    return $.getJSON({{ namespace }}.resolve(name, kwargs), params, callback);
};
