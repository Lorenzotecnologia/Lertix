from django import forms

from .models import ContactMessage, Order


class ContactForm(forms.ModelForm):
    # Campo isca: bots o preenchem, pessoas não o veem.
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = ContactMessage
        fields = ("name", "email", "subject", "message")

    def clean_website(self):
        if self.cleaned_data["website"]:
            raise forms.ValidationError("Envio inválido.")
        return ""


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = (
            "customer_name",
            "customer_email",
            "customer_phone",
            "postal_code",
            "address",
            "address_number",
            "address_complement",
            "district",
            "city",
            "state",
            "notes",
        )

    def clean_state(self):
        state = self.cleaned_data["state"].strip().upper()
        if len(state) != 2 or not state.isalpha():
            raise forms.ValidationError("Informe a sigla do estado, como SP.")
        return state
