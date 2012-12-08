
define [
  'jquery',
  'underscore'
  'spine',
], ($, _, Spine) ->
  
  class Lock extends Spine.Controller
    constructor: ->
      super
      @$lock = $('<div></div>').css(
        display: 'none'
        position: 'absolute'
        top: 0
        left: 0
        width: '100%'
        height: '100%'
        'background-color': 'white'
        opacity: .5
        filter: 'alpha(opacity=50)'
        'z-index': 999999999999999999
      )
      @$el.append @$lock
      @state = 'stopped'
  
    start: =>
      @initialPosition = @$el.css('position')
      if @initialPosition not in ['absolute', 'fixed']
        @$el.css 'position', 'relative'
      
      @$lock.show()
      @spinner = new Spinner(
        lines: 13
        length: 15
        width: 4
        radius: 18
        color: '#222'
        trail: 60
        shadow: true
      ).spin(@$lock.get(0))
      @$lock.children('.spinner').css
        top: '50%'
        left: '50%'
      @state = 'started'
      @
    
    stop: =>
      @spinner.stop()
      @$lock.hide()
      @$el.css 'position', @initialPosition
      @initialPosition = null
      @state = 'stopped'
      @
    
    remove: =>
      @stop() if @state is 'started'
      @$lock.remove()
      @
  
