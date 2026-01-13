import customtkinter as ctk
from datetime import datetime
from tkinter import filedialog
import re
import os

# ============================================
# FILE PATH CONFIGURATION
# ============================================
DEFAULT_FILE_PATH = "test.txt"  # Relative path to your DID file

# --- Theme Configuration ---
ctk.set_appearance_mode("Dark")

# Precise Hex Codes from Screenshot Analysis
VALEO_GREEN = "#82E600"
VALEO_BLUE = "#4888D1"
FLASH_GREEN = "#55A630"
BG_MAIN = "#202024"        # Deep dashboard gray
SIDEBAR_BG = "#2B2B30"     # Slightly lighter sidebar
BORDER_GRAY = "#444448"    # Border color for sections
TEXT_LABEL_GRAY = "#AAAAAA" # Secondary text color

class ValeoProfessionalGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("Valeo Advanced Diagnostic & Flashing Tool")
        self.geometry("1300x750")
        self.configure(fg_color=BG_MAIN)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- DID Functionality Variables ---
        self.file_path = DEFAULT_FILE_PATH
        self.file_content = ""  # Cached file content for faster access
        self.all_dids = []  # List of all DID hex values
        self.selected_did_hex = None
        self.selected_did_length = None
        self.is_selecting_from_list = False  # Flag to prevent dropdown reopening

        # --- 1. SIDEBAR (Command Rail) ---
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=SIDEBAR_BG, border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        # BRAND SECTION (Logo + Corrected Swoosh Placement)
        self.brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=120)
        self.brand_frame.grid(row=0, column=0, padx=20, pady=(60, 70))
        self.brand_frame.pack_propagate(False) # Maintain fixed size for precise logo placement
        
        self.brand = ctk.CTkLabel(self.brand_frame, text="Valeo", 
                                  font=("Arial", 60, "bold", "italic"), 
                                  text_color=VALEO_GREEN)
        self.brand.pack(pady=(0, 0))
        
        # FIX: Using .place() for the swoosh to avoid the 'bad pad value' crash
        self.swash = ctk.CTkLabel(self.brand_frame, text="◣──────────", 
                                  font=("Arial", 20, "bold"), text_color="#435D61")
        self.swash.place(x=5, y=55) # Absolute placement to mimic the image swoosh precisely

        # ACTION BUTTONS
        self.btn_sig = ctk.CTkButton(self.sidebar, text="🔑 Generate Signature", 
                                     height=55, font=("Arial", 16, "bold"),
                                     fg_color=VALEO_BLUE, hover_color="#3A6DA8",
                                     corner_radius=10, anchor="w")
        self.btn_sig.grid(row=1, column=0, padx=25, pady=12, sticky="ew")

        self.btn_flash = ctk.CTkButton(self.sidebar, text="⚡ Start Flashing", 
                                       height=55, font=("Arial", 16, "bold"),
                                       fg_color=FLASH_GREEN, hover_color="#458A26",
                                       corner_radius=10, anchor="w")
        self.btn_flash.grid(row=2, column=0, padx=25, pady=12, sticky="ew")

        # BOTTOM BUTTONS
        self.btn_help = ctk.CTkButton(self.sidebar, text="❓ Help", 
                                      fg_color="#333338", height=42, hover_color="#444", anchor="w")
        self.btn_help.grid(row=5, column=0, padx=25, pady=5, sticky="ew")

        self.btn_about = ctk.CTkButton(self.sidebar, text="ℹ️ About", 
                                       fg_color="#333338", height=42, hover_color="#444", anchor="w")
        self.btn_about.grid(row=6, column=0, padx=25, pady=(5, 40), sticky="ew")

        # --- 2. WORKSPACE ---
        self.workspace = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace.grid(row=0, column=1, sticky="nsew", padx=35, pady=35)
        self.workspace.grid_columnconfigure(0, weight=3)
        self.workspace.grid_columnconfigure(1, weight=2)
        self.workspace.grid_rowconfigure(1, weight=1)

        # BOX A: Setup & Configuration
        self.setup_box = self.create_bordered_group(self.workspace, "⚙️ Setup & Configuration", 0, 0, padx=(0, 15))
        ctk.CTkLabel(self.setup_box, text="CANoe Channel", font=("Arial", 13), text_color=TEXT_LABEL_GRAY).pack(anchor="w", padx=25, pady=(25, 0))
        self.chan_cb = ctk.CTkComboBox(self.setup_box, values=["CANoe 1"], width=350, height=35, fg_color="#2B2B30")
        self.chan_cb.pack(anchor="w", padx=25, pady=(5, 25))

        # BOX B: DID Selection
        self.did_box = self.create_bordered_group(self.workspace, "📋 DID Selection", 0, 1)
        did_grid = ctk.CTkFrame(self.did_box, fg_color="transparent")
        did_grid.pack(fill="x", padx=25, pady=25)
        
        ctk.CTkLabel(did_grid, text="DID Number", font=("Arial", 13), text_color=TEXT_LABEL_GRAY).grid(row=0, column=0, sticky="w")
        
        # Create container for custom dropdown
        self.did_num_container = ctk.CTkFrame(did_grid, fg_color="transparent")
        self.did_num_container.grid(row=1, column=0, padx=(0, 20), pady=5, sticky="w")
        
        # Entry for DID Number with dropdown button
        self.did_entry_frame = ctk.CTkFrame(self.did_num_container, fg_color="transparent")
        self.did_entry_frame.pack(side="left")
        
        self.did_num = ctk.CTkEntry(self.did_entry_frame, width=115, height=35, fg_color="#2B2B30")
        self.did_num.pack(side="left")
        self.did_num.bind("<KeyRelease>", self.on_did_entry_change)
        self.did_num.bind("<Return>", self.validate_did_selection)
        self.did_num.bind("<Down>", self.on_entry_arrow_down)  # Move to dropdown with Down arrow
        self.did_num.bind("<Up>", self.on_entry_arrow_up)      # Move to dropdown with Up arrow
        # Note: Removed FocusOut binding to prevent validation when clicking arrow
        
        # Dropdown arrow button
        self.did_arrow_btn = ctk.CTkButton(self.did_entry_frame, text="▼", width=25, height=35,
                                          fg_color="#2B2B30", hover_color="#3B3B40",
                                          command=self.toggle_did_dropdown)
        self.did_arrow_btn.pack(side="left")
        
        # Create dropdown window (will be shown/hidden as needed)
        import tkinter as tk
        self.dropdown_window = None
        self.did_listbox = None
        self.did_scrollbar = None

        ctk.CTkLabel(did_grid, text="DID Value", font=("Arial", 13), text_color=TEXT_LABEL_GRAY).grid(row=0, column=1, sticky="w")
        self.did_val = ctk.CTkEntry(did_grid, width=140, height=35, placeholder_text="0", fg_color="#0D0D0F",
                                    state="disabled")
        self.did_val.grid(row=1, column=1, pady=5)
        self.did_val.bind("<Return>", self.validate_and_update_data)

        # BOX C: Output Log
        self.log_box = self.create_bordered_group(self.workspace, "Output Log", 1, 0, columnspan=2, pady=(25, 0))
        self.terminal = ctk.CTkTextbox(self.log_box, font=("Consolas", 14), fg_color="#0D0D0F", border_width=0)
        self.terminal.pack(fill="both", expand=True, padx=15, pady=(25, 75))
        
        self.terminal.tag_config("gray", foreground="#666666")
        self.terminal.tag_config("blue", foreground=VALEO_BLUE)
        self.terminal.tag_config("green", foreground=VALEO_GREEN)
        self.terminal.tag_config("red", foreground="#F44336")  # Red for errors

        # UTILITY BUTTONS (Correctly Aligned)
        self.button_container = ctk.CTkFrame(self.log_box, fg_color="transparent")
        self.button_container.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")

        self.btn_save = ctk.CTkButton(self.button_container, text="💾 Save Log", width=110, height=32, fg_color="#333338",
                                      command=self.save_log)
        self.btn_save.pack(side="left", padx=(0, 10))
        
        self.btn_clear = ctk.CTkButton(self.button_container, text="🗑️ Clear Output", width=130, height=32, fg_color="#333338",
                                       command=self.clear_output)
        self.btn_clear.pack(side="left")

        # Load DID file on startup
        self.load_did_file()
        
        # Bind window move/resize to close dropdown
        self.bind('<Configure>', self.on_window_configure)
        
        # Initial Log entry
        self.log_entry("Diagnostic Engine Online", "green")

    def create_bordered_group(self, parent, title, row, col, columnspan=1, padx=0, pady=0):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=col, columnspan=columnspan, sticky="nsew", padx=padx, pady=pady)
        border_frame = ctk.CTkFrame(container, border_width=1, border_color=BORDER_GRAY, fg_color="transparent")
        border_frame.pack(fill="both", expand=True, pady=(12, 0))
        title_label = ctk.CTkLabel(container, text=f" {title} ", bg_color=BG_MAIN, font=("Arial", 14, "bold"))
        title_label.place(x=20, y=0)
        return border_frame

    def log_entry(self, message, color="white"):
        # Format: [HH:MM:SS:mmmm] with 4-digit milliseconds
        now = datetime.now()
        stamp = now.strftime("[%H:%M:%S:") + f"{now.microsecond // 100:04d}]"
        
        # Temporarily enable editing to insert text
        self.terminal.configure(state="normal")
        self.terminal.insert("end", f"{stamp} ", "gray")
        self.terminal.insert("end", f"Flashing the {message}\n", color)
        self.terminal.see("end")
        # Make read-only again
        self.terminal.configure(state="disabled")
    
    # ============================================
    # LOG FUNCTIONALITY
    # ============================================
    
    def save_log(self):
        """Save the output log to a file"""
        from tkinter import filedialog
        
        # Open file save dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Log files", "*.log"), ("All files", "*.*")],
            title="Save Log File"
        )
        
        if file_path:
            try:
                # Get all text from terminal
                log_content = self.terminal.get("1.0", "end-1c")
                
                # Write to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                
                self.log_entry(f"Log saved to: {file_path}", "green")
            except Exception as e:
                self.log_entry(f"Error saving log: {str(e)}", "red")
    
    def clear_output(self):
        """Clear the output log"""
        # Temporarily enable to clear, then disable again
        self.terminal.configure(state="normal")
        self.terminal.delete("1.0", "end")
        self.terminal.configure(state="disabled")
    
    # ============================================
    # DID DROPDOWN FUNCTIONALITY
    # ============================================
    
    def toggle_did_dropdown(self):
        """Toggle the DID dropdown list visibility"""
        import tkinter as tk
        
        # If dropdown exists and is visible, destroy it
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            self.dropdown_window.destroy()
            self.dropdown_window = None
            return
        
        if not self.all_dids:
            self.log_entry("No DID values loaded", "red")
            return
        
        # Create new dropdown window
        self.dropdown_window = tk.Toplevel(self)
        self.dropdown_window.overrideredirect(True)  # Remove window decorations
        self.dropdown_window.configure(bg="#2B2B30")
        
        # Get position of entry field
        entry_x = self.did_num.winfo_rootx()
        entry_y = self.did_num.winfo_rooty()
        entry_height = self.did_num.winfo_height()
        entry_width = self.did_num.winfo_width() + self.did_arrow_btn.winfo_width()
        
        # Position dropdown below entry
        self.dropdown_window.geometry(f"{entry_width}x200+{entry_x}+{entry_y + entry_height + 2}")
        
        # Create frame for listbox and scrollbar
        frame = tk.Frame(self.dropdown_window, bg="#2B2B30")
        frame.pack(fill="both", expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        # Listbox
        self.did_listbox = tk.Listbox(
            frame,
            font=("Arial", 11),
            bg="#2B2B30",
            fg="white",
            selectbackground="#4A4A50",
            selectforeground="white",
            relief="flat",
            yscrollcommand=scrollbar.set,
            activestyle='none',
            highlightthickness=0,
            borderwidth=1
        )
        self.did_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.did_listbox.yview)
        
        # Populate listbox
        sorted_dids = sorted(self.all_dids)
        for did in sorted_dids:
            self.did_listbox.insert("end", did)
        
        # Bind events
        self.did_listbox.bind('<ButtonRelease-1>', self.on_listbox_click)  # Single click
        self.did_listbox.bind('<Double-Button-1>', self.on_listbox_double_click)
        self.did_listbox.bind('<Motion>', self.on_listbox_hover)  # Mouse hover
        
        # Keyboard navigation
        self.did_listbox.bind('<Return>', self.on_listbox_enter)  # Enter key to select
        self.did_listbox.bind('<Escape>', lambda e: self.close_dropdown())  # Escape to close
        self.did_listbox.bind('<Up>', self.on_arrow_key)  # Up arrow
        self.did_listbox.bind('<Down>', self.on_arrow_key)  # Down arrow
        
        # Bind click outside to close
        self.dropdown_window.bind('<FocusOut>', lambda e: self.close_dropdown())
        
        # Set focus to listbox for keyboard navigation
        self.did_listbox.focus_set()
        
        # Select first item by default
        if self.did_listbox.size() > 0:
            self.did_listbox.selection_set(0)
            self.did_listbox.see(0)
    
    def close_dropdown(self):
        """Close the dropdown window"""
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            self.dropdown_window.destroy()
            self.dropdown_window = None
    
    def on_window_configure(self, event=None):
        """Handle window move/resize - close dropdown"""
        # Only close dropdown if it exists and event is for the main window
        if event and event.widget == self:
            self.close_dropdown()
    
    def on_entry_arrow_down(self, event=None):
        """Handle Down arrow in entry field - move to dropdown"""
        if self.dropdown_window and self.dropdown_window.winfo_exists() and self.did_listbox:
            # Transfer focus to listbox
            self.did_listbox.focus_set()
            # Select first item if nothing selected
            if not self.did_listbox.curselection() and self.did_listbox.size() > 0:
                self.did_listbox.selection_set(0)
                self.did_listbox.see(0)
        return "break"  # Prevent default behavior
    
    def on_entry_arrow_up(self, event=None):
        """Handle Up arrow in entry field - move to dropdown"""
        if self.dropdown_window and self.dropdown_window.winfo_exists() and self.did_listbox:
            # Transfer focus to listbox
            self.did_listbox.focus_set()
            # Select last item if nothing selected
            if not self.did_listbox.curselection() and self.did_listbox.size() > 0:
                last_index = self.did_listbox.size() - 1
                self.did_listbox.selection_set(last_index)
                self.did_listbox.see(last_index)
        return "break"  # Prevent default behavior
    
    def on_did_entry_change(self, event=None):
        """Handle changes to DID Number entry"""
        # Skip if we're programmatically setting the value from list selection
        if self.is_selecting_from_list:
            return
        
        did_value = self.did_num.get().strip()
        
        # If DID Number is empty, disable and clear DID Value, close dropdown
        if not did_value:
            self.did_val.configure(state="disabled")
            self.did_val.delete(0, "end")
            self.selected_did_hex = None
            self.selected_did_length = None
            self.close_dropdown()
        else:
            # Show filtered recommendations as user types
            self.show_filtered_dropdown(did_value)
    
    def show_filtered_dropdown(self, typed_text):
        """Show dropdown with filtered DIDs based on typed text"""
        if not self.all_dids or not typed_text:
            return
        
        # If typed text is already an exact match (case-insensitive), don't show dropdown
        typed_lower = typed_text.lower()
        if any(did.lower() == typed_lower for did in self.all_dids):
            self.close_dropdown()
            return
        
        # Filter DIDs that start with typed text (case-insensitive)
        filtered = [did for did in self.all_dids if did.lower().startswith(typed_lower)]
        
        if not filtered:
            self.close_dropdown()
            return
        
        # Close existing dropdown if any
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            self.dropdown_window.destroy()
        
        # Create new dropdown window with filtered results
        import tkinter as tk
        self.dropdown_window = tk.Toplevel(self)
        self.dropdown_window.overrideredirect(True)
        self.dropdown_window.configure(bg="#2B2B30")
        
        # Get position of entry field
        entry_x = self.did_num.winfo_rootx()
        entry_y = self.did_num.winfo_rooty()
        entry_height = self.did_num.winfo_height()
        entry_width = self.did_num.winfo_width() + self.did_arrow_btn.winfo_width()
        
        # Position dropdown below entry
        self.dropdown_window.geometry(f"{entry_width}x200+{entry_x}+{entry_y + entry_height + 2}")
        
        # Create frame for listbox and scrollbar
        frame = tk.Frame(self.dropdown_window, bg="#2B2B30")
        frame.pack(fill="both", expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        # Listbox with filtered results
        self.did_listbox = tk.Listbox(
            frame,
            font=("Arial", 11),
            bg="#2B2B30",
            fg="white",
            selectbackground="#4A4A50",
            selectforeground="white",
            relief="flat",
            yscrollcommand=scrollbar.set,
            activestyle='none',
            highlightthickness=0,
            borderwidth=1
        )
        self.did_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.did_listbox.yview)
        
        # Populate with filtered DIDs
        for did in sorted(filtered):
            self.did_listbox.insert("end", did)
        
        # Bind events
        self.did_listbox.bind('<ButtonRelease-1>', self.on_listbox_click)
        self.did_listbox.bind('<Double-Button-1>', self.on_listbox_double_click)
        self.did_listbox.bind('<Motion>', self.on_listbox_hover)
        self.did_listbox.bind('<Return>', self.on_listbox_enter)
        self.did_listbox.bind('<Escape>', lambda e: self.close_dropdown())
        self.did_listbox.bind('<Up>', self.on_arrow_key)
        self.did_listbox.bind('<Down>', self.on_arrow_key)
        
        # DON'T set focus - let user keep typing in entry field
        # Focus only set when clicking arrow button
    
    def on_listbox_hover(self, event=None):
        """Handle mouse hover over listbox items"""
        if self.did_listbox:
            # Get the index of the item under the cursor
            index = self.did_listbox.nearest(event.y)
            # Clear previous selection
            self.did_listbox.selection_clear(0, 'end')
            # Highlight the item under cursor
            self.did_listbox.selection_set(index)
            self.did_listbox.activate(index)
    
    def on_listbox_click(self, event=None):
        """Handle listbox click"""
        if self.did_listbox and self.did_listbox.curselection():
            selected = self.did_listbox.get(self.did_listbox.curselection())
            # Set flag to prevent dropdown from reopening
            self.is_selecting_from_list = True
            self.did_num.delete(0, "end")
            self.did_num.insert(0, selected)
            self.close_dropdown()
            self.on_did_selected(selected)
            # Reset flag
            self.is_selecting_from_list = False
    
    def on_arrow_key(self, event=None):
        """Handle arrow key navigation"""
        # Let the listbox handle the navigation naturally
        # This will trigger after the selection has moved
        if self.did_listbox and self.did_listbox.curselection():
            # Make sure the selected item is visible
            self.did_listbox.see(self.did_listbox.curselection()[0])
    
    def on_listbox_double_click(self, event=None):
        """Handle listbox double-click (same as single click)"""
        self.on_listbox_click(event)
    
    def on_listbox_enter(self, event=None):
        """Handle Enter key in listbox"""
        if self.did_listbox and self.did_listbox.curselection():
            selected = self.did_listbox.get(self.did_listbox.curselection())
            # Set flag to prevent dropdown from reopening
            self.is_selecting_from_list = True
            self.did_num.delete(0, "end")
            self.did_num.insert(0, selected)
            self.close_dropdown()
            self.on_did_selected(selected)
            # Reset flag
            self.is_selecting_from_list = False
    
    def validate_did_selection(self, event=None):
        """Validate DID when Enter is pressed"""
        # Close dropdown first
        self.close_dropdown()
        
        selected_did = self.did_num.get().strip()
        if selected_did:
            # Case-insensitive matching: find the actual DID from the list
            selected_did_lower = selected_did.lower()
            matching_did = None
            for did in self.all_dids:
                if did.lower() == selected_did_lower:
                    matching_did = did
                    break
            
            if matching_did:
                # Update entry with the correct case from file
                self.is_selecting_from_list = True
                self.did_num.delete(0, "end")
                self.did_num.insert(0, matching_did)
                self.on_did_selected(matching_did)
                self.is_selecting_from_list = False
            else:
                self.log_entry(f"Invalid DID: {selected_did}", "red")
                self.did_val.configure(state="disabled")
                self.did_val.delete(0, "end")
    
    # ============================================
    # DID FUNCTIONALITY
    # ============================================
    
    def load_did_file(self):
        """Load and parse the DID file"""
        if not os.path.exists(self.file_path):
            self.log_entry(f"Error: File not found - {self.file_path}", "red")
            return
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                self.file_content = file.read()  # Cache file content
            
            self.all_dids = self.parse_did_entries(self.file_content)
            
            if self.all_dids:
                self.log_entry(f"Loaded {len(self.all_dids)} DID entries", "green")
            else:
                self.log_entry("No DID entries found in file", "red")
                
        except Exception as e:
            self.log_entry(f"Error loading file: {str(e)}", "red")
    
    def parse_did_entries(self, content):
        """Parse DID entries from file content"""
        hex_values = []
        lines = content.split('\n')
        
        for line in lines:
            # Match lines like: DID3 = 0xB014
            match = re.match(r'^DID(\d+)\s*=\s*(0x[0-9A-Fa-f]+)', line, re.IGNORECASE)
            if match:
                hex_value = match.group(2)
                if hex_value not in hex_values:
                    hex_values.append(hex_value)
        
        return sorted(hex_values)
    
    def on_did_selected(self, selected_value):
        """Called when a DID is selected from dropdown"""
        if selected_value and selected_value in self.all_dids:
            self.selected_did_hex = selected_value
            # Enable DID Value entry
            self.did_val.configure(state="normal")
            self.did_val.delete(0, "end")
            # Read DataLength for this DID
            self.read_did_data_length(selected_value)
            # Log the selection with DID number
            self.log_did_selection(selected_value)
        else:
            self.did_val.configure(state="disabled")
            self.did_val.delete(0, "end")
    
    def log_did_selection(self, did_hex_value):
        """Log the DID selection with DID number"""
        if not self.file_content:
            return
        
        try:
            lines = self.file_content.split('\n')
            
            # Find the DID number
            for line in lines:
                match = re.match(r'^DID(\d+)\s*=\s*' + re.escape(did_hex_value), line, re.IGNORECASE)
                if match:
                    did_number = match.group(1)
                    self.log_entry(f"DID{did_number} = {did_hex_value} is selected", "blue")
                    return
        
        except Exception as e:
            pass  # Silently fail if can't find DID number
    
    def read_did_data_length(self, did_hex_value):
        """Read the DataLength for the selected DID"""
        if not self.file_content:
            return
        
        try:
            lines = self.file_content.split('\n')
            
            # Find the DID number
            did_number = None
            for line in lines:
                match = re.match(r'^DID(\d+)\s*=\s*' + re.escape(did_hex_value), line, re.IGNORECASE)
                if match:
                    did_number = match.group(1)
                    break
            
            if did_number:
                # Find DataLength for this DID
                pattern = f'^DataLength{did_number}\\s*=\\s*(0x[0-9A-Fa-f]+)'
                for line in lines:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        data_length_hex = match.group(1)
                        self.selected_did_length = int(data_length_hex, 16)
                        return
        
        except Exception as e:
            self.log_entry(f"Error reading DataLength: {str(e)}", "red")
    
    def validate_and_update_data(self, event=None):
        """Validate hex input and update file"""
        if not self.selected_did_hex:
            self.log_entry("Please select a DID first", "red")
            return
        
        current_value = self.did_val.get().strip()
        
        # Validate hex format
        if not current_value.lower().startswith('0x'):
            self.log_entry("Error: Value must start with '0x'", "red")
            return
        
        # Check if it's just "0x" without any digits
        if len(current_value) <= 2:
            self.log_entry("Error: Please enter a valid hex value after '0x'", "red")
            return
        
        try:
            # Remove 0x prefix for validation
            hex_digits = current_value[2:]
            value_int = int(hex_digits, 16)
            
            # Validate against DataLength
            if self.selected_did_length:
                max_value = (256 ** self.selected_did_length) - 1
                if value_int > max_value:
                    self.log_entry(f"Error: Value exceeds DataLength ({self.selected_did_length} byte(s))", "red")
                    return
                
                # Format with leading zeros based on DataLength
                formatted_hex = f"0x{value_int:0{self.selected_did_length*2}X}"
                self.did_val.delete(0, "end")
                self.did_val.insert(0, formatted_hex)
                current_value = formatted_hex
            
            # Update file
            self.update_data_in_file(self.selected_did_hex, current_value)
            
        except ValueError:
            self.log_entry("Error: Invalid hexadecimal value", "red")
    
    def update_data_in_file(self, did_hex_value, new_data_value):
        """Update _Data value in the file"""
        if not os.path.exists(self.file_path):
            self.log_entry("Error: File not found", "red")
            return
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # Find the DID number
            did_number = None
            for line in lines:
                match = re.match(r'^DID(\d+)\s*=\s*' + re.escape(did_hex_value), line, re.IGNORECASE)
                if match:
                    did_number = match.group(1)
                    break
            
            if not did_number:
                self.log_entry(f"Error: DID {did_hex_value} not found in file", "red")
                return
            
            # Find and update _Data line
            pattern = f'^(_Data{did_number}\\s*=\\s*)0x[0-9A-Fa-f]+'
            updated = False
            
            for i, line in enumerate(lines):
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    lines[i] = f"{match.group(1)}{new_data_value}\n"
                    updated = True
                    break
            
            if updated:
                with open(self.file_path, 'w', encoding='utf-8') as file:
                    file.writelines(lines)
                # Update cached content
                self.file_content = ''.join(lines)
                self.log_entry(f"Updated Data{did_number} = {new_data_value}", "green")
            else:
                self.log_entry(f"Error: _Data{did_number} entry not found", "red")
                
        except Exception as e:
            self.log_entry(f"Error updating file: {str(e)}", "red")

if __name__ == "__main__":
    app = ValeoProfessionalGUI()
    app.mainloop()