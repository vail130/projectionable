$ ->
  
  $formBody = $ '.home-form .proj-form-body'
  $alert = $formBody.find '> .alert'
  
  $signinInputs = $formBody.find '.home-signin > input'
  $signinEmail = $ '#signin-email'
  $password = $ '#password'
  $signinButton = $formBody.find '.signin-button'
  
  $signupInputs = $formBody.find '.home-signup > input'
  $signupEmail = $ '#signup-email'
  $password1 = $ '#password1'
  $password2 = $ '#password2'
  $signupButton = $formBody.find '.signup-button'
  
  $signupInputs.first().get(0).focus()
  
  $showSigninButton = $ '.home-form .proj-form-head .show-signin-button'
  $showSignupButton = $ '.home-form .proj-form-head .show-signup-button'
  
  $showSigninButton.click (event) ->
    event.preventDefault()
    $showSigninButton.parent().toggleClass 'active'
    $formBody.toggleClass 'active'
    $alert.hide()
    $signinInputs.first().get(0).focus()
  
  $showSignupButton.click (event) ->
    event.preventDefault()
    $showSignupButton.parent().toggleClass 'active'
    $formBody.toggleClass 'active'
    $alert.hide()
    $signupInputs.first().get(0).focus()
  
  $signupEmail.add($password1).add($password2).keypress (event) ->
    code = if event.keyCode then event.keyCode else event.charCode
    if code is 13
      $signupButton.trigger 'click'
  
  $signupButton.click (event) ->
    event.preventDefault()
    
    email = $signupEmail.val()
    if email is ''
      displayError 'Missing email field'
      $signupInputs.get(0).focus()
      return
    
    password1 = $password1.val()
    password2 = $password2.val()
    if password1 is ''
      displayError 'Missing password field'
      $signupInputs.get(1).focus()
      return
    else if password2 is ''
      displayError 'Missing password field'
      $signupInputs.get(2).focus()
      return
    else if password1 isnt password2
      displayError 'Mismatching password fields'
      $signupInputs.get(1).focus()
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
        $signupInputs.get(0).focus()
        $signupButton.button 'reset'
    
  $signinEmail.add($password).keypress (event) ->
    code = if event.keyCode then event.keyCode else event.charCode
    if code is 13
      $signinButton.trigger 'click'
  
  $signinButton.click (event) ->
    event.preventDefault()
    
    email = $signinEmail.val()
    if email is ''
      displayError 'Missing email field'
      $signinInputs.get(0).focus()
      return
    
    password = $password.val()
    if password1 is ''
      displayError 'Missing password field'
      $signinInputs.get(1).focus()
      return
    
    $signinButton.button 'loading'
    $alert.hide()
    
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
  
