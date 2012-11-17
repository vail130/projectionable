// Generated by CoffeeScript 1.3.3
(function() {

  $(function() {
    var $alert, $email, $forgotPasswordButton, $formBody, $formInputs, $password, $signinButton, displayError, displaySuccess;
    $formBody = $('.signin-form .proj-form-body');
    $formInputs = $formBody.children('input');
    $alert = $formBody.children('.alert');
    $email = $('#email');
    $password = $('#password');
    $signinButton = $formBody.find('.signin-button');
    $forgotPasswordButton = $formBody.find('.forgot-password-button');
    $formInputs.first().get(0).focus();
    $formInputs.on('keypress', function(event) {
      var code;
      code = event.keyCode ? event.keyCode : event.charCode;
      if (code === 13) {
        return $signinButton.trigger('click');
      }
    }).on('keyup blur', function(event) {
      if ($email.val().match(/^[\w\.%\+-]+@[A-Z0-9\.-]+\.[A-Z]{2,4}(?:\.[A-Z]{2,4})?$/i) !== null) {
        return $forgotPasswordButton.removeClass('disabled');
      } else {
        return $forgotPasswordButton.addClass('disabled');
      }
    });
    $signinButton.on('click', function(event) {
      var email, password,
        _this = this;
      event.preventDefault();
      email = $email.val();
      if (email === '') {
        displayError('Missing email field');
        $formInputs.get(0).focus();
        return;
      }
      password = $password.val();
      if (password === '') {
        displayError('Missing password field');
        $formInputs.get(1).focus();
        return;
      }
      $signinButton.button('loading');
      return $.ajax({
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        url: '/api/sessions',
        data: JSON.stringify({
          email: email,
          password: password
        }),
        success: function(json) {
          displaySuccess('Logging in...');
          $formBody.children().not('.alert').hide().filter('input').val('');
          return setTimeout((function() {
            return window.location.href = 'http://' + window.location.host;
          }), 750);
        },
        error: function(jqXHR) {
          try {
            displayError(_.pairs(JSON.parse(jqXHR.responseText))[0][1]);
          } catch (e) {
            displayError(jqXHR.statusText);
          }
          $signinButton.button('reset');
          return $formInputs.get(0).focus();
        }
      });
    });
    $forgotPasswordButton.on('click', function(event) {
      var email,
        _this = this;
      event.preventDefault();
      email = $email.val();
      if (email.match(/^[\w\.%\+-]+@[A-Z0-9\.-]+\.[A-Z]{2,4}(?:\.[A-Z]{2,4})?$/i) === null) {
        displayError('Invald email address.');
        $formInputs.get(0).focus();
        return;
      }
      $forgotPasswordButton.button('loading');
      return $.ajax({
        type: 'PUT',
        dataType: 'json',
        contentType: 'application/json',
        url: '/api/accounts',
        data: JSON.stringify({
          email: email,
          action: 'request_password_reset'
        }),
        success: function(json) {
          return displaySuccess('Please check your email to reset your password.');
        },
        error: function(jqXHR) {
          try {
            displayError(_.pairs(JSON.parse(jqXHR.responseText))[0][1]);
          } catch (e) {
            displayError(jqXHR.statusText);
          }
          $formInputs.get(0).focus();
          return $forgotPasswordButton.button('reset');
        }
      });
    });
    displayError = function(msg) {
      return $alert.removeClass('alert-success').find('span').text(msg).end().addClass('alert-error').show();
    };
    return displaySuccess = function(msg) {
      return $alert.removeClass('alert-error').find('span').text(msg).end().addClass('alert-success').show();
    };
  });

}).call(this);
