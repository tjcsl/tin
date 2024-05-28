function collapse() {
  $('#submission-list').addClass('submission-list-collapsed');

  $('.submissions-overview-expand').text('<< Show All Submissions');
  $('.submissions-overview-collapse').text('');
}

function expand() {
  $('#submission-list').removeClass('submission-list-collapsed');

  $('.submissions-overview-expand').text('');
  $('.submissions-overview-collapse').text('Collapse >>');
}
