$ ->

  $formBody = $ '.signin-form .proj-form-body'
  $formInputs = $formBody.children 'input'
  $alert = $formBody.children '.alert'
  $email = $ '#email'
  $password = $ '#password'
  $signinButton = $formBody.find '.signin-button'
  $forgotPasswordButton = $formBody.find '.forgot-password-button'
  
  $formInputs.first().get(0).focus()

  $formInputs.on('keypress', (event) ->
    code = if event.keyCode then event.keyCode else event.charCode
    if code is 13
      $signinButton.trigger 'click'
  ).on 'keyup blur', (event) ->
    if $email.val().match(/^[\w\.%\+-]+@[A-Z0-9\.-]+\.[A-Z]{2,4}(?:\.[A-Z]{2,4})?$/i) isnt null
      $forgotPasswordButton.removeClass 'disabled'
    else
      $forgotPasswordButton.addClass 'disabled'
  
  $signinButton.on 'click', (event) ->
    event.preventDefault()
    
    email = $email.val()
    if email is ''
      displayError 'Missing email field'
      $formInputs.get(0).focus()
      return
    
    password = $password.val()
    if password is ''
      displayError 'Missing password field'
      $formInputs.get(1).focus()
      return
  
    $signinButton.button 'loading'
    
    $.ajax
      type: 'POST'
      dataType: 'json'
      contentType: 'application/json'
      url: '/api/sessions'
      data:
        JSON.stringify
          email: email
          password: password
      success: (json) =>
        displaySuccess 'Logging in...'
        $formBody.children().not('.alert').hide().filter('input').val('')
        setTimeout (-> window.location.href = 'http://' + window.location.host), 750
      error: (jqXHR) =>
        try
          displayError _.pairs(JSON.parse(jqXHR.responseText))[0][1]
        catch e
          displayError jqXHR.statusText
        $signinButton.button 'reset'
        $formInputs.get(0).focus()
  
  $forgotPasswordButton.on 'click', (event) ->
    event.preventDefault()
    email = $email.val()
    if email.match(/^[\w\.%\+-]+@[A-Z0-9\.-]+\.[A-Z]{2,4}(?:\.[A-Z]{2,4})?$/i) is null
      displayError 'Invald email address.'
      $formInputs.get(0).focus()
      return
    
    $forgotPasswordButton.button 'loading'
    
    $.ajax
      type: 'PUT'
      dataType: 'json'
      contentType: 'application/json'
      url: '/api/accounts'
      data:
        JSON.stringify
          email: email
          action: 'request_password_reset'
      success: (json) =>
        displaySuccess 'Please check your email to reset your password.'
      error: (jqXHR) =>
        try
          displayError _.pairs(JSON.parse(jqXHR.responseText))[0][1]
        catch e
          displayError jqXHR.statusText
        $formInputs.get(0).focus()
        $forgotPasswordButton.button 'reset'
      
  displayError = (msg) ->
    $alert
      .removeClass('alert-success')
      .find('span').text(msg)
      .end().addClass('alert-error').show()
  
  displaySuccess = (msg) ->
    $alert
      .removeClass('alert-error')
      .find('span').text(msg)
      .end().addClass('alert-success').show()
  
