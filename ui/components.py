"""
Modern UI components using customtkinter
"""

import customtkinter as ctk
from config.constants import THEME_COLORS


class StatsCard(ctk.CTkFrame):
    """Animated statistics card"""
    
    def __init__(self, parent, title, icon="", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.configure(
            fg_color=THEME_COLORS['card_bg'],
            corner_radius=15,
            border_width=2,
            border_color=THEME_COLORS['accent']
        )
        
        # Icon and title
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        if icon:
            icon_label = ctk.CTkLabel(
                header_frame,
                text=icon,
                font=("Segoe UI Emoji", 24),
                text_color=THEME_COLORS['text']
            )
            icon_label.pack(side="left", padx=(0, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=("Segoe UI", 14, "bold"),
            text_color=THEME_COLORS['text_secondary']
        )
        title_label.pack(side="left")
        
        # Value
        self.value_label = ctk.CTkLabel(
            self,
            text="0",
            font=("Segoe UI", 36, "bold"),
            text_color=THEME_COLORS['text']
        )
        self.value_label.pack(pady=(5, 15))
    
    def update_value(self, value):
        """Update card value with animation"""
        self.value_label.configure(text=str(value))


class ModernButton(ctk.CTkButton):
    """Custom styled button"""
    
    def __init__(self, parent, text, icon="", command=None, style="primary", **kwargs):
        # Style configurations
        styles = {
            'primary': {'fg_color': THEME_COLORS['info'], 'hover_color': THEME_COLORS['hover']},
            'success': {'fg_color': THEME_COLORS['success'], 'hover_color': '#05c090'},
            'warning': {'fg_color': THEME_COLORS['warning'], 'hover_color': '#ffbe4d'},
            'danger': {'fg_color': THEME_COLORS['danger'], 'hover_color': '#d93654'},
            'secondary': {'fg_color': THEME_COLORS['accent'], 'hover_color': THEME_COLORS['secondary']}
        }
        
        style_config = styles.get(style, styles['primary'])
        
        button_text = f"{icon}  {text}" if icon else text
        
        super().__init__(
            parent,
            text=button_text,
            command=command,
            font=("Segoe UI", 13, "bold"),
            fg_color=style_config['fg_color'],
            hover_color=style_config['hover_color'],
            corner_radius=10,
            height=45,
            border_width=0,
            cursor="hand2",
            **kwargs
        )


class VideoDisplay(ctk.CTkFrame):
    """Video display widget with border"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.configure(
            fg_color=THEME_COLORS['card_bg'],
            corner_radius=15,
            border_width=2,
            border_color=THEME_COLORS['accent']
        )
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="📹 Live Feed",
            font=("Segoe UI", 16, "bold"),
            text_color=THEME_COLORS['text']
        )
        title_label.pack(pady=(15, 10))
        
        # Video canvas container
        self.canvas_frame = ctk.CTkFrame(
            self,
            fg_color="#000000",
            corner_radius=10
        )
        self.canvas_frame.pack(padx=15, pady=(0, 15), fill="both", expand=True)
        
        # Video label (will be replaced with actual video)
        self.video_label = ctk.CTkLabel(
            self.canvas_frame,
            text="",
            fg_color="#000000"
        )
        self.video_label.pack(fill="both", expand=True)
    
    def get_video_label(self):
        """Get the label for video display"""
        return self.video_label


class StatusBar(ctk.CTkFrame):
    """Modern status bar"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.configure(
            fg_color=THEME_COLORS['sidebar'],
            corner_radius=0,
            height=40
        )
        
        # Status indicator
        self.indicator = ctk.CTkLabel(
            self,
            text="●",
            font=("Segoe UI", 16),
            text_color=THEME_COLORS['text_secondary']
        )
        self.indicator.pack(side="left", padx=(15, 5))
        
        # Status text
        self.status_text = ctk.CTkLabel(
            self,
            text="Ready",
            font=("Segoe UI", 11),
            text_color=THEME_COLORS['text']
        )
        self.status_text.pack(side="left")
        
    def set_status(self, text, status_type="info"):
        """Update status bar"""
        colors = {
            'success': THEME_COLORS['success'],
            'warning': THEME_COLORS['warning'],
            'danger': THEME_COLORS['danger'],
            'info': THEME_COLORS['info']
        }
        
        self.indicator.configure(text_color=colors.get(status_type, THEME_COLORS['text_secondary']))
        self.status_text.configure(text=text)


class InfoCard(ctk.CTkFrame):
    """Information display card"""
    
    def __init__(self, parent, title, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.configure(
            fg_color=THEME_COLORS['card_bg'],
            corner_radius=12,
            border_width=1,
            border_color=THEME_COLORS['accent']
        )
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text=title,
            font=("Segoe UI", 13, "bold"),
            text_color=THEME_COLORS['text']
        )
        title_label.pack(pady=(12, 8), padx=12, anchor="w")
        
        # Content frame
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
