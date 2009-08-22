function submitForm(form){
  var data = $(form).serialize();
  $("#loading").show();
  $("#result").fadeOut(0);
  $.post("/check_regex/", data, function(responseText, data){
    $("#loading").hide();
    $("#result").fadeIn();
  }, "script");
  return false;
}

$(function(){
  $("#id_regex_flags_5").click(function(){
    $(".regex").toggle(300);
  });
});
