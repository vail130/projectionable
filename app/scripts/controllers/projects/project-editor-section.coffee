define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/editor/section.html'
  'models/requirementgroup'
  'models/projectasset'
  'models/projectfile'
  'controllers/projects/project-editor-section-group'
  'controllers/projects/project-editor-section-item'
], ($, _, Spine, sectionTemplate, RequirementGroup, ProjectAsset, ProjectFile, SectionGroup, SectionItem) ->
  
  class ProjectSection extends Spine.Controller
    constructor: ->
      super
    
    className: 'project-editor-section'
    
    elements:
      '.section-group-list' : '$sectionGroupList'
      '.new-button' : '$newButton'
    
    hide: =>
      @$el.removeClass 'active'
      @
    
    show: =>
      @$el.addClass 'active'
      @
    
    getContext: =>
      key: @key
      text: @textData
    
    render: =>
      @html _.template sectionTemplate, @getContext()
      @addAllItems()
    
    addAllItems: =>
      switch @key
        when 'front'
          records = _.sortBy _.where(
            RequirementGroup.findAllByAttribute('project_id', @parent.project.id),
            {'type': 'front_end'}
          ), 'index'
        when 'back'
          records = _.sortBy _.where(
            RequirementGroup.findAllByAttribute('project_id', @parent.project.id),
            {'type': 'back_end'}
          ), 'index'
        when 'assets'
          records = _.sortBy ProjectAsset.findAllByAttribute('project_id', @parent.project.id), 'index'
        when 'files'
          records = _.sortBy ProjectFile.findAllByAttribute('project_id', @parent.project.id), (file) -> -file.unix_updated
      
      for record in records
        if @key in ['front', 'back']
          controller = new SectionGroup
            parent: @
            key: @key
            group: record
        else
          controller = new SectionItem
            parent: @
            key: @key
            item: record
        
        @$sectionGroupList.append controller.render().el
      
      @
    
    events:
      'click .new-button' : 'addNewListItem'
    
    addNewListItem: (event) =>
      event.preventDefault()
      switch @key
        when 'front'
          record = RequirementGroup.create
            project_id: @parent.project.id
            type: 'front_end'
          
          controller = new SectionGroup
            parent: @
            key: @key
            group: record
        when 'back'
          record = RequirementGroup.create
            project_id: @parent.project.id
            type: 'back_end'
          
          controller = new SectionGroup
            parent: @
            key: @key
            group: record
        when 'assets'
          record = ProjectAsset.create
            project_id: @parent.project.id
          
          controller = new SectionItem
            parent: @
            key: @key
            item: record
        when 'files'
          record = ProjectFile.create
            project_id: @parent.project.id
          
          controller = new SectionItem
            parent: @
            key: @key
            item: record
      
      @$sectionGroupList.append controller.render().el
      

