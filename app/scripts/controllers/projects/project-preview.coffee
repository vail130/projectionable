define [
  'jquery'
  'underscore'
  'spine'
  'models/project'
  'text!views/projects/manager/manager-preview.html'
  'models/requirement'
  'models/projectasset'
  'utilities'
], ($, _, Spine, Project, projectPreviewTemplate, Requirement, ProjectAsset, Util) ->

  class ProjectPreview extends Spine.Controller
    constructor: ->
      super
      @project.bind('update', @render).bind 'destroy', @release
    
    tag: 'li'
    className: 'well'
    
    getContext: =>
      reqs = Requirement.findAllByAttribute 'project_id', @project.id
      #frontEndReqs = _.where reqs, {type: 'front_end'}
      #backEndReqs = _.where reqs, {type: 'back_end'}
      assets = ProjectAsset.findAllByAttribute 'project_id', @project.id
      union = _.union(reqs, assets)
      hours = _.reduce(
        union,
        (memo, obj) -> memo + (if isNaN(parseInt(obj.hours)) then 0 else parseInt(obj.hours)),
        0
      )
      
      hours_worked = _.reduce(
        union,
        (memo, obj) -> memo + (if isNaN(parseInt(obj.hours_worked)) then 0 else parseInt(obj.hours_worked)),
        0
      )
      
      percent = parseInt(hours_worked / hours * 100)
      percent = 0 if isNaN percent
      
      if isNaN(parseFloat(@project.rate)) or isNaN(parseFloat(@project.budget))
        budgetNote = "$ -- per hour"
        budgetPercent = 0
      else
        budgetNote = "$#{Util::formatNumber(hours_worked * @project.rate)} / $#{Util::formatNumber(hours * @project.rate)}"
        budgetPercent = hours_worked * @project.rate / @project.budget
      
      project: @project
      sections: [
        {
          label: 'Work'
          note: "#{Util::formatNumber(hours_worked)}h / #{Util::formatNumber(hours)}h"
          percent: percent
        }, {
          label: 'Budget'
          note: budgetNote
          percent: 50
        }, {
          label: 'Deadline'
          note: "-- days left"
          percent: 50
        }
      ]
    
    render: =>
      @html _.template projectPreviewTemplate, @getContext()
      @
    
    events:
      'click .delete' : 'remove'
      
    remove: (event) ->
      event.preventDefault()
      @project.destroy()
  
