define [
  'jquery'
  'underscore'
  'spine'
  'text!views/settings/settings-credentials.html'
  'models/account'
], ($, _, Spine, credentialsTemplate, Account) ->
  
  class Credentials extends Spine.Controller
    constructor: ->
      super
      
    className: 'credentials'
    
    elements:
      '.new-email-message' : '$newEmailMessage'
      '.new-email-input' : '$newEmailInput'
      '.new-email-password-input' : '$newEmailPasswordInput'
      '.new-email-button' : '$newEmailButton'
      '.new-password-message' : '$newPasswordMessage'
      '.new-password-current-input' : '$newPasswordCurrentInput'
      '.new-password-new-input' : '$newPasswordNewInput'
      '.new-password-verify-input' : '$newPasswordVerifyInput'
      '.new-password-button' : '$newPasswordButton'
    
    events:
      'keyup .new-email-input' : 'updateNewEmailButtonStatus'
      'keyup .new-email-password-input' : 'updateNewEmailButtonStatus'
      'click .new-email-button' : 'submitNewEmail'
      'keyup .new-password-current-input' : 'updateNewPasswordButtonStatus'
      'keyup .new-password-new-input' : 'updateNewPasswordButtonStatus'
      'keyup .new-password-verify-input' : 'updateNewPasswordButtonStatus'
      'click .new-password-button' : 'submitNewPassword'
    
    updateNewEmailButtonStatus: (event) =>
      code = if event.keyCode then event.keyCode else event.charCode
      if code is 13
        @$newEmailButton.trigger 'click'
      else if '' in [$.trim(@$newEmailInput.val()), @$newEmailPasswordInput.val()]
        @$newEmailButton.addClass 'disabled'
      else
        @$newEmailButton.removeClass 'disabled'
    
    submitNewEmail: (event) =>
      event.preventDefault()
      return if @$newEmailButton.hasClass 'disabled'
      
      @$newEmailMessage.hide().text('').removeClass('alert-error alert-success')
      
      email = $.trim(@$newEmailInput.val())
      password = @$newEmailPasswordInput.val()
      
      if email.search(/^.+@.+\..+$/) is -1
        @$newEmailMessage.addClass('alert-error').text('Invalid email address').show()
        @$newEmailInput.get(0).focus()
        @$newEmailButton.addClass 'disabled'
        return
      
      payload =
        action: 'change_email'
        password: password
        email: email
      
      @updateAccount payload
    
    updateNewPasswordButtonStatus: (event) =>
      code = if event.keyCode then event.keyCode else event.charCode
      if code is 13
        @$newPasswordButton.trigger 'click'
      else if '' in [@$newPasswordCurrentInput.val(), @$newPasswordNewInput.val(), @$newPasswordVerifyInput.val()]
        @$newPasswordButton.addClass 'disabled'
      else
        @$newPasswordButton.removeClass 'disabled'
    
    submitNewPassword: (event) =>
      event.preventDefault()
      return if @$newPasswordButton.hasClass 'disabled'
      
      @$newPasswordMessage.hide().text('').removeClass('alert-error alert-success')
      
      current = @$newPasswordCurrentInput.val()
      newPass = @$newPasswordNewInput.val()
      verify = @$newPasswordVerifyInput.val()
      
      if newPass isnt verify
        @$newPasswordMessage.addClass('alert-error').text('Mismatching passwords').show()
        @$newPasswordNewInput.get(0).focus()
        @$newPasswordButton.addClass 'disabled'
        return
      
      @$newPasswordButton.button 'loading'
      
      payload =
        action: 'change_password'
        old_password: current
        new_password: newPass
      
      @updateAccount payload
    
    updateAccount: (payload) =>
      
      switch payload.action
        when 'change_email'
          $message = @$newEmailMessage
          successText = 'Please check your email to confirm your new address.'
          $fields = @$newEmailInput.add @$newEmailPasswordInput
          $button = @$newEmailButton
        when 'change_password'
          $message = @$newPasswordMessage
          successText = 'Your password has been changed successfully.'
          $fields = @$newPasswordCurrentInput.add(@$newPasswordNewInput).add(@$newPasswordVerifyInput)
          $button = @$newPasswordButton
      
      @lock = new App.Lock el: @parent.$wrapper
      @lock.start()
      
      $.ajax
        url: '/api/accounts/' + Account.findByAttribute('id', window.sessionID)
        type: 'PUT'
        contentType: 'application/json'
        data: JSON.stringify payload
        success: =>
          $message.addClass('alert-success').text(successText).show()
          $fields.each -> @value = ''
        error: (jqXHR) =>
          response = JSON.parse(jqXHR.responseText)
          $message.addClass('alert-error').text(response[_.keys(response)[0]]).show()
        complete: =>
          @lock.stop().remove()
          $button.button('reset').addClass('disabled')
      
      @
    
    getContext: =>
      account: Account.findByAttribute('id', window.sessionID)
    
    render: =>
      @html _.template credentialsTemplate, @getContext()
      
      @$newEmailMessage.add(@$newPasswordMessage).hide()
      
      @
  
