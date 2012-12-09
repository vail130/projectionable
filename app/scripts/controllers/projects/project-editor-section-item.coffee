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
      '.item-edit-button' : '$itemEditButton'
      '.item-edit-form' : '$itemEditForm'
      '.item-title' : '$itemTitle'
    
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
      @
    
    events:
      'click .item-edit-button' : 'editItem'
      'click .item-delete-button' : 'deleteItem'
      'click .item-cancel-button' : 'cancelEditItem'
      'click .item-save-button' : 'saveItem'
    
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
      @item.updateAttributes
        title: (if @$itemTitle.length is 1 then @$itemTitle.val() else '')
      @render()
    


