define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/editor/editor-requirement.html'
  'text!views/projects/editor/editor-asset.html'
  'text!views/projects/editor/editor-file.html'
  'models/permission'
], ($, _, Spine, requirementTemplate, assetTemplate, fileTemplate, Permission) ->

  class SectionItem extends Spine.Controller
    constructor: ->
      super
    
    tag: 'li'
    className: 'section-item'
    
    elements:
      '.item-display' : '$itemDisplay'
      '.item-progress' : '$itemProgress'
      '.item-edit-button' : '$itemEditButton'
      '.item-edit-form' : '$itemEditForm'
      '.item-title' : '$itemTitle'
      '.item-status-select' : '$itemStatusSelect'
      '.item-hours-input' : '$itemHoursInput'
      '.item-requester-select' : '$itemRequesterSelect'
    
    getContext: =>
      item: @item
      key: @key
      permissions: _.sortBy Permission.findAllByAttribute('project_id', @item.project_id), 'email'
    
    render: =>
      if @key in ['front', 'back']
        @html _.template requirementTemplate, @getContext()
      else if @key is 'assets'
        @html _.template assetTemplate, @getContext()
      else if @key is 'files'
        @html _.template fileTemplate, @getContext()
      
      if typeof @item.title is 'undefined' or @item.title is ''
        @$itemEditButton.trigger 'click'
      
      else if @key in ['front', 'back', 'assets']
        @initLabelProgressBar()
      
      @
    
    initLabelProgressBar: =>
      percent = parseInt(@$itemProgress.data 'percent')
      @$itemProgress.css 'width', percent + '%'
      @
    
    events:
      'click .item-edit-button' : 'editItem'
      'click .item-delete-button' : 'deleteItem'
      'click .item-cancel-button' : 'cancelEditItem'
      'click .item-save-button' : 'saveItem'
      'click .item-start-button' : 'startItem'
      'click .item-pause-button' : 'pauseItem'
      'click .item-finish-button' : 'finishItem'
      'click .item-approve-button' : 'approveItem'
      'click .item-reject-button' : 'rejectItem'
      'click .item-revert-button' : 'revertItem'
    
    deleteItem: (event) =>
      event.preventDefault()
      @item.destroy()
    
    editItem: (event) =>
      event.preventDefault()
      @$itemDisplay.hide()
      @$itemEditForm.show().find('textarea').first().get(0).focus()
    
    cancelEditItem: (event) =>
      event.preventDefault()
      @render()
      
    saveItem: (event) =>
      event.preventDefault()
      hours = parseFloat(@$itemHoursInput.val())
      @item.updateAttributes
        title: (if @$itemTitle.length is 1 then @$itemTitle.val() else '')
        status: @$itemStatusSelect.val()
        hours: (if isNaN(hours) then 0 else hours)
        requester: @$itemRequesterSelect.val()
      @render()
    
    startItem: (event) =>
      event.preventDefault()
      @item.updateAttribute 'status', 'working'
      @render()
    
    pauseItem: (event) =>
      event.preventDefault()
      @item.updateAttribute 'status', 'pending'
      @render()

    finishItem: (event) =>
      event.preventDefault()
      @item.updateAttribute 'status', 'complete'
      @render()

    rejectItem: (event) =>
      event.preventDefault()
      @item.updateAttribute 'status', 'rejected'
      @render()

    approveItem: (event) =>
      event.preventDefault()
      @item.updateAttribute 'status', 'approved'
      @render()

    revertItem: (event) =>
      event.preventDefault()
      @item.updateAttribute 'status', 'pending'
      @render()


