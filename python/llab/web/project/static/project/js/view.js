/**
 * requires: 3rd-party/humanize.js
 */

llab.build_from_tree = function (full_tree) {
    var $tree = $('#source-tree');
    var $breadcrumb = $('#source-tree-breadcrumb');
    var prev_tree = [];
    var prev_tree_path = ['llab'];
    var curr_tree = full_tree.tree;
    var tree_path = 'tree/' + branch + '/';
    var initial_path = full_tree.path;

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
            var url = '#';
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

            var commit_url = '<img title="' + email + '"';
            commit_url += ' class="gravatar" width=16 height=16 ';
            commit_url += 'src="' + gravatar_url + '"> ';
            commit_url += '<a href="#">' + item.commit.message + '</a>';

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
            return false;
        });

        $('td.folder > span').click(function () {
            var item_name = $(this).parent().data('name');
            prev_tree.push(curr_tree);
            prev_tree_path.push(item_name);
            curr_tree = curr_tree[item_name].tree;
            build_tree(curr_tree);
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

    build_tree(curr_tree);
};

llab.build_tree = function (project, owner, branch, commit, path) {
    var kwargs = {'project': project, 'owner': owner,
                  'commit': commit, 'path': path};
    llab.getJSON('project:tree', kwargs, llab.build_from_tree);
};
