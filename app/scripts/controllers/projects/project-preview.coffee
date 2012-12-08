define [
  'jquery'
  'underscore'
  'spine'
  'models/project'
  'text!views/projects/manager/manager-preview.html'
], ($, _, Spine, Project, projectPreviewTemplate) ->

  class ProjectPreview extends Spine.Controller
    constructor: ->
      super
      @project.bind('update', @render).bind 'destroy', @release
    
    tag: 'li'
    className: 'well'
    
    events:
      'click .edit-title-link' : 'editProjectTitle'
      'click .delete' : 'remove'
    
    editProjectTitle: (event) =>
      event.preventDefault()
      App.project = @project
      @navigate '/editor'
      
    remove: (event) ->
      event.preventDefault()
      @project.destroy()
  
    render: =>
      @html _.template projectPreviewTemplate, project: @project
      @
  