$ ->
  
  $formBody = $ '.verify-email-form .proj-form-body'
  $formInputs = $formBody.find '> input'
  $alert = $formBody.find '> .alert'
  $account_id = $ '#account_id'
  $code = $ '#code'
  $submitButton = $formBody.find '.verify-email-button'
  
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
    
    $submitButton.button 'loading'
    $alert.hide()
    
    $.ajax
      type: 'PUT'
      dataType: 'json'
      contentType: 'application/json'
      url: '/api/accounts/' + $account_id.val()
      data:
        JSON.stringify
          action: 'verify_email'
          code: code
      success: (json) =>
        displaySuccess 'Redirecting to sign in...'
        setTimeout (-> window.location.href = 'http://' + window.location.host + '/signin'), 750
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
      
  if $code.val() isnt ''
    $submitButton.trigger 'click'
  
