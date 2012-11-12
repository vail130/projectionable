// Generated by CoffeeScript 1.3.3
(function() {

  $(function() {
    var $alert, $email, $formBody, $formInputs, $password1, $password2, $signupButton, displayError, displaySuccess;
    $formBody = $('.trial-form .proj-form-body');
    $formInputs = $formBody.find('> input');
    $alert = $formBody.find('> .alert');
    $email = $('#email');
    $password1 = $('#password1');
    $password2 = $('#password2');
    $signupButton = $formBody.find('.signup-button');
    $formInputs.first().get(0).focus();
    $email.add($password1).add($password2).keypress(function(event) {
      var code;
      code = event.keyCode ? event.keyCode : event.charCode;
      if (code === 13) {
        return $signupButton.trigger('click');
      }
    });
    $signupButton.click(function(event) {
      var email, password1, password2,
        _this = this;
      event.preventDefault();
      email = $email.val();
      if (email === '') {
        displayError('Missing email field');
        $formInputs.get(0).focus();
        return;
      }
      password1 = $password1.val();
      password2 = $password2.val();
      if (password1 === '') {
        displayError('Missing password field');
        $formInputs.get(1).focus();
        return;
      } else if (password2 === '') {
        displayError('Missing password field');
        $formInputs.get(2).focus();
        return;
      } else if (password1 !== password2) {
        displayError('Mismatching password fields');
        $formInputs.get(1).focus();
        return;
      }
      $signupButton.button('loading');
      $alert.hide();
      return $.ajax({
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        url: '/api/accounts',
        data: JSON.stringify({
          email: email,
          password: password1
        }),
        success: function(json) {
          return displaySuccess('Thank you! Please follow the instructions in the email we just sent to you.');
        },
        error: function(jqXHR) {
          var json;
          json = JSON.parse(jqXHR.responseText);
          return displayError(json[_.keys(JSON.parse(jqXHR.responseText))[0]]);
        },
        complete: function(jqXHR) {
          $signupButton.button('reset');
          return $formInputs.get(0).focus();
        }
      });
    });
    displayError = function(msg) {
      return $alert.removeClass('alert-success').find('span').text(msg).end().find('strong').text('Error').end().addClass('alert-error').show();
    };
    return displaySuccess = function(msg) {
      return $alert.removeClass('alert-error').find('span').text(msg).end().find('strong').text('Success').end().addClass('alert-success').show();
    };
  });

}).call(this);