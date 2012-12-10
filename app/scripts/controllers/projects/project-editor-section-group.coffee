define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/editor/editor-group.html'
  'models/requirementgroup'
  'models/requirement'
  'controllers/projects/project-editor-section-item'
], ($, _, Spine, groupTemplate, RequirementGroup, Requirement, SectionItem) ->

  class SectionGroup extends Spine.Controller
    constructor: ->
      super
      Requirement.bind 'destroy', @render
    
    tag: 'li'
    className: 'section-group'
    
    elements:
      '.group-title-row' : '$groupTitleRow'
      '.group-edit-button' : '$groupEditButton'
      '.section-item-list' : '$sectionItemList'
      '.group-edit-form' : '$groupEditForm'
      '.group-title' : '$groupTitle'
      '.group-uri' : '$groupURI'
      '.group-method' : '$groupMethod'
      '.new-item-button' : '$newItemButton'
    
    addAllItems: =>
      @$sectionItemList.empty()
      records = _.sortBy Requirement.findAllByAttribute('group_id', @group.id), 'index'
      for record in records
        controller = new SectionItem
          parent: @
          key: @key
          item: record
        @$sectionItemList.append controller.render().el
      
      if records.length is 0
        @$sectionItemList.append $("<li class='no-items'><span>No stories yet.</span></li>")
      
      @
    
    getContext: =>
      group: @group
      key: @key
    
    render: =>
      @html _.template groupTemplate, @getContext()
      @addAllItems()
      
      triggerClick = true
      for p in ['title', 'uri', 'method']
        if typeof @group[p] isnt 'undefined' and @group[p] isnt ''
          triggerClick = false
      
      @$groupEditButton.trigger 'click'  if triggerClick
      @
    
    events:
      'click .group-edit-button' : 'editGroup'
      'click .group-delete-button' : 'deleteGroup'
      'click .group-cancel-button' : 'cancelEditGroup'
      'click .group-save-button' : 'saveGroup'
      'click .new-item-button' : 'addNewStory'
    
    editGroup: (event) =>
      event.preventDefault()
      @$groupTitleRow.add(@$sectionItemList).hide()
      @$groupEditForm.show().find('input').first().get(0).focus()
    
    cancelEditGroup: (event) =>
      event.preventDefault()
      @render()
      
    saveGroup: (event) =>
      event.preventDefault()
      @group.updateAttributes
        title: (if @$groupTitle.length is 1 then @$groupTitle.val() else '')
        uri: (if @$groupURI.length is 1 then @$groupURI.val() else '')
        method: (if @$groupMethod.length is 1 then @$groupMethod.val() else '')
      @render()
    
    deleteGroup: (event) =>
      event.preventDefault()
      @group.destroy()
    
    addNewStory: (event) =>
      event.preventDefault()
      records = Requirement.findAllByAttribute('group_id', @group.id)
      record = Requirement.create
        group_id: @group.id
        hours: 0
        hours_worked: 0
        status: 'pending'
        index: RequirementGroup.findAllByAttribute('project_id', @parent.parent.project.id).length
      
      controller = new SectionItem
        parent: @
        key: @key
        item: record
      
      if records.length is 0
        @$sectionItemList.empty()
      @$sectionItemList.append controller.render().el

