class Projectionable.Editor extends Spine.Controller
  constructor: ->
    super
    App.Editor = @
    
    @routes
      '/editor': (params) =>
        if App.project is null or not App.project.__proto__.hasOwnProperty('id')
          @navigate '/manager'
        else
          @project = App.project
          @render().active()
          App.trigger 'renderNavigation', 'editor'
          
    @bind 'calculateHours', =>
      hours = 0
      _.each @children, (child) =>
        if not isNaN(parseFloat(child.group.hours)) and not child.$el.find('.edit-group-form').hasClass('rejected')
          hours += parseFloat(child.group.hours)
      @project.hours = hours
      @$hoursDisplay.text "#{App.formatNumber(hours)}"
      dollars = parseFloat(@project.rate) * parseFloat(hours)
      dollarText = if isNaN(dollars) then ' --' else App.formatNumber(dollars)
      @$dollarsDisplay.text "$#{dollarText}"
      
  className: 'work-editor'
  
  elements:
    '.project-title-input' : '$titleInput'
    '.project-rate-input' : '$rateInput'
    '.project-groups' : '$groupList'
    '.project-hours' : '$hoursDisplay'
    '.project-dollars' : '$dollarsDisplay'
    '.start-button' : '$startButton'
    '.sharing-button' : '$sharingButton'
    '.permissions-modal-container' : '$permissionModalContainer'
  
  events:
    'blur .project-title-input' : 'saveTitle'
    'blur .project-rate-input' : 'saveRate'
    
  saveTitle: (event) =>
    title = @$titleInput.val()
    if title isnt @project.title
      @project.updateAttribute 'title', title
  
  saveRate: (event) =>
    rate = parseFloat(@$rateInput.val())
    if not isNaN(rate) and rate isnt @project.rate
      @trigger 'calculateHours'
      @project.updateAttribute 'rate', rate
  
  new: (event=null) ->
    event.preventDefault() if event isnt null
    group = RequirementGroup.create App.makeGroupTemplate(@project.id, RequirementGroup.findAllByAttribute('project_id', @project.id).length)
    @addOne group
  
  addOne: (group) =>
    controller = new WorkGroup
      parent: @
      group: group
    @children.push controller
    @$groupList.append controller.render().el

  addAll: =>
    groups = _.sortBy(RequirementGroup.findAllByAttribute('project_id', @project.id), 'index')
    @$groupList.empty()
    @children = []
    
    if groups.length > 0
      @addOne group for group in groups
      
    if @project.status is 'pending'
      group = App.makeGroupTemplate(@project.id, groups.length)
      @addOne group
    @
  
  assessStartable: =>
    if @project.permission is 'client'
      enable = true
      _.each RequirementGroup.findAllByAttribute('project_id', @project.id), (group) ->
        enable = false if group.status in ['pending', 'requested']
      _.each Requirement.findAllByAttribute('project_id', @project.id), (req) ->
        enable = false if req.status in ['pending', 'requested']
      
      if enable is true
        @$startButton.removeClass('disabled').off('click').on 'click', @startProject
    @
      
  startProject: (event) =>
    event.preventDefault()
    return if @$startButton.hasClass 'disabled'
    
    @project.status = 'started'
    @project.updateAttribute 'status', 'started'
    @render()
    
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
            groups.push RequirementGroup.findByAttribute('id', groupID)
        
        _.each groups, (group, index) => group.updateAttribute 'index', index
    
    @$groupList.sortable sortableOptions
    @
  
  getContext: =>
    project: @project
    permissions: Permission.findAllByAttribute 'project_id', @project.id
    groups: RequirementGroup.findAllByAttribute 'project_id', @project.id
  
  render: =>
    @html(@view('work_editor_editor')(@getContext()))
    $('#work-editor').html @$el
    
    @addAll().assessStartable().initSortable()
    
    if @project.permission is 'owner'
      @permissionModal = new WorkPermissionModal
        parent: @
      @$permissionModalContainer.html @permissionModal.render().el
      @$sharingButton.off('click').on 'click', (event) =>
        event.preventDefault()
        @permissionModal.trigger 'showSharingModal'
    
    setTimeout (=>
      focused = false
      $('.project-groups input').each ->
        if not focused and this.value is ''
          this.focus()
          focused = true
      ), 1
  
    @
    
class WorkPermissionModal extends Spine.Controller
  constructor: ->
    super
    @bind 'showSharingModal', @showSharingModal
  
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
    perm = Permission.create
      email: $.trim(@$coworkerInput.val())
      project_id: @parent.project.id
      permission: 'coworker'
    @addAllPermissions()
    @$coworkerInput.val('')
  
  inviteClient: (event) =>
    event.preventDefault()
    return if @$clientButton.hasClass 'disabled'
    perm = Permission.create
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
    permissions = Permission.findAllByAttribute('project_id', @parent.project.id)
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
  
  showSharingModal: =>
    @$sharingModal.fadeIn 500, =>
      @$sharingModal.find('input').first().get(0).focus()
    
    if @parent.project.client_enabled is false
      setTimeout @showStripeButton, 10
    
  hideSharingModal: (event=null) =>
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
    project: @parent.project
    permission: @permission
    type: @type
  
  render: =>
    if @parent.project.permission is 'owner' 
      @html(@view('work_editor_editor-permission')(@getContext()))
    @
    
