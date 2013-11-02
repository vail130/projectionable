define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/editor/editor.html'
  'controllers/projects/project-editor-toggle-link'
  'controllers/projects/project-editor-section'
  'controllers/projects/project-editor-reports-modal'
  'controllers/projects/project-editor-configure-modal'
  'controllers/projects/project-editor-collaborate-modal'
  'models/permission'
  'models/session'
], ($, _, Spine, projectEditorTemplate, ToggleLink, ProjectSection,
  ReportsModal, ConfigureModal, CollaborateModal, Permission, Session) ->

  class ProjectEditor extends Spine.Controller
    constructor: ->
      super
      @toggleLinks = {}
      @sections = {}
      
      @project.bind 'update', @render
      
      @bind('hide', (key) =>
        if @sections.hasOwnProperty key
          @sections[key].hide()
          @resetWidths()
      ).bind('show', (key) =>
        if @sections.hasOwnProperty key
          @sections[key].show()
          @resetWidths()
      )
    
    className: 'project-editor'
    
    textData:
      front: 'Front-End Views & Stories'
      back: 'API Endpoints & Stories'
      assets: 'Asset Deliverables'
      files: 'Project Files'
    
    elements:
      '.section-toggle-link-list' : '$sectionToggleLinkList'
      '.section-list' : '$sectionList'
      '.configure-button' : '$configureButton'
      '.collaborate-button' : '$collaborateButton'
      '.reports-button' : '$reportsButton'
      '.configure-modal' : '$configureModal'
      '.collaborate-modal' : '$collaborateModal'
      '.reports-modal' : '$reportsModal'
    
    resetWidths: =>
      numActive = _.reduce(
        _.values(@sections),
        (memo, obj) -> memo + (if obj.isHidden() then 0 else 1),
        0
      )
      
      if 0 < numActive < 5
        classes = ['whole', 'half', 'third', 'quarter']
        first = false
        _.each @sections, (obj) =>
          _.each _.union(classes, ['first']), (cls) => obj.$el.removeClass cls
          obj.$el.addClass classes[numActive-1]
          if not first and not obj.isHidden()
            obj.$el.addClass 'first'
            first = true
      @
    
    addAllSections: =>
      # Use an array to ensure order
      for key in ['front', 'back', 'assets', 'files']
        $linkLI = $('<li></li>')
        $sectionLI = $('<li></li>')
        
        @toggleLinks[key] = new ToggleLink
          parent: @
          key: key
          textData: @textData[key]
          el: $linkLI
        @$sectionToggleLinkList.append @toggleLinks[key].render().$el.addClass('active').get(0)
        
        @sections[key] = new ProjectSection
          parent: @
          key: key
          textData: @textData[key]
          el: $sectionLI
        @$sectionList.append @sections[key].render().$el.addClass('quarter active').get(0)
      @
    
    addReportsModal: =>
      @reportsModal = new ReportsModal
        parent: @
      @$reportsModal.html @reportsModal.render().el
      @
    
    addConfigureModal: =>
      @configureModal = new ConfigureModal
        parent: @
      @$configureModal.html @configureModal.render().el
      @
    
    addCollaborateModal: =>
      p = _.where Permission.all(),
        project_id: @project.id
        account_id: Session.first().id
        permission: 'owner'
      
      if p.length > 0
        @collaborateModal = new CollaborateModal
          parent: @
        @$collaborateModal.html @collaborateModal.render().el
      
      @
    
    getContext: =>
      project: @project
      permission: _.where(Permission.all(), {project_id: @project.id, account_id: Session.first().id})[0].permission
    
    render: =>
      @html _.template projectEditorTemplate, @getContext()
      @addAllSections().addReportsModal().addConfigureModal().addCollaborateModal().resetWidths()

