
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, colorchooser
from PIL import Image, ImageTk
import numpy as np
import os

class PixelEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pixel Editor to VGA C Array Converter")
        self.root.geometry("1280x720")
        
        # Image properties
        self.source_image = None
        self.edited_image = None
        self.pixel_data = None
        self.canvas_image = None
        
        # Editor settings
        self.cell_size = 16  # Size of each pixel in the editor
        self.editor_width = 32  # Width of the editor in pixels
        self.editor_height = 32  # Height of the editor in pixels
        self.current_color = "#FF0000"  # Default color (red)
        self.editor_zoom = 1.0  # Initial zoom level
        
        # VGA specific settings
        self.max_width = 320
        self.max_height = 240
        
        # Create UI components
        self.create_menu()
        self.create_toolbar()
        self.create_main_frame()
        
        # Initialize color palette
        self.init_color_palette()
        
        # Initialize with an empty editor
        self.new_image()
        
    def open_image(self):
        """Open an image file and load it into the editor"""
        file_path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=(
                ("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
                ("All files", "*.*")
            )
        )
        
        if file_path:
            try:
                # Open the image with PIL
                img = Image.open(file_path)
                
                # Ask if user wants to resize the image
                if img.width > self.max_width or img.height > self.max_height:
                    if messagebox.askyesno("Resize Image", 
                                          f"The image is larger than the maximum dimensions ({self.max_width}x{self.max_height}). "
                                          "Would you like to resize it to fit?"):
                        # Calculate new dimensions preserving aspect ratio
                        ratio = min(self.max_width / img.width, self.max_height / img.height)
                        new_width = int(img.width * ratio)
                        new_height = int(img.height * ratio)
                        img = img.resize((new_width, new_height), Image.LANCZOS)
                
                # Update dimensions
                self.editor_width = img.width
                self.editor_height = img.height
                self.width_var.set(str(self.editor_width))
                self.height_var.set(str(self.editor_height))
                
                # Convert to RGB mode if needed
                if img.mode != "RGB":
                    img = img.convert("RGB")
                
                # Update the image and pixel data
                self.edited_image = img
                self.pixel_data = np.array(img)
                
                # Reset canvas and redraw
                self.setup_canvas()
                self.draw_editor()
                self.update_preview()
                
                # Ask if user wants to also use this as a reference image
                if messagebox.askyesno("Reference Image", 
                                      "Would you like to also use this image as a reference?"):
                    self.reference_image = img.copy()
                    self.display_reference()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open image: {str(e)}")
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_image)
        file_menu.add_command(label="Open Image", command=self.open_image)
        file_menu.add_command(label="Load Reference", command=self.load_reference)
        file_menu.add_separator()
        file_menu.add_command(label="Import C Array", command=self.import_c_array)
        file_menu.add_command(label="Save C Array", command=self.save_c_array)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Clear All", command=self.clear_all)
        edit_menu.add_command(label="Choose Color", command=self.choose_color)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=lambda: self.set_zoom(self.editor_zoom * 1.2))
        view_menu.add_command(label="Zoom Out", command=lambda: self.set_zoom(self.editor_zoom * 0.8))
        view_menu.add_command(label="Reset Zoom", command=lambda: self.set_zoom(1.0))
        view_menu.add_separator()
        view_menu.add_command(label="Show Grid", command=self.toggle_grid)
        menubar.add_cascade(label="View", menu=view_menu)
        
        self.root.config(menu=menubar)
    
    def create_toolbar(self):
        toolbar_frame = ttk.Frame(self.root, padding="5")
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Size controls
        ttk.Label(toolbar_frame, text="Width:").pack(side=tk.LEFT, padx=2)
        self.width_var = tk.StringVar(value=str(self.editor_width))
        width_entry = ttk.Entry(toolbar_frame, textvariable=self.width_var, width=4)
        width_entry.pack(side=tk.LEFT, padx=2)
        width_entry.bind("<Return>", lambda e: self.resize_editor())
        
        ttk.Label(toolbar_frame, text="Height:").pack(side=tk.LEFT, padx=2)
        self.height_var = tk.StringVar(value=str(self.editor_height))
        height_entry = ttk.Entry(toolbar_frame, textvariable=self.height_var, width=4)
        height_entry.pack(side=tk.LEFT, padx=2)
        height_entry.bind("<Return>", lambda e: self.resize_editor())
        
        ttk.Button(toolbar_frame, text="Resize", command=self.resize_editor).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        # Tool buttons
        self.tool_var = tk.StringVar(value="pen")
        ttk.Radiobutton(toolbar_frame, text="Pen", variable=self.tool_var, value="pen").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(toolbar_frame, text="Fill", variable=self.tool_var, value="fill").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(toolbar_frame, text="Picker", variable=self.tool_var, value="picker").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(toolbar_frame, text="(You can also pick colors directly from the reference image)").pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        # Current color display
        ttk.Label(toolbar_frame, text="Current Color:").pack(side=tk.LEFT, padx=2)
        self.color_preview = tk.Canvas(toolbar_frame, width=24, height=24, bg=self.current_color, highlightthickness=1)
        self.color_preview.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar_frame, text="Choose Color", command=self.choose_color).pack(side=tk.LEFT, padx=2)
        
        # C Array preview button
        ttk.Button(toolbar_frame, text="Preview C Array", command=self.show_c_array).pack(side=tk.RIGHT, padx=5)
        
        # Variable name entry for the C array
        ttk.Label(toolbar_frame, text="Variable Name:").pack(side=tk.RIGHT, padx=2)
        self.var_name = tk.StringVar(value="pixel_data")
        ttk.Entry(toolbar_frame, textvariable=self.var_name, width=15).pack(side=tk.RIGHT, padx=2)
        
        # Grid toggle
        self.show_grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(toolbar_frame, text="Show Grid", variable=self.show_grid_var, 
                        command=self.toggle_grid).pack(side=tk.RIGHT, padx=10)
    
    def create_main_frame(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Reference Image
        reference_frame = ttk.LabelFrame(main_frame, text="Reference Image")
        reference_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5, ipadx=5, ipady=5)
        
        # Canvas for the reference image
        self.reference_canvas = tk.Canvas(reference_frame, bg="#f0f0f0")
        self.reference_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Reference controls
        ref_controls = ttk.Frame(reference_frame)
        ref_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(ref_controls, text="Load Reference", command=self.load_reference).pack(side=tk.LEFT, padx=5)
        ttk.Button(ref_controls, text="Clear Reference", command=self.clear_reference).pack(side=tk.LEFT, padx=5)
        ttk.Button(ref_controls, text="Import to Editor", command=self.import_to_editor).pack(side=tk.LEFT, padx=5)
        
        # Reference canvas events for color picking
        self.reference_canvas.bind("<Button-1>", self.on_reference_click)
        
        # Middle panel - Editor
        editor_frame = ttk.LabelFrame(main_frame, text="Pixel Editor")
        editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for editing pixels
        self.canvas_frame = ttk.Frame(editor_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars for the canvas
        h_scrollbar = ttk.Scrollbar(editor_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        v_scrollbar = ttk.Scrollbar(editor_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.config(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # Canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows and macOS
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)    # Linux - scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)    # Linux - scroll down
        
        # Right panel - Tools and Preview
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Color palette
        palette_frame = ttk.LabelFrame(right_panel, text="Color Palette")
        palette_frame.pack(fill=tk.X, pady=5)
        
        self.palette_canvas = tk.Canvas(palette_frame, height=100, bg="white")
        self.palette_canvas.pack(fill=tk.X, padx=5, pady=5)
        self.palette_canvas.bind("<Button-1>", self.on_palette_click)
        
        # VGA Preview
        preview_frame = ttk.LabelFrame(right_panel, text="VGA Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.preview_canvas = tk.Canvas(preview_frame, bg="black")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # C Array Preview
        self.array_frame = ttk.LabelFrame(right_panel, text="C Array Preview")
        self.array_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Text widget for C array preview with scrollbars
        array_text_frame = ttk.Frame(self.array_frame)
        array_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.array_text = tk.Text(array_text_frame, height=10, wrap=tk.NONE, font=("Courier", 10))
        self.array_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        array_y_scroll = ttk.Scrollbar(array_text_frame, orient=tk.VERTICAL, command=self.array_text.yview)
        array_y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.array_text.config(yscrollcommand=array_y_scroll.set)
        
        array_x_scroll = ttk.Scrollbar(self.array_frame, orient=tk.HORIZONTAL, command=self.array_text.xview)
        array_x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.array_text.config(xscrollcommand=array_x_scroll.set)
        
        # Initialize reference image
        self.reference_image = None
        self.reference_photo = None
    
    def init_color_palette(self):
        # Define a set of predefined colors for the palette
        # Basic 16 VGA colors
        self.palette_colors = [
            "#000000", "#0000AA", "#00AA00", "#00AAAA", "#AA0000", "#AA00AA", "#AA5500", "#AAAAAA",
            "#555555", "#5555FF", "#55FF55", "#55FFFF", "#FF5555", "#FF55FF", "#FFFF55", "#FFFFFF"
        ]
        
        # Add more colors - common web colors
        web_colors = [
            "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#00FFFF", "#FF00FF",  # Primary & Secondary
            "#800000", "#008000", "#000080", "#808000", "#008080", "#800080",  # Darker versions
            "#FFA500", "#A52A2A", "#FFC0CB", "#DDA0DD", "#FF1493", "#00CED1",  # Various other colors
            "#1E90FF", "#FF6347", "#ADFF2F", "#32CD32"
        ]
        self.palette_colors.extend(web_colors)
        
        # Draw the palette
        self.draw_palette()
    
    def draw_palette(self):
        self.palette_canvas.delete("all")
        
        # Calculate the size and arrangement of color swatches
        palette_width = self.palette_canvas.winfo_width()
        if palette_width < 10:  # Not yet sized properly
            palette_width = 300  # Default width
            
        swatch_size = 20
        swatches_per_row = max(1, palette_width // swatch_size)
        
        # Draw each color swatch
        for i, color in enumerate(self.palette_colors):
            row = i // swatches_per_row
            col = i % swatches_per_row
            x1 = col * swatch_size
            y1 = row * swatch_size
            x2 = x1 + swatch_size
            y2 = y1 + swatch_size
            
            self.palette_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black", tags=("palette", color))
        
        # Update canvas size for scrolling
        rows_needed = (len(self.palette_colors) + swatches_per_row - 1) // swatches_per_row
        self.palette_canvas.config(height=min(100, rows_needed * swatch_size))
    
    def new_image(self):
        # Initialize a blank image with white pixels
        self.editor_width = int(self.width_var.get())
        self.editor_height = int(self.height_var.get())
        
        # Create a blank pixel data array (filled with white)
        self.pixel_data = np.ones((self.editor_height, self.editor_width, 3), dtype=np.uint8) * 255
        
        # Create a PIL Image from the pixel data
        self.edited_image = Image.fromarray(self.pixel_data.astype('uint8'))
        
        # Reset canvas and redraw
        self.setup_canvas()
        self.draw_editor()
        self.update_preview()
    
    def setup_canvas(self):
        # Set up the canvas for the current image size and zoom
        canvas_width = int(self.editor_width * self.cell_size * self.editor_zoom)
        canvas_height = int(self.editor_height * self.cell_size * self.editor_zoom)
        
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
    
    def draw_editor(self):
        self.canvas.delete("all")
        
        # Calculate cell size with zoom factor
        cell_size = int(self.cell_size * self.editor_zoom)
        
        # Draw each pixel from the data
        for y in range(self.editor_height):
            for x in range(self.editor_width):
                # Get the RGB values from the pixel data
                r, g, b = self.pixel_data[y, x]
                color = f"#{r:02x}{g:02x}{b:02x}"
                
                # Create a rectangle for this pixel
                x1 = x * cell_size
                y1 = y * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                # Draw the filled rectangle
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="", tags=("pixel", f"{x},{y}"))
        
        # Draw grid if enabled
        if self.show_grid_var.get():
            self.draw_grid()
    
    def draw_grid(self):
        cell_size = int(self.cell_size * self.editor_zoom)
        width = self.editor_width * cell_size
        height = self.editor_height * cell_size
        
        # Draw vertical grid lines
        for x in range(0, width + 1, cell_size):
            self.canvas.create_line(x, 0, x, height, fill="#cccccc", tags="grid")
        
        # Draw horizontal grid lines
        for y in range(0, height + 1, cell_size):
            self.canvas.create_line(0, y, width, y, fill="#cccccc", tags="grid")
    
    def toggle_grid(self):
        self.draw_editor()
    
    def set_zoom(self, zoom_level):
        # Limit zoom to reasonable values
        zoom_level = max(0.1, min(5.0, zoom_level))
        
        self.editor_zoom = zoom_level
        self.setup_canvas()
        self.draw_editor()
    
    def on_mouse_wheel(self, event):
        # Handle mouse wheel for zooming
        delta = 0
        
        # Different event formats on different platforms
        if event.num == 4:
            delta = 1
        elif event.num == 5:
            delta = -1
        else:
            delta = event.delta // 120
        
        # Zoom in or out
        new_zoom = self.editor_zoom * (1.1 if delta > 0 else 0.9)
        self.set_zoom(new_zoom)
    
    def on_canvas_click(self, event):
        # Get mouse coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Calculate pixel coordinates
        cell_size = int(self.cell_size * self.editor_zoom)
        x = int(canvas_x // cell_size)
        y = int(canvas_y // cell_size)
        
        # Check bounds
        if 0 <= x < self.editor_width and 0 <= y < self.editor_height:
            tool = self.tool_var.get()
            
            if tool == "pen":
                self.set_pixel(x, y)
            elif tool == "fill":
                self.fill_area(x, y)
            elif tool == "picker":
                self.pick_color(x, y)
    
    def on_canvas_drag(self, event):
        # Only respond to drag if the pen tool is active
        if self.tool_var.get() == "pen":
            # Get mouse coordinates
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            
            # Calculate pixel coordinates
            cell_size = int(self.cell_size * self.editor_zoom)
            x = int(canvas_x // cell_size)
            y = int(canvas_y // cell_size)
            
            # Check bounds
            if 0 <= x < self.editor_width and 0 <= y < self.editor_height:
                self.set_pixel(x, y)
    
    def on_palette_click(self, event):
        # Get mouse coordinates
        x = event.x
        y = event.y
        
        # Get color from palette canvas
        items = self.palette_canvas.find_overlapping(x, y, x, y)
        if items:
            tags = self.palette_canvas.gettags(items[0])
            for tag in tags:
                if tag.startswith("#"):
                    self.current_color = tag
                    self.color_preview.config(bg=self.current_color)
                    break
    
    def set_pixel(self, x, y):
        # Parse the current color to RGB values
        hex_color = self.current_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Ensure RGB values are in the correct range
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        # Update the pixel data
        self.pixel_data[y, x] = [r, g, b]
        
        # Calculate cell position in canvas
        cell_size = int(self.cell_size * self.editor_zoom)
        x1 = x * cell_size
        y1 = y * cell_size
        x2 = x1 + cell_size
        y2 = y1 + cell_size
        
        # Update the canvas pixel
        self.canvas.delete(f"pixel && {x},{y}")
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.current_color, outline="", tags=("pixel", f"{x},{y}"))
        
        # If grid is enabled, redraw the grid lines for this cell
        if self.show_grid_var.get():
            self.canvas.create_line(x1, y1, x1, y2, fill="#cccccc", tags="grid")
            self.canvas.create_line(x1, y1, x2, y1, fill="#cccccc", tags="grid")
            self.canvas.create_line(x2, y1, x2, y2, fill="#cccccc", tags="grid")
            self.canvas.create_line(x1, y2, x2, y2, fill="#cccccc", tags="grid")
        
        # Update the edited image
        self.edited_image = Image.fromarray(self.pixel_data.astype('uint8'))
        
        # Update the preview
        self.update_preview()
    
    def fill_area(self, start_x, start_y):
        # Get the color to replace
        orig_r, orig_g, orig_b = self.pixel_data[start_y, start_x]
        orig_color = (orig_r, orig_g, orig_b)
        
        # Parse the new color
        hex_color = self.current_color.lstrip('#')
        new_r, new_g, new_b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_color = [new_r, new_g, new_b]
        
        # If old and new colors are the same, do nothing
        if orig_color == tuple(new_color):
            return
        
        # Perform flood fill using a queue
        queue = [(start_x, start_y)]
        visited = set()
        
        while queue:
            x, y = queue.pop(0)
            
            # Skip if already visited or out of bounds
            if (x, y) in visited or x < 0 or y < 0 or x >= self.editor_width or y >= self.editor_height:
                continue
            
            # Skip if color doesn't match original
            if tuple(self.pixel_data[y, x]) != orig_color:
                continue
            
            # Mark as visited and set new color
            visited.add((x, y))
            self.pixel_data[y, x] = new_color
            
            # Add neighbors to queue
            queue.append((x+1, y))
            queue.append((x-1, y))
            queue.append((x, y+1))
            queue.append((x, y-1))
        
        # Redraw the editor
        self.draw_editor()
        
        # Update the edited image
        self.edited_image = Image.fromarray(self.pixel_data.astype('uint8'))
        
        # Update the preview
        self.update_preview()
    
    def pick_color(self, x, y):
        # Get the color from the pixel
        r, g, b = self.pixel_data[y, x]
        
        # Ensure RGB values are in the correct range
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        
        # Format as hex color
        picked_color = f"#{r:02x}{g:02x}{b:02x}"
        
        # Set as current color
        self.current_color = picked_color
        self.color_preview.config(bg=self.current_color)
        
        # Calculate 16-bit RGB565 value
        r5 = (r * 31) // 255
        g6 = (g * 63) // 255
        b5 = (b * 31) // 255
        color16 = (r5 << 11) | (g6 << 5) | b5
        
        # Show color info in title
        self.root.title(f"Pixel Editor - Color: {picked_color} RGB({r},{g},{b}) VGA: 0x{color16:04X}")
    
    def choose_color(self):
        color = colorchooser.askcolor(initialcolor=self.current_color)
        if color[1]:  # If a color was chosen (not canceled)
            self.current_color = color[1]
            self.color_preview.config(bg=self.current_color)
            
            # Parse RGB values
            hex_color = self.current_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            # Calculate 16-bit RGB565 value
            r5 = (r * 31) // 255
            g6 = (g * 63) // 255
            b5 = (b * 31) // 255
            color16 = (r5 << 11) | (g6 << 5) | b5
            
            # Show color info in title
            self.root.title(f"Pixel Editor - Color: {self.current_color} RGB({r},{g},{b}) VGA: 0x{color16:04X}")
    
    def clear_all(self):
        # Ask for confirmation
        if messagebox.askyesno("Clear All", "Are you sure you want to clear the entire image?"):
            # Reset pixel data to white
            self.pixel_data = np.ones((self.editor_height, self.editor_width, 3), dtype=np.uint8) * 255
            
            # Update the edited image
            self.edited_image = Image.fromarray(self.pixel_data.astype('uint8'))
            
            # Redraw editor and update preview
            self.draw_editor()
            self.update_preview()
    
    def resize_editor(self):
        try:
            new_width = int(self.width_var.get())
            new_height = int(self.height_var.get())
            
            # Ensure dimensions are within limits
            new_width = min(self.max_width, max(1, new_width))
            new_height = min(self.max_height, max(1, new_height))
            
            # Update the entries in case we clamped the values
            self.width_var.set(str(new_width))
            self.height_var.set(str(new_height))
            
            # Create a new pixel data array
            new_pixel_data = np.ones((new_height, new_width, 3), dtype=np.uint8) * 255
            
            # Copy over the existing pixel data, up to the new dimensions
            copy_height = min(self.editor_height, new_height)
            copy_width = min(self.editor_width, new_width)
            
            new_pixel_data[:copy_height, :copy_width] = self.pixel_data[:copy_height, :copy_width]
            
            # Update dimensions and pixel data
            self.editor_width = new_width
            self.editor_height = new_height
            self.pixel_data = new_pixel_data
            
            # Update the edited image
            self.edited_image = Image.fromarray(self.pixel_data.astype('uint8'))
            
            # Reset canvas and redraw
            self.setup_canvas()
            self.draw_editor()
            self.update_preview()
            
        except ValueError:
            messagebox.showerror("Error", "Width and height must be integers")
    
    def load_reference(self):
        """Load a reference image to use as a guide"""
        file_path = filedialog.askopenfilename(
            title="Open Reference Image",
            filetypes=(
                ("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
                ("All files", "*.*")
            )
        )
        
        if file_path:
            try:
                # Open the image with PIL
                self.reference_image = Image.open(file_path)
                
                # Display the reference image
                self.display_reference()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open reference image: {str(e)}")
    
    def on_reference_click(self, event):
        """Handle clicks on the reference image for color picking"""
        if self.reference_image is None:
            return
            
        try:
            # Get canvas dimensions and scale
            canvas_width = self.reference_canvas.winfo_width()
            canvas_height = self.reference_canvas.winfo_height()
            
            # Get reference image dimensions
            img_width, img_height = self.reference_image.size
            
            # Calculate the scaling and position of the image in the canvas
            ratio = min(canvas_width / img_width, canvas_height / img_height)
            display_width = int(img_width * ratio)
            display_height = int(img_height * ratio)
            
            # Calculate the position of the image in the canvas (centered)
            x_offset = (canvas_width - display_width) // 2
            y_offset = (canvas_height - display_height) // 2
            
            # Calculate the position in the image
            img_x = int((event.x - x_offset) / ratio)
            img_y = int((event.y - y_offset) / ratio)
            
            # Check if within image bounds
            if 0 <= img_x < img_width and 0 <= img_y < img_height:
                # Get the color at this position
                try:
                    # Convert image to RGB if needed
                    if self.reference_image.mode != "RGB":
                        ref_img = self.reference_image.convert("RGB")
                    else:
                        ref_img = self.reference_image
                        
                    # Get pixel color - ensure it's an RGB tuple
                    pixel = ref_img.getpixel((img_x, img_y))
                    if isinstance(pixel, tuple) and len(pixel) >= 3:
                        r, g, b = pixel[0], pixel[1], pixel[2]
                    else:
                        # Handle grayscale or other formats
                        r = g = b = pixel
                    
                    # Ensure values are in range
                    r = max(0, min(255, int(r)))
                    g = max(0, min(255, int(g)))
                    b = max(0, min(255, int(b)))
                    
                    # Format as hex color
                    picked_color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    # Set as current color
                    self.current_color = picked_color
                    self.color_preview.config(bg=self.current_color)
                    
                    # Calculate 16-bit RGB565 value
                    r5 = (r * 31) // 255
                    g6 = (g * 63) // 255
                    b5 = (b * 31) // 255
                    color16 = (r5 << 11) | (g6 << 5) | b5
                    
                    # Show a message about the picked color
                    self.root.title(f"Pixel Editor - Color: {picked_color} RGB({r},{g},{b}) VGA: 0x{color16:04X}")
                    
                    # Draw a small indicator on the canvas to show where color was picked from
                    self.reference_canvas.delete("indicator")
                    indicator_x = x_offset + img_x * ratio
                    indicator_y = y_offset + img_y * ratio
                    indicator_size = max(5, int(ratio))  # Make indicator visible but not too large
                    
                    # Draw a contrasting circle
                    contrast_color = "#FFFFFF" if (r + g + b) / 3 < 128 else "#000000"
                    self.reference_canvas.create_oval(
                        indicator_x - indicator_size, indicator_y - indicator_size,
                        indicator_x + indicator_size, indicator_y + indicator_size,
                        outline=contrast_color, width=2, tags="indicator"
                    )
                    
                except Exception as e:
                    print(f"Error picking color from pixel: {e}")
        except Exception as e:
            print(f"Error in reference click handler: {e}")
    
    def display_reference(self):
        """Display the reference image in the reference canvas"""
        if self.reference_image:
            # Get canvas dimensions
            canvas_width = self.reference_canvas.winfo_width()
            canvas_height = self.reference_canvas.winfo_height()
            
            if canvas_width < 10 or canvas_height < 10:  # Not yet sized properly
                # Use placeholder dimensions until the canvas is properly sized
                canvas_width = 300
                canvas_height = 300
            
            # Calculate display size maintaining aspect ratio
            img_width, img_height = self.reference_image.size
            ratio = min(canvas_width / img_width, canvas_height / img_height)
            display_width = int(img_width * ratio)
            display_height = int(img_height * ratio)
            
            # Create a copy of the reference image at the display size
            display_image = self.reference_image.copy()
            display_image = display_image.resize((display_width, display_height), Image.LANCZOS)
            
            # Convert to PhotoImage for display
            self.reference_photo = ImageTk.PhotoImage(display_image)
            
            # Clear canvas and display the image
            self.reference_canvas.delete("all")
            self.reference_canvas.create_image(
                canvas_width // 2, canvas_height // 2,  # Center of canvas
                image=self.reference_photo, anchor=tk.CENTER
            )
            
            # Add a status message
            self.reference_canvas.create_text(
                canvas_width // 2, canvas_height - 15,
                text="Click on image to pick colors - shows VGA and RGB values",
                fill="black", font=("Arial", 10)
            )
    
    def clear_reference(self):
        """Clear the reference image"""
        self.reference_image = None
        self.reference_canvas.delete("all")
    
    def import_to_editor(self):
        """Import the reference image into the pixel editor"""
        if not self.reference_image:
            messagebox.showinfo("Info", "No reference image loaded.")
            return
        
        # Ask user for dimensions
        dialog = tk.Toplevel(self.root)
        dialog.title("Import Options")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Import Dimensions:").pack(pady=(10, 5))
        
        # Dimension frame
        dim_frame = ttk.Frame(dialog)
        dim_frame.pack(pady=5)
        
        # Get reference image size
        ref_width, ref_height = self.reference_image.size
        
        # Limit to max size
        target_width = min(ref_width, self.max_width)
        target_height = min(ref_height, self.max_height)
        
        # Width entry
        ttk.Label(dim_frame, text="Width:").grid(row=0, column=0, padx=5)
        width_var = tk.StringVar(value=str(target_width))
        ttk.Entry(dim_frame, textvariable=width_var, width=5).grid(row=0, column=1, padx=5)
        
        # Height entry
        ttk.Label(dim_frame, text="Height:").grid(row=1, column=0, padx=5)
        height_var = tk.StringVar(value=str(target_height))
        ttk.Entry(dim_frame, textvariable=height_var, width=5).grid(row=1, column=1, padx=5)
        
        # Options
        option_frame = ttk.Frame(dialog)
        option_frame.pack(pady=5)
        
        dither_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(option_frame, text="Apply dithering", variable=dither_var).pack(anchor=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10, fill=tk.X)
        
        def on_import():
            try:
                width = int(width_var.get())
                height = int(height_var.get())
                dither = dither_var.get()
                
                # Ensure dimensions are within limits
                width = min(self.max_width, max(1, width))
                height = min(self.max_height, max(1, height))
                
                # Import the image
                self.do_import(width, height, dither)
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Width and height must be integers")
        
        ttk.Button(button_frame, text="Import", command=on_import).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def do_import(self, width, height, dither=False):
        """Perform the actual import"""
        # Resize the reference image to the specified dimensions
        resample_method = Image.LANCZOS
        if dither:
            # Use reduced quantizer for dithering
            resized = self.reference_image.resize((width, height), resample_method).convert(
                "P", palette=Image.ADAPTIVE, colors=16
            ).convert("RGB")
        else:
            resized = self.reference_image.resize((width, height), resample_method)
        
        # Update the editor dimensions
        self.editor_width = width
        self.editor_height = height
        self.width_var.set(str(width))
        self.height_var.set(str(height))
        
        # Update the pixel data
        self.pixel_data = np.array(resized)
        
        # Create a new edited image
        self.edited_image = Image.fromarray(self.pixel_data)
        
        # Reset canvas and redraw
        self.setup_canvas()
        self.draw_editor()
        self.update_preview()
    
    def import_c_array(self):
        """Import a C array and convert it back to an image for editing"""
        # Create a dialog for importing C array
        dialog = tk.Toplevel(self.root)
        dialog.title("Import C Array")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Array dimensions
        dim_frame = ttk.Frame(dialog, padding=10)
        dim_frame.pack(fill=tk.X)
        
        ttk.Label(dim_frame, text="Array Width:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        width_var = tk.StringVar(value="32")
        ttk.Entry(dim_frame, textvariable=width_var, width=8).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(dim_frame, text="Array Height:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        height_var = tk.StringVar(value="32")
        ttk.Entry(dim_frame, textvariable=height_var, width=8).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Text entry for the C array
        array_frame = ttk.LabelFrame(dialog, text="Paste C array data", padding=10)
        array_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Example text
        example_text = "Example format:\n{\n    {0xF800, 0x07E0, 0x001F},\n    {0xFFFF, 0x0000, 0x07FF}\n}\n\nPaste your array below:"
        ttk.Label(array_frame, text=example_text, font=("Courier", 10)).pack(anchor=tk.W, pady=(0, 10))
        
        # Text widget for pasting array
        text_frame = ttk.Frame(array_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        array_text = tk.Text(text_frame, wrap=tk.NONE, font=("Courier", 10))
        array_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        y_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=array_text.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        array_text.config(yscrollcommand=y_scroll.set)
        
        x_scroll = ttk.Scrollbar(array_frame, orient=tk.HORIZONTAL, command=array_text.xview)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        array_text.config(xscrollcommand=x_scroll.set)
        
        # Button frame
        button_frame = ttk.Frame(dialog, padding=10)
        button_frame.pack(fill=tk.X)
        
        def on_import():
            try:
                width = int(width_var.get())
                height = int(height_var.get())
                
                if width <= 0 or height <= 0 or width > self.max_width or height > self.max_height:
                    messagebox.showerror("Error", f"Dimensions must be between 1 and {self.max_width}x{self.max_height}")
                    return
                
                # Get array text
                array_data = array_text.get(1.0, tk.END).strip()
                
                # Parse and convert to image
                result = self.parse_c_array(array_data, width, height)
                if result:
                    dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Width and height must be integers")
        
        ttk.Button(button_frame, text="Import", command=on_import).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def parse_c_array(self, array_text, width, height):
        """Parse C array text and convert to image data
           Returns True if successful, False otherwise
        """
        try:
            # Remove all whitespace and newlines to simplify parsing
            array_text = ''.join(array_text.split())
            
            # Find the opening and closing braces of the main array
            start_idx = array_text.find('{')
            end_idx = array_text.rfind('}')
            
            if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
                messagebox.showerror("Error", "Invalid array format. Missing opening or closing braces.")
                return False
            
            # Extract the content between the main braces
            content = array_text[start_idx+1:end_idx].strip()
            
            # Split the content into rows (each enclosed by {})
            rows = []
            depth = 0
            start = 0
            
            for i, c in enumerate(content):
                if c == '{':
                    if depth == 0:
                        start = i + 1
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        rows.append(content[start:i])
            
            # Check if we got enough rows
            if len(rows) != height:
                if messagebox.askyesno("Warning", 
                                      f"Array has {len(rows)} rows but you specified {height} rows. Continue anyway?"):
                    # Adjust height to match actual data
                    height = len(rows)
                else:
                    return False
            
            # Parse each row into pixel values
            pixel_data = np.zeros((height, width, 3), dtype=np.uint8)
            
            for y, row in enumerate(rows[:height]):
                # Split the row by commas
                elements = row.split(',')
                
                # Check if we have enough elements
                if len(elements) != width:
                    if messagebox.askyesno("Warning", 
                                          f"Row {y+1} has {len(elements)} elements but you specified {width} columns. Continue anyway?"):
                        # Adjust width to match first row's data
                        if y == 0:
                            width = len(elements)
                            # Resize pixel_data
                            pixel_data = np.zeros((height, width, 3), dtype=np.uint8)
                    else:
                        return False
                
                # Process each element in the row
                for x, elem in enumerate(elements[:width]):
                    # Clean up the element and convert to int
                    elem = elem.strip()
                    
                    # Handle different formats (0xFFFF, 0xFF, etc.)
                    if elem.startswith('0x') or elem.startswith('0X'):
                        value = int(elem, 16)
                    else:
                        value = int(elem)
                    
                    # Convert from RGB565 (16-bit) to RGB888
                    r5 = (value >> 11) & 0x1F
                    g6 = (value >> 5) & 0x3F
                    b5 = value & 0x1F
                    
                    r8 = (r5 * 255) // 31
                    g8 = (g6 * 255) // 63
                    b8 = (b5 * 255) // 31
                    
                    # Store in pixel data
                    pixel_data[y, x] = [r8, g8, b8]
            
            # Update the editor dimensions
            self.editor_width = width
            self.editor_height = height
            self.width_var.set(str(width))
            self.height_var.set(str(height))
            
            # Update pixel data and image
            self.pixel_data = pixel_data
            self.edited_image = Image.fromarray(self.pixel_data.astype('uint8'))
            
            # Reset canvas and redraw
            self.setup_canvas()
            self.draw_editor()
            self.update_preview()
            
            messagebox.showinfo("Success", f"Successfully imported C array as {width}x{height} image")
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse C array: {str(e)}")
            print(f"Exception details: {e}")
            return False
                
    def update_preview(self):
        # Create a preview of the image for the VGA display
        if not hasattr(self, 'preview_canvas') or not self.edited_image:
            return
            
        self.preview_canvas.delete("all")
        
        # Calculate preview size
        preview_width = self.preview_canvas.winfo_width()
        preview_height = self.preview_canvas.winfo_height()
        
        if preview_width < 10 or preview_height < 10:  # Not yet sized properly
            preview_width = 150
            preview_height = 150
        
        # Calculate scaling to fit the canvas
        scale = min(preview_width / self.editor_width, preview_height / self.editor_height)
        display_width = int(self.editor_width * scale)
        display_height = int(self.editor_height * scale)
        
        # Resize the image for display
        display_img = self.edited_image.resize((display_width, display_height), Image.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(display_img)
        
        # Center the image in the canvas
        x_offset = (preview_width - display_width) // 2
        y_offset = (preview_height - display_height) // 2
        
        self.preview_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.preview_photo)
        
        # Generate the C array representation
        self.generate_c_array()
    
    def generate_c_array(self):
        # Convert the image pixels to 5R-6G-5B format for VGA
        if self.edited_image is None:
            return
        
        # Create output array for the 16-bit color values
        output_array = np.zeros((self.editor_height, self.editor_width), dtype=np.uint16)
        
        # Process each pixel
        for y in range(self.editor_height):
            for x in range(self.editor_width):
                r, g, b = self.pixel_data[y, x]
                
                # Ensure RGB values are in the correct range to avoid overflow
                r = max(0, min(255, int(r)))
                g = max(0, min(255, int(g)))
                b = max(0, min(255, int(b)))
                
                # Convert to 5-6-5 format
                r5 = (r * 31) // 255  # 5 bits (0-31)
                g6 = (g * 63) // 255  # 6 bits (0-63)
                b5 = (b * 31) // 255  # 5 bits (0-31)
                
                # Combine into 16-bit color
                color16 = (r5 << 11) | (g6 << 5) | b5
                output_array[y, x] = color16
        
        # Store the array data
        self.vga_array = output_array
    
    def show_c_array(self):
        # Display the C array in the text widget
        if not hasattr(self, 'vga_array'):
            messagebox.showinfo("Info", "No image data available.")
            return
        
        # Generate C array code
        var_name = self.var_name.get().strip()
        if not var_name:
            var_name = "pixel_data"
        
        # Create header
        c_code = f"// VGA Image Data - {self.editor_width}x{self.editor_height} - 16-bit color (5R-6G-5B)\n"
        c_code += f"// Generated by Pixel Editor\n\n"
        c_code += f"#define IMAGE_WIDTH {self.editor_width}\n"
        c_code += f"#define IMAGE_HEIGHT {self.editor_height}\n\n"
        c_code += f"const unsigned short {var_name}[IMAGE_HEIGHT][IMAGE_WIDTH] = {{\n"
        
        # Add array data
        for y in range(self.editor_height):
            c_code += "    {"
            for x in range(self.editor_width):
                c_code += f"0x{self.vga_array[y, x]:04X}"
                if x < self.editor_width - 1:
                    c_code += ", "
            c_code += "}"
            if y < self.editor_height - 1:
                c_code += ",\n"
            else:
                c_code += "\n"
        
        c_code += "};\n\n"
        
        
        
        # Display in the text widget
        self.array_text.delete(1.0, tk.END)
        self.array_text.insert(tk.END, c_code)
        
    def save_c_array(self):
        # Save the C array to a file
        if not hasattr(self, 'vga_array'):
            messagebox.showinfo("Info", "No image data available.")
            return
        
        # First make sure the C array is generated
        self.show_c_array()
        
        # Ask for file path
        file_path = filedialog.asksaveasfilename(
            title="Save C Array",
            defaultextension=".c",
            filetypes=(
                ("C files", "*.c"),
                ("Header files", "*.h"),
                ("All files", "*.*")
            )
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.array_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"C array saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PixelEditorApp(root)
    
    # Update palette on window resize
    def on_window_resize(event):
        app.draw_palette()
    
    root.bind("<Configure>", on_window_resize)
    
    root.mainloop()
