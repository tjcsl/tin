// Turns links marked with `data-post-action` into CSRF-protected POST requests.
//
// State-changing endpoints (delete, publish, rerun, file actions, ...) must not
// be reachable via GET, because Django's CSRF protection deliberately exempts
// safe methods -- a cross-site <img>/<script> GET would otherwise trigger them
// with the victim's session. Rendering these as ordinary links keeps the exact
// same appearance while submitting a real POST (with the CSRF token) on click.
//
// Usage in templates:
//   <a href="#" data-post-action="{% url '...' %}">Label</a>
//   <a href="#" data-post-action="{% url '...' %}"
//      data-period-from="#assignment-action-period-select">Rerun</a>
(function () {
  function getCookie(name) {
    var match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? match.pop() : '';
  }

  $(document).on('click', 'a[data-post-action]', function (event) {
    event.preventDefault();

    var $link = $(this);
    var $form = $('<form>', {
      method: 'post',
      action: $link.attr('data-post-action'),
    });

    $('<input>', {
      type: 'hidden',
      name: 'csrfmiddlewaretoken',
      value: getCookie('csrftoken'),
    }).appendTo($form);

    // Optionally forward the value of another element (e.g. the period select
    // used by the "Rerun submissions" action) as a POST field.
    var periodSelector = $link.attr('data-period-from');
    if (periodSelector) {
      $('<input>', {
        type: 'hidden',
        name: 'period',
        value: $(periodSelector).val(),
      }).appendTo($form);
    }

    $form.appendTo(document.body);
    $form.get(0).submit();
  });
})();
