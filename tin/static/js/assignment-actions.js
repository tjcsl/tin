function updateAssignmentActionHrefs() {
  const period = $('#assignment-action-period-select').val();
  $('.assignment-action').each(function () {
    const dataHref = $(this).data('href');
    $(this).attr('href', dataHref + '?period=' + period);
  });
}

$(document).ready(function () {
  $('#assignment-action-period-select').change(function () {
    updateAssignmentActionHrefs();
  });

  updateAssignmentActionHrefs();
});
