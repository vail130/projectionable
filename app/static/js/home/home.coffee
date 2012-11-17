$ ->
  
  $formBody = $ '.trial-form .proj-form-body'
  $formInputs = $formBody.find '> input'
  $alert = $formBody.find '> .alert'
  $email = $ '#email'
  $password1 = $ '#password1'
  $password2 = $ '#password2'
  $signupButton = $formBody.find '.signup-button'
  
  $formInputs.first().get(0).focus()
  
  $email.add($password1).add($password2).keypress (event) ->
    code = if event.keyCode then event.keyCode else event.charCode
    if code is 13
      $signupButton.trigger 'click'
  
  $signupButton.click (event) ->
    event.preventDefault()
    
    email = $email.val()
    if email is ''
      displayError 'Missing email field'
      $formInputs.get(0).focus()
      return
    
    password1 = $password1.val()
    password2 = $password2.val()
    if password1 is ''
      displayError 'Missing password field'
      $formInputs.get(1).focus()
      return
    else if password2 is ''
      displayError 'Missing password field'
      $formInputs.get(2).focus()
      return
    else if password1 isnt password2
      displayError 'Mismatching password fields'
      $formInputs.get(1).focus()
      return
    
    $signupButton.button 'loading'
    $alert.hide()
    
    $.ajax
      type: 'POST'
      dataType: 'json'
      contentType: 'application/json'
      url: '/api/accounts'
      data:
        JSON.stringify
          email: email
          password: password1
      success: (json) =>
        displaySuccess 'Thank you! Please check your email to activate your account.'
        $formBody.children().not('.alert').hide().filter('input').val('')
      error: (jqXHR) =>
        try
          displayError _.pairs(JSON.parse(jqXHR.responseText))[0][1]
        catch e
          displayError jqXHR.statusText
        $formInputs.get(0).focus()
        $signupButton.button 'reset'
    
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
  
