# ui/frames/explorador_frame.py
import secrets

import customtkinter as ctk

from ui import styles as st
from ui.components.concept_card import ConceptCard


class ExploradorFrame(ctk.CTkFrame):
    """Frame principal mejorado con mejor diseño y UX."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        # Contenedor principal con mejor espaciado
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True)

        # Cabecera mejorada
        header = ctk.CTkFrame(main_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, st.SPACING_LG))

        # Título principal
        ctk.CTkLabel(
            header,
            text="GENERADOR DE CONCEPTOS",
            font=st.FONT_H2,
            text_color=st.COLOR_TEXT
        ).pack(anchor="w")

        # Subtítulo descriptivo
        ctk.CTkLabel(
            header,
            text="Genera ideas únicas para tus series combinando elementos aleatorios",
            font=st.FONT_BODY,
            text_color=st.COLOR_TEXT_DIM
        ).pack(anchor="w", pady=(st.SPACING_XS, 0))

        # Contenedor de tarjetas con mejor diseño
        cards_container = ctk.CTkFrame(main_container, fg_color="transparent")
        cards_container.pack(fill="both", expand=True, pady=st.SPACING_MD)

        self.cards = {}
        categories = [
            ("TEMAS", st.COLOR_CATEGORY_THEME),
            ("OBJETOS", st.COLOR_CATEGORY_OBJECT),
            ("ANOMALIAS", st.COLOR_CATEGORY_ANOMALY),
            ("EMOCIONES", st.COLOR_CATEGORY_EMOTION)
        ]

        for cat, color in categories:
            # Obtener un valor aleatorio del directorio
            val = secrets.SystemRandom().choice(self.app.config["directory"].get(cat, ["?"]))

            # Crear tarjeta con mejor espaciado
            card_frame = ctk.CTkFrame(cards_container, fg_color="transparent")
            card_frame.pack(side="left", fill="both", expand=True, padx=st.SPACING_SM)

            card = ConceptCard(card_frame, cat, st.ICONS[cat], val, color)
            card.pack(fill="both", expand=True)
            self.cards[cat] = card

        # Contenedor de botones de acción
        actions_container = ctk.CTkFrame(main_container, fg_color="transparent")
        actions_container.pack(fill="x", pady=st.SPACING_LG)

        # Botón de nueva idea mejorado
        generate_btn = ctk.CTkButton(
            actions_container,
            text=f"{st.ICONS['REFRESH']}  GENERAR NUEVA IDEA",
            height=56,
            corner_radius=st.RADIUS_LG,
            font=st.FONT_BUTTON,
            fg_color=st.COLOR_ACCENT,
            hover_color=st.COLOR_ACCENT_HOVER,
            text_color="#ffffff",
            command=self.generate_random_concept
        )
        generate_btn.pack(fill="x", pady=(0, st.SPACING_MD))

        # Botón para ir al guionista mejorado
        next_btn = ctk.CTkButton(
            actions_container,
            text=f"Siguiente Paso: Redactar Guion  {st.ICONS['GUION']}",
            height=48,
            corner_radius=st.RADIUS_LG,
            font=st.FONT_BUTTON,
            fg_color=st.COLOR_SUCCESS,
            hover_color=st.COLOR_SUCCESS_HOVER,
            text_color="#ffffff",
            command=self.app.show_guionista
        )
        next_btn.pack(fill="x")

    def generate_random_concept(self):
        """Genera nuevos conceptos aleatorios para las tarjetas desbloqueadas."""
        d = self.app.config["directory"]
        for cat, card in self.cards.items():
            new_val = secrets.SystemRandom().choice(d.get(cat, ["?"]))
            card.update_value(new_val)
