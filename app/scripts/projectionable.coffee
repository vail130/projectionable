
define [
  'jquery'
  'underscore'
  'spine'
  'text!views/structure.html'
  'controllers/lock'
  'controllers/navigation'
  'controllers/footer'
  'models/account'
  'models/permission'
  'models/project'
  'models/projectasset'
  'models/projectfile'
  'models/requirementgroup'
  'models/requirement'
  'models/session'
], ($, _, Spine, structureTemplate, Lock, Navigation, Footer, Account, Permission,
    Project, ProjectAsset, ProjectFile, RequirementGroup, Requirement, Session) ->
  
  class Projectionable extends Spine.Controller
    constructor: ->
      super
      @html structureTemplate
      
      @Lock = Lock
      @navigation = new Navigation el: $('#navigation')
      @navigation.render()
      @footer = new Footer el: $('#footer')
      @footer.render()
      #@contact = new Contact
      
      sessionDeferred = $.Deferred()
      sessionPromise = sessionDeferred.promise()
      
      Session.one 'refresh', => sessionDeferred.resolve()
      Session.fetch()
      
      $.when(
        sessionPromise
      ).done =>
        masterDeferred = $.Deferred()
        @masterPromise = masterDeferred.promise()
        
        if Session.first().id?
          @loadData =>
            masterDeferred.resolve()
            if window.location.hash in ['', '#']
              window.location.hash = '#/projects'
        
        else
          masterDeferred.resolve()
          if window.location.hash in ['', '#']
            window.location.hash = '#/home'
    
    loadData: (callback) =>
      accountDeferred = $.Deferred()
      Account.one 'refresh', => accountDeferred.resolve()
      
      permissionDeferred = $.Deferred()
      Permission.one 'refresh', => permissionDeferred.resolve()
      
      projectDeferred = $.Deferred()
      Project.one 'refresh', => projectDeferred.resolve()
      
      reqGroupDeferred = $.Deferred()
      RequirementGroup.one 'refresh', => reqGroupDeferred.resolve()
      
      reqDeferred = $.Deferred()
      Requirement.one 'refresh', => reqDeferred.resolve()
      
      assetDeferred = $.Deferred()
      ProjectAsset.one 'refresh', => assetDeferred.resolve()
      
      fileDeferred = $.Deferred()
      ProjectFile.one 'refresh', => fileDeferred.resolve()
      
      Account.fetch()
      Project.fetch()
      Permission.fetch()
      RequirementGroup.fetch()
      Requirement.fetch()
      ProjectAsset.fetch()
      ProjectFile.fetch()
      
      $.when(
        accountDeferred, permissionDeferred, reqGroupDeferred, reqDeferred, assetDeferred, fileDeferred
      ).done =>
        @navigation.render()
        callback?()
      
      @
    
    makeProjectTemplate: ->
      account_id: ""
      title: ""
      rate: ""
      deadline: ""
      budget: ""
      hours: ""
      hours_worked: ""
      date_updated: ""
      date_created: ""
    
    makePermissionTemplate: (email, project_id) ->
      email: email
      project_id: project_id
    
    makeGroupTemplate: (pid, idx=0) ->
      project_id: pid
      title: ""
      status: ""
      index: idx
      hours: ""
      hours_worked: ""
      date_updated: ""
      date_created: ""
    
    makeRequirementTemplate: (gid, idx=0) ->
      project_id: ""
      group_id: gid
      title: ""
      status: ""
      index: idx
      hours: ""
      hours_worked: ""
      date_updated: ""
      date_created: ""
    
    makeModelTemplate: (pid, idx=0) ->
      project_id: pid
      title: ""
      endpoint: ""
      index: idx
      date_updated: ""
      date_created: ""
    
    makeFieldTemplate: (mid, idx=0) ->
      project_id: ""
      model_id: mid
      title: ""
      note: ""
      index: idx
      date_updated: ""
      date_created: ""
    
    formatNumber: (number) ->
      return '' if typeof(number) is 'undefined'
      
      parts = number.toString().split '.'
      decimal = parts[1] || ''
      number = parts[0]
      
      negative = false
      if number.substr(0, 1) is '-'
        negative = true
        number = number.substr(1)
      
      number = number.replace /[^0-9]/ig, ''
      decimal = decimal.replace /[^0-9]/ig, ''
      output = ''
      while number.length > 0
        output = ',' + output if output.length > 0
        
        if number.length > 3
          output = number.substr(-3, 3) + output
          number = number.substr(0, number.length - 3)
        else
          output = number + output
          number = ''
      
      output =  '-'+output if negative
      output += '.'+decimal if decimal.length > 0
      output
  
  ###
  class Contact extends Spine.Controller
    constructor: ->
      @el = $('#contact')
      super
      @render()
    
    elements:
      '.contact-modal' : '$contactModal'
      '.contact-tab-link' : '$contactTabLink'
      '.contact-reply-to-input' : '$replyTo'
      '.contact-subject-input' : '$subject'
      '.contact-message-textarea' : '$message'
      '.contact-submit-button' : '$submitButton'
      '.contact-alert' : '$alert'
    
    events:
      'click .contact-modal-close-button' : 'hideContactModal'
      'click .contact-modal-shadow' : 'hideContactModal'
      'click .contact-tab-link' : 'showContactModal'
      'click .contact-submit-button' : 'submitContact'
    
    showContactModal: (event) =>
      @$contactModal.fadeIn 500, =>
        @$contactModal.find('input').first().get(0).focus()
    
    hideContactModal: (event=null) =>
      event.preventDefault() if event isnt null
      @$contactModal.fadeOut 500
    
    submitContact: (event) =>
      event.preventDefault()
      
      replyTo = $.trim(@$replyTo.val())
      if replyTo is ''
        @displayError 'Missing reply-to field'
        @$replyTo.val('').get(0).focus()
        return
      
      subject = $.trim(@$subject.val())
      if subject is ''
        @displayError 'Missing subject field'
        @$subject.val('').get(0).focus()
        return
      
      message = $.trim(@$message.val())
      if message is ''
        @displayError 'Missing message field'
        @$message.val('').get(0).focus()
        return
      
      @$submitButton.button 'loading'
      @$alert.hide()
      
      $.ajax
        type: 'POST'
        dataType: 'json'
        contentType: 'application/json'
        url: '/api/contacts/'
        data:
          JSON.stringify
            reply_to: replyTo
            subject: subject
            message: message
        success: (json) =>
          @displaySuccess 'Thank you for your contact.'
          @$contactModal.find('.proj-modal-body').children().not('.alert').hide().filter('input, textarea').val('')
          setTimeout @hideContactModal, 3000
        error: (jqXHR) =>
          try
            @displayError _.pairs(JSON.parse(jqXHR.responseText))[0][1]
          catch e
            @displayError jqXHR.statusText
          @$submitButton.button 'reset'
          @$replyTo.get(0).focus()
    
    displayError: (msg) ->
      @$alert
        .removeClass('alert-success')
        .children('span').text(msg)
        .end().addClass('alert-error').show()
      @
    
    displaySuccess: (msg) ->
      @$alert
        .removeClass('alert-error')
        .children('span').text(msg)
        .end().addClass('alert-success').show()
      @
    
    render: =>
      @html @view 'contact'
      @
  
  ###
