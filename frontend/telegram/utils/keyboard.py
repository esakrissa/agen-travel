from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any, Optional

def create_keyboard_from_list(
    items: List[str], 
    callback_prefix: str = "", 
    row_width: int = 2
) -> InlineKeyboardMarkup:
    """
    Create a keyboard from a list of items
    
    Args:
        items: List of items to create buttons for
        callback_prefix: Prefix for callback data
        row_width: Number of buttons per row
        
    Returns:
        InlineKeyboardMarkup
    """
    keyboard = []
    row = []
    
    for i, item in enumerate(items):
        callback_data = f"{callback_prefix}{item}" if callback_prefix else item
        row.append(InlineKeyboardButton(text=item, callback_data=callback_data))
        
        # Add row when it reaches the specified width or at the end of items
        if (i + 1) % row_width == 0 or i == len(items) - 1:
            keyboard.append(row)
            row = []
    
    return InlineKeyboardMarkup(keyboard)

def create_confirmation_keyboard(
    confirm_text: str = "✅ Ya", 
    cancel_text: str = "❌ Tidak",
    confirm_callback: str = "confirm",
    cancel_callback: str = "cancel"
) -> InlineKeyboardMarkup:
    """
    Create a simple confirmation keyboard with Yes/No buttons
    
    Args:
        confirm_text: Text for confirm button
        cancel_text: Text for cancel button
        confirm_callback: Callback data for confirm button
        cancel_callback: Callback data for cancel button
        
    Returns:
        InlineKeyboardMarkup
    """
    keyboard = [
        [
            InlineKeyboardButton(text=confirm_text, callback_data=confirm_callback),
            InlineKeyboardButton(text=cancel_text, callback_data=cancel_callback)
        ]
    ]
    return InlineKeyboardMarkup(keyboard) 