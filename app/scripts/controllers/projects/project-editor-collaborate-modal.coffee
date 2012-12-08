define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/editor/collaborate-modal.html'
], ($, _, Spine, collaborateModalTemplate) ->

  class CollaborateModal extends Spine.Controller
    constructor: ->
      super
    
    className: ''
    
    getContext: =>
      {}
    
    render: =>
      @html _.template collaborateModalTemplate, @getContext()
      @

