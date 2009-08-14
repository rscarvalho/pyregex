from django import forms
import re
import sre_constants

class RegexForm(forms.Form):
    regex = forms.CharField(required=True)
    test_text = forms.CharField(widget=forms.Textarea, required=False)
    
    def clean_regex(self):
        try:
            # If regex is None, force compile to faile
            re.compile(self.cleaned_data.get('regex', '(Invalid Regex'))
        except sre_constants.error, e:
            raise forms.ValidationError("Invalid Regexp")
        
        return self.cleaned_data['regex']
