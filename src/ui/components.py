# Reusable UI widgets
import streamlit as st
from typing import Optional


class ColorPicker:
    """A beautiful color picker component using Streamlit's native color picker."""

    # Curated list of trendy pastel colors (2024 trends) for reference
    PASTEL_COLORS = [
        {"name": "Soft Pink", "hex": "#F8BBD9"},
        {"name": "Rose Quartz", "hex": "#F7CAC9"},
        {"name": "Blush", "hex": "#FFB3BA"},
        {"name": "Baby Blue", "hex": "#A8DADC"},
        {"name": "Lavender Mist", "hex": "#E6E6FA"},
        {"name": "Periwinkle", "hex": "#CCCCFF"},
        {"name": "Sage Green", "hex": "#B2C2A1"},
        {"name": "Mint", "hex": "#98D8C8"},
        {"name": "Champagne", "hex": "#F7E7CE"},
        {"name": "Peach", "hex": "#FFDAB9"},
        {"name": "Cream", "hex": "#FFFACD"},
        {"name": "Apricot", "hex": "#FDD5B1"},
        {"name": "Powder Blue", "hex": "#B0E0E6"},
        {"name": "Lilac", "hex": "#D8BFD8"},
        {"name": "Seafoam", "hex": "#90EE90"},
        {"name": "Sky Blue", "hex": "#87CEEB"},
        {"name": "Light Coral", "hex": "#F08080"},
        {"name": "Pale Green", "hex": "#98FB98"},
        {"name": "Moccasin", "hex": "#FFE4B5"},
        {"name": "Light Steel", "hex": "#B0C4DE"},
    ]

    @classmethod
    def color_picker(
        cls,
        label: str = "Choose Color",
        key: str = "color_picker",
        default_color: Optional[str] = None,
        help_text: Optional[str] = None
    ) -> Optional[str]:
        """
        Render a color picker using Streamlit's native component.

        Args:
            label: Label for the color picker
            key: Unique key for the component
            default_color: Default hex color value
            help_text: Help text to display

        Returns:
            Selected hex color or None
        """
        # Set default color if not provided
        if default_color is None:
            default_color = cls.PASTEL_COLORS[0]["hex"]

        # Use Streamlit's native color picker
        kwargs = dict(label=label, value=default_color, help=help_text)
        if key is not None:
            kwargs["key"] = key
        selected_color = st.color_picker(**kwargs)
        # Display current selection with preview
        if selected_color:
            st.markdown(
                f"""
                <div style="
                    display: inline-block;
                    width: 100px;
                    height: 30px;
                    background-color: {selected_color};
                    border: 2px solid #666;
                    border-radius: 5px;
                    margin: 5px 0;
                "></div>
                <p style="margin: 0; font-size: 0.9em; color: #666;">
                    Current: {selected_color}
                </p>
                """,
                unsafe_allow_html=True
            )

        return selected_color


# Convenience function for easy usage
def color_picker(label: str = "Choose Color", key: str = "color_picker",
                default_color: Optional[str] = None, help_text: Optional[str] = None) -> Optional[str]:
    """Convenience function to use the ColorPicker component."""
    return ColorPicker.color_picker(label, key, default_color, help_text)
