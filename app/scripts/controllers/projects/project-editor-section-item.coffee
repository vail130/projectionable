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
      '.item-danger' : '$itemDanger'
      '.item-edit-button' : '$itemEditButton'
      '.item-edit-form' : '$itemEditForm'
      '.item-title' : '$itemTitle'
      '.item-status-select' : '$itemStatusSelect'
      '.item-hours-input' : '$itemHoursInput'
      '.item-requester-select' : '$itemRequesterSelect'
      '.item-deliverable-input' : '$itemDeliverableInput'
    
    getContext: =>
      if @key in ['assets', 'files'] and @item.asset_url isnt ''
        asset_url_parts = @item.asset_url.split('/')
        filename = asset_url_parts[asset_url_parts.length-1]
        
        fileNameData = filename.split '.'
        ext = fileNameData[fileNameData.length - 1]
        basename = filename.substr(0, filename.length - (ext.length + 1))
        
        if basename.length > 20 and @key is 'assets'
          basename = basename.substr(0, 10) + '...' + basename.substr(basename.length - 5)
        
        file_size = @item.file_size
        if file_size > 1000000000
          file_size = Math.round(file_size/1000000000) + 'gb'
        else if file_size > 1000000
          file_size = Math.round(file_size/1000000) + 'mb'
        else if file_size > 1000
          file_size = Math.round(file_size/1000) + 'kb'
        
        filename = "#{basename}.#{ext} (#{file_size})" 
      else
        filename = ''
      
      item: @item
      key: @key
      permissions: _.sortBy Permission.findAllByAttribute('project_id', @item.project_id), 'email'
      filename: filename
    
    render: =>
      @$el.addClass @key
      if @key in ['front', 'back']
        @html _.template requirementTemplate, @getContext()
      else if @key is 'assets'
        @html _.template assetTemplate, @getContext()
        @initFileUpload()
      else if @key is 'files'
        @html _.template fileTemplate, @getContext()
        @initFileUpload()
      
      if typeof @item.title is 'undefined' or @item.title is ''
        @$itemEditButton.trigger 'click'
      
      else if @key in ['front', 'back', 'assets']
        @initLabelProgressBar()
      
      @
    
    initLabelProgressBar: =>
      percent = parseInt(@$itemProgress.data 'percent')
      @$itemProgress.css 'width', percent + '%'
      if percent > 100
        @$itemDanger.css 'width', (percent - 100) + '%'
      @
    
    initFileUpload: =>
      @$itemDeliverableInput.fileupload
        type: 'POST'
        url: "/api/#{@key}/#{@item.id}"
        dataType: 'json'
        paramName: 'asset'
        dropZone: @$itemDeliverableInput.parent()
        drop: (event, data) =>
          true
        submit: (e, data) =>
          if data.files[0].type not in ['image/png', 'image/gif', 'image/jpeg']
            false

          else if data.files[0].size > 33554432
            false

        send: =>
        done: =>
      @
    
    events:
      'click .item-edit-button' : 'editItem'
      'click .item-delete-button' : 'deleteItem'
      'click .item-cancel-button' : 'cancelEditItem'
      'click .item-save-button' : 'saveItem'
      'click .asset-upload-button' : 'triggerFileInput'
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
      @$itemEditForm.show().find('textarea').first().get(0)?.focus()
    
    cancelEditItem: (event) =>
      event.preventDefault()
      @render()
      
    saveItem: (event) =>
      event.preventDefault()
      hours = parseFloat(@$itemHoursInput.val())
      requester_id = parseInt(@$itemRequesterSelect.val())
      @item.updateAttributes
        title: (if @$itemTitle.length is 1 then @$itemTitle.val() else '')
        status: @$itemStatusSelect.val()
        hours: (if isNaN(hours) then 0 else hours)
        requester_id: (if isNaN(requester_id) then null else requester_id)
      @render()
    
    triggerFileInput: (event) =>
      event.preventDefault()
      @$itemDeliverableInput.trigger 'click'
    
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


