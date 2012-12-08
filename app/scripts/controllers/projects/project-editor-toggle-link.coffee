define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/editor/toggle-link.html'
], ($, _, Spine, toggleLinkTemplate) ->

  class ToggleLink extends Spine.Controller
    constructor: ->
      super
    
    className: ''
    
    getContext: =>
      key: @key
      text: @textData
    
    render: =>
      @html _.template toggleLinkTemplate, @getContext()
      @
    
    events:
      'click' : 'toggleSection'
    
    toggleSection: (event) =>
      event.preventDefault()
      if @$el.hasClass 'active'
        @parent.trigger "hide", @key
      else
        @parent.trigger "show", @key
      @$el.toggleClass 'active'

