from django import forms
from .models import Student

class StudentRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'pattern': '^(?=.*[A-Z])(?=.*\\d).{8,}$',
            'title': 'Password must be at least 8 characters long, contain at least one uppercase letter and one number.'
        })
    )
    terms = forms.BooleanField(required=True, label='I agree to the terms and conditions')
    
    class Meta:
        model = Student
        fields = [
            'admission_number', 'full_name', 'email', 'password',
            'guardian_name', 'guardian_email', 'address', 'mobile',
            'date_of_birth', 'gender', 'city', 'program', 'discipline',
            'room_type', 'ac_type'
        ]
        
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'ac_type': forms.RadioSelect(),
        }

class StudentLoginForm(forms.Form):
    admission_number = forms.CharField(max_length=50, label='Admission Number')
    password = forms.CharField(widget=forms.PasswordInput(), label='Password')
