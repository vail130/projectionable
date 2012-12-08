define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/work-structure.html'
  'controllers/projects/project-manager'
  'controllers/projects/project-editor'
  'models/project'
], ($, _, Spine, workStructureTemplate, ProjectManager, ProjectEditor, Project) ->

  class Work extends Spine.Controller
    constructor: ->
      super
      
      @routes
        '/projects': =>
          @render().activate()
          App.navigation.render()
          @projectManager.render().activate()
          
        '/projects/:id': (params) =>
          project = Project.findByAttribute('id', parseInt(params.id))
          if typeof project is 'undefined'
            @navigate '/projects'
          else
            @render().activate()
            App.navigation.render()
            @projectManager.deactivate()
            @projectEditor?.release()
            @projectEditor = new ProjectEditor
              parent: @
              el: @$el.children('.project-editor')
              project: project
            @projectEditor.render().activate()
    
    className: 'work main-stack'
    
    render: =>
      @html workStructureTemplate
      $('#app-body').append @$el
      
      @projectEditor = null
      @projectManager = new ProjectManager
        el: @$el.children('.project-manager')
        parent: @
      
      @

  ###
  class GroupManager extends Spine.Controller
    constructor: ->
      super
      @children = []
    
    className: 'group-container'
    
    elements:
      '.group-list' : '$groupList'
    
    addOne: (group) =>
      controller = new ProjectGroup
        parent: @
        group: group
      @children.push controller
      @$groupList.append controller.render().el
  
    addAll: =>
      groups = _.sortBy(Projectionable.RequirementGroup.findAllByAttribute('project_id', @parent.project.id), 'index')
      @$groupList.empty()
      @children = []
      
      if groups.length > 0
        @addOne group for group in groups
        
      if @project.status is 'pending'
        group = App.makeGroupTemplate(@project.id, groups.length)
        @addOne group
      @
    
    initSortable: =>
      sortableOptions =
        axis: 'y'
        containment: 'parent'
        scrollSensitivity: 100
        stop: =>
          groups = []
          @$groupList.children('li').each (index, el) =>
            groupID = parseInt($(el).data('group-id'))
            if not isNaN groupID
              groups.push Projectionable.RequirementGroup.findByAttribute('id', groupID)
          
          _.each groups, (group, index) => group.updateAttribute 'index', index
      
      @$groupList.sortable sortableOptions
      @
    
    getContext: =>
      project: @parent.project
      type: @type
      groups: _.sortBy(Projectionable.RequirementGroup.findAllByAttribute('project_id', @project.id), 'index')
    
    render: =>
      @html(@view('work_editor-group-manager')(@getContext()))
      @
  
  class StoryWorkView extends Spine.Controller
    constructor: ->
      super
      
    tag: 'li'
    className: ''
    
    elements:
      '.group-title-input' : '$titleInput'
      '.group-delete-button' : '$deleteLink'
      
    saveTitle: =>
      title = @$titleInput.val()
      return if title is @group.title
      @group.updateAttribute 'title', title
    
    deleteGroup: (event) =>
      event.preventDefault()
      index = @group.index
      @group.destroy() if @group.__proto__.hasOwnProperty('id')
      @release()
      
      if @parent.project.status is 'started'
        @parent.project.updateAttribute 'status', 'pending'
      @parent.render()
    
    getContext: =>
      project: @parent.project
      group: @group
    
    render: =>
      @html(@view('work_editor_editor-group')(@getContext()))
      @
  
  class WorkRequirement extends Spine.Controller
    constructor: ->
      super
      
    tag: 'li'
    className: 'edit-req-wrapper clearfix'
    
    elements:
      '.requirement-title-input' : '$titleInput'
      '.requirement-hours-input' : '$hoursInput'
      '.requirement-dollars' : '$dollarsDisplay'
      '.requirement-delete-wrapper' : '$deleteWrapper'
      '.requirement-delete-link' : '$deleteLink'
      '.requirement-status-wrapper' : '$statusWrapper'
      '.requirement-approve-button' : '$approveButton'
      '.requirement-reject-button' : '$rejectButton'
      '.owner-delete-requirement' : '$ownerDeleteLink'
      '.owner-revert-requirement' : '$ownerRevertLink'
      '.client-revert-requirement' : '$clientRevertLink'
      '.client-approve-requirement' : '$clientApproveLink'
      '.client-reject-requirement' : '$clientRejectLink'
    
    arrowToggle: (event) =>
      code = if event.keyCode then event.keyCode else event.charCode
      switch code
        when 38 #up
          console.log 'up'
        when 40 #down
          console.log 'down'
    
    createNewRequirement: =>
      title = $.trim(@$titleInput.val())
      return if title is ''
      
      @$titleInput.off 'keyup'
      hours = parseFloat($.trim(@$hoursInput.val()))
      hours = 0 if isNaN(hours)
      
      $.extend(@requirement, {title: title, hours: hours})
      @requirement = Projectionable.Requirement.create @requirement
      
      req = App.makeRequirementTemplate @parent.group.id, Projectionable.Requirement.findAllByAttribute('group_id', @parent.group.id).length
      @parent.addOne req
      
      @$deleteWrapper.add(@$statusWrapper).addClass 'active'
      @$titleInput.on 'blur', @saveTitle
      @$deleteLink.on 'click', @deleteRequirement
      
      if @parent.parent.project.permission in ['owner', 'coworker']
        @$hoursInput.on 'blur', @saveHours
    
    saveTitle: =>
      title = @$titleInput.val()
      return if title is @requirement.title
      @requirement.updateAttribute 'title', title
    
    saveHours: =>
      return if @$hoursInput.attr('readonly') is 'readonly'
      hours = parseFloat($.trim(@$hoursInput.val()))
      
      @requirement.updateAttribute 'hours', hours
      @parent.trigger 'calculateHours'
      
      dollars = parseFloat(@parent.parent.project.rate)*parseFloat(hours)
      if isNaN(dollars) or @requirement.status is 'rejected'
        dollars = ' --'
      else
        dollars = App.formatNumber(dollars)
      @$dollarsDisplay.text "$#{dollars}"
      
    updateApproveButtonStatus: =>
      return if @$hoursInput.attr('readonly') is 'readonly'
      hours = parseFloat($.trim(@$hoursInput.val()))
      oldHours = @requirement.hours
      
      # If agent just added hours to a Req that didn't have an estimate, enable approve button
      if not isNaN(hours) and isNaN(parseFloat(oldHours))
        @$approveButton.removeClass 'disabled'
        
      # If hours are removed, disabled approve button
      else if isNaN(hours) and not isNaN(parseFloat(oldHours))
        @$approveButton.addClass 'disabled'
    
    approveRequirement: (event) =>
      event.preventDefault()
      return if @$approveButton.hasClass 'disabled'
      
      @requirement.status = 'approved'
      @$titleInput.add(@$hoursInput).attr('readonly', 'readonly').off('keyup')
      @$approveButton.add(@$rejectButton).addClass 'disabled'
      @requirement.updateAttribute 'status', 'approved'
      
      @parent.trigger 'calculateHours'
      if @parent.group.status isnt 'approved'
        @parent.group.status = 'approved'
      @parent.parent.render()
    
    rejectRequirement: (event) =>
      event.preventDefault()
      return if @$rejectButton.hasClass 'disabled'
      
      @requirement.status = 'rejected'
      @$titleInput.add(@$hoursInput).attr('readonly', 'readonly').off('keyup')
      @$approveButton.add(@$rejectButton).addClass 'disabled'
      @requirement.updateAttribute 'status', 'rejected'
      @render()
      @parent.parent.assessStartable()
      @parent.trigger 'calculateHours'
    
    deleteRequirement: (event) =>
      event.preventDefault()
      index = @requirement.index
      @requirement.destroy() if @requirement.__proto__.hasOwnProperty('id')
      @release()
      @parent.trigger 'calculateHours'
      
      if @parent.parent.project.status is 'started'
        @parent.parent.project.updateAttribute 'status', 'pending'
      @parent.parent.render()
    
    revertRequirement: (event) =>
      event.preventDefault()
      @requirement.status = 'pending'
      @requirement.updateAttribute 'status', 'pending'
      
      @parent.trigger 'calculateHours'
      if @parent.parent.project.status is 'started'
        @parent.parent.project.updateAttribute 'status', 'pending'
      @parent.parent.render()
    
    clientRevertRequirement: (event) =>
      event.preventDefault()
      @requirement.status = 'requested'
      @requirement.updateAttribute 'status', 'requested'
      
      @parent.trigger 'calculateHours'
      if @parent.parent.project.status is 'started'
        @parent.parent.project.updateAttribute 'status', 'pending'
      @parent.parent.render()
    
    clientApproveRequirement: (event) =>
      event.preventDefault()
      
      if not isNaN(parseFloat(@requirement.hours))
        @requirement.status = 'approved'
        @requirement.updateAttribute 'status', 'approved'
      else
        @requirement.status = 'requested'
        @requirement.updateAttribute 'status', 'requested'
      
      if @parent.group.status isnt 'approved'
        @parent.group.status = 'approved'
        
      @parent.trigger 'calculateHours'
      if @parent.parent.project.status is 'started'
        @parent.parent.project.updateAttribute 'status', 'pending'
      @parent.parent.render()
    
    clientRejectRequirement: (event) =>
      event.preventDefault()
      @requirement.status = 'rejected'
      @requirement.updateAttribute 'status', 'rejected'
      
      @parent.trigger 'calculateHours'
      if @parent.parent.project.status is 'started'
        @parent.parent.project.updateAttribute 'status', 'pending'
      @parent.parent.render()
    
    getContext: =>
      project: @parent.parent.project
      group: @parent.group
      req: @requirement
    
    render: =>
      context = @getContext()
      @$el.attr 'data-req-id', @requirement.id
      @html(@view('work_editor_editor-requirement')(context))
      
      if @parent.parent.project.status is 'pending'
        if not @requirement.__proto__.hasOwnProperty('id')
          @$titleInput.on 'keyup', @createNewRequirement
        
        else if @parent.parent.project.permission in ['owner', 'coworker']
          if @requirement.status is 'pending'
            @$titleInput.on 'blur', @saveTitle
            @$hoursInput.on 'blur', @saveHours
            @$hoursInput.on 'keyup', @updateApproveButtonStatus
            @$deleteLink.on 'click', @deleteRequirement
          
          else if @requirement.status is 'requested'
            @$hoursInput.on 'blur', @saveHours
            @$hoursInput.on 'keyup', @updateApproveButtonStatus
            @$approveButton.on 'click', @approveRequirement
            @$rejectButton.on 'click', @rejectRequirement
        
        else if @parent.parent.project.permission is 'client'
          if @requirement.status is 'requested'
            @$titleInput.on 'blur', @saveTitle
            @$deleteLink.on 'click', @deleteRequirement
          
          else if @requirement.status is 'pending'
            @$approveButton.on 'click', @approveRequirement
            @$rejectButton.on 'click', @rejectRequirement
        
      if @parent.parent.project.permission is 'owner'
        @$ownerRevertLink.click @revertRequirement
        @$ownerDeleteLink.click @deleteRequirement
        
      else if @parent.parent.project.permission is 'client'
        @$clientRevertLink.click @clientRevertRequirement
        @$clientApproveLink.click @clientApproveRequirement
        @$clientRejectLink.click @clientRejectRequirement
      
      @
  
  class CollaborateModal extends Spine.Controller
    constructor: ->
      super
    
    elements:
      '.sharing-modal-close-button' : '$sharingModalCloseButton'
      '.sharing-modal' : '$sharingModal'
      '.sharing-modal-shadow' : '$sharingModalShadow'
      '.coworker-input' : '$coworkerInput'
      '.client-input' : '$clientInput'
      '.invite-coworker-button' : '$coworkerButton'
      '.invite-client-button' : '$clientButton'
      '.coworker-list' : '$coworkerList'
      '.client-list' : '$clientList'
    
    events:
      'keyup .coworker-input' : 'validateNewCoworker'
      'keyup .client-input' : 'validateNewClient'
      'keypress .coworker-input' : 'coworkerInputEnter'
      'keypress .client-input' : 'clientInputEnter'
      'click .invite-coworker-button' : 'inviteCoworker'
      'click .invite-client-button' : 'inviteClient'
      
    inviteCoworker: (event) =>
      event.preventDefault()
      return if @$coworkerButton.hasClass 'disabled'
      perm = Projectionable.Permission.create
        email: $.trim(@$coworkerInput.val())
        project_id: @parent.project.id
        permission: 'coworker'
      @addAllPermissions()
      @$coworkerInput.val('')
    
    inviteClient: (event) =>
      event.preventDefault()
      return if @$clientButton.hasClass 'disabled'
      perm = Projectionable.Permission.create
        email: $.trim(@$clientInput.val())
        project_id: @parent.project.id
        permission: 'client'
      @addAllPermissions()
      @$clientInput.val('')
    
    coworkerInputEnter: (event) =>
      code = if event.charCode then event.charCode else event.keyCode
      if code is 13
        @$coworkerButton.trigger 'click'
      
    clientInputEnter: (event) =>
      code = if event.charCode then event.charCode else event.keyCode
      if code is 13
        @$clientButton.trigger 'click'
      
    validateNewCoworker: =>
      if @validateEmail @$coworkerInput.val()
        @$coworkerButton.removeClass 'disabled'
      else
        @$coworkerButton.addClass 'disabled'
      
    validateNewClient: =>
      if @validateEmail @$clientInput.val()
        @$clientButton.removeClass 'disabled'
      else
        @$clientButton.addClass 'disabled'
        
    validateEmail: (email) =>
      email.toString().search(/^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$/) > -1
      
    addOneClient: (client) =>
      controller = new WorkPermission
        parent: @
        permission: client
        type: 'client'
      @$clientList.append controller.render().el
  
    addOneCoworker: (coworker) =>
      controller = new WorkPermission
        parent: @
        permission: coworker
        type: 'coworker'
      @$coworkerList.append controller.render().el
  
    addAllPermissions: =>
      @$coworkerList.empty()
      permissions = Projectionable.Permission.findAllByAttribute('project_id', @parent.project.id)
      coworkers = _.where permissions, {permission: 'coworker'}
      if coworkers.length > 0
        @addOneCoworker coworker for coworker in coworkers
      else
        @$coworkerList.html "<div class='permission empty'><span>No coworkers.</span></div>"
      
      if @parent.project.client_enabled is true
        @$clientList.empty()
        clients = _.where permissions, {permission: 'client'}
        if clients.length > 0
          @addOneClient client for client in clients
        else
          @$clientList.html "<div class='permission empty'><span>No clients.</span></div>"
      
      @
    
    show: =>
      @$sharingModal.fadeIn 500, =>
        @$sharingModal.find('input').first().get(0).focus()
      
      if @parent.project.client_enabled is false
        setTimeout @showStripeButton, 10
      
    hide: (event=null) =>
      event.preventDefault() if event isnt null
      $('#stripe-button-container').fadeOut 500
      @$sharingModal.fadeOut 500, => @hideStripeButton()
        
    showStripeButton: =>
      offset = @$sharingModal.find('.right-half').offset()
      $('#stripe-button-container').css(
        display: 'none'
        top: offset.top + 100
        left: offset.left
      ).fadeIn 490
      @
      
    hideStripeButton: =>
      $('#stripe-button-container').css(
        top: -100
        left: -200
      )
      @
    
    enableClient: (event) =>
      event.preventDefault()
      @parent.project.updateAttribute 'client_enabled', true
      @hideStripeButton().render().showSharingModal()
    
    getContext: =>
      project: @parent.project
    
    render: =>
      @html(@view('work_editor_editor-permission-modal')(@getContext()))
      @addAllPermissions()
      @$sharingModalCloseButton.off('click').on 'click', @hideSharingModal
      @$sharingModalShadow.off('click').on 'click', @hideSharingModal
      
      $('#stripe-button-container .enable-client-button').off('click').on 'click', @enableClient
      
      @
  
  class WorkPermission extends Spine.Controller
    constructor: ->
      super
      
    tag: 'li'
    className: 'permission clearfix'
    
    events:
      'click .remove-link' : 'deletePermission'
      
    deletePermission: (event) =>
      event.preventDefault()
      @permission.destroy()
      @release()
      @parent.addAllPermissions()
      @
    
    getContext: =>
      project: @parent.parent.project
      permission: @permission
      type: @type
    
    render: =>
      if @parent.parent.project.permission is 'owner' 
        @html(@view('work_editor_editor-permission')(@getContext()))
      @
      
  ###