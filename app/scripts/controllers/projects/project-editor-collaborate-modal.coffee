define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/editor/collaborate-modal.html'
  'models/permission'
  'controllers/projects/project-editor-collaborate-modal-permission'
], ($, _, Spine, collaborateModalTemplate, Permission, CollaborateModalPermission) ->

  class CollaborateModal extends Spine.Controller
    constructor: ->
      super
      Permission.bind 'destroy', @addAllPermissions
    
    emailRegEx: /^[^@]+@[^.]+\..+$/
    
    elements:
      '.coworker-list' : '$coworkerList'
      '.client-list' : '$clientList'
      '.invite-coworker-button' : '$inviteCoworkerButton'
      '.invite-client-button' : '$inviteClientButton'
      '.client-input' : '$clientInput'
      '.coworker-input' : '$coworkerInput'
    
    addAllPermissions: =>
      permissions = _.sortBy Permission.findAllByAttribute('project_id', @parent.project.id), (p) -> -p.unix_updated
      
      @$coworkerList.empty()
      for p in _.where permissions, {permission: 'coworker'}
        @addPermission p, @$coworkerList
      
      @$clientList.empty()
      for p in _.where permissions, {permission: 'client'}
        @addPermission p, @$clientList
      
      @
    
    addPermission: (p, $list) =>
      controller = new CollaborateModalPermission
        parent: @
        permission: p
      $list.append controller.render().el
    
    isProjectPermissionEmail: (email) =>
      _.where(Permission.findAllByAttribute('project_id', @parent.project.id), {email: email}).length > 0
    
    getContext: =>
      {}
    
    render: =>
      @html _.template collaborateModalTemplate, @getContext()
      @addAllPermissions()
    
    events:
      'keyup .coworker-input' : 'updateCoworkerButton'
      'click .invite-coworker-button' : 'inviteCoworker'
      'keyup .client-input' : 'updateClientButton'
      'click .invite-client-button' : 'inviteClient'
    
    updateCoworkerButton: (event) =>
      code = if event.keyCode then event.keyCode else event.charCode
      if code is 13
        @$inviteCoworkerButton.trigger 'click'
      else
        if @$coworkerInput.val().search(@emailRegEx) is -1
          @$inviteCoworkerButton.addClass 'disabled'
        else
          @$inviteCoworkerButton.removeClass 'disabled'
    
    inviteCoworker: (event) =>
      event.preventDefault()
      return if @$inviteCoworkerButton.hasClass 'disabled'
      email = @$coworkerInput.val()
      
      if email is '' or email.search(@emailRegEx) is -1
        return @$inviteCoworkerButton.addClass 'disabled'
      
      if @isProjectPermissionEmail email
        return @$inviteClientButton.addClass 'disabled'
      
      p = Permission.create
        email: email
        project_id: @parent.project.id
        permission: 'coworker'
      @addPermission p, @$coworkerList
      
      @$coworkerInput.val ''
      @$inviteCoworkerButton.addClass 'disabled'
    
    updateClientButton: (event) =>
      code = if event.keyCode then event.keyCode else event.charCode
      if code is 13
        @$inviteClientButton.trigger 'click'
      else
        if @$clientInput.val().search(@emailRegEx) is -1
          @$inviteClientButton.addClass 'disabled'
        else
          @$inviteClientButton.removeClass 'disabled'
    
    inviteClient: (event) =>
      event.preventDefault()
      return if @$inviteClientButton.hasClass 'disabled'
      email = @$clientInput.val()
      
      if email is '' or email.search(@emailRegEx) is -1
        return @$inviteClientButton.addClass 'disabled'
      
      if @isProjectPermissionEmail email
        return @$inviteClientButton.addClass 'disabled'
      
      p = Permission.create
        email: email
        project_id: @parent.project.id
        permission: 'client'
      @addPermission p, @$clientList
      
      @$clientInput.val ''
      @$inviteClientButton.addClass 'disabled'
    

