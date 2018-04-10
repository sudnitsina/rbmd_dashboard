var a, selected_node, deadNode, node2;

$(function() {
  var url = "ws://" + location.host + "/socket";
  var ws = new WebSocket(url);

  ws.onopen = function() {ws.send(""); };
  ws.onmessage = function (evt) {
    a = JSON.parse(evt.data);
    displayData(a);
  };

  $('#mountForm').submit(function(event){
    event.preventDefault();
    $.ajax({url:"mount", data:$(this).serialize(), method:'POST',
            success:function(data){
              $('#mount').css('display', 'none');
              $('input[type = "text"]').val('');
              var res = JSON.parse(data);
              message = "<h3>" + res["state"] + "</h3> <p>"
                        + res["message"] +"</p>";
              $("#rspContainer").css("display", "block");
              $("#rsp").html(message)
              if (res["state"] == 'OK'){
                $("#rspContainer").css("background-color", "#4CAF50" );
              }
              else {
                $("#rspContainer").css("background-color", "#f44336" )
              }
            }
    })
  })

  $('#mountFormTrigger').click(function(event){
    var htmlSelect = '';
    a.quorum.forEach(function(item) {
      htmlSelect += "<option value=" + item.node + ">" + item.node + "</option>";
    })
    $('#selectNode').html(htmlSelect);
  })
});

function resolve() {
  $.ajax({
    url:"resolve",
    data:{"node": deadNode},
    success:function(data){
      $('#details').css("display", "none");
    }
  })
}

function unmount(node, mountpoint, block) {
  var u = confirm(node + ": confirm unmount of " + mountpoint);
  if (u == true) {
    $.ajax({
      url:"unmount",
      data:{"node": node, "mountpoint": mountpoint, "block": block},
      success:function(data){
        var res = JSON.parse(data);
        message = "<h3>" + res["state"] + "</h3> <p>"+ res["message"] +"</p>";
        $("#rspContainer").css("display", "block");
        $("#rsp").html(message)
        if (res["state"] == 'OK'){
          $("#rspContainer").css("background-color", "#4CAF50" );
        }
        else {
          $("#rspContainer").css("background-color", "#f44336" );
        }
      }
    })
  }
}

function displayData(a){
  $("#status").html("<p>"+a.health+"</p>");
  if (a.health == 'deadly.') {
    deadNode = a.deadlyreason["node"];
    $('#showDeadlyDetails').css("display","block");
    $('#resolve').css("display","block");
    $("#mountFormTrigger").addClass("w3-disabled")
  } else {
    $('#showDeadlyDetails').css("display","none");
    $('#resolve').css("display","none");
    $("#mountFormTrigger").removeClass("w3-disabled")
    // $('#details').css("border", "0");
  }
  $("#statusContainer:contains('alive')").css("background-color", "#4CAF50");
  $("#statusContainer:contains('resizing')").css("background-color", "#ff9800");
  $("#statusContainer:contains('deadly')").css("background-color", "#f44336");
  if (node2 != undefined) {
    var one = a.quorum.map(function(item) {return item.node});
    var two = node2.quorum.map(function(item) {return item.node});
    if (JSON.stringify(one) != JSON.stringify(two)) {
      node2 = a;
      w3DisplayData("id01", node2);
    }
  }
  else { // initial load
    node2 = a;
    w3DisplayData("id01", node2);
    $('.tablink').css('display', 'block');
  }
  if (selected_node != undefined){
    var selected_node_body = a.quorum.find(function(node) {
      return node.node == selected_node;
    });
    var t = new Date(selected_node_body["updated"] * 1000)
    var up_formatted = t.getFullYear() + "/"
                       + (t.getMonth() + 1) + "/"
                       + t.getDate() + " "
                       + t.getHours() + ":"
                       + t.getMinutes() + ":"
                       + t.getSeconds();
    $("#name").html(selected_node);
    $("#ipv4").html(selected_node_body["ip"]["v4"].join("<br>"));
    $("#ipv6").html(selected_node_body["ip"]["v6"].join("<br>"));
    $("#updated").html(up_formatted);
    if (selected_node_body["mounts"] != null) {
      var mnt_block = "";
      for (i in selected_node_body.mounts) {
        var mnt = selected_node_body.mounts[i];
        mnt_block += '<a href=\'javascript:void(0)\' onClick=\'unmount("'
                   + selected_node + '", "'
                   + selected_node_body.mounts[i].mountpoint + '", "'
                   + selected_node_body.mounts[i].block
                   + '")\' >unmount</a><br>Mountpoint: ' + mnt.mountpoint
                   + '<br>Mountopts: ' + mnt.mountopts
                   + '<br>Fstype: ' + mnt.fstype
                   + '<br>Pool: ' + mnt.pool
                   + '<br>Image: ' + mnt.image
                   + '<br>Block: ' + mnt.block + '<br>';
      }
      $("#mon").html(mnt_block);
    } else {
      $("#mon").html("");
    }
  }
  $("#leader").html(a.leader);
}

function openNode(evt, nodeName) {
  var i, x, tablinks;
  selected_node = nodeName;
  x = document.getElementsByClassName("node");
  tablinks = document.getElementsByClassName("tablink");
  $('#showDeadlyDetails').text('Show details');
  if (selected_node == deadNode) {
    $('#details').css("border", "2px solid #f44336").css("display", "block");
  } else {
    $('#details').css("border", "").css("display", "block");
  }
    displayData(a);
}
