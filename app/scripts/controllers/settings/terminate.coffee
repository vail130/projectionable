define [
  'jquery'
  'underscore'
  'spine'
  'text!views/settings/settings-terminate.html'
  'models/account'
], ($, _, Spine, terminateTemplate, Account) ->
  
  class Terminate extends Spine.Controller
    constructor: ->
      super
      
    className: 'terminate'
    
    elements:
      '.terminate-message' : '$terminateMessage'
      '.terminate-password-input' : '$terminatePasswordInput'
      '.terminate-button' : '$terminateButton'
    
    events:
      'keyup .terminate-password-input' : 'updateTerminateButtonStatus'
      'click .terminate-button' : 'submitTermination'
    
    updateTerminateButtonStatus: (event) =>
      code = if event.keyCode then event.keyCode else event.charCode
      if code is 13
        @$terminateButton.trigger 'click'
      else if '' is @$terminatePasswordInput.val()
        @$terminateButton.addClass 'disabled'
      else
        @$terminateButton.removeClass 'disabled'
    
    submitTermination: (event) =>
      event.preventDefault()
      return if @$terminateButton.hasClass 'disabled'
      
      @$terminateMessage.hide().text('').removeClass('alert-error alert-success')
      password = @$terminatePasswordInput.val()
      @lock = new App.Lock el: @parent.$wrapper
      @lock.start()
      
      $.ajax
        url: '/api/accounts/' + Account.findByAttribute('id', window.sessionID) + '?password=' +password
        type: 'DELETE'
        success: =>
          $message.addClass('alert-success').text('Your account was successfully delete...').show()
          @$terminatePasswordInput.val('')
          setTimeout (=> @navigate '/exit' ), 1000
        error: (jqXHR) =>
          response = JSON.parse(jqXHR.responseText)
          @$terminatePasswordInput.val('').get(0).focus()
          @$terminateMessage.addClass('alert-error').text(response[_.keys(response)[0]]).show()
        complete: =>
          @lock.stop().remove()
          @$terminateButton.button('reset').addClass('disabled')
      
      @
    
    getContext: =>
      {}
    
    render: =>
      @html _.template terminateTemplate, @getContext()
      @
  
