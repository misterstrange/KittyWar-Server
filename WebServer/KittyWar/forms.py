from django import forms

class RegistrationForm(forms.Form):

    username  = forms.CharField(label = 'User Name', max_length = 16)
    email     = forms.CharField(label = 'Email', max_length = 64)
    password  = forms.CharField(label = 'Password', max_length = 16, widget = forms.PasswordInput)
    passwordc = forms.CharField(label = 'Confirm Password', max_length = 16, widget = forms.PasswordInput)

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get("password")
        passwordc = cleaned_data.get("passwordc")
        if password != passwordc:
            raise forms.ValidationError("Password fields must be identical")
