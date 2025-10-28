import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

class ScaleAndCropApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Scale and Crop to 1632x2912")
        self.original_image = None
        self.processed_image = None

        # Default target size
        self.target_width = tk.IntVar(value=1632)
        self.target_height = tk.IntVar(value=2912)

        self.create_widgets()

    def create_widgets(self):
        # Frame for dimension entries and buttons
        control_frame = tk.Frame(self.master)
        control_frame.pack(padx=10, pady=10, fill=tk.X)

        tk.Label(control_frame, text="Target Width:").grid(row=0, column=0, sticky=tk.W)
        self.width_entry = tk.Entry(control_frame, textvariable=self.target_width, width=8)
        self.width_entry.grid(row=0, column=1, padx=5)

        tk.Label(control_frame, text="Target Height:").grid(row=0, column=2, sticky=tk.W)
        self.height_entry = tk.Entry(control_frame, textvariable=self.target_height, width=8)
        self.height_entry.grid(row=0, column=3, padx=5)

        btn_frame = tk.Frame(control_frame)
        btn_frame.grid(row=1, column=0, columnspan=4, pady=(10,0))
        tk.Button(btn_frame, text="Open Image", command=self.open_image).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Process", command=self.process_image).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Save Image", command=self.save_image).pack(side=tk.LEFT, padx=5)

        # Canvas for preview
        self.canvas = tk.Canvas(self.master, bg="gray", width=500, height=500)
        self.canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def open_image(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        try:
            with Image.open(filepath) as opened_image:
                self.original_image = opened_image.copy()
            self.display_preview(self.original_image)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image:\n{e}")

    def process_image(self):
        if not self.original_image:
            messagebox.showwarning("No Image", "Please open an image first.")
            return

        tw = self.target_width.get()
        th = self.target_height.get()
        if tw <= 0 or th <= 0:
            messagebox.showerror("Invalid Dimensions", "Target dimensions must be positive integers.")
            return

        # 1) Scale so that the final height = target_height.
        orig_w, orig_h = self.original_image.size
        scale_factor = th / orig_h
        new_w = int(orig_w * scale_factor)
        new_h = th  # exactly target height

        scaled_img = self.original_image.resize((new_w, new_h), Image.LANCZOS)

        # 2) If scaled width is bigger than target width, we crop the center to get exactly target_width.
        #    If for some reason scaled width is smaller, we can letterbox or do a partial fill, but
        #    in your case, the new_w > tw scenario is expected.
        if new_w >= tw:
            # Center-crop horizontally
            left = (new_w - tw) // 2
            right = left + tw
            top = 0
            bottom = new_h
            final_img = scaled_img.crop((left, top, right, bottom))
        else:
            # (Optional) If new_w < tw, we can paste onto a background.
            # But in your example, it's typically not needed. We'll do it just in case.
            background = Image.new("RGB", (tw, th), "black")
            x_offset = (tw - new_w) // 2
            background.paste(scaled_img, (x_offset, 0))
            final_img = background

        self.processed_image = final_img
        self.display_preview(final_img)

    def display_preview(self, img):
        # Fit image to canvas
        canvas_w = self.canvas.winfo_width() or 500
        canvas_h = self.canvas.winfo_height() or 500
        img_ratio = img.width / img.height
        canvas_ratio = canvas_w / canvas_h

        if img_ratio > canvas_ratio:
            preview_w = canvas_w
            preview_h = int(canvas_w / img_ratio)
        else:
            preview_h = canvas_h
            preview_w = int(canvas_h * img_ratio)

        preview = img.resize((preview_w, preview_h), Image.LANCZOS)
        self.tk_preview = ImageTk.PhotoImage(preview)
        self.canvas.delete("all")
        self.canvas.create_image(canvas_w // 2, canvas_h // 2, image=self.tk_preview, anchor=tk.CENTER)

    def save_image(self):
        if not self.processed_image:
            messagebox.showwarning("No Processed Image", "Please process an image before saving.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg;*.jpeg"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        try:
            self.processed_image.save(filepath)
            messagebox.showinfo("Saved", f"Image saved to:\n{os.path.abspath(filepath)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScaleAndCropApp(root)
    root.mainloop()
