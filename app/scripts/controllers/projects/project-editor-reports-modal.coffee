define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/editor/reports-modal.html'
], ($, _, Spine, reportsModalTemplate) ->

  class ReportsModal extends Spine.Controller
    constructor: ->
      super
    
    getContext: =>
      project: @parent.project
    
    render: =>
      @html _.template reportsModalTemplate, @getContext()
      @
