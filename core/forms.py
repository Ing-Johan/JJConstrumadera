from django import forms

from .models import Lead


class ContactForm(forms.ModelForm):
    name = forms.CharField(
        max_length=120,
        required=True,
        error_messages={'required': 'Este campo es obligatorio.'},
        widget=forms.TextInput(attrs={'placeholder': 'Tu nombre', 'required': True}),
    )
    phone = forms.CharField(
        max_length=30,
        required=True,
        error_messages={'required': 'Este campo es obligatorio.'},
        widget=forms.TextInput(attrs={'placeholder': 'Tu teléfono', 'required': True}),
    )
    email = forms.EmailField(
        required=True,
        error_messages={
            'required': 'Este campo es obligatorio.',
            'invalid': 'Introduce un correo electrónico válido.',
        },
        widget=forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com', 'required': True}),
    )
    address = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Tu dirección (opcional)'}),
    )
    message = forms.CharField(
        required=True,
        error_messages={'required': 'Este campo es obligatorio.'},
        widget=forms.Textarea(attrs={'placeholder': 'Cuéntanos sobre tu proyecto', 'rows': 5, 'required': True}),
    )

    class Meta:
        model = Lead
        fields = ['name', 'phone', 'email', 'address', 'message']
