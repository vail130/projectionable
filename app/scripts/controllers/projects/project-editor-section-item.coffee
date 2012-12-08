define [
  'jquery'
  'underscore'
  'spine'
  'text!views/projects/editor/editor-requirement.html'
  'text!views/projects/editor/editor-asset.html'
  'text!views/projects/editor/editor-file.html'
  'models/permission'
], ($, _, Spine, requirementTemplate, assetTemplate, fileTemplate, Permission) ->

  class SectionItem extends Spine.Controller
    constructor: ->
      super
    
    tag: 'li'
    className: 'section-item'
    
    getContext: =>
      item: @item
      key: @key
      permissions: _.sortBy Permission.findAllByAttribute('project_id', @item.project_id), 'email'
    
    render: =>
      if @key in ['front', 'back']
        @html _.template requirementTemplate, @getContext()
      else if @key is 'assets'
        @html _.template assetTemplate, @getContext()
      else if @key is 'files'
        @html _.template fileTemplate, @getContext()
      @

