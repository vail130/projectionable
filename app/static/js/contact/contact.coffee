$ ->
  
  $formBody = $ '.contact-form .proj-form-body'
  $formInputs = $formBody.find '> input'
  $alert = $formBody.find '> .alert'
  $replyTo = $ '#reply-to'
  $subject = $ '#subject'
  $message = $ '#message'
  $submitButton = $formBody.find '.submit-button'
  
  focused = false
  $formInputs.each ->
    if not focused and this.value is ''
      this.focus()
      focused = true
  
  $submitButton.click (event) ->
    event.preventDefault()
    
    replyTo = $replyTo.val()
    if replyTo is ''
      displayError 'Missing reply-to field'
      $formInputs.get(0).focus()
      return
    
    subject = $subject.val()
    if subject is ''
      displayError 'Missing subject field'
      $formInputs.get(1).focus()
      return
    
    message = $message.val()
    if message is ''
      displayError 'Missing message field'
      $formBody.find('textarea').get(0).focus()
      return
    
    $submitButton.button 'loading'
    $alert.hide()
    
    $.ajax
      type: 'POST'
      dataType: 'json'
      contentType: 'application/json'
      url: '/api/contacts/'
      data:
        JSON.stringify
          replyTo: replyTo
          subject: subject
          message: message
      success: (json) =>
        displaySuccess 'Thank you for your contact.'
        $formBody.children().not('.alert').hide().filter('input, textarea').val('')
      error: (jqXHR) =>
        json = JSON.parse(jqXHR.responseText)
        displayError json[_.keys(JSON.parse(jqXHR.responseText))[0]]
        $submitButton.button 'reset'
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
  
