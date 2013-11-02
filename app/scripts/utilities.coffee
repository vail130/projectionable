
define [
  'jquery'
  'underscore'
  'spine'
], ($, _, Spine) ->
  
  class Utilities extends Spine.Controller
    @::formatNumber = (number) ->
      return '' if typeof(number) is 'undefined'
      
      parts = number.toString().split '.'
      decimal = parts[1] || ''
      number = parts[0]
      
      negative = false
      if number.substr(0, 1) is '-'
        negative = true
        number = number.substr(1)
      
      number = number.replace /[^0-9]/ig, ''
      decimal = decimal.replace /[^0-9]/ig, ''
      output = ''
      while number.length > 0
        output = ',' + output if output.length > 0
        
        if number.length > 3
          output = number.substr(-3, 3) + output
          number = number.substr(0, number.length - 3)
        else
          output = number + output
          number = ''
      
      output =  '-'+output if negative
      output += '.'+decimal if decimal.length > 0
      output
