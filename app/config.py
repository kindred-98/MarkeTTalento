"""
Configuración global de la aplicación MarkeTTalento
"""

# URL de la API
API_URL = "http://127.0.0.1:8002"

# Configuración de paginación
PRODUCTOS_POR_PAGINA = 10

# Colores del tema
COLORS = {
    "cyan": "#00f0ff",
    "purple": "#8b5cf6",
    "pink": "#ec4899",
    "green": "#10b981",
    "red": "#ef4444",
    "orange": "#f59e0b",
    "bg_primary": "#0a0e17",
    "bg_secondary": "#111827",
    "bg_card": "#1a2332",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
}

# Estados de stock con colores
ESTADOS_STOCK = {
    "Agotado": {"color": "#6b7280", "bg": "#6b7280", "texto": "⚫ Agotado"},
    "Crítico": {"color": "#ef4444", "bg": "#ef4444", "texto": "🔴 Crítico"},
    "Bajo": {"color": "#f59e0b", "bg": "#f59e0b", "texto": "🟡 Bajo"},
    "Saludable": {"color": "#10b981", "bg": "#10b981", "texto": "🟢 Saludable"},
}

# Categorías con emojis
CATEGORIA_EMOJIS = {
    "Lácteos": "🥛",
    "Lacteos": "🥛",
    "Bebidas": "🥤",
    "Frutas": "🍎",
    "Verduras": "🥬",
    "Panadería": "🥐",
    "Panaderia": "🥐",
    "Carnes": "🥩",
    "Snacks": "🍿",
    "General": "📦",
}

# Descripciones por defecto para productos
DESCRIPCIONES_DEFAULT = {
    "leche": "Leche entera UHT 1.5L clásica de Central Lechera Asturiana, rica en calcio y vitaminas esenciales, perfecta para el desayuno de toda la familia. Formato cómodo con tapón antigoteo, envase reciclable",
    "huevos": "Docena de huevos frescos de gallinas criadas en libertad, ideales para cualquier receta culinaria. Huevos de categoría A, frescos y nutritivos, perfecta fuente de proteínas",
    "pan": "Pan artesanal recién horneado cada día con harina de trigo selecta, crujiente por fuera y suave por dentro. Perfecto para sandwiches, tostadas o acompanar cualquier comida",
    "agua": "Agua mineral natural de fuente pura, sin gases ni impurezas, parfait para hidratarse durante todo el día. Envase plástico reciclable, origen sostenible",
    "cafe": "Café molido premium de tueste natural con aroma intenso y sabor equilibrado, ideal para empezar el día con energía. Paquete sellado para preservar frescura",
    "arroz": "Arroz blanco de grano largo tipo basmati, perfecto para arroces tres delicals, paellas y guarniciones. Grano independientes que no se pegan",
    "aceite": "Aceite de oliva virgen extra de primera presión en frío, color dorado y saborFruit intense, ideal para ensaladas, frituras y aliños. Envase de vidrio oscuro",
    "azucar": "Azúcar blanco refinado de caña de alta pureza, perfecto para endulzar bebidas calientes frías y recetas de repostería. Textura fina de disolución rápida",
    "harina": "Harina de trigo multiuso para repostería y panadería, textura suave y esponjosa. Ideal para cakes, pastas,pasteles y panes caseros",
    "galletas": "Galletas dulces crujientes tipo snack con sabor clásico, ideales para merendar con leche o café. Paquete familiar con cierre hermético para preservar crocancia",
    "cereal": "Cereal de desayuno integral rico en fibra y vitaminas, fuente de energía natural para la mañana. Crujiente y delicioso con leche",
}
