define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/manager/manager.html'
  'models/project'
  'controllers/projects/project-preview'
  'text!views/projects/manager/manager-no-previews.html'
], ($, _, Spine, projectManagerTemplate, Project, ProjectPreview, projectManagerNoPreviewsTemplate) ->

  class ProjectManager extends Spine.Controller
    constructor: ->
      super
      Project.bind 'refresh change', @addAll
    
    elements:
      'ul.project-list': '$projectList'
      '.new-project-button' : '$newProjectButton'
    
    addOne: (project) =>
      controller = new ProjectPreview
        parent: @
        project: project
        selectedID: (if @parent.projectEditor? then @parent.projectEditor.project.id else null)
      @$projectList.append controller.render().el
      @
  
    addAll: =>
      @$projectList.empty()
      projects = Project.all()
      if projects.length > 0
        @addOne project for project in projects
      else
        @$projectList.html projectManagerNoPreviewsTemplate
      @
      
    render: =>
      @html projectManagerTemplate
      @addAll()
      @
  
    events:
      '.new-project-button' : 'newProject'
      
    newProject: (event) =>
      event.preventDefault()
      Project.create App.makeProjectTemplate()
      @addAll()

