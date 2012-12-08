define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/editor/editor.html'
  'controllers/projects/project-editor-toggle-link'
  'controllers/projects/project-editor-section'
  'controllers/projects/project-editor-collaborate-modal'
], ($, _, Spine, projectEditorTemplate, ToggleLink, ProjectSection, CollaborateModal) ->

  class ProjectEditor extends Spine.Controller
    constructor: ->
      super
      @toggleLinks = {}
      @sections = {}
      
      @bind('hide', (key) =>
        @sections[key]?.hide()
        
      ).bind('show', (key) =>
        @sections[key]?.show()
        
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
      '.configure-modal' : '$collaborateModal'
      '.collaborate-modal' : '$collaborateModal'
      '.reports-modal' : '$reportsModal'
    
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
        @$sectionList.append @sections[key].render().$el.addClass('active').get(0)
      @
    
    addAllModals: =>
      if @project.permission is 'owner'
        @collaborateModal = new CollaborateModal
          parent: @
        @$collaborateModal.html @collaborateModal.render().el
      
      @
    
    getContext: =>
      project: @project
    
    render: =>
      @html _.template projectEditorTemplate, @getContext()
      @addAllSections().addAllModals()
      @
    
    events:
      'click .collaborate-button' : 'openCollaborateModal'
    
    openCollaborateModal: (event) =>
      event.preventDefault()
      @collaborateModal.show()

