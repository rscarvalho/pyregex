function submitForm(form){
  var data = $(form).serialize();
  
  $.post("/check_regex/", data, null, "script");
  return false;
}