class WorkGroup extends Spine.Controller
  constructor: ->
    super
    
    @bind 'calculateHours', =>
      hours = 0
      _.each @children, (child) =>
        if not isNaN(parseFloat(child.requirement.hours)) and not child.$el.find('.edit-requirement-form').hasClass('rejected')
          hours += parseFloat(child.requirement.hours)
      @group.hours = hours
      @$hoursDisplay.text "#{App.formatNumber(hours)}"
      dollars = parseFloat(@parent.project.rate) * parseFloat(hours)
      dollarText = if isNaN(dollars) then ' --' else App.formatNumber(dollars)
      @$dollarsDisplay.text "$#{dollarText}"
      @parent.trigger 'calculateHours'
      
  tag: 'li'
  className: 'edit-group-wrapper clearfix'
  
  elements:
    '.group-title-input' : '$titleInput'
    '.group-hours' : '$hoursDisplay'
    '.group-dollars' : '$dollarsDisplay'
    '.edit-group-form-body' : '$groupBody'
    '.group-requirements' : '$reqList'
    '.group-delete-wrapper' : '$deleteWrapper'
    '.group-delete-link' : '$deleteLink'
    '.group-status-wrapper' : '$statusWrapper'
    '.group-approve-button' : '$approveButton'
    '.group-reject-button' : '$rejectButton'
    '.owner-delete-group' : '$ownerDeleteLink'
    '.owner-revert-group' : '$ownerRevertLink'
    '.client-revert-group' : '$clientRevertLink'
    '.client-approve-group' : '$clientApproveLink'
    '.client-reject-group' : '$clientRejectLink'
    
  addOne: (req) =>
    controller = new WorkRequirement
      parent: @
      requirement: req
    @children.push controller
    @$reqList.append controller.render().el
  
  addAll: =>
    requirements = _.sortBy(Requirement.findAllByAttribute('group_id', @group.id), 'index')
    @$reqList.empty()
    @children = []
    
    if requirements.length > 0
      @$groupBody.addClass 'active'
      @addOne req for req in requirements
      
    if @group.__proto__.hasOwnProperty('id') and @parent.project.status is 'pending' and @group.status isnt 'rejected'
      @$groupBody.addClass 'active'
      req = App.makeRequirementTemplate @group.id, requirements.length
      @addOne req
    
    @trigger 'calculateHours'
    @
    
  createNewGroup: =>
    title = $.trim(@$titleInput.val())
    return if title is ''
    
    @$titleInput.off 'keyup'
    
    $.extend(@group, {title: title})
    @group = RequirementGroup.create @group
    
    group = App.makeGroupTemplate @parent.project.id, RequirementGroup.findAllByAttribute('project_id', @parent.project.id).length
    @parent.addOne group
    
    @$groupBody.add(@$deleteWrapper).add(@$statusWrapper).addClass 'active'
    @$titleInput.on 'blur', @saveTitle
    @$deleteLink.on 'click', @deleteRequirement
    
    # This ensures that the requirement will be created with a valid group ID
    @group.one 'ajaxSuccess', =>
      req = App.makeRequirementTemplate @group.id, 0
      @addOne req
    
    @group.trigger 'update'
  
  saveTitle: =>
    title = @$titleInput.val()
    return if title is @group.title
    @group.updateAttribute 'title', title
  
  approveGroup: (event) =>
    event.preventDefault()
    return if @$approveButton.hasClass 'disabled'
    
    @group.status = 'approved'
    @$titleInput.attr('readonly', 'readonly').off('keyup')
    @$approveButton.add(@$rejectButton).addClass 'disabled'
    @group.updateAttribute 'status', 'approved'
    @render()
    @parent.assessStartable()
    @trigger 'calculateHours'
  
  rejectGroup: (event) =>
    event.preventDefault()
    return if @$rejectButton.hasClass 'disabled'
    
    @group.status = 'rejected'
    @$titleInput.attr('readonly', 'readonly').off('keyup')
    @$approveButton.add(@$rejectButton).addClass 'disabled'
    
    @group.updateAttribute 'status', 'rejected'
    _.each Requirement.findAllByAttribute('group_id', @group.id), (req) => req.status = 'rejected'
    @render()
    @parent.assessStartable()
    @trigger 'calculateHours'
  
  deleteGroup: (event) =>
    event.preventDefault()
    index = @group.index
    @group.destroy() if @group.__proto__.hasOwnProperty('id')
    @release()
    
    @trigger 'calculateHours'
    if @parent.project.status is 'started'
      @parent.project.updateAttribute 'status', 'pending'
      @parent.project.render()
    else
      @render()
      @parent.assessStartable()
  
  revertGroup: (event) =>
    event.preventDefault()
    @group.status = 'pending'
    @group.updateAttribute 'status', 'pending'
    
    @trigger 'calculateHours'
    if @parent.project.status is 'started'
      @parent.project.updateAttribute 'status', 'pending'
      @parent.project.render()
    else
      @render()
      @parent.assessStartable()
  
  clientRevertGroup: (event) =>
    event.preventDefault()
    @group.status = 'requested'
    @group.updateAttribute 'status', 'requested'
    
    @trigger 'calculateHours'
    if @parent.project.status is 'started'
      @parent.project.updateAttribute 'status', 'pending'
      @parent.project.render()
    else
      @render()
      @parent.assessStartable()
  
  clientApproveGroup: (event) =>
    event.preventDefault()
    @group.status = 'approved'
    @group.updateAttribute 'status', 'approved'
    
    @trigger 'calculateHours'
    if @parent.project.status is 'started'
      @parent.project.updateAttribute 'status', 'pending'
      @parent.project.render()
    else
      @render()
      @parent.assessStartable()
  
  clientRejectGroup: (event) =>
    event.preventDefault()
    @group.status = 'rejected'
    @group.updateAttribute 'status', 'rejected'
    
    @trigger 'calculateHours'
    if @parent.project.status is 'started'
      @parent.project.updateAttribute 'status', 'pending'
      @parent.project.render()
    else
      @render()
      @parent.assessStartable()
  
  getContext: =>
    project: @parent.project
    group: @group
  
  render: =>
    context = @getContext()
    @$el.attr 'data-group-id', @group.id
    @html(@view('work_editor_editor-group')(context))
    
    @addAll()
    
    if @parent.project.status is 'pending'
      if not @group.__proto__.hasOwnProperty('id')
        @$titleInput.on 'keyup', @createNewGroup
      
      else if @parent.project.permission in ['owner', 'coworker']
        if @group.status is 'pending'
          @$titleInput.on 'blur', @saveTitle
          @$deleteLink.on 'click', @deleteGroup
        
        else if @group.status is 'requested'
          @$approveButton.on 'click', @approveGroup
          @$rejectButton.on 'click', @rejectGroup
      
      else if @parent.project.permission is 'client'
        if @group.status is 'requested'
          @$titleInput.on 'blur', @saveTitle
          @$deleteLink.on 'click', @deleteGroup
        
        else if @group.status is 'pending'
          @$approveButton.on 'click', @approveGroup
          @$rejectButton.on 'click', @rejectGroup
      
    if @parent.project.permission is 'owner'
      @$ownerRevertLink.click @revertGroup
      @$ownerDeleteLink.click @deleteGroup
      
    else if @parent.project.permission is 'client'
      @$clientRevertLink.click @clientRevertGroup
    
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
    @requirement = Requirement.create @requirement
    
    req = App.makeRequirementTemplate @parent.group.id, Requirement.findAllByAttribute('group_id', @parent.group.id).length
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
      @parent.render()
    else
      @render()
      @parent.parent.assessStartable()
  
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
      @parent.parent.project.render()
    else
      @render()
      @parent.parent.assessStartable()
  
  revertRequirement: (event) =>
    event.preventDefault()
    @requirement.status = 'pending'
    @requirement.updateAttribute 'status', 'pending'
    
    @parent.trigger 'calculateHours'
    if @parent.parent.project.status is 'started'
      @parent.parent.project.updateAttribute 'status', 'pending'
      @parent.parent.project.render()
    else
      @render()
      @parent.parent.assessStartable()
  
  clientRevertRequirement: (event) =>
    event.preventDefault()
    @requirement.status = 'requested'
    @requirement.updateAttribute 'status', 'requested'
    
    @parent.trigger 'calculateHours'
    if @parent.parent.project.status is 'started'
      @parent.parent.project.updateAttribute 'status', 'pending'
      @parent.parent.project.render()
    else
      @render()
      @parent.parent.assessStartable()
  
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
      @parent.parent.project.render()
    else
      @parent.render()
      @parent.parent.assessStartable()
  
  clientRejectRequirement: (event) =>
    event.preventDefault()
    @requirement.status = 'rejected'
    @requirement.updateAttribute 'status', 'rejected'
    
    @parent.trigger 'calculateHours'
    if @parent.parent.project.status is 'started'
      @parent.parent.project.updateAttribute 'status', 'pending'
      @parent.parent.project.render()
    else
      @render()
      @parent.parent.assessStartable()
  
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

