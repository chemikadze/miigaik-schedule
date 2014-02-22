(function() {

    // http://stackoverflow.com/questions/126100/how-to-efficiently-count-the-number-of-keys-properties-of-an-object-in-javascrip
    if (!Object.keys) {
        Object.keys = function (obj) {
            var keys = [],
                k;
            for (k in obj) {
                if (Object.prototype.hasOwnProperty.call(obj, k)) {
                    keys.push(k);
                }
            }
            return keys;
        };
    }

    function getItems($select) {
        var result = {};
        var $items = $select.children("option");
        for (var i = 0; i < $items.length; ++i) {
            var key = $items[i].value;
            result[key] = $.trim($($items[i]).text());
        }
        return result;
    }

    var $facultySelector = $("select[name=faculty]");
    var $yearSelector = $("select[name=year]");
    var $groupSelector = $("select[name=group]");
    var $submitButton = $(".js-open-group");

    var fullGroupMap = getItems($groupSelector);

    $("select[name=faculty], select[name=year]").change(function (e) {
        refreshGroups($facultySelector.val(), $yearSelector.val());
    });

    function refreshGroups(faculty, year) {
        var url = "/rest/groups/" + faculty + "/" + year;
        $submitButton.prop('disabled', true);
        $groupSelector.empty().prop('disabled', true);
        $.ajax(url, {
            cache: false,
            success: function(data) {
                console.log(data);
                onRefreshGroupsFinish(data.groups);
            },
            error: function() {
                console.error("Не удалось загрузить список групп, отображается нефильтрованный список");
                onRefreshGroupsFinish(fullGroupMap);
            }
        });
    }

    function onRefreshGroupsFinish(groups) {
        setGroups(groups);
        if (Object.keys(groups).length > 0) {
            $submitButton.prop('disabled', false);
            $groupSelector.prop('disabled', false);
        } else {
            $groupSelector.append(
                $("<option></option>").text("Нет таких групп"));
        }
    }

    function setGroups(groups) {
        $groupSelector.empty();
        for (var id in groups) {
            if (groups.hasOwnProperty(id)) {
                var name = groups[id];
                var $el = $("<option></option>").attr("value", id).text(name);
                $groupSelector.append($el);
            }
        }
    }

    refreshGroups($facultySelector.val(), $yearSelector.val());

})();
