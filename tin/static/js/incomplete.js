//Based off of https://github.com/ovkulkarni/ai-grader/blob/master/templates/upload.html

function join_url(base, url) {
  return new URL(url, base).href;
}

function filter_incomplete_by_endpoint(endpoint) {
  return $(".incomplete").filter((i, elem) => ($(elem).data("endpoint") == endpoint));
}

var websockets = {};

function create_websocket(endpoint) {
  var ws_endpoint = join_url(location.protocol + "//" + location.host, endpoint).replace(/^http(s?):/, "ws$1:");
  var sock = new WebSocket(ws_endpoint);
  sock.onmessage = function(e) {
    data = JSON.parse(e.data);
    handle_data(endpoint, data);
    if(filter_incomplete_by_endpoint(endpoint).get().length == 0) {
      sock.close();
    }
  };
  sock.onclose = function(e) {
    websockets[endpoint] = false;
  };
  websockets[endpoint] = sock;
}

function update() {
  var endpoints = new Set();
  $(".incomplete").each(function(i, obj) {
    endpoint = $(obj).data("endpoint")
    if(!endpoints.has(endpoint)) {
      if($(obj).data("no-websocket") == true) {
        $.get(endpoint, function(data) {
          handle_data(endpoint, data);
        });
      }
      else {
        if(websockets[endpoint] === undefined) {
          // Just not created yet
          create_websocket(endpoint);
        }
        else if(websockets[endpoint] == false) {
          // Connection closed
          $.get(endpoint, function(data) {
            handle_data(endpoint, data);
            create_websocket(endpoint);
          });
        }
      }
      endpoints.add(endpoint);
    }
  });
}

function handle_data(endpoint, res) {
  filter_incomplete_by_endpoint(endpoint).each(function(i, obj) {
    obj = $(obj);
    if(res.complete) {
      obj.removeClass("incomplete");
      obj.addClass("complete");
    }
    var result_obj = obj;
    if(obj.children().length) {
      var result_div = null;
      var other_result_div = null;

      if(res.complete) {
        result_div = obj.find(".result-complete");
        other_result_div = obj.find(".result-incomplete");
      }
      else {
        result_div = obj.find(".result-incomplete");
        other_result_div = obj.find(".result-complete");
      }

      if(!result_div.length) {
        if(res.has_been_graded) {
          result_div = obj.find(".result-graded");
          other_result_div = obj.find(".result-not-graded");
        }
        else {
          result_div = obj.find(".result-not-graded");
          other_result_div = obj.find(".result-graded");
        }
      }

      if(!result_div.length) {
        result_div = obj.find(".result");
      }

      if(result_div.length) {
        result_obj = result_div;
      }

      if(other_result_div.length) {
        other_result_div.text("");
      }
    }
    var value = res[obj.data("endpoint-key")];
    if(obj.hasClass("code-result")) {
      result_obj.text("");
      $("<pre>").appendTo($("<code>").appendTo(result_obj)).text(value);
    }
    else if(obj.hasClass("conditional-result")) {
      var show = Boolean(value);
      if(obj.data("resultNegate") == true) {
        show = !show;
      }
      result_obj.css("display", (show ? "initial" : "none"));
    }
    else {
      if(typeof value == "boolean") {
        value = (value ? "Yes": "No");
      }
      result_obj.text(value);
    }

    if(res.complete && obj.data("hideWhenComplete") == true) {
      result_obj.css("display", "none");
    }
  });
}

$(function() {
  update();
  setInterval(update, 3000);
});
