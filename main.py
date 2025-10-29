import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
from kivy.uix.carousel import Carousel
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.stacklayout import StackLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty, ObjectProperty
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex
from kivy.storage.jsonstore import JsonStore

import json
import datetime
import csv
import os
from collections import defaultdict

# Configuration des couleurs
COLORS = {
    'primary': get_color_from_hex('#8e44ad'),
    'primary_light': get_color_from_hex('#bb8fce'),
    'primary_dark': get_color_from_hex('#6c3483'),
    'secondary': get_color_from_hex('#f39c12'),
    'light': get_color_from_hex('#f8f9fa'),
    'dark': get_color_from_hex('#343a40'),
    'success': get_color_from_hex('#28a745'),
    'danger': get_color_from_hex('#dc3545'),
    'warning': get_color_from_hex('#ffc107'),
    'info': get_color_from_hex('#17a2b8'),
    'gray': get_color_from_hex('#6c757d'),
    'gray_light': get_color_from_hex('#e9ecef')
}

# Configuration de sécurité
SECURITY_CONFIG = {
    'access_key': "BallaKonate2024!",
    'personal_code': "010189",
    'max_attempts': 5,
    'lockout_duration': 30,  # minutes
    'session_duration': 8    # heures
}

class SecurityGate(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.failed_attempts = 0
        self.is_locked = False
        self.lock_until = 0
        
        self.setup_ui()
        self.load_security_state()
    
    def setup_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # Carte de sécurité
        security_card = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(400),
            padding=dp(20),
            spacing=dp(15)
        )
        security_card.background_color = COLORS['light']
        
        with security_card.canvas.before:
            Color(*COLORS['light'])
            RoundedRectangle(pos=security_card.pos, size=security_card.size, radius=[dp(12),])
        
        # Titre
        title_layout = BoxLayout(size_hint=(1, None), height=dp(50))
        title_label = Label(
            text='[b]Accès Sécurisé[/b]',
            markup=True,
            font_size=sp(24),
            color=COLORS['primary']
        )
        title_layout.add_widget(title_label)
        
        # Sous-titre
        subtitle_label = Label(
            text='Application réservée à Balla KONATE',
            font_size=sp(16),
            color=COLORS['gray']
        )
        
        # Formulaire
        form_layout = BoxLayout(orientation='vertical', spacing=dp(10))
        
        # Clé d'accès
        access_key_layout = BoxLayout(orientation='vertical', spacing=dp(5))
        access_key_label = Label(
            text='Clé d\'accès :',
            size_hint=(1, None),
            height=dp(30),
            font_size=sp(16)
        )
        self.access_key_input = TextInput(
            password=True,
            hint_text='Entrez votre clé d\'accès',
            size_hint=(1, None),
            height=dp(50),
            font_size=sp(16)
        )
        access_key_layout.add_widget(access_key_label)
        access_key_layout.add_widget(self.access_key_input)
        
        # Code personnel
        personal_code_layout = BoxLayout(orientation='vertical', spacing=dp(5))
        personal_code_label = Label(
            text='Code personnel :',
            size_hint=(1, None),
            height=dp(30),
            font_size=sp(16)
        )
        self.personal_code_input = TextInput(
            password=True,
            hint_text='Entrez votre code personnel',
            size_hint=(1, None),
            height=dp(50),
            font_size=sp(16)
        )
        personal_code_layout.add_widget(personal_code_label)
        personal_code_layout.add_widget(self.personal_code_input)
        
        # Bouton d'accès
        access_button = Button(
            text='Accéder à l\'application',
            size_hint=(1, None),
            height=dp(50),
            background_color=COLORS['primary'],
            font_size=sp(16)
        )
        access_button.bind(on_press=self.attempt_access)
        
        # Messages d'alerte
        self.warning_label = Label(
            text='',
            size_hint=(1, None),
            height=dp(40),
            color=COLORS['warning'],
            font_size=sp(14)
        )
        self.warning_label.opacity = 0
        
        self.error_label = Label(
            text='Identifiants incorrects. Veuillez réessayer.',
            size_hint=(1, None),
            height=dp(40),
            color=COLORS['danger'],
            font_size=sp(14)
        )
        self.error_label.opacity = 0
        
        # Assemblage
        form_layout.add_widget(access_key_layout)
        form_layout.add_widget(personal_code_layout)
        form_layout.add_widget(access_button)
        form_layout.add_widget(self.warning_label)
        form_layout.add_widget(self.error_label)
        
        security_card.add_widget(title_layout)
        security_card.add_widget(subtitle_label)
        security_card.add_widget(form_layout)
        
        layout.add_widget(security_card)
        self.add_widget(layout)
    
    def load_security_state(self):
        store = JsonStore('security.json')
        if store.exists('security'):
            data = store.get('security')
            self.failed_attempts = data.get('failed_attempts', 0)
            self.is_locked = data.get('is_locked', False)
            self.lock_until = data.get('lock_until', 0)
    
    def save_security_state(self):
        store = JsonStore('security.json')
        store.put('security', 
            failed_attempts=self.failed_attempts,
            is_locked=self.is_locked,
            lock_until=self.lock_until
        )
    
    def attempt_access(self, instance):
        if self.is_locked and datetime.datetime.now().timestamp() < self.lock_until:
            self.show_lockout()
            return
        
        access_key = self.access_key_input.text
        personal_code = self.personal_code_input.text
        
        if (access_key == SECURITY_CONFIG['access_key'] and 
            personal_code == SECURITY_CONFIG['personal_code']):
            self.grant_access()
            self.reset_security()
        else:
            self.failed_attempts += 1
            self.save_security_state()
            
            if self.failed_attempts >= SECURITY_CONFIG['max_attempts']:
                self.lock_access()
            else:
                self.show_error()
                self.update_warning()
                self.clear_inputs()
    
    def grant_access(self):
        # Sauvegarder l'authentification
        store = JsonStore('security.json')
        session_expiry = datetime.datetime.now().timestamp() + (SECURITY_CONFIG['session_duration'] * 3600)
        store.put('session', 
            authenticated=True,
            auth_expiry=session_expiry
        )
        
        # Passer à l'écran principal
        self.manager.current = 'main'
    
    def lock_access(self):
        self.is_locked = True
        self.lock_until = datetime.datetime.now().timestamp() + (SECURITY_CONFIG['lockout_duration'] * 60)
        self.save_security_state()
        self.show_lockout()
    
    def reset_security(self):
        self.failed_attempts = 0
        self.is_locked = False
        self.lock_until = 0
        self.save_security_state()
    
    def show_lockout(self):
        remaining_time = int((self.lock_until - datetime.datetime.now().timestamp()) / 60)
        self.warning_label.text = f'🔒 Accès temporairement bloqué. Réessayez dans {remaining_time} minute(s).'
        self.warning_label.opacity = 1
        self.error_label.opacity = 0
    
    def show_error(self):
        self.error_label.opacity = 1
        self.warning_label.opacity = 0
    
    def update_warning(self):
        if self.failed_attempts > 0:
            remaining_attempts = SECURITY_CONFIG['max_attempts'] - self.failed_attempts
            self.warning_label.text = f'{self.failed_attempts} tentative(s) échouée(s). {remaining_attempts} tentative(s) restante(s).'
            self.warning_label.opacity = 1
    
    def clear_inputs(self):
        self.access_key_input.text = ''
        self.personal_code_input.text = ''

