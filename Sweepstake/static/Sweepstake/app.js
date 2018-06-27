$(document).ready(function(){
    var page = $(location).attr('pathname');

    if(page=='/leaderbords'){
        $.getJSON("api/participants")
        .then(function(data){
            addParticipantItems(data['Participants'])
        })
    } else if (page=='/teams') {
        $.getJSON("api/teams")
        .then(function(data){
            addTeamItems(data['Teams'])
        })
    }
})

function addTeamItems(items){
    items.forEach(function(item, index){

        var newItem = createItem(item);

        if(index<3){
            $('#top' + index).children('h1').text(item.name)
            $('#top' + index).children('h3').text(item.points + ' Points')
        }

        $('#pot' + item.pot).children('.item_list').append(newItem);
    })
}


function addParticipantItems(items){
    var locations = {'name': 'location'};
    var pots = {'name': 'pot'};

    items.forEach(function(item){
        var newItem = createItem(item)
        $('#participant_list').children('.item_list').append(newItem);

        insertGroups.apply(item, [locations, pots]);
    });

    var locationList = makeList(locations);
    locationList.sort(function(a, b){
        return b.points - a.points;
    });
    locationList.forEach(function(item){
        var newItem = createItem(item);
        $('#participant_location').children('.item_list').append(newItem);
    });

    var potsList = makeList(pots);
    potsList.sort(function(a, b){
        return b.points - a.points;
    });
    potsList.forEach(function(item){
        var newItem = createItem(item);
        $('#participant_pot').children('.item_list').append(newItem);
    })
}

function insertGroups(){
    /* Only used with apply! */
    lists = [].slice.call(arguments);
    item = this

    lists.forEach(function(list){
        var listName = list.name
        if(list[item[listName]] === undefined){
            list[item[listName]] = {
                'name': item[list.name],
                'total': item.points,
                'participants': 1
            };
        } else {
            list[item[listName]]['total'] += item.points;
            list[item[listName]]['participants']++;
        }
    });
}

function makeList(list){
    var newArr = [];
    for(var key in list){
        if (key=='name') continue;
        list[key]['points'] = list[key]['total']/list[key]['participants'];
        newArr.push(list[key])
    }
    return newArr;
}

function createItem(item){
    var newItem = $('<li class="item"></li>')
    var name = $('<div class="item_name">' + item.name + '</div>')
    var points = $('<div class="item_points">' + item.points.toFixed(0) + '</div>')
    newItem.append(name);
    newItem.append(points);
    return newItem;
}

