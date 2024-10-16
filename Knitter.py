import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
import json
import copy

class KnittingPatternApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Knitting Pattern Designer")
        self.master.geometry("800x400")

        self.selected_color = "#aabbcc"
        self.default_width = 16
        self.default_height = 16
        self.max_width = 128
        self.max_height = 128

        self.history = []
        self.redo_stack = []
        self.resize_timer = None

        self.create_controls()
        self.bind_shortcuts()
        self.generate_grid(self.default_width, self.default_height)


    def create_controls(self):
        control_frame = tk.Frame(self.master)
        control_frame.grid(row=0, column=0, rowspan=2, sticky="ns")

        self.create_save_load_controls(control_frame)
        self.create_grid_controls(control_frame)
        self.create_history_controls(control_frame)
        self.create_grid_resize_controls(control_frame)
        self.create_color_controls(control_frame)

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
        tk.Button(parent, text="Reset Grid", command=self.reset_grid).grid(row=4, column=0, columnspan=2, sticky="ew")

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
        color_frame.grid(row=8, column=0, columnspan=2, sticky="ew")

        self.choose_color_button = tk.Button(color_frame, text="Choose Color", bg=self.selected_color, command=self.choose_color)
        self.choose_color_button.pack(fill=tk.X, expand=True)

        palette_frame = tk.Frame(color_frame)
        palette_frame.pack(fill=tk.X, expand=True)
        self.create_color_palette(palette_frame)

    def create_color_palette(self, parent):
        colors = ['#EB9DA2', '#F0B884', '#E8E6A5', '#BBE8B5', '#ACBBE8', '#C5ACE8']
        for i, color in enumerate(colors):
            tk.Button(parent, bg=color, command=lambda c=color: self.set_color(c))\
                .grid(row=0, column=i, sticky="nsew")
            parent.grid_columnconfigure(i, weight=1)

    def set_color(self, color):
        self.selected_color = color
        self.choose_color_button.config(bg=color)

    def bind_shortcuts(self):
        self.master.bind("<Control-s>", lambda e: self.save_pattern())
        self.master.bind("<Control-z>", lambda e: self.undo())
        self.master.bind("<Control-y>", lambda e: self.redo())
        self.master.bind("<Control-r>", lambda e: self.reset_grid())

    def choose_color(self):
        color = colorchooser.askcolor(title="Choose color")[1]
        if color:
            self.set_color(color)

    def handle_generate_grid(self):
        try:
            width = int(self.width_entry.get()) if self.width_entry.get() else self.default_width
            height = int(self.height_entry.get()) if self.height_entry.get() else self.default_height
            if width > 0 and height > 0 and width <= self.max_width and height <= self.max_height:
                self.resize_grid_preserve_state(width, height)
            else:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid positive integers for grid dimensions (max 128x128).")

    def generate_grid(self, width, height):
        if hasattr(self, 'grid_frame'):
            self.grid_frame.destroy()

        self.grid_frame = tk.Frame(self.master)
        self.grid_frame.grid(row=0, column=1, rowspan=3, sticky="nsew")

        self.master.grid_rowconfigure(3, weight=1)
        self.master.grid_columnconfigure(1, weight=1)

        self.cells = {}
        self.grid_width = width
        self.grid_height = height

        for row in range(height):
            for col in range(width):
                cell = tk.Button(self.grid_frame, command=lambda r=row, c=col: self.toggle_cell(r, c))
                cell.grid(row=row, column=col, sticky='nsew')
                self.cells[(row, col)] = cell

        for row in range(height):
            self.grid_frame.rowconfigure(row, weight=1)
        for col in range(width):
            self.grid_frame.columnconfigure(col, weight=1)

        self.update_grid_dimensions_label()
        self.save_state_to_history()

    def resize_grid_preserve_state(self, new_width, new_height):
        old_width, old_height = self.grid_width, self.grid_height
        old_cells = self.cells.copy()

        self.generate_grid(new_width, new_height)

        for row in range(min(old_height, new_height)):
            for col in range(min(old_width, new_width)):
                if (row, col) in old_cells:
                    self.cells[(row, col)].config(bg=old_cells[(row, col)].cget('bg'))

    def toggle_cell(self, row, col):
        if (row, col) in self.cells:
            cell = self.cells[(row, col)]
            cell.config(bg=self.selected_color if cell.cget("bg") != self.selected_color else "SystemButtonFace")
            self.save_state_to_history()

    def reset_grid(self):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset the grid?"):
            for cell in self.cells.values():
                cell.config(bg="SystemButtonFace")
            self.save_state_to_history()

    def save_pattern(self):
        pattern = {
            "width": self.grid_width,
            "height": self.grid_height,
            "selected_color": self.selected_color,
            "cells": {str((row, col)): cell["bg"] for (row, col), cell in self.cells.items()}
        }
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(pattern, file)

    def load_pattern(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as file:
                pattern = json.load(file)

            self.selected_color = pattern.get("selected_color", self.selected_color)
            self.choose_color_button.config(bg=self.selected_color)
            self.generate_grid(pattern.get("width", self.default_width), pattern.get("height", self.default_height))

            for key, color in pattern.get("cells", {}).items():
                row, col = eval(key)
                if (row, col) in self.cells:
                    self.cells[(row, col)].config(bg=color)

            self.save_state_to_history()

    def save_state_to_history(self):
        state = {
            "cells": {str((row, col)): cell.cget("bg") for (row, col), cell in self.cells.items()}
        }
        self.history.append(copy.deepcopy(state))
        self.redo_stack.clear()

    def undo(self):
        if len(self.history) > 1:
            self.redo_stack.append(self.history.pop())
            self.load_grid_from_state(self.history[-1])

    def redo(self):
        if self.redo_stack:
            next_state = self.redo_stack.pop()
            self.history.append(next_state)
            self.load_grid_from_state(next_state)

    def load_grid_from_state(self, state):
        for key, color in state["cells"].items():
            row, col = eval(key)
            if (row, col) in self.cells:
                self.cells[(row, col)].config(bg=color)

    def modify_grid(self, operation, axis, position):
        if axis == "row":
            if operation == "add":
                if position == "top":
                    for row in reversed(range(self.grid_height)):
                        for col in range(self.grid_width):
                            if (row, col) in self.cells:
                                self.cells[(row + 1, col)] = self.cells.pop((row, col))
                                self.cells[(row + 1, col)].grid(row=row + 1, column=col)
                    for col in range(self.grid_width):
                        cell = tk.Button(self.grid_frame, command=lambda r=0, c=col: self.toggle_cell(r, c))
                        cell.grid(row=0, column=col, sticky='nsew')
                        self.cells[(0, col)] = cell
                else:
                    for col in range(self.grid_width):
                        cell = tk.Button(self.grid_frame, command=lambda r=self.grid_height, c=col: self.toggle_cell(r, c))
                        cell.grid(row=self.grid_height, column=col, sticky='nsew')
                        self.cells[(self.grid_height, col)] = cell
                self.grid_height += 1
            elif operation == "remove" and self.grid_height > 1:
                if position == "top":
                    for col in range(self.grid_width):
                        if (0, col) in self.cells:
                            self.cells[(0, col)].destroy()
                            del self.cells[(0, col)]
                    for row in range(1, self.grid_height):
                        for col in range(self.grid_width):
                            if (row, col) in self.cells:
                                self.cells[(row - 1, col)] = self.cells.pop((row, col))
                                self.cells[(row - 1, col)].grid(row=row - 1, column=col)
                elif position == "bottom":
                    for col in range(self.grid_width):
                        if (self.grid_height - 1, col) in self.cells:
                            self.cells[(self.grid_height - 1, col)].destroy()
                            del self.cells[(self.grid_height - 1, col)]
                self.grid_height -= 1
        elif axis == "column":
            if operation == "add":
                if position == "left":
                    for row in range(self.grid_height):
                        for col in reversed(range(self.grid_width)):
                            if (row, col) in self.cells:
                                self.cells[(row, col + 1)] = self.cells.pop((row, col))
                                self.cells[(row, col + 1)].grid(row=row, column=col + 1)
                    for row in range(self.grid_height):
                        cell = tk.Button(self.grid_frame, command=lambda r=row, c=0: self.toggle_cell(r, c))
                        cell.grid(row=row, column=0, sticky='nsew')
                        self.cells[(row, 0)] = cell
                else:
                    for row in range(self.grid_height):
                        cell = tk.Button(self.grid_frame, command=lambda r=row, c=self.grid_width: self.toggle_cell(r, c))
                        cell.grid(row=row, column=self.grid_width, sticky='nsew')
                        self.cells[(row, self.grid_width)] = cell
                self.grid_width += 1
            elif operation == "remove" and self.grid_width > 1:
                if position == "left":
                    for row in range(self.grid_height):
                        if (row, 0) in self.cells:
                            self.cells[(row, 0)].destroy()
                            del self.cells[(row, 0)]
                    for row in range(self.grid_height):
                        for col in range(1, self.grid_width):
                            if (row, col) in self.cells:
                                self.cells[(row, col - 1)] = self.cells.pop((row, col))
                                self.cells[(row, col - 1)].grid(row=row, column=col - 1)
                elif position == "right":
                    for row in range(self.grid_height):
                        if (row, self.grid_width - 1) in self.cells:
                            self.cells[(row, self.grid_width - 1)].destroy()
                            del self.cells[(row, self.grid_width - 1)]
                self.grid_width -= 1

        self.reindex_cells()
        self.update_grid_dimensions_label()
        self.save_state_to_history()

    def reindex_cells(self):
        for (row, col), cell in self.cells.items():
            cell.config(command=lambda r=row, c=col: self.toggle_cell(r, c))

    def update_grid_dimensions_label(self):
        self.grid_dimensions_label.config(text=f"Grid Dimensions: {self.grid_width} x {self.grid_height}")

if __name__ == "__main__":
    root = tk.Tk()
    app = KnittingPatternApp(root)
    root.mainloop()