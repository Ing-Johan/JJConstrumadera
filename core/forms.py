from django import forms

from .models import Lead, PortfolioCategory, PortfolioImage, PortfolioProject, Service, SiteContent


def get_portfolio_category_choices():
    category_names = list(PortfolioCategory.objects.filter(is_active=True).order_by('sort_order', 'name').values_list('name', flat=True))
    legacy_names = [choice[0] for choice in PortfolioProject.CATEGORY_CHOICES]
    merged = []
    for name in [*category_names, *legacy_names]:
        if name and name not in merged:
            merged.append(name)
    return [(name, name) for name in merged]


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


class SiteContentForm(forms.ModelForm):
    class Meta:
        model = SiteContent
        fields = ['title', 'body', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle-input'}),
        }


class PortfolioCategoryForm(forms.ModelForm):
    class Meta:
        model = PortfolioCategory
        fields = ['name', 'sort_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle-input'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            from django.utils.text import slugify
            instance.slug = slugify(instance.name)
        if commit:
            instance.save()
        return instance


class PortfolioProjectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = get_portfolio_category_choices()

    class Meta:
        model = PortfolioProject
        fields = ['name', 'description', 'category', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle-input'}),
        }


class PortfolioImageForm(forms.ModelForm):
    caption = forms.CharField(
        required=False,
        label='Título / leyenda',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Cocina central'}),
    )

    class Meta:
        model = PortfolioImage
        fields = ['image', 'caption', 'sort_order', 'is_primary']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'toggle-input'}),
        }
