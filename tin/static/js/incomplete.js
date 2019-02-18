//Based off of https://github.com/ovkulkarni/ai-grader/blob/master/templates/upload.html
setInterval(function() {
  var endpoint_elems = {};
  $(".incomplete").each(function(i, obj) {
    var obj = $(obj);
    var endpoint = obj.data("endpoint");
    endpoint_elems[endpoint] = endpoint_elems[endpoint] || [];
    endpoint_elems[endpoint].push(obj);
  });
  Object.keys(endpoint_elems).forEach(function(endpoint) {
    $.get(endpoint, function(res) {
      var remove_elems = [];
      endpoint_elems[endpoint].forEach(function(obj) {
        if(res.complete) {
          obj.removeClass("incomplete");
          obj.addClass("complete");
          remove_elems.push(obj);
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
        if(obj.hasClass("code-result")) {
          result_obj.text("");
          $("<pre>").appendTo($("<code>").appendTo(result_obj)).text(res[obj.data("endpoint-key")]);
        }
        else {
          result_obj.text(res[obj.data("endpoint-key")]);
        }
      });
      endpoint_elems[endpoint].filter(function(obj) {
        return remove_elems.includes(obj);
      });
    });
  });
}, 3000);
