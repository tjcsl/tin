$(function() {
  var output_div = $("#grader-output");
  var status_div = $("#grader-status");
  var grade_element = $("#grade");

  if(output_div.hasClass("not-graded")) {
    status_div.css({"padding-top": "15px"});
    var update_time_seconds = 5;
    var update_in_count = update_time_seconds;
    function update() {
      status_div.text("Updating in " + update_in_count + " seconds");
      if(update_in_count <= 0) {
        status_div.text("Updating...");
        $.getJSON(submission_json_url, {}, function(data) {
          if(data.error) {
            output_div.text("Error: " + data.error)
          }
          else {
            if(data.grader_output) {
              output_div.text("");
              output_div.append($("<code>").append($("<pre>").text(data.grader_output)));
            }
            if(data.has_been_graded) {
              grade_element.text(data.points_received + "/" + data.points_possible + " (" + data.grade_percent + ")");
            }
            if(data.grader_output && data.has_been_graded) {
              status_div.text("");
              status_div.css({"padding-top": "0px"});
              clearInterval(interval_id);
            }
          }
        });
        update_time_seconds = Math.min(update_time_seconds * 2, 30);
        update_in_count = update_time_seconds;
        status_div.text("Updating in " + update_in_count + " seconds");
      }
      update_in_count--;
    }
    update()
    var interval_id = setInterval(update, 1000);
  }
});
