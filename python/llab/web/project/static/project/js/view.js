/**
 * requires: 3rd-party/humanize.js
 */

llab.readme_cache = {};
llab.render_readme = function (owner, project, commit, directory) {
    var kwargs = {'owner': owner, 'project': project,
                  'commit': commit, 'directory': directory};
    var url = llab.resolve('project:readme', kwargs);
    var $readme = $('#readme');
    var $body = $('#readme-body');

    if (url in llab.readme_cache) {
        $readme.show();
        $body.html(llab.readme_cache[url]);
        return true;
    }

    $.get(url, function (content) {
        $readme.show();
        $body.html(content);
        llab.readme_cache[url] = content;
    }).fail(function () {
        $readme.hide();
    });
};

llab.readme_exists = function (curr_tree) {
    var to_try = ['README.md', 'readme.md', 'README.txt', 'readme.txt'];
    for (var i = 0; i < to_try.length; i++) {
        if (to_try[i] in curr_tree) {
            return curr_tree[to_try[i]].path;
        }
    }
    return false;
}

llab.readme_if_exists = function (curr_tree, owner, project, commit) {
    var path = llab.readme_exists(curr_tree);
    if (path) {
        var directory = path.split('/').slice(0, -1).join('/');
        return llab.render_readme(owner, project, commit, directory);
    } else {
        $('#readme').hide();
    }
};

llab.build_from_tree = function (ftree, project, owner, branch, commit, path) {
    var $tree = $('#source-tree');
    var $breadcrumb = $('#source-tree-breadcrumb');
    var prev_tree = [];
    var prev_tree_path = ['llab'];
    var curr_tree = ftree.tree;
    var tree_path = 'tree/' + branch + '/';
    var real_path = path;
    var initial_path = path.split('/');

    if (window.location.toString().indexOf('tree') !== -1) {
        tree_path = '';
    }

    var build_tree = function (tree) {
        $tree.html('');

        if (prev_tree.length) {
            var record = '<tr>';
            record += '<td class="prev-tree">';
            record += '<span class="text-primary link">../</span>' +'</td>';
            record += '<td></td>';
            record += '<td></td>';
            record += '</tr>';
            $tree.append($(record));
        }

        for (var obj in tree) {
            var item = tree[obj];
            var item_name = obj;

            // Construct the appropriate URL
            var kwargs = {'owner': owner, 'project': project,
                          'commit': commit, 'path': item.path};
            var url = llab.resolve('project:commit:raw', kwargs);
            var item_url = '<a href="' + url + '">' + item_name + '</a>';

            // Construct the appropriate glyph
            var glyph = 'glyphicon-file';
            if (item.type == 'folder') {
                glyph = 'glyphicon-folder-close';
                item_url = '<span class="text-primary link">';
                item_url += item_name + '</span>';
            }

            var email = item.commit.committer_email;
            var gravatar_url = llab.resolve('account:gravatar');
            gravatar_url += '?email=' + email + '&size=16';

            kwargs = {'owner': owner, 'project': project,
                      'commit': item.commit.sha};
            var commit_view_url = llab.resolve('project:commit:view', kwargs);
            var commit_url = '<img title="' + email + '"';
            commit_url += ' class="gravatar" width=16 height=16 ';
            commit_url += 'src="' + gravatar_url + '"> ';
            commit_url += '<a href="' + commit_view_url + '">';
            commit_url += item.commit.message + '</a>';

            glyph = '<span class="glyphicon ' + glyph + '"></span>&nbsp;';

            // Construct the record
            var record = '<tr>';
            record += '<td class="' + item.type + '" data-name="';
            record += item_name + '">' + glyph + item_url + '</td>';
            record += '<td>' + commit_url + '</td>';
            record += '<td>';
            record += humanize.relativeTime(item.commit.commit_time);
            record += '</td>';
            record += '</tr>';

            $tree.append($(record));
        }

        $('td.prev-tree > span').click(function () {
            history.back();
            curr_tree = prev_tree.pop()
            prev_tree_path.pop();
            build_tree(curr_tree);
            llab.readme_if_exists(curr_tree, owner, project, commit);
            return false;
        });

        $('td.folder > span').click(function () {
            var item_name = $(this).parent().data('name');
            prev_tree.push(curr_tree);
            prev_tree_path.push(item_name);
            curr_tree = curr_tree[item_name].tree;
            build_tree(curr_tree);
            llab.readme_if_exists(curr_tree, owner, project, commit);
            if (prev_tree.length == 1) {
                item_name = tree_path + item_name;
            }
            history.pushState({}, '', item_name + '/');
            return false;
        });
    };

    for (var i = 0; i < initial_path.length; i++) {
        var name = initial_path[i];
        if (curr_tree[name] && curr_tree[name].type == "folder") {
            prev_tree.push(curr_tree);
            prev_tree_path.push(name);
            curr_tree = curr_tree[name].tree;
        }
    }

    // Construct the file tree and then render out any available README
    build_tree(curr_tree);
    llab.readme_if_exists(curr_tree, owner, project, commit);
};

llab.build_tree = function (project, owner, branch, commit, path) {
    var kwargs = {'project': project, 'owner': owner,
                  'commit': commit, 'path': path};
    llab.getJSON('project:json_tree', kwargs, function (full_tree) {
        llab.build_from_tree(full_tree, project, owner, branch, commit, path);
    });
};
