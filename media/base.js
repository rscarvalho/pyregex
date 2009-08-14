function submitForm(form){
  var data = $(form).serialize();
  
  $.post("/check_regex/", data, function(data, textStatus){
    $("#result").html(data);
  })
  return false;
}

$(function(){
  
});