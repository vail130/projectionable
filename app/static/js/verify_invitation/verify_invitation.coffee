$ ->
  
  $formBody = $ '.verify-invitation-form .proj-form-body'
  $formInputs = $formBody.find '> input'
  $alert = $formBody.find '> .alert'
  $account_id = $ '#account_id'
  $code = $ '#code'
  $password1 = $ '#password1'
  $password2 = $ '#password2'
  $submitButton = $formBody.find '.verify-invitation-button'
  
  focused = false
  $formInputs.each ->
    if not focused and this.value is ''
      this.focus()
      focused = true
  
  $code.add($password1).add($password2).keypress (event) ->
    code = if event.keyCode then event.keyCode else event.charCode
    if code is 13
      $submitButton.trigger 'click'
  
  $submitButton.click (event) ->
    event.preventDefault()
    
    code = $code.val()
    if code is ''
      displayError 'Missing code field'
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
    
    $submitButton.button 'loading'
    $alert.hide()
    
    $.ajax
      type: 'PUT'
      dataType: 'json'
      contentType: 'application/json'
      url: '/api/accounts/' + $account_id.val()
      data:
        JSON.stringify
          action: 'verify_invitation'
          code: code
          password: password1
      success: (json) =>
        displaySuccess 'Logging in...'
        setTimeout (-> window.location.href = 'http://' + window.location.host), 750
      error: (jqXHR) =>
        json = JSON.parse(jqXHR.responseText)
        displayError json[_.keys(JSON.parse(jqXHR.responseText))[0]]
      complete: (jqXHR) =>
        $submitButton.button 'reset'
        $formInputs.get(0).focus()
    
  displayError = (msg) ->
    $alert
      .removeClass('alert-success')
      .find('span').text(msg)
      .end().find('strong').text('Error')
      .end().addClass('alert-error').show()
  
  displaySuccess = (msg) ->
    $alert
      .removeClass('alert-error')
      .find('span').text(msg)
      .end().find('strong').text('Success')
      .end().addClass('alert-success').show()
  
