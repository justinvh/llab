/**
 * requires: 3rd-party/humanize.js
 */

jQuery.fn.extend({
    disableSelection : function() {
        return this.each(function() {
            this.onselectstart = function() { return false; };
            this.unselectable = "on";
            jQuery(this).css('user-select', 'none');
            jQuery(this).css('-o-user-select', 'none');
            jQuery(this).css('-moz-user-select', 'none');
            jQuery(this).css('-khtml-user-select', 'none');
            jQuery(this).css('-webkit-user-select', 'none');
        });
    }
});

llab.readme_cache = {};
llab.render_readme = function (owner, project, commit, directory) {
    var kwargs = {'owner': owner, 'project': project,
                  'commit': commit, 'directory': directory};
    var url = llab.resolve('project:readme', kwargs);
    var $readme = $('#readme');
    var $body = $('#readme-body');

    if (url in llab.readme_cache) {
        $readme.show();
        $body.html(llab.readme_cache[url]).show();
        return true;
    }

    $.get(url, function (content) {
        $readme.show();
        $body.hide().html(content).fadeIn()
        llab.readme_cache[url] = content;
    }).fail(function () {
        $readme.fadeOut();
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
    var curr_tree = ftree;
    var tree_path = 'tree/' + branch + '/';

    if (path[0] === '/') {
        path = path.substr(1);
    }

    var real_path = path;
    var curr_path = path.split('/');
    var pseudo_history = [];
    var action_id = 0;

    window.onpopstate = function (event) {
        if (!event.state) {
            return;
        }
        var new_path = event.state.path;
        return llab.build_from_tree(
            ftree, project, owner, branch, commit, new_path);
    };

    var build_tree = function (obj, dir) {
        action_id++;
        $tree.html('');

        if (dir[0] === '/') {
            dir = dir.substr(1);
        }

        var record = '';
        if (prev_tree.length) {
            record = '<tr>';
            record += '<td class="prev-tree">';
            record += '<span class="text-primary link">../</span>' +'</td>';
            record += '<td></td>';
            record += '<td></td>';
            record += '</tr>';
        } else {
            record = '<tr>';
            record += '<td>&nbsp;</td>';
            record += '<td></td>';
            record += '<td></td>';
            record += '</tr>';
        }

        var $record = $(record).disableSelection();
        $tree.append($record);

        var missing_commits = !obj.commit;
        if (missing_commits) {
            (function (prev_action_id) {
                var url = 'project:commit:revtree';
                var kwargs = commit;
                kwargs = {'owner': owner, 'project': project,
                          'commit': commit, 'directory': dir};
                llab.getJSON(url, kwargs, function (partial_tree) {
                    if (action_id != prev_action_id)
                        return;
                    build_tree(partial_tree, curr_path.join('/'));
                });
            })(action_id);
        }

        for (var name in obj.tree) {
            var item = obj.tree[name];
            var item_name = name;

            // Construct the appropriate URL
            var kwargs = {'owner': owner, 'project': project,
                          'commit': commit, 'path': item.path};
            var url = llab.resolve('project:commit:raw', kwargs);
            var item_url = '<a href="' + url + '">' + item_name + '</a>';

            // Construct the appropriate glyph
            var glyph = 'glyphicon-file';
            if (item.type === 'folder') {
                glyph = 'glyphicon-folder-close';
                item_url = '<span class="text-primary link">';
                item_url += item_name + '</span>';
            }

            glyph = '<span class="glyphicon ' + glyph + '"></span>&nbsp;';

            if (missing_commits || item.type === 'folder') {
                var record = '<tr>';
                record += '<td class="' + item.type + '" data-name="';
                record += item_name + '">' + glyph + item_url + '</td>';

                if (missing_commits && item.type !== 'folder') {
                    record += '<td>';
                    record += '<a href="#">Retrieving latest commit...</a>';
                    record += '</td>';
                } else {
                    record += '<td></td>';
                }

                record += '<td></td>';
                record += '</tr>';
                $tree.append($(record));
                continue;
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

        $('td.prev-tree').click(function () {
            curr_tree = prev_tree.pop()
            curr_path.pop();
            prev_tree_path.pop();
            build_tree(curr_tree, curr_path.join('/'));
            llab.readme_if_exists(curr_tree.tree, owner, project, commit);

            var item_name = window.location.pathname.split('/');
            item_name = item_name.slice(0, -2);
            item_name = item_name.join('/');
            var path_name = curr_path.join('/')
            history.pushState({'path': path_name}, '', item_name + '/');
            return false;
        });

        $('td.folder > span').click(function () {
            var item_name = $(this).parent().data('name');
            prev_tree.push(curr_tree);
            prev_tree_path.push(item_name);
            curr_path.push(item_name);
            curr_tree = curr_tree.tree[item_name];

            var new_path = curr_path.join('/');
            build_tree(curr_tree, new_path);
            llab.readme_if_exists(curr_tree.tree, owner, project, commit);

            if (prev_tree.length === 1) {
                if (window.location.toString().indexOf('tree') === -1) {
                    item_name = tree_path + item_name;
                }
            }

            history.pushState({'path': new_path}, '', item_name + '/');
            pseudo_history.push(item_name);
            return false;
        });
    };

    for (var i = 0; i < curr_path.length; i++) {
        var name = curr_path[i];
        var ttree = curr_tree.tree;
        if (ttree[name] && ttree[name].type === "folder") {
            prev_tree.push(curr_tree);
            prev_tree_path.push(name);
            curr_tree = curr_tree.tree[name];
        }
    }

    // Construct the file tree and then render out any available README
    build_tree(curr_tree.tree, curr_path.join('/'));
    llab.readme_if_exists(curr_tree.tree, owner, project, commit);
};

llab.build_tree = function (project, owner, branch, commit, path) {
    var commit_or_branch = commit.length ? commit : branch;
    var url = commit.length ? 'project:json_tree' : 'project:json_tree_branch';
    var kwargs = {'project': project, 'owner': owner,
                  'commit': commit_or_branch, 'path': path};
    var $wait_prompt = $('#wait-prompt');
    llab.getJSON(url, kwargs, function (full_tree) {
        tree = full_tree.tree
        llab.build_from_tree(tree, project, owner, branch, commit, path);
        $wait_prompt.hide();
    }, false);
};
