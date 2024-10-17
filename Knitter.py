import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
import json
import copy

class KnittingPatternApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Knitting Pattern Designer")
        self.master.geometry("1040x400")

        self.selected_color = "#aabbcc"
        self.default_width = 32
        self.default_height = 16
        self.max_width = 128
        self.max_height = 128
        self.cell_size = 24

        self.history = []
        self.redo_stack = []
        self.resize_timer = None

        self.create_controls()
        self.bind_shortcuts()
        self.generate_grid(self.default_width, self.default_height)

    def create_controls(self):
        control_frame = tk.Frame(self.master)
        control_frame.grid(row=0, column=0, sticky="ns")

        self.create_save_load_controls(control_frame)
        self.create_grid_controls(control_frame)
        self.create_history_controls(control_frame)
        self.create_grid_resize_controls(control_frame)
        self.create_zoom_controls(control_frame)
        self.create_color_controls(control_frame)

        self.canvas = tk.Canvas(self.master, bg='white')
        self.canvas.grid(row=0, column=1, sticky="nsew")

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1) 

        self.master.grid_rowconfigure(1, weight=0)

    def create_save_load_controls(self, parent):
        save_load_frame = tk.Frame(parent)
        save_load_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        save_load_frame.columnconfigure([0, 1], weight=1)

        buttons = [
            ("Save Pattern", self.save_pattern),
            ("Load Pattern", self.load_pattern),
        ]
        for i, (text, cmd) in enumerate(buttons):
            tk.Button(save_load_frame, text=text, command=cmd).grid(row=0, column=i, sticky="nsew")

    def create_grid_controls(self, parent):
        tk.Label(parent, text="Grid Width: (Max 128)").grid(row=1, column=0)
        self.width_entry = tk.Entry(parent)
        self.width_entry.grid(row=1, column=1)

        tk.Label(parent, text="Grid Height: (Max 128)").grid(row=2, column=0)
        self.height_entry = tk.Entry(parent)
        self.height_entry.grid(row=2, column=1)

        tk.Button(parent, text="Generate Grid", command=self.handle_generate_grid).grid(row=3, column=0, columnspan=2, sticky="ew")

    def create_history_controls(self, parent):
        history_frame = tk.Frame(parent)
        history_frame.grid(row=5, column=0, columnspan=2, sticky="ew")
        history_frame.columnconfigure([0, 1], weight=1)

        buttons = [
            ("Undo", self.undo),
            ("Redo", self.redo),
        ]
        for i, (text, cmd) in enumerate(buttons):
            tk.Button(history_frame, text=text, command=cmd).grid(row=0, column=i, sticky="nsew")

    def create_grid_resize_controls(self, parent):
        arrow_frame = tk.Frame(parent)
        arrow_frame.grid(row=6, column=0, columnspan=2)

        directions = [
            ("↑", lambda: self.modify_grid("add", "row", "top"), 0, 1),
            ("↓", lambda: self.modify_grid("add", "row", "bottom"), 2, 1),
            ("←", lambda: self.modify_grid("add", "column", "left"), 1, 0),
            ("→", lambda: self.modify_grid("add", "column", "right"), 1, 2)
        ]
        for text, cmd, row, col in directions:
            tk.Button(arrow_frame, text=text, command=cmd).grid(row=row, column=col)

        tk.Label(arrow_frame, text="+").grid(row=1, column=1)

        remove_controls = [
            ("↓", lambda: self.modify_grid("remove", "row", "top"), 0, 5),
            ("↑", lambda: self.modify_grid("remove", "row", "bottom"), 2, 5),
            ("→", lambda: self.modify_grid("remove", "column", "left"), 1, 4),
            ("←", lambda: self.modify_grid("remove", "column", "right"), 1, 6)
        ]
        for text, cmd, row, col in remove_controls:
            tk.Button(arrow_frame, text=text, command=cmd).grid(row=row, column=col)

        tk.Label(arrow_frame, text="-").grid(row=1, column=5)
        tk.Label(arrow_frame, text="Add/Rem").grid(row=1, column=3)

        self.grid_dimensions_label = tk.Label(parent, text=f"Grid Dimensions: {self.default_width} x {self.default_height}")
        self.grid_dimensions_label.grid(row=7, column=0, columnspan=2)

    def create_color_controls(self, parent):
        color_frame = tk.Frame(parent)
        color_frame.grid(row=9, column=0, columnspan=2, sticky="ew")

        self.choose_color_button = tk.Button(color_frame, text="Choose Color", bg=self.selected_color, command=self.choose_color)
        self.choose_color_button.pack(fill=tk.X, expand=True)

        palette_frame = tk.Frame(color_frame)
        palette_frame.pack(fill=tk.X, expand=True)
        self.create_color_palette(palette_frame)

    def create_color_palette(self, parent):
        colors = [
            ['#EB9DA2', '#F0B884', '#E8E6A5', '#BBE8B5', '#ACBBE8', '#C5ACE8'],  # Lightest
            ['#D07479', '#D9975A', '#C6C474', '#85C688', '#889BDE', '#A183D5'],  # Mid-tone
            ['#B15A5E', '#B87C3D', '#A2A455', '#669E6B', '#6678B3', '#7E5CAD']   # Dark-tone
        ]

        
        for row_index, row_colors in enumerate(colors):
            for col_index, color in enumerate(row_colors):
                tk.Button(parent, bg=color, command=lambda c=color: self.set_color(c))\
                    .grid(row=row_index, column=col_index, sticky="nsew")
                parent.grid_columnconfigure(col_index, weight=1)


    def create_zoom_controls(self, parent):
        zoom_frame = tk.Frame(parent)
        zoom_frame.grid(row=8, column=0, columnspan=2, sticky="ew")

        zoom_in_button = tk.Button(zoom_frame, text="Zoom In", command=self.zoom_in)
        zoom_in_button.grid(row=0, column=0, sticky="nsew")

        zoom_out_button = tk.Button(zoom_frame, text="Zoom Out", command=self.zoom_out)
        zoom_out_button.grid(row=0, column=1, sticky="nsew")

        zoom_to_fit_button = tk.Button(zoom_frame, text="Zoom to Fit", command=self.zoom_to_fit)
        zoom_to_fit_button.grid(row=1, column=0, columnspan=2, sticky="nsew")

        zoom_frame.columnconfigure([0, 1], weight=1)

    def set_color(self, color):
        self.selected_color = color
        self.choose_color_button.config(bg=color)

    def bind_shortcuts(self):
        self.master.bind("<Control-s>", lambda e: self.save_pattern())
        self.master.bind("<Control-z>", lambda e: self.undo())
        self.master.bind("<Control-y>", lambda e: self.redo())
        self.master.bind("<Control-r>", lambda e: self.reset_grid())
        self.master.bind("<Control-plus>", lambda e: self.zoom_in())
        self.master.bind("<Control-minus>", lambda e: self.zoom_out())

    def zoom_in(self):
        if self.cell_size < 50:
            self.cell_size += 2
            self.refresh_canvas()
            self.update_grid_dimensions_label()

    def zoom_out(self):
        if self.cell_size > 5:
            self.cell_size -= 2
            self.refresh_canvas()
            self.update_grid_dimensions_label()

    def zoom_to_fit(self):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        max_cell_size_width = canvas_width // self.grid_width
        max_cell_size_height = canvas_height // self.grid_height

        optimal_cell_size = min(max_cell_size_width, max_cell_size_height)

        self.cell_size = max(5, optimal_cell_size)

        self.refresh_canvas()
        self.update_grid_dimensions_label()

    def choose_color(self):
        color = colorchooser.askcolor(title="Choose color")[1]
        if color:
            self.set_color(color)

    def handle_generate_grid(self):
        try:
            width = int(self.width_entry.get()) if self.width_entry.get() else self.default_width
            height = int(self.height_entry.get()) if self.height_entry.get() else self.default_height
            if width > 0 and height > 0 and width <= self.max_width and height <= self.max_height:
                self.generate_grid(width, height)
            else:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid positive integers for grid dimensions (max 128x128).")

    def generate_grid(self, width, height):
        self.grid_width = width
        self.grid_height = height

        canvas_width = self.grid_width * self.cell_size
        canvas_height = self.grid_height * self.cell_size

        if hasattr(self, 'canvas'):
            self.canvas.destroy()

        self.canvas = tk.Canvas(self.master, bg='white', width=canvas_width, height=canvas_height)
        self.canvas.grid(row=0, column=1, sticky="nsew")

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1)

        self.cells = {}

        for row in range(self.grid_height):
            for col in range(self.grid_width):
                x1, y1 = col * self.cell_size, row * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                cell_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black")
                self.cells[(row, col)] = "white"

        self.canvas.bind("<Button-1>", self.toggle_cell)

        self.grid_dimensions_label.config(text=f"Grid Dimensions: {self.grid_width} x {self.grid_height}")

        self.update_grid_dimensions_label()

    def toggle_cell(self, event):
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        if 0 <= col < self.grid_width and 0 <= row < self.grid_height:
            current_color = self.cells[(row, col)]
            new_color = self.selected_color if current_color == "white" else "white"
            self.canvas.itemconfig(self.get_canvas_id(row, col), fill=new_color)
            self.cells[(row, col)] = new_color
            self.save_state_to_history()

    def get_canvas_id(self, row, col):
        return self.canvas.find_closest(col * self.cell_size + 1, row * self.cell_size + 1)[0]

    def reset_grid(self):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset the grid?"):
            for row in range(self.grid_height):
                for col in range(self.grid_width):
                    self.canvas.itemconfig(self.get_canvas_id(row, col), fill="white")
                    self.cells[(row, col)] = "white"
            self.save_state_to_history()

    def save_pattern(self):
        pattern = {
            "width": self.grid_width,
            "height": self.grid_height,
            "selected_color": self.selected_color,
            "cells": {f"{row},{col}": color for (row, col), color in self.cells.items()}
        }
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(pattern, file)

    def load_pattern(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    pattern = json.load(file)

                self.selected_color = pattern.get("selected_color", self.selected_color)
                self.choose_color_button.config(bg=self.selected_color)
                width = pattern.get("width", self.default_width)
                height = pattern.get("height", self.default_height)

                self.generate_grid(width, height)

                for key, color in pattern.get("cells", {}).items():
                    row, col = map(int, key.split(','))
                    if (row, col) in self.cells:
                        self.canvas.itemconfig(self.get_canvas_id(row, col), fill=color)
                        self.cells[(row, col)] = color

                self.save_state_to_history()
            except json.JSONDecodeError as e:
                messagebox.showerror("Invalid File", f"Failed to load the pattern. The file is not valid JSON.\nError: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def save_state_to_history(self):
        state = {
            "width": self.grid_width,
            "height": self.grid_height,
            "cells": copy.deepcopy(self.cells)
        }
        self.history.append(state)
        self.redo_stack.clear()

    def undo(self):
        if len(self.history) > 1:
            self.redo_stack.append(self.history.pop())
            self.restore_from_history(self.history[-1])

    def redo(self):
        if self.redo_stack:
            next_state = self.redo_stack.pop()
            self.history.append(next_state)
            self.restore_from_history(next_state)

    def restore_from_history(self, state):
        self.grid_width = state["width"]
        self.grid_height = state["height"]
        self.cells = copy.deepcopy(state["cells"])
        self.refresh_canvas()

    def modify_grid(self, operation, axis, position):
        if axis == "row":
            if operation == "add":
                if position == "top":
                    for row in reversed(range(self.grid_height)):
                        for col in range(self.grid_width):
                            self.cells[(row + 1, col)] = self.cells.pop((row, col))
                    for col in range(self.grid_width):
                        self.cells[(0, col)] = "white"
                elif position == "bottom":
                    for col in range(self.grid_width):
                        self.cells[(self.grid_height, col)] = "white"
                self.grid_height += 1

            elif operation == "remove" and self.grid_height > 1:
                if position == "top":
                    for col in range(self.grid_width):
                        del self.cells[(0, col)]
                    for row in range(1, self.grid_height):
                        for col in range(self.grid_width):
                            self.cells[(row - 1, col)] = self.cells.pop((row, col))
                elif position == "bottom":
                    for col in range(self.grid_width):
                        del self.cells[(self.grid_height - 1, col)]
                self.grid_height -= 1

        elif axis == "column":
            if operation == "add":
                if position == "left":
                    for row in range(self.grid_height):
                        for col in reversed(range(self.grid_width)):
                            self.cells[(row, col + 1)] = self.cells.pop((row, col))
                    for row in range(self.grid_height):
                        self.cells[(row, 0)] = "white"
                elif position == "right":
                    for row in range(self.grid_height):
                        self.cells[(row, self.grid_width)] = "white"
                self.grid_width += 1

            elif operation == "remove" and self.grid_width > 1:
                if position == "left":
                    for row in range(self.grid_height):
                        del self.cells[(row, 0)]
                    for row in range(self.grid_height):
                        for col in range(1, self.grid_width):
                            self.cells[(row, col - 1)] = self.cells.pop((row, col))
                elif position == "right":
                    for row in range(self.grid_height):
                        del self.cells[(row, self.grid_width - 1)]
                self.grid_width -= 1

        self.refresh_canvas()
        self.update_grid_dimensions_label()
        self.save_state_to_history()

    def refresh_canvas(self):
        self.canvas.delete("all")
        for row in range(self.grid_height):
            for col in range(self.grid_width):
                x1, y1 = col * self.cell_size, row * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                cell_color = self.cells.get((row, col), "white")
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=cell_color, outline="black")

        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
    def update_grid_dimensions_label(self):
        zoom_level = (self.cell_size / 20) * 100
        self.grid_dimensions_label.config(text=f"Grid Dimensions: {self.grid_width} x {self.grid_height} | Zoom: {int(zoom_level)}%")

if __name__ == "__main__":
    root = tk.Tk()
    app = KnittingPatternApp(root)
    root.mainloop()