class Product:
    def __init__(self, id, name, price, stock, alert_threshold=5, category="", description=""):
        self.id = id
        self.name = name
        self.price = price
        self.stock = stock
        self.alert_threshold = alert_threshold
        self.category = category
        self.description = description

class CartItem:
    def __init__(self, product, quantity=1, discount=0):
        self.product = product
        self.quantity = quantity
        self.discount = discount

class Sale:
    def __init__(self, id, date, amount, items):
        self.id = id
        self.date = date
        self.amount = amount
        self.items = items

class Reservation:
    def __init__(self, id, product_id, product_name, phone, notes, date, status='active'):
        self.id = id
        self.product_id = product_id
        self.product_name = product_name
        self.phone = phone
        self.notes = notes
        self.date = date
        self.status = status

class CustomButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = COLORS['primary']
        self.color = COLORS['light']
        self.font_size = sp(16)
        self.size_hint_y = None
        self.height = dp(50)

class ProductCard(BoxLayout):
    def __init__(self, product, on_sell_callback, on_reserve_callback, **kwargs):
        super().__init__(**kwargs)
        self.product = product
        self.on_sell_callback = on_sell_callback
        self.on_reserve_callback = on_reserve_callback
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(120)
        self.padding = dp(10)
        self.spacing = dp(5)
        
        with self.canvas.before:
            Color(*COLORS['light'])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8),])
        
        # Nom du produit
        name_label = Label(
            text=product.name,
            size_hint=(1, None),
            height=dp(25),
            font_size=sp(18),
            bold=True
        )
        
        # Détails
        details_layout = BoxLayout(size_hint=(1, None), height=dp(25))
        price_label = Label(
            text=f"{product.price:.2f} €",
            font_size=sp(16),
            color=COLORS['primary']
        )
        stock_label = Label(
            text=f"{product.stock} en stock",
            font_size=sp(14)
        )
        category_label = Label(
            text=product.category,
            font_size=sp(12),
            color=COLORS['gray']
        )
        
        details_layout.add_widget(price_label)
        details_layout.add_widget(stock_label)
        details_layout.add_widget(category_label)
        
        # Avertissement stock faible
        warning_label = None
        if product.stock <= product.alert_threshold:
            warning_label = Label(
                text=f"Stock faible (seuil: {product.alert_threshold})",
                size_hint=(1, None),
                height=dp(20),
                font_size=sp(12),
                color=COLORS['danger']
            )
        
        # Actions
        actions_layout = BoxLayout(size_hint=(1, None), height=dp(40), spacing=dp(5))
        sell_button = Button(
            text='Vendre',
            size_hint=(0.5, 1),
            background_color=COLORS['primary']
        )
        reserve_button = Button(
            text='Réserver',
            size_hint=(0.5, 1),
            background_color=COLORS['secondary']
        )
        
        sell_button.bind(on_press=lambda x: on_sell_callback(product.id))
        reserve_button.bind(on_press=lambda x: on_reserve_callback(product.id))
        
        actions_layout.add_widget(sell_button)
        actions_layout.add_widget(reserve_button)
        
        # Assemblage
        self.add_widget(name_label)
        self.add_widget(details_layout)
        if warning_label:
            self.add_widget(warning_label)
        self.add_widget(actions_layout)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.products = []
        self.cart = []
        self.reservations = []
        self.sales_history = []
        self.current_currency = 'EUR'
        self.global_discount = 0
        self.search_term = ''
        
        self.load_data()
        self.setup_ui()
    
    def load_data(self):
        # Charger les données depuis le stockage
        store = JsonStore('data.json')
        
        if store.exists('products'):
            products_data = store.get('products')['data']
            self.products = [Product(**p) for p in products_data]
        else:
            # Données par défaut
            self.products = [
                Product(1, "Parfum Fleur de Printemps", 75.00, 15, 5, "Parfum", "Parfum floral printanier"),
                Product(2, "Crème Hydratante Nuit", 45.00, 22, 5, "Cosmétique", "Crème hydratante pour la nuit"),
                Product(3, "Eau de Toilette Citrus", 60.00, 10, 5, "Parfum", "Eau de toilette aux notes d'agrumes"),
                Product(4, "Sérum Anti-Âge", 89.00, 8, 5, "Cosmétique", "Sérum anti-rides et anti-âge")
            ]
        
        if store.exists('sales'):
            sales_data = store.get('sales')['data']
            self.sales_history = [Sale(**s) for s in sales_data]
        
        if store.exists('reservations'):
            reservations_data = store.get('reservations')['data']
            self.reservations = [Reservation(**r) for r in reservations_data]
    
    def save_data(self):
        store = JsonStore('data.json')
        
        products_data = [{
            'id': p.id, 'name': p.name, 'price': p.price, 'stock': p.stock,
            'alert_threshold': p.alert_threshold, 'category': p.category, 'description': p.description
        } for p in self.products]
        
        sales_data = [{
            'id': s.id, 'date': s.date, 'amount': s.amount, 'items': [
                {'product': {
                    'id': item.product.id, 'name': item.product.name, 'price': item.product.price,
                    'stock': item.product.stock, 'alert_threshold': item.product.alert_threshold,
                    'category': item.product.category, 'description': item.product.description
                }, 'quantity': item.quantity, 'discount': item.discount}
                for item in s.items
            ]
        } for s in self.sales_history]
        
        reservations_data = [{
            'id': r.id, 'product_id': r.product_id, 'product_name': r.product_name,
            'phone': r.phone, 'notes': r.notes, 'date': r.date, 'status': r.status
        } for r in self.reservations]
        
        store.put('products', data=products_data)
        store.put('sales', data=sales_data)
        store.put('reservations', data=reservations_data)
    
    def setup_ui(self):
        # Layout principal avec onglets
        self.tab_panel = TabbedPanel()
        self.tab_panel.do_default_tab = False
        
        # Onglet Vente
        sale_tab = TabbedPanelItem(text='Vente')
        sale_tab.add_widget(self.create_sale_tab())
        self.tab_panel.add_widget(sale_tab)
        
        # Onglet Stock
        stock_tab = TabbedPanelItem(text='Stock')
        stock_tab.add_widget(self.create_stock_tab())
        self.tab_panel.add_widget(stock_tab)
        
        # Onglet Réservations
        reservations_tab = TabbedPanelItem(text='Réservations')
        reservations_tab.add_widget(self.create_reservations_tab())
        self.tab_panel.add_widget(reservations_tab)
        
        # Onglet Historique
        history_tab = TabbedPanelItem(text='Historique')
        history_tab.add_widget(self.create_history_tab())
        self.tab_panel.add_widget(history_tab)
        
        self.add_widget(self.tab_panel)
    
    def create_sale_tab(self):
        layout = BoxLayout(orientation='vertical')
        
        # Barre de recherche
        search_layout = BoxLayout(size_hint=(1, None), height=dp(50), padding=dp(5))
        self.search_input = TextInput(
            hint_text='Rechercher un produit...',
            size_hint=(0.8, 1)
        )
        search_button = Button(
            text='🔍',
            size_hint=(0.2, 1),
            background_color=COLORS['primary']
        )
        search_button.bind(on_press=self.search_products)
        search_layout.add_widget(self.search_input)
        search_layout.add_widget(search_button)
        
        # Liste des produits
        self.products_scroll = ScrollView()
        self.products_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        self.products_layout.bind(minimum_height=self.products_layout.setter('height'))
        
        self.refresh_products_list()
        self.products_scroll.add_widget(self.products_layout)
        
        # Panier
        cart_label = Label(
            text='Panier',
            size_hint=(1, None),
            height=dp(30),
            font_size=sp(20),
            bold=True
        )
        
        self.cart_scroll = ScrollView(size_hint=(1, 0.4))
        self.cart_layout = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None)
        self.cart_layout.bind(minimum_height=self.cart_layout.setter('height'))
        
        self.refresh_cart()
        self.cart_scroll.add_widget(self.cart_layout)
        
        # Total et actions
        total_layout = BoxLayout(size_hint=(1, None), height=dp(50))
        self.total_label = Label(
            text='Total : 0.00 €',
            font_size=sp(18),
            bold=True
        )
        
        actions_layout = BoxLayout(size_hint=(0.6, 1), spacing=dp(5))
        validate_button = Button(
            text='Valider',
            background_color=COLORS['success']
        )
        clear_button = Button(
            text='Vider',
            background_color=COLORS['danger']
        )
        
        validate_button.bind(on_press=self.validate_payment)
        clear_button.bind(on_press=self.clear_cart)
        
        actions_layout.add_widget(validate_button)
        actions_layout.add_widget(clear_button)
        
        total_layout.add_widget(self.total_label)
        total_layout.add_widget(actions_layout)
        
        # Assemblage
        layout.add_widget(search_layout)
        layout.add_widget(self.products_scroll)
        layout.add_widget(cart_label)
        layout.add_widget(self.cart_scroll)
        layout.add_widget(total_layout)
        
        return layout
    
    def create_stock_tab(self):
        layout = BoxLayout(orientation='vertical')
        
        # Bouton d'ajout
        add_button = Button(
            text='Ajouter un produit',
            size_hint=(1, None),
            height=dp(50),
            background_color=COLORS['primary']
        )
        add_button.bind(on_press=self.show_add_product_popup)
        
        # Liste des produits en stock
        self.stock_scroll = ScrollView()
        self.stock_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        self.stock_layout.bind(minimum_height=self.stock_layout.setter('height'))
        
        self.refresh_stock_list()
        self.stock_scroll.add_widget(self.stock_layout)
        
        layout.add_widget(add_button)
        layout.add_widget(self.stock_scroll)
        
        return layout
    
    def create_reservations_tab(self):
        layout = BoxLayout(orientation='vertical')
        
        # Formulaire de réservation
        form_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(200), spacing=dp(10))
        
        # Produit
        product_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(60))
        product_label = Label(text='Produit:', size_hint=(1, None), height=dp(30))
        self.reservation_product_input = TextInput(hint_text='Nom du produit', size_hint=(1, None), height=dp(30))
        product_layout.add_widget(product_label)
        product_layout.add_widget(self.reservation_product_input)
        
        # Téléphone
        phone_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(60))
        phone_label = Label(text='Téléphone:', size_hint=(1, None), height=dp(30))
        self.reservation_phone_input = TextInput(hint_text='Numéro de téléphone', size_hint=(1, None), height=dp(30))
        phone_layout.add_widget(phone_label)
        phone_layout.add_widget(self.reservation_phone_input)
        
        # Bouton d'ajout
        add_reservation_button = Button(
            text='Ajouter réservation',
            size_hint=(1, None),
            height=dp(50),
            background_color=COLORS['primary']
        )
        add_reservation_button.bind(on_press=self.add_reservation)
        
        form_layout.add_widget(product_layout)
        form_layout.add_widget(phone_layout)
        form_layout.add_widget(add_reservation_button)
        
        # Liste des réservations
        self.reservations_scroll = ScrollView()
        self.reservations_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        self.reservations_layout.bind(minimum_height=self.reservations_layout.setter('height'))
        
        self.refresh_reservations_list()
        self.reservations_scroll.add_widget(self.reservations_layout)
        
        layout.add_widget(form_layout)
        layout.add_widget(self.reservations_scroll)
        
        return layout
    
    def create_history_tab(self):
        layout = BoxLayout(orientation='vertical')
        
        # Filtre par date
        filter_layout = BoxLayout(size_hint=(1, None), height=dp(50))
        filter_label = Label(text='Filtrer par date:', size_hint=(0.4, 1))
        self.history_date_input = TextInput(
            text=datetime.datetime.now().strftime('%Y-%m-%d'),
            size_hint=(0.6, 1)
        )
        filter_layout.add_widget(filter_label)
        filter_layout.add_widget(self.history_date_input)
        
        # Bouton de suppression
        delete_button = Button(
            text='Supprimer ventes du jour',
            size_hint=(1, None),
            height=dp(50),
            background_color=COLORS['danger']
        )
        delete_button.bind(on_press=self.delete_today_sales)
        
        # Historique
        self.history_scroll = ScrollView()
        self.history_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        self.history_layout.bind(minimum_height=self.history_layout.setter('height'))
        
        self.refresh_history()
        self.history_scroll.add_widget(self.history_layout)
        
        layout.add_widget(filter_layout)
        layout.add_widget(delete_button)
        layout.add_widget(self.history_scroll)
        
        return layout
    
    def refresh_products_list(self):
        self.products_layout.clear_widgets()
        
        filtered_products = [p for p in self.products 
                           if p.stock > 0 and 
                           (self.search_term.lower() in p.name.lower() or 
                            self.search_term.lower() in p.category.lower())]
        
        for product in filtered_products:
            card = ProductCard(
                product, 
                self.add_to_cart,
                self.prepare_reservation
            )
            self.products_layout.add_widget(card)
    
    def refresh_stock_list(self):
        self.stock_layout.clear_widgets()
        
        for product in self.products:
            card = self.create_stock_card(product)
            self.stock_layout.add_widget(card)
    
    def create_stock_card(self, product):
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), padding=dp(10), spacing=dp(5))
        
        with card.canvas.before:
            Color(*COLORS['light'])
            RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(8),])
        
        # En-tête
        header_layout = BoxLayout(size_hint=(1, None), height=dp(25))
        name_label = Label(text=product.name, font_size=sp(16), bold=True)
        stock_label = Label(
            text=f"Stock: {product.stock}",
            color=COLORS['danger'] if product.stock <= product.alert_threshold else COLORS['dark']
        )
        header_layout.add_widget(name_label)
        header_layout.add_widget(stock_label)
        
        # Détails
        details_layout = BoxLayout(size_hint=(1, None), height=dp(25))
        price_label = Label(text=f"{product.price:.2f} €", color=COLORS['primary'])
        category_label = Label(text=product.category, color=COLORS['gray'])
        details_layout.add_widget(price_label)
        details_layout.add_widget(category_label)
        
        # Actions
        actions_layout = BoxLayout(size_hint=(1, None), height=dp(30), spacing=dp(5))
        edit_button = Button(text='Modifier', size_hint=(0.5, 1), background_color=COLORS['warning'])
        delete_button = Button(text='Supprimer', size_hint=(0.5, 1), background_color=COLORS['danger'])
        
        edit_button.bind(on_press=lambda x: self.edit_product(product))
        delete_button.bind(on_press=lambda x: self.delete_product(product))
        
        actions_layout.add_widget(edit_button)
        actions_layout.add_widget(delete_button)
        
        card.add_widget(header_layout)
        card.add_widget(details_layout)
        card.add_widget(actions_layout)
        
        return card
    
    def refresh_cart(self):
        self.cart_layout.clear_widgets()
        
        if not self.cart:
            empty_label = Label(
                text='Panier vide\nAjoutez des produits pour commencer',
                font_size=sp(16),
                color=COLORS['gray']
            )
            self.cart_layout.add_widget(empty_label)
            return
        
        total = 0
        for item in self.cart:
            item_layout = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
            
            # Informations produit
            info_layout = BoxLayout(orientation='vertical', size_hint=(0.7, 1))
            name_label = Label(text=item.product.name, font_size=sp(14))
            details_label = Label(
                text=f"{item.quantity} x {item.product.price:.2f} €",
                font_size=sp(12),
                color=COLORS['gray']
            )
            info_layout.add_widget(name_label)
            info_layout.add_widget(details_label)
            
            # Actions
            actions_layout = BoxLayout(orientation='vertical', size_hint=(0.3, 1), spacing=dp(2))
            remove_button = Button(text='❌', size_hint=(1, 0.5), font_size=sp(12))
            edit_button = Button(text='✏️', size_hint=(1, 0.5), font_size=sp(12))
            
            remove_button.bind(on_press=lambda x, it=item: self.remove_from_cart(it))
            edit_button.bind(on_press=lambda x, it=item: self.edit_cart_item(it))
            
            actions_layout.add_widget(remove_button)
            actions_layout.add_widget(edit_button)
            
            item_layout.add_widget(info_layout)
            item_layout.add_widget(actions_layout)
            
            self.cart_layout.add_widget(item_layout)
            
            total += item.product.price * item.quantity
        
        self.total_label.text = f'Total : {total:.2f} €'
    
    def refresh_reservations_list(self):
        self.reservations_layout.clear_widgets()
        
        active_reservations = [r for r in self.reservations if r.status == 'active']
        
        if not active_reservations:
            empty_label = Label(text='Aucune réservation active', font_size=sp(16), color=COLORS['gray'])
            self.reservations_layout.add_widget(empty_label)
            return
        
        for reservation in active_reservations:
            reservation_card = self.create_reservation_card(reservation)
            self.reservations_layout.add_widget(reservation_card)
    
    def create_reservation_card(self, reservation):
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120), padding=dp(10), spacing=dp(5))
        
        with card.canvas.before:
            Color(*COLORS['light'])
            RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(8),])
        
        # Produit
        product_label = Label(text=reservation.product_name, font_size=sp(16), bold=True)
        
        # Détails
        phone_label = Label(text=f"Téléphone: {reservation.phone}", font_size=sp(14))
        date_label = Label(text=f"Date: {reservation.date}", font_size=sp(12), color=COLORS['gray'])
        
        # Actions
        actions_layout = BoxLayout(size_hint=(1, None), height=dp(30), spacing=dp(5))
        complete_button = Button(text='Vendre', size_hint=(0.5, 1), background_color=COLORS['success'])
        cancel_button = Button(text='Annuler', size_hint=(0.5, 1), background_color=COLORS['danger'])
        
        complete_button.bind(on_press=lambda x: self.complete_reservation(reservation))
        cancel_button.bind(on_press=lambda x: self.cancel_reservation(reservation))
        
        actions_layout.add_widget(complete_button)
        actions_layout.add_widget(cancel_button)
        
        card.add_widget(product_label)
        card.add_widget(phone_label)
        card.add_widget(date_label)
        card.add_widget(actions_layout)
        
        return card
    
    def refresh_history(self):
        self.history_layout.clear_widgets()
        
        filter_date = self.history_date_input.text
        filtered_sales = [s for s in self.sales_history if s.date == filter_date]
        
        if not filtered_sales:
            empty_label = Label(text='Aucune vente pour cette date', font_size=sp(16), color=COLORS['gray'])
            self.history_layout.add_widget(empty_label)
            return
        
        for sale in filtered_sales:
            sale_card = self.create_sale_card(sale)
            self.history_layout.add_widget(sale_card)
    
    def create_sale_card(self, sale):
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), padding=dp(10), spacing=dp(5))
        
        with card.canvas.before:
            Color(*COLORS['light'])
            RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(8),])
        
        # En-tête
        header_layout = BoxLayout(size_hint=(1, None), height=dp(25))
        date_label = Label(text=f"Vente du {sale.date}", font_size=sp(16), bold=True)
        amount_label = Label(text=f"{sale.amount:.2f} €", color=COLORS['primary'])
        header_layout.add_widget(date_label)
        header_layout.add_widget(amount_label)
        
        # Produits
        products_text = ", ".join([f"{item.product.name} (x{item.quantity})" for item in sale.items])
        products_label = Label(text=products_text, font_size=sp(12), text_size=(Window.width - dp(40), None))
        
        # Action
        delete_button = Button(
            text='Supprimer',
            size_hint=(1, None),
            height=dp(30),
            background_color=COLORS['danger']
        )
        delete_button.bind(on_press=lambda x: self.delete_sale(sale))
        
        card.add_widget(header_layout)
        card.add_widget(products_label)
        card.add_widget(delete_button)
        
        return card
    
    def search_products(self, instance):
        self.search_term = self.search_input.text
        self.refresh_products_list()
    
    def add_to_cart(self, product_id):
        product = next((p for p in self.products if p.id == product_id), None)
        if not product:
            return
        
        if product.stock <= 0:
            self.show_popup("Erreur", "Ce produit est en rupture de stock.")
            return
        
        # Vérifier si le produit est déjà dans le panier
        existing_item = next((item for item in self.cart if item.product.id == product_id), None)
        
        if existing_item:
            if existing_item.quantity >= product.stock:
                self.show_popup("Erreur", f"Quantité maximale disponible: {product.stock}")
                return
            existing_item.quantity += 1
        else:
            self.cart.append(CartItem(product))
        
        self.refresh_cart()
    
    def remove_from_cart(self, cart_item):
        self.cart.remove(cart_item)
        self.refresh_cart()
    
    def edit_cart_item(self, cart_item):
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        
        quantity_label = Label(text=f"Modifier la quantité pour {cart_item.product.name}:")
        quantity_input = TextInput(text=str(cart_item.quantity), multiline=False)
        
        buttons_layout = BoxLayout(spacing=dp(10))
        save_button = Button(text='Sauvegarder', background_color=COLORS['success'])
        cancel_button = Button(text='Annuler', background_color=COLORS['danger'])
        
        popup = Popup(
            title='Modifier quantité',
            content=content,
            size_hint=(0.8, 0.4)
        )
        
        def save_quantity(instance):
            try:
                new_quantity = int(quantity_input.text)
                if new_quantity <= 0:
                    self.show_popup("Erreur", "La quantité doit être positive.")
                    return
                if new_quantity > cart_item.product.stock:
                    self.show_popup("Erreur", f"Stock insuffisant. Stock actuel: {cart_item.product.stock}")
                    return
                
                cart_item.quantity = new_quantity
                self.refresh_cart()
                popup.dismiss()
            except ValueError:
                self.show_popup("Erreur", "Veuillez entrer un nombre valide.")
        
        save_button.bind(on_press=save_quantity)
        cancel_button.bind(on_press=lambda x: popup.dismiss())
        
        content.add_widget(quantity_label)
        content.add_widget(quantity_input)
        buttons_layout.add_widget(save_button)
        buttons_layout.add_widget(cancel_button)
        content.add_widget(buttons_layout)
        
        popup.open()
    
    def validate_payment(self, instance):
        if not self.cart:
            self.show_popup("Erreur", "Le panier est vide.")
            return
        
        # Vérifier le stock
        for item in self.cart:
            if item.quantity > item.product.stock:
                self.show_popup("Erreur", f"Stock insuffisant pour {item.product.name}. Stock actuel: {item.product.stock}")
                return
        
        # Calculer le total
        total = sum(item.product.price * item.quantity for item in self.cart)
        
        # Mettre à jour le stock
        for item in self.cart:
            item.product.stock -= item.quantity
        
        # Enregistrer la vente
        sale = Sale(
            id=len(self.sales_history) + 1,
            date=datetime.datetime.now().strftime('%Y-%m-%d'),
            amount=total,
            items=self.cart.copy()
        )
        self.sales_history.append(sale)
        
        # Vider le panier
        self.cart.clear()
        
        # Mettre à jour l'interface
        self.refresh_cart()
        self.refresh_products_list()
        self.refresh_stock_list()
        self.refresh_history()
        
        # Sauvegarder les données
        self.save_data()
        
        self.show_popup("Succès", f"Vente enregistrée !\nMontant: {total:.2f} €")
    
    def clear_cart(self, instance):
        if not self.cart:
            self.show_popup("Information", "Le panier est déjà vide.")
            return
        
        self.cart.clear()
        self.refresh_cart()
    
    def prepare_reservation(self, product_id):
        product = next((p for p in self.products if p.id == product_id), None)
        if product:
            self.reservation_product_input.text = product.name
            self.tab_panel.switch_to(self.tab_panel.tab_list[2])  # Aller à l'onglet Réservations
    
    def add_reservation(self, instance):
        product_name = self.reservation_product_input.text
        phone = self.reservation_phone_input.text
        
        if not product_name or not phone:
            self.show_popup("Erreur", "Veuillez remplir tous les champs.")
            return
        
        product = next((p for p in self.products if p.name == product_name), None)
        if not product:
            self.show_popup("Erreur", "Produit non trouvé.")
            return
        
        if product.stock <= 0:
            self.show_popup("Erreur", "Ce produit est en rupture de stock.")
            return
        
        # Vérifier si une réservation existe déjà
        existing_reservation = next((r for r in self.reservations 
                                   if r.product_id == product.id and r.phone == phone and r.status == 'active'), None)
        if existing_reservation:
            self.show_popup("Erreur", "Une réservation active existe déjà pour ce produit et ce numéro.")
            return
        
        # Créer la réservation
        reservation = Reservation(
            id=len(self.reservations) + 1,
            product_id=product.id,
            product_name=product.name,
            phone=phone,
            notes="",
            date=datetime.datetime.now().strftime('%Y-%m-%d')
        )
        self.reservations.append(reservation)
        
        # Réinitialiser le formulaire
        self.reservation_product_input.text = ""
        self.reservation_phone_input.text = ""
        
        # Mettre à jour l'interface
        self.refresh_reservations_list()
        self.save_data()
        
        self.show_popup("Succès", "Réservation ajoutée avec succès !")
    
    def complete_reservation(self, reservation):
        product = next((p for p in self.products if p.id == reservation.product_id), None)
        if product:
            self.add_to_cart(product.id)
            reservation.status = 'completed'
            self.refresh_reservations_list()
            self.save_data()
            self.show_popup("Succès", "Réservation complétée. Produit ajouté au panier.")
    
    def cancel_reservation(self, reservation):
        reservation.status = 'cancelled'
        self.refresh_reservations_list()
        self.save_data()
        self.show_popup("Information", "Réservation annulée.")
    
    def delete_sale(self, sale):
        # Restaurer le stock
        for item in sale.items:
            product = next((p for p in self.products if p.id == item.product.id), None)
            if product:
                product.stock += item.quantity
        
        # Supprimer la vente
        self.sales_history.remove(sale)
        
        # Mettre à jour l'interface
        self.refresh_history()
        self.refresh_stock_list()
        self.save_data()
        
        self.show_popup("Succès", "Vente supprimée. Stock restauré.")
    
    def delete_today_sales(self, instance):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        today_sales = [s for s in self.sales_history if s.date == today]
        
        if not today_sales:
            self.show_popup("Information", "Aucune vente trouvée pour aujourd'hui.")
            return
        
        # Restaurer le stock
        for sale in today_sales:
            for item in sale.items:
                product = next((p for p in self.products if p.id == item.product.id), None)
                if product:
                    product.stock += item.quantity
        
        # Supprimer les ventes
        self.sales_history = [s for s in self.sales_history if s.date != today]
        
        # Mettre à jour l'interface
        self.refresh_history()
        self.refresh_stock_list()
        self.save_data()
        
        self.show_popup("Succès", f"{len(today_sales)} ventes du jour supprimées. Stock restauré.")
    
    def show_add_product_popup(self, instance):
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        
        # Champs du formulaire
        name_input = TextInput(hint_text='Nom du produit', multiline=False)
        price_input = TextInput(hint_text='Prix', multiline=False)
        stock_input = TextInput(hint_text='Stock initial', multiline=False)
        category_input = TextInput(hint_text='Catégorie', multiline=False)
        
        # Boutons
        buttons_layout = BoxLayout(spacing=dp(10))
        save_button = Button(text='Sauvegarder', background_color=COLORS['success'])
        cancel_button = Button(text='Annuler', background_color=COLORS['danger'])
        
        popup = Popup(
            title='Ajouter un produit',
            content=content,
            size_hint=(0.9, 0.8)
        )
        
        def save_product(instance):
            try:
                name = name_input.text
                price = float(price_input.text)
                stock = int(stock_input.text)
                category = category_input.text
                
                if not name or not category:
                    self.show_popup("Erreur", "Veuillez remplir tous les champs.")
                    return
                
                new_product = Product(
                    id=max([p.id for p in self.products], default=0) + 1,
                    name=name,
                    price=price,
                    stock=stock,
                    category=category
                )
                
                self.products.append(new_product)
                self.refresh_products_list()
                self.refresh_stock_list()
                self.save_data()
                
                popup.dismiss()
                self.show_popup("Succès", "Produit ajouté avec succès !")
                
            except ValueError:
                self.show_popup("Erreur", "Veuillez entrer des valeurs numériques valides pour le prix et le stock.")
        
        save_button.bind(on_press=save_product)
        cancel_button.bind(on_press=lambda x: popup.dismiss())
        
        content.add_widget(name_input)
        content.add_widget(price_input)
        content.add_widget(stock_input)
        content.add_widget(category_input)
        buttons_layout.add_widget(save_button)
        buttons_layout.add_widget(cancel_button)
        content.add_widget(buttons_layout)
        
        popup.open()
    
    def edit_product(self, product):
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        
        # Champs du formulaire pré-remplis
        name_input = TextInput(text=product.name, multiline=False)
        price_input = TextInput(text=str(product.price), multiline=False)
        stock_input = TextInput(text=str(product.stock), multiline=False)
        category_input = TextInput(text=product.category, multiline=False)
        
        # Boutons
        buttons_layout = BoxLayout(spacing=dp(10))
        save_button = Button(text='Sauvegarder', background_color=COLORS['success'])
        cancel_button = Button(text='Annuler', background_color=COLORS['danger'])
        
        popup = Popup(
            title='Modifier le produit',
            content=content,
            size_hint=(0.9, 0.8)
        )
        
        def save_changes(instance):
            try:
                product.name = name_input.text
                product.price = float(price_input.text)
                product.stock = int(stock_input.text)
                product.category = category_input.text
                
                self.refresh_products_list()
                self.refresh_stock_list()
                self.save_data()
                
                popup.dismiss()
                self.show_popup("Succès", "Produit modifié avec succès !")
                
            except ValueError:
                self.show_popup("Erreur", "Veuillez entrer des valeurs numériques valides pour le prix et le stock.")
        
        save_button.bind(on_press=save_changes)
        cancel_button.bind(on_press=lambda x: popup.dismiss())
        
        content.add_widget(name_input)
        content.add_widget(price_input)
        content.add_widget(stock_input)
        content.add_widget(category_input)
        buttons_layout.add_widget(save_button)
        buttons_layout.add_widget(cancel_button)
        content.add_widget(buttons_layout)
        
        popup.open()
    
    def delete_product(self, product):
        def confirm_delete(instance):
            self.products.remove(product)
            self.refresh_products_list()
            self.refresh_stock_list()
            self.save_data()
            popup.dismiss()
            self.show_popup("Succès", "Produit supprimé avec succès !")
        
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        message = Label(text=f"Êtes-vous sûr de vouloir supprimer {product.name} ?")
        buttons_layout = BoxLayout(spacing=dp(10))
        yes_button = Button(text='Oui', background_color=COLORS['danger'])
        no_button = Button(text='Non', background_color=COLORS['primary'])
        
        yes_button.bind(on_press=confirm_delete)
        no_button.bind(on_press=lambda x: popup.dismiss())
        
        buttons_layout.add_widget(yes_button)
        buttons_layout.add_widget(no_button)
        
        content.add_widget(message)
        content.add_widget(buttons_layout)
        
        popup = Popup(
            title='Confirmation',
            content=content,
            size_hint=(0.7, 0.3)
        )
        popup.open()
    
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        message_label = Label(text=message)
        ok_button = Button(text='OK', background_color=COLORS['primary'])
        
        content.add_widget(message_label)
        content.add_widget(ok_button)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.7, 0.3)
        )
        
        ok_button.bind(on_press=lambda x: popup.dismiss())
        popup.open()

class PerfumeriaKonateApp(App):
    def build(self):
        self.title = "Perfumeria KONATE - Gestion des ventes"
        
        # Configuration de la fenêtre pour mobile
        Window.size = (360, 640)
        
        # Gestionnaire d'écrans
        sm = ScreenManager()
        
        # Vérifier si l'utilisateur est déjà authentifié
        store = JsonStore('security.json')
        if store.exists('session'):
            session_data = store.get('session')
            if (session_data.get('authenticated', False) and 
                datetime.datetime.now().timestamp() < session_data.get('auth_expiry', 0)):
                sm.add_widget(MainScreen(name='main'))
            else:
                sm.add_widget(SecurityGate(name='security'))
        else:
            sm.add_widget(SecurityGate(name='security'))
        
        return sm

if __name__ == '__main__':
    PerfumeriaKonateApp().run()
