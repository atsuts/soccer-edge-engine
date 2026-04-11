#!/usr/bin/env python3
"""
# =============================================================================
# SOCCER EDGE ENGINE - OLD DASHBOARD PROTOTYPE
# =============================================================================
# This is an OLD dashboard prototype for Soccer Edge Engine project.
# Use soccer_gui.py as the main launcher instead.
# =============================================================================

import tkinter as tk
from tkinter import ttk, font
import random
from datetime import datetime, timedelta

# Color Scheme
BG = "#0f0f14"
CARD = "#1a1a1f"
CARD_HOVER = "#25252f"
TEXT = "#ffffff"
MUTED = "#888888"
GREEN = "#00ff88"
RED = "#ff4444"
YELLOW = "#ffaa00"
BLUE = "#4488ff"
PURPLE = "#aa44ff"
EDGE_POSITIVE = "#00ff88"
EDGE_NEGATIVE = "#ff4444"
EDGE_NEUTRAL = "#888888"

class SoccerDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Soccer Edge Engine")
        self.root.geometry("1400x900")
        self.root.configure(bg=BG)
        
        # Data storage
        self.matches = self.generate_mock_data()
        self.watchlist = set()
        self.selected_match = None
        self.current_tab = "All"
        
        # Fonts
        self.header_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self.team_font = font.Font(family="Segoe UI", size=10)
        self.score_font = font.Font(family="Segoe UI", size=11, weight="bold")
        self.edge_font = font.Font(family="Segoe UI", size=9, weight="bold")
        
        self.create_layout()
        self.populate_matches()
        
    def generate_mock_data(self):
        """Generate mock match data for demonstration"""
        matches = []
        
        # Serie A matches
        for i in range(5):
            matches.append({
                'id': f'serie_a_{i}',
                'league': 'Serie A — Italy',
                'home': 'Inter Milan' if i == 0 else ['Juventus', 'AC Milan', 'Napoli', 'Roma'][i-1],
                'away': ['AC Milan', 'Juventus', 'Inter Milan', 'Lazio', 'Fiorentina'][i],
                'score': f"{random.randint(0,3)}-{random.randint(0,2)}" if random.random() > 0.3 else "-",
                'status': random.choice(['LIVE', 'HT', 'FT', "15'", "30'", "45'"]),
                'edge': round(random.uniform(-15, 25), 1),
                'has_alert': random.random() > 0.7
            })
        
        # Premier League matches
        for i in range(6):
            matches.append({
                'id': f'premier_league_{i}',
                'league': 'Premier League — England',
                'home': ['Manchester City', 'Liverpool', 'Arsenal', 'Chelsea', 'Man United', 'Tottenham'][i],
                'away': ['Liverpool', 'Manchester City', 'Chelsea', 'Arsenal', 'Newcastle', 'West Ham'][i],
                'score': f"{random.randint(0,4)}-{random.randint(0,3)}" if random.random() > 0.3 else "-",
                'status': random.choice(['LIVE', 'HT', 'FT', "20'", "35'", "60'"]),
                'edge': round(random.uniform(-20, 30), 1),
                'has_alert': random.random() > 0.6
            })
        
        # La Liga matches
        for i in range(4):
            matches.append({
                'id': f'la_liga_{i}',
                'league': 'La Liga — Spain',
                'home': ['Real Madrid', 'Barcelona', 'Atletico', 'Sevilla'][i],
                'away': ['Barcelona', 'Real Madrid', 'Real Sociedad', 'Real Betis'][i],
                'score': f"{random.randint(0,3)}-{random.randint(0,2)}" if random.random() > 0.3 else "-",
                'status': random.choice(['LIVE', 'HT', 'FT', "25'", "50'", "70'"]),
                'edge': round(random.uniform(-12, 22), 1),
                'has_alert': random.random() > 0.8
            })
        
        return matches
    
    def create_layout(self):
        """Create the main layout structure"""
        # Top summary strip
        self.create_summary_strip()
        
        # Main area with 3 panels
        main_frame = tk.Frame(self.root, bg=BG)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure grid weights
        main_frame.grid_columnconfigure(0, weight=1)  # Left panel
        main_frame.grid_columnconfigure(1, weight=2)  # Center panel
        main_frame.grid_columnconfigure(2, weight=1)  # Right panel
        
        # Create panels
        self.create_left_panel(main_frame)
        self.create_center_panel(main_frame)
        self.create_right_panel(main_frame)
    
    def create_summary_strip(self):
        """Create top summary strip"""
        summary_frame = tk.Frame(self.root, bg=CARD, height=60)
        summary_frame.pack(fill="x", padx=10, pady=(10, 0))
        summary_frame.pack_propagate(False)
        
        # Three summary boxes
        for i, (label, value, color) in enumerate([
            ("Recommended", "OVER 2.5", GREEN),
            ("Confidence", "78%", YELLOW),
            ("Best Edge", "+12.4", EDGE_POSITIVE)
        ]):
            box_frame = tk.Frame(summary_frame, bg=CARD, relief="ridge", borderwidth=1)
            box_frame.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            summary_frame.grid_columnconfigure(i, weight=1)
            
            tk.Label(box_frame, text=label, bg=CARD, fg=MUTED, 
                    font=("Segoe UI", 9)).pack(pady=(5, 0))
            tk.Label(box_frame, text=value, bg=CARD, fg=color, 
                    font=("Segoe UI", 14, "bold")).pack(pady=(0, 5))
    
    def create_left_panel(self, parent):
        """Create left scanner panel"""
        left_frame = tk.Frame(parent, bg=CARD)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Top controls
        controls_frame = tk.Frame(left_frame, bg=CARD)
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        # Search input
        tk.Label(controls_frame, text="Search:", bg=CARD, fg=TEXT,
                font=("Segoe UI", 10)).pack(anchor="w")
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(controls_frame, textvariable=self.search_var, bg=CARD_HOVER, 
                              fg=TEXT, insertbackground=TEXT, font=("Segoe UI", 10))
        search_entry.pack(fill="x", pady=(5, 10))
        search_entry.bind('<KeyRelease>', self.on_search)
        
        # Country and League dropdowns
        dropdown_frame = tk.Frame(controls_frame, bg=CARD)
        dropdown_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(dropdown_frame, text="Country:", bg=CARD, fg=TEXT,
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
        self.country_var = tk.StringVar(value="All")
        country_combo = ttk.Combobox(dropdown_frame, textvariable=self.country_var, 
                                   values=["All", "Italy", "England", "Spain"],
                                   state="readonly", width=12)
        country_combo.pack(side="left", padx=(5, 20))
        country_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        
        tk.Label(dropdown_frame, text="League:", bg=CARD, fg=TEXT,
                font=("Segoe UI", 10)).pack(side="left")
        self.league_var = tk.StringVar(value="All")
        league_combo = ttk.Combobox(dropdown_frame, textvariable=self.league_var,
                                  values=["All", "Serie A", "Premier League", "La Liga"],
                                  state="readonly", width=12)
        league_combo.pack(side="left", padx=(5, 0))
        league_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        
        # Tab buttons
        tabs_frame = tk.Frame(left_frame, bg=CARD)
        tabs_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.tab_buttons = {}
        for tab in ["All", "Live", "Today", "Upcoming", "Finished", "Watchlist"]:
            btn = tk.Button(tabs_frame, text=tab, bg=CARD_HOVER, fg=TEXT,
                         font=("Segoe UI", 9, "bold"), relief="flat",
                         command=lambda t=tab: self.switch_tab(t))
            btn.pack(side="left", padx=1, fill="x", expand=True)
            self.tab_buttons[tab] = btn
        
        # Highlight default tab
        self.tab_buttons["All"].configure(bg=BLUE)
        
        # Scrollable match feed
        self.create_match_feed(left_frame)
    
    def create_match_feed(self, parent):
        """Create scrollable match feed"""
        feed_frame = tk.Frame(parent, bg=CARD)
        feed_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(feed_frame, bg=CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(feed_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=CARD)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.canvas = canvas
        self.match_widgets = {}
    
    def create_center_panel(self, parent):
        """Create center match workspace panel"""
        center_frame = tk.Frame(parent, bg=CARD)
        center_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        # Default empty state
        self.center_content = tk.Frame(center_frame, bg=CARD)
        self.center_content.pack(fill="both", expand=True, padx=15, pady=15)
        
        tk.Label(self.center_content, text="Select a match to analyze", 
                bg=CARD, fg=MUTED, font=("Segoe UI", 16)).pack(expand=True)
    
    def create_right_panel(self, parent):
        """Create right edge analysis panel"""
        right_frame = tk.Frame(parent, bg=CARD)
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        
        # Default empty state
        self.right_content = tk.Frame(right_frame, bg=CARD)
        self.right_content.pack(fill="both", expand=True, padx=15, pady=15)
        
        tk.Label(self.right_content, text="No analysis selected", 
                bg=CARD, fg=MUTED, font=("Segoe UI", 16)).pack(expand=True)
    
    def populate_matches(self):
        """Populate match feed with matches"""
        # Clear existing widgets
        for widget in self.match_widgets.values():
            widget.destroy()
        self.match_widgets.clear()
        
        # Group matches by league
        leagues = {}
        for match in self.matches:
            if match['league'] not in leagues:
                leagues[match['league']] = []
            leagues[match['league']].append(match)
        
        # Create league sections
        row = 0
        for league_name, league_matches in leagues.items():
            # League header
            header = tk.Label(self.scrollable_frame, text=league_name, 
                           bg=CARD, fg=BLUE, font=self.header_font, anchor="w")
            header.grid(row=row, column=0, sticky="ew", padx=10, pady=(10, 5))
            self.match_widgets[f"header_{league_name}"] = header
            row += 1
            
            # Match rows
            for match in league_matches:
                self.create_match_row(match, row)
                row += 1
    
    def create_match_row(self, match, row):
        """Create a single match row"""
        row_frame = tk.Frame(self.scrollable_frame, bg=CARD_HOVER, relief="solid", borderwidth=1)
        row_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
        self.match_widgets[match['id']] = row_frame
        
        # Edge bar
        edge_color = EDGE_POSITIVE if match['edge'] > 0 else EDGE_NEGATIVE if match['edge'] < 0 else EDGE_NEUTRAL
        edge_bar = tk.Frame(row_frame, bg=edge_color, width=3)
        edge_bar.pack(side="left", fill="y")
        
        # Content
        content_frame = tk.Frame(row_frame, bg=CARD_HOVER)
        content_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        
        # Status
        status_label = tk.Label(content_frame, text=match['status'], bg=CARD_HOVER, 
                              fg=MUTED, font=("Segoe UI", 8), width=5)
        status_label.pack(side="left", padx=(0, 10))
        
        # Teams (two lines)
        teams_frame = tk.Frame(content_frame, bg=CARD_HOVER)
        teams_frame.pack(side="left", padx=(0, 15))
        
        home_label = tk.Label(teams_frame, text=match['home'], bg=CARD_HOVER, 
                            fg=TEXT, font=self.team_font, anchor="w")
        home_label.pack(anchor="w")
        
        away_label = tk.Label(teams_frame, text=match['away'], bg=CARD_HOVER, 
                            fg=TEXT, font=self.team_font, anchor="w")
        away_label.pack(anchor="w")
        
        # Score
        score_label = tk.Label(content_frame, text=match['score'], bg=CARD_HOVER, 
                            fg=TEXT, font=self.score_font, width=6)
        score_label.pack(side="left", padx=15)
        
        # Edge value
        edge_color = EDGE_POSITIVE if match['edge'] > 0 else EDGE_NEGATIVE if match['edge'] < 0 else EDGE_NEUTRAL
        edge_label = tk.Label(content_frame, text=f"{match['edge']:+.1f}", bg=CARD_HOVER, 
                            fg=edge_color, font=self.edge_font, width=6)
        edge_label.pack(side="left", padx=10)
        
        # Watchlist star
        star_text = "★" if match['id'] in self.watchlist else "☆"
        star_btn = tk.Button(content_frame, text=star_text, bg=CARD_HOVER, fg=YELLOW,
                         font=("Segoe UI", 12), relief="flat", borderwidth=0,
                         command=lambda m=match: self.toggle_watchlist(m))
        star_btn.pack(side="left", padx=5)
        
        # Alert icon
        if match['has_alert']:
            alert_btn = tk.Button(content_frame, text="△", bg=CARD_HOVER, fg=RED,
                             font=("Segoe UI", 10), relief="flat", borderwidth=0,
                             state="disabled")
            alert_btn.pack(side="left", padx=5)
        
        # Click binding for match selection
        row_frame.bind("<Button-1>", lambda e, m=match: self.select_match(m))
        for widget in content_frame.winfo_children():
            widget.bind("<Button-1>", lambda e, m=match: self.select_match(m))
    
    def select_match(self, match):
        """Handle match selection"""
        self.selected_match = match
        self.update_center_panel()
    
    def toggle_watchlist(self, match):
        """Toggle match in watchlist"""
        if match['id'] in self.watchlist:
            self.watchlist.remove(match['id'])
        else:
            self.watchlist.add(match['id'])
        self.populate_matches()
    
    def switch_tab(self, tab):
        """Switch between tabs"""
        # Reset all tab buttons
        for btn in self.tab_buttons.values():
            btn.configure(bg=CARD_HOVER)
        
        # Highlight selected tab
        self.tab_buttons[tab].configure(bg=BLUE)
        self.current_tab = tab
        
        # Filter matches based on tab
        self.filter_matches()
    
    def filter_matches(self):
        """Filter matches based on current tab and search"""
        # This would filter the matches list
        # For now, just repopulate with same data
        self.populate_matches()
    
    def on_search(self, event):
        """Handle search input"""
        self.filter_matches()
    
    def on_filter_change(self, event):
        """Handle country/league filter change"""
        self.filter_matches()
    
    def update_center_panel(self):
        """Update center panel with selected match"""
        # Clear existing content
        for widget in self.center_content.winfo_children():
            widget.destroy()
        
        if not self.selected_match:
            return
        
        match = self.selected_match
        
        # Match header
        header_frame = tk.Frame(self.center_content, bg=CARD)
        header_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(header_frame, text=match['league'], bg=CARD, fg=BLUE,
                font=("Segoe UI", 12)).pack(anchor="w")
        
        title_frame = tk.Frame(header_frame, bg=CARD)
        title_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(title_frame, text=f"{match['home']} vs {match['away']}", bg=CARD, fg=TEXT,
                font=("Segoe UI", 18, "bold")).pack(side="left")
        
        tk.Label(title_frame, text=match['score'], bg=CARD, fg=TEXT,
                font=("Segoe UI", 20, "bold")).pack(side="right", padx=(20, 0))
        
        tk.Label(header_frame, text=f"Status: {match['status']}", bg=CARD, fg=MUTED,
                font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 0))
        
        # Tabs
        tabs_frame = tk.Frame(self.center_content, bg=CARD)
        tabs_frame.pack(fill="x", pady=20)
        
        self.detail_tabs = {}
        for tab in ["Info", "Stats", "Lineups", "H2H", "Odds", "Timeline"]:
            btn = tk.Button(tabs_frame, text=tab, bg=CARD_HOVER, fg=TEXT,
                         font=("Segoe UI", 10, "bold"), relief="flat",
                         command=lambda t=tab: self.show_detail_tab(t))
            btn.pack(side="left", padx=1, fill="x", expand=True)
            self.detail_tabs[tab] = btn
        
        # Detail content area
        self.detail_content = tk.Frame(self.center_content, bg=CARD)
        self.detail_content.pack(fill="both", expand=True, pady=20)
        
        # Default to Info tab
        self.show_detail_tab("Info")
        
        # Deep Analyze button
        analyze_btn = tk.Button(self.center_content, text="Deep Analyze", bg=GREEN, fg=BG,
                             font=("Segoe UI", 12, "bold"), relief="flat",
                             command=self.deep_analyze)
        analyze_btn.pack(pady=20)
    
    def show_detail_tab(self, tab):
        """Show detail tab content"""
        # Reset all tab buttons
        for btn in self.detail_tabs.values():
            btn.configure(bg=CARD_HOVER)
        
        # Highlight selected tab
        self.detail_tabs[tab].configure(bg=BLUE)
        
        # Clear detail content
        for widget in self.detail_content.winfo_children():
            widget.destroy()
        
        # Show placeholder content
        tk.Label(self.detail_content, text=f"{tab} content for {self.selected_match['home']} vs {self.selected_match['away']}",
                bg=CARD, fg=MUTED, font=("Segoe UI", 12)).pack(expand=True)
    
    def deep_analyze(self):
        """Perform deep analysis and update right panel"""
        if not self.selected_match:
            return
        
        # Update right panel
        for widget in self.right_content.winfo_children():
            widget.destroy()
        
        match = self.selected_match
        
        # Analysis sections
        sections = [
            ("Final Recommendation", "OVER 2.5", GREEN),
            ("Confidence", "82%", YELLOW),
            ("Best Edge", f"{match['edge']:+.1f}", EDGE_POSITIVE if match['edge'] > 0 else EDGE_NEGATIVE),
            ("Reasons", "• Strong attacking form\n• Weak defensive record\n• Historical head-to-head", TEXT),
            ("Risk", "Medium", YELLOW),
            ("Market Notes", "Odds movement detected\nVolume increase on Over", MUTED)
        ]
        
        for title, content, color in sections:
            section_frame = tk.Frame(self.right_content, bg=CARD_HOVER, relief="ridge", borderwidth=1)
            section_frame.pack(fill="x", pady=5)
            
            tk.Label(section_frame, text=title, bg=CARD_HOVER, fg=BLUE,
                    font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
            tk.Label(section_frame, text=content, bg=CARD_HOVER, fg=color,
                    font=("Segoe UI", 9), wraplength=200, justify="left").pack(anchor="w", padx=10, pady=(0, 8))

def main():
    root = tk.Tk()
    app = SoccerDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()